#!/usr/bin/env python
"""
手动运行 get_person_dialog_list() 函数
"""

import asyncio
import datetime
from jd.utils.logging_config import get_logger
import os
from zoneinfo import ZoneInfo

from jCelery import celery
from jd import app, db
from jd.models.tg_account import TgAccount
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.services.spider.tg import TgService
from jd.services.spider.telegram_spider import TelegramAPIs
from jd.tasks.telegram.tg import fetch_group_user_info

logger = get_logger('jd.jobs.tg.person_dialog', {'component': 'telegram', 'module': 'person_dialog'})


class PersonDialogJob:

    async def fetch_chat_history(self, tg, group_name, chat_id, chat_type='group'):
        """获取聊天历史记录"""
        chat_id = int(chat_id)
        try:
            chat = await tg.get_dialog(chat_id)
        except Exception as e:
            logger.info(f'{group_name}, 未获取到群组，准备重新加入...{e}')
            chat = None
        
        if not chat:
            result = await tg.join_conversation(group_name)
            chat_id = result.get('data', {}).get('id', 0)
            if not chat_id:
                logger.info(f'{group_name}, 未获取到群组id')
                return
            chat = await tg.get_dialog(chat_id)
            if not chat:
                logger.info(f'{group_name}, 未加入到到群组')
                return
        
        param = {
            "limit": 60,
            "last_message_id": -1,
        }
        
        history_list = []
        async for data in tg.scan_message(chat, **param):
            history_list.append(data)
        
        history_list.reverse()
        message_id_list = [str(data.get("message_id", 0)) for data in history_list if data.get("message_id", 0)]
        msg = TgGroupChatHistory.query.filter(TgGroupChatHistory.message_id.in_(message_id_list),
                                              TgGroupChatHistory.chat_id == str(chat_id)).all()
        old_msg_info = {d.message_id: d for d in msg}
        
        for data in history_list:
            logger.debug(f'chat history data:{data}')
            message_id = str(data.get("message_id", 0))
            if message_id in old_msg_info:
                old_msg: TgGroupChatHistory = old_msg_info[message_id]
                new_photo_path = data.get("photo", {}).get('file_path', '')
                if new_photo_path and new_photo_path != old_msg.photo_path:
                    TgGroupChatHistory.query.filter(TgGroupChatHistory.id == old_msg.id).update(
                        {'photo_path': new_photo_path}
                    )
                    db.session.commit()
                continue
                
            user_id = str(data.get("user_id", 0))
            nickname = data.get("nick_name", "")

            obj = TgGroupChatHistory(
                chat_id=str(chat_id),
                message_id=message_id,
                nickname=nickname,
                username=data.get("user_name", ""),
                user_id=user_id,
                postal_time=data.get("postal_time", datetime.datetime.now()) + datetime.timedelta(hours=8),
                message=data.get("message", ""),
                reply_to_msg_id=str(data.get("reply_to_msg_id", 0)),
                photo_path=data.get("photo", {}).get('file_path', ''),
                document_path=data.get("document", {}).get('file_path', ''),
                document_ext=data.get("document", {}).get('ext', ''),
                replies_info=data.get('replies_info', '')
            )
            db.session.add(obj)
            db.session.commit()
            
        # 获取用户信息
        if chat_type == 'group':
            for data in history_list:
                user_id = str(data.get("user_id", 0))
                nickname = data.get("nick_name", "")
                username = data.get("user_name", "")
                if not username:
                    continue
                fetch_group_user_info.delay(chat_id, user_id, nickname, username)

    async def get_person_dialog_list(self, tg):
        """获取私人对话列表并处理聊天历史"""
        logger.info("开始获取私人对话列表...")
        try:
            chat_list = await tg.get_person_dialog_list()
            logger.info(f"获取到 {len(chat_list)} 个私人对话")
            
            for chat in chat_list:
                logger.info(f"处理私人对话: {chat}")
                await self.fetch_chat_history(tg, '私人聊天', chat['id'], chat_type='person')
                
        except Exception as e:
            logger.error(f"获取私人对话列表失败: {e}")
            raise

    async def main(self):
        """主函数"""
        logger.info("初始化 Telegram 服务...")
        tg = await TgService.init_tg('job')
        if not tg:
            logger.error('Telegram 连接失败')
            return
            
        try:
            logger.info("开始执行私人对话列表获取...")
            with tg.client:
                tg.client.loop.run_until_complete(self.get_person_dialog_list(tg))
            logger.info("私人对话列表获取完成")
            
        except Exception as e:
            logger.error(f"执行过程中出现错误: {e}")
            raise
        finally:
            logger.info("关闭 Telegram 客户端")
            tg.close_client()


