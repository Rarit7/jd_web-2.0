#!/usr/bin/env python
"""
私人聊天记录获取任务
使用BaseTgHistoryFetcher基类，保持与群组聊天一致的架构
接入BaseTask系统，提供队列管理和冲突检测
"""

import asyncio
import datetime
from typing import Dict, Any
from zoneinfo import ZoneInfo

from jCelery import celery
from jd import app, db
from jd.utils.logging_config import get_logger
from jd.models.tg_account import TgAccount
from jd.models.tg_person_chat_history import TgPersonChatHistory
from jd.jobs.tg_base_history_fetcher import BaseTgHistoryFetcher
from jd.tasks.base_task import AsyncBaseTask

logger = get_logger('jd.jobs.tg.person_dialog', {
    'component': 'telegram',
    'module': 'person_dialog'
})


class PersonChatHistoryFetcher(BaseTgHistoryFetcher):
    """私人聊天记录获取器，继承自BaseTgHistoryFetcher"""

    def __init__(self, account_id: int):
        super().__init__()
        self.account_id = account_id
        self.account = None
        self.owner_user_id = None

    def _load_account_info(self):
        """加载账户信息"""
        self.account = TgAccount.query.filter_by(id=self.account_id).first()
        if not self.account:
            raise Exception(f'账户不存在: {self.account_id}')

        if not self.account.user_id:
            raise Exception(f'账户未登录或user_id为空: {self.account_id}')

        self.owner_user_id = self.account.user_id
        logger.info(f'加载账户信息|账户ID={self.account_id}|用户ID={self.owner_user_id}|Session={self.account.name}')

    async def get_private_dialog_list(self):
        """获取私人对话列表"""
        logger.info(f'开始获取私人对话列表|账户ID={self.account_id}')

        try:
            # 使用专门的个人对话获取方法
            person_dialogs = await self.tg.get_person_dialog_list()

            dialog_list = []
            for dialog_data in person_dialogs:
                chat_id = dialog_data.get('id', 0) or dialog_data.get('user_id', 0)
                username = dialog_data.get('username', '')

                if chat_id:
                    dialog_list.append({
                        'chat_id': chat_id,
                        'title': username or str(chat_id),  # 使用username作为title，或使用ID
                        'username': username,
                    })
                    logger.info(f'✓ 找到私人对话|chat_id={chat_id}|username={username}')

            logger.info(f'获取到 {len(dialog_list)} 个私人对话')
            return dialog_list

        except Exception as e:
            logger.error(f'获取私人对话列表失败: {e}')
            raise

    async def process_message_batch(self, batch_messages, chat_id: int, batch_num: int, peer_user_id: str) -> int:
        """
        重写批量处理消息方法，保存到tg_person_chat_history表

        Args:
            batch_messages: 消息列表
            chat_id: 聊天ID
            batch_num: 批次号
            peer_user_id: 对方用户ID

        Returns:
            保存的消息数量
        """
        if not batch_messages:
            return 0

        try:
            # 1. 批量检查重复消息
            message_ids = [str(msg.get("message_id", 0)) for msg in batch_messages if msg.get("message_id")]
            existing_ids = set()

            if message_ids:
                existing_records = TgPersonChatHistory.query.filter(
                    TgPersonChatHistory.message_id.in_(message_ids),
                    TgPersonChatHistory.chat_id == str(chat_id),
                    TgPersonChatHistory.owner_user_id == self.owner_user_id  # 使用业务ID
                ).with_entities(TgPersonChatHistory.message_id).all()
                existing_ids = {record.message_id for record in existing_records}

            # 2. 过滤重复和无效消息
            valid_messages = []
            for data in batch_messages:
                message_id = str(data.get("message_id", 0))
                user_id = data.get("user_id", 0)

                if (message_id and message_id != "0" and
                    message_id not in existing_ids and
                    user_id != 777000):  # 过滤系统消息
                    valid_messages.append(data)

            if not valid_messages:
                logger.debug(f'第 {batch_num} 批次|无有效消息')
                return 0

            # 3. 批量创建私聊消息对象（优化版：使用业务ID和sender_type）
            chat_objects = []
            for data in valid_messages:
                sender_user_id = str(data.get("user_id", 0))

                # 判断发送方类型：比较sender_user_id和owner_user_id
                if sender_user_id == self.owner_user_id:
                    sender_type = 'owner'
                else:
                    sender_type = 'peer'

                obj = TgPersonChatHistory(
                    chat_id=str(chat_id),
                    message_id=str(data.get("message_id", 0)),
                    owner_user_id=self.owner_user_id,  # 使用业务ID
                    owner_session_name=self.account.name if self.account else '',  # Session名称
                    peer_user_id=peer_user_id,
                    sender_type=sender_type,  # 使用枚举类型
                    postal_time=self._process_postal_time(data.get("postal_time")),
                    message=self._safe_str(data.get("message", "")),
                    reply_to_msg_id=str(data.get("reply_to_msg_id", 0)),
                    photo_path=data.get("photo", {}).get('file_path', ''),
                    document_path=data.get("document", {}).get('file_path', ''),
                    document_ext=data.get("document", {}).get('ext', ''),
                    replies_info=self._safe_str(data.get('replies_info', ''))
                )
                chat_objects.append(obj)

            # 4. 批量插入
            if chat_objects:
                db.session.add_all(chat_objects)
                db.session.commit()

            logger.info(f'第 {batch_num} 批次|保存 {len(chat_objects)} 条私聊消息')
            return len(chat_objects)

        except Exception as e:
            if db.session.in_transaction():
                db.session.rollback()
            logger.error(f'第 {batch_num} 批次|保存私聊消息失败: {e}')
            return 0

    async def fetch_private_chat_history(self, chat_id: int, peer_user_id: str, limit: int = 100):
        """
        获取单个私聊的历史记录

        Args:
            chat_id: 聊天ID
            peer_user_id: 对方用户ID
            limit: 每批次获取数量
        """
        logger.info(f'开始获取私聊历史|chat_id={chat_id}|peer={peer_user_id}')

        try:
            # 获取dialog
            chat = await self.tg.get_dialog(chat_id)
            if not chat:
                logger.warning(f'无法获取私聊dialog|chat_id={chat_id}')
                return 0

            # 获取历史记录参数
            param = {
                "limit": limit,
                "last_message_id": -1,
            }

            batch_messages = []
            batch_num = 0
            total_saved_count = 0

            # 获取消息
            async for data in self.tg.scan_message(chat, **param):
                batch_messages.append(data)

                # 每批次处理
                if len(batch_messages) >= limit:
                    batch_num += 1
                    saved_count = await self.process_message_batch(
                        batch_messages, chat_id, batch_num, peer_user_id
                    )
                    total_saved_count += saved_count
                    batch_messages = []

                    # 添加小延迟
                    await asyncio.sleep(0.5)

            # 处理剩余消息
            if batch_messages:
                batch_num += 1
                saved_count = await self.process_message_batch(
                    batch_messages, chat_id, batch_num, peer_user_id
                )
                total_saved_count += saved_count

            logger.info(f'私聊历史获取完成|chat_id={chat_id}|保存={total_saved_count}条')
            return total_saved_count

        except Exception as e:
            logger.error(f'获取私聊历史失败|chat_id={chat_id}: {e}')
            return 0

    async def process_all_private_chats(self):
        """处理所有私人对话"""
        try:
            # 1. 加载账户信息
            self._load_account_info()

            # 2. 初始化TG服务
            session_names = self.get_sessionnames_by_accountid(self.account_id)
            if not session_names:
                session_names = [self.account.name]

            success = await self.init_telegram_service(session_names)
            if not success:
                raise Exception('Telegram服务初始化失败')

            # 3. 获取私人对话列表
            dialog_list = await self.get_private_dialog_list()

            # 保存对话数量供外部使用
            self.dialog_count = len(dialog_list)

            # 4. 逐个处理私聊
            total_count = 0
            for dialog in dialog_list:
                chat_id = dialog['chat_id']
                # 对于私聊，peer_user_id就是chat_id
                peer_user_id = str(chat_id)

                saved_count = await self.fetch_private_chat_history(chat_id, peer_user_id)
                total_count += saved_count

            logger.info(f'所有私聊处理完成|总保存={total_count}条')
            return True, total_count

        except Exception as e:
            logger.error(f'处理私聊失败: {e}')
            return False, 0
        finally:
            # 关闭连接
            await self.close_telegram_service()