@celery.task
def fetch_person_chat_history(account_id, origin='celery'):
    """
    获取指定账户的个人聊天记录
    """
    logger.info(f'开始获取账户 {account_id} 的个人聊天记录')
    tg_account = TgAccount.query.filter(TgAccount.id == account_id).first()
    if not tg_account:
        logger.error(f'账户 {account_id} 不存在')
        return

    tg = TelegramAPIs()
    session_dir = f'{app.static_folder}/utils'
    session_name = f'{session_dir}/{tg_account.name}-telegram.session'
    logger.info(f'使用session文件: {tg_account.name}-telegram.session')
    if not os.path.exists(session_name):
        logger.warning(f'Session文件不存在: {session_name}')
    else:
        logger.info(f'Session文件存在: {session_name}')
    try:
        logger.info(f'开始初始化Telegram客户端，账户: {tg_account.name}')
        tg.init_client(
            session_name=session_name, api_id=tg_account.api_id, api_hash=tg_account.api_hash
        )
        logger.info(f'Telegram客户端初始化成功，账户: {tg_account.name}')
    except Exception as e:
        logger.error(f'Telegram客户端初始化失败，账户: {tg_account.name}, 错误: {e}')
        return

    group_id_list = []

    async def get_person_dialog_list():
        async for chat_info in tg.get_dialog_list():
            temp_data = chat_info.get('data', {})
            _chat_id = temp_data.get('id', 0)
            if not _chat_id:
                logger.info(f'account, {account_id}, chat_id is empty, data:{temp_data}')
                continue

            group_id_list.append(_chat_id)

    async def get_chat_history_list(chat_id):
        param = {
            "limit": 60,
            # "offset_date": datetime.datetime.now() - datetime.timedelta(hours=8) - datetime.timedelta(minutes=20),
            "last_message_id": -1,
        }
        logger.info(f'account:{account_id}, 开始获取群组：{chat_id}，记录')

        try:
            chat = await tg.get_dialog(chat_id)
        except Exception as e:
            logger.info(f'chat_id:{chat_id}, 未获取到群组...{e}')
            return
        history_list = []
        async for data in tg.scan_message(chat, **param):
            history_list.append(data)
        history_list.reverse()
        message_id_list = [str(data.get("message_id", 0)) for data in history_list if data.get("message_id", 0)]
        msg = TgGroupChatHistory.query.filter(TgGroupChatHistory.message_id.in_(message_id_list),
                                              TgGroupChatHistory.chat_id == str(chat_id)).all()
        already_message_id_list = [data.message_id for data in msg]
        for data in history_list:
            user_id = data.get("user_id", 0)
            if user_id == 777000:
                # 客服
                continue
            message_id = str(data.get("message_id", 0))
            if message_id in already_message_id_list:
                continue
            logger.info(f'fetch_person_chat_history data:{data}')
            user_id = str(user_id)
            nickname = data.get("nick_name", "")

            obj = TgGroupChatHistory(
                chat_id=str(chat_id),
                message_id=message_id,
                nickname=nickname,
                username=data.get("user_name", ""),
                user_id=user_id,
                postal_time=data.get("postal_time", datetime.datetime.now(ZoneInfo('UTC'))).replace(tzinfo=None) + datetime.timedelta(hours=8),
                message=data.get("message", ""),
                reply_to_msg_id=str(data.get("reply_to_msg_id", 0)),
                photo_path=data.get("photo", {}).get('file_path', ''),
                document_path=data.get("document", {}).get('file_path', ''),
                document_ext=data.get("document", {}).get('ext', ''),
                replies_info=data.get('replies_info', '')
            )
            db.session.add(obj)
        db.session.commit()

    with tg.client:
        tg.client.loop.run_until_complete(get_person_dialog_list())

    try:
        for chat_id in group_id_list:
            with tg.client:
                tg.client.loop.run_until_complete(get_chat_history_list(chat_id))
    finally:
        if tg:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(tg.close_client())
                loop.close()
            except Exception as close_error:
                logger.error(f'关闭TG客户端失败: {close_error}')
    
    logger.info(f'账户 {account_id} 的个人聊天记录获取完成')


def run():
    job = PersonDialogJob()
    job.main()