class FetchPersonChatHistoryTask(AsyncBaseTask):
    """私人聊天记录获取任务（基于 BaseTask）"""

    def __init__(self, account_id: int):
        """
        初始化私人聊天历史获取任务

        Args:
            account_id: TG账户ID
        """
        # 从数据库加载账户信息以获取 session_name
        account = TgAccount.query.filter_by(id=account_id).first()
        if not account:
            raise Exception(f'账户不存在: {account_id}')

        session_name = account.name or 'default'

        # resource_id 使用 person_chat_{account_id}，防止同一账户的任务冲突
        # session_id 使用 session_name，防止同一 session 的任务冲突
        resource_id = f"person_chat_{account_id}"
        super().__init__(
            resource_id=resource_id,
            session_id=session_name
        )

        self.account_id = account_id
        self.account = account
        # 冲突时进入等待队列
        self.wait_if_conflict = True

    def get_job_name(self) -> str:
        return 'fetch_person_chat_history'

    def generate_result_summary(self, result: Dict[str, Any]) -> str:
        """生成私人聊天历史获取任务的友好结果摘要"""
        if not result:
            return "任务完成，无结果数据"

        err_code = result.get('err_code', 0)
        if err_code != 0:
            return f"任务失败: {result.get('err_msg', '未知错误')}"

        payload = result.get('payload', {})
        if not payload:
            return "任务成功"

        # 提取统计信息
        account_id = payload.get('account_id', self.account_id)
        message_count = payload.get('message_count', 0)
        dialog_count = payload.get('dialog_count', 0)
        duration = payload.get('duration_seconds', 0)

        # 格式化持续时间
        if duration >= 60:
            duration_text = f"{duration/60:.1f}分钟"
        else:
            duration_text = f"{duration:.1f}秒"

        # 构建结果摘要
        if message_count > 0:
            return f"账户 {account_id} 私聊历史获取成功，处理 {dialog_count} 个对话，保存 {message_count} 条消息，耗时 {duration_text}"
        else:
            return f"账户 {account_id} 私聊历史获取完成，{dialog_count} 个对话无新消息，耗时 {duration_text}"

    async def execute_async_task(self) -> Dict[str, Any]:
        """执行私人聊天历史获取任务"""
        start_time = datetime.datetime.now(ZoneInfo('UTC'))
        logger.info(f'开始私人聊天历史获取任务|账户ID={self.account_id}')

        try:
            # 创建 fetcher 实例
            fetcher = PersonChatHistoryFetcher(self.account_id)

            # 执行获取任务
            success, count = await fetcher.process_all_private_chats()
            end_time = datetime.datetime.now(ZoneInfo('UTC'))

            # 获取对话数量（从 fetcher 中）
            dialog_count = getattr(fetcher, 'dialog_count', 0) if hasattr(fetcher, 'dialog_count') else 0

            if success:
                logger.info(f'私人聊天历史获取任务完成|账户ID={self.account_id}|保存={count}条')
                return {
                    'err_code': 0,
                    'err_msg': '',
                    'payload': {
                        'status': 'completed',
                        'success': True,
                        'account_id': self.account_id,
                        'message_count': count,
                        'dialog_count': dialog_count,
                        'start_time': start_time.isoformat(),
                        'end_time': end_time.isoformat(),
                        'duration_seconds': (end_time - start_time).total_seconds(),
                        'session_name': self.session_id
                    }
                }
            else:
                error_msg = f'私人聊天历史获取任务失败|账户ID={self.account_id}'
                logger.error(error_msg)
                return {
                    'err_code': 1,
                    'err_msg': error_msg,
                    'payload': {
                        'status': 'failed',
                        'success': False,
                        'account_id': self.account_id,
                        'message_count': count,
                        'dialog_count': dialog_count,
                        'start_time': start_time.isoformat(),
                        'end_time': end_time.isoformat(),
                        'duration_seconds': (end_time - start_time).total_seconds(),
                        'session_name': self.session_id
                    }
                }

        except Exception as e:
            end_time = datetime.datetime.now(ZoneInfo('UTC'))
            error_msg = f'私人聊天历史获取任务异常|账户ID={self.account_id}: {e}'
            logger.error(error_msg)
            return {
                'err_code': 1,
                'err_msg': error_msg,
                'payload': {
                    'status': 'error',
                    'success': False,
                    'account_id': self.account_id,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': (end_time - start_time).total_seconds(),
                    'session_name': self.session_id,
                    'exception': str(e)
                }
            }


@celery.task(name='jd.tasks.telegram.fetch_person_chat_history')
def fetch_person_chat_history(account_id: int):
    """
    Celery任务：获取指定账户的私人聊天记录（使用 BaseTask 架构）

    Args:
        account_id: TG账户ID
    """
    task = FetchPersonChatHistoryTask(account_id)
    return task.start_task()


def run():
    """命令行运行入口"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python -m jd.jobs.tg_person_dialog <account_id>")
        sys.exit(1)

    account_id = int(sys.argv[1])

    # 使用with app.app_context()确保数据库连接正常
    with app.app_context():
        fetch_person_chat_history(account_id)


if __name__ == '__main__':
    run()
