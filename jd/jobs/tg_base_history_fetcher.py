import datetime
import logging
import signal
import asyncio
from typing import Dict, Any
from zoneinfo import ZoneInfo

from jd import db
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group import TgGroup
from jd.models.tg_group_session import TgGroupSession
from jd.models.tg_group_status import TgGroupStatus
from jd.services.spider.tg import TgService
from jd.jobs.tg_user_info import TgUserInfoProcessor


logger = logging.getLogger(__name__)

# 全局变量用于跟踪活跃的TG连接
_active_connections = []

def _cleanup_connections():
    """清理所有活跃的Telegram连接"""
    for connection in _active_connections:
        try:
            if connection.tg and connection.tg.client:
                # 在同步上下文中运行异步清理
                loop = None
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                loop.run_until_complete(connection.close_telegram_service())
        except Exception as e:
            logger.error(f'清理Telegram连接时发生错误: {e}')
    _active_connections.clear()

# 注册信号处理器
signal.signal(signal.SIGTERM, lambda signum, frame: _cleanup_connections())
signal.signal(signal.SIGINT, lambda signum, frame: _cleanup_connections())


class BaseTgHistoryFetcher:
    """Telegram聊天历史获取基类，提供通用功能"""
    
    def __init__(self):
        self.tg = None
        self.user_processor = None
        # 将此实例添加到活跃连接列表中
        _active_connections.append(self)
    
    async def init_telegram_service(self, sessionnames) -> bool:
        """初始化Telegram服务，使用带重试机制的初始化"""
        # 如果传入的是字符串，转换为列表
        if isinstance(sessionnames, str):
            sessionnames = [sessionnames] if sessionnames else []
        
        self.tg = await TgService.init_tg_with_retry(sessionnames)
        if not self.tg:
            logger.error(f'Session列表：{sessionnames} Telegram服务初始化失败')
            return False
        self.user_processor = TgUserInfoProcessor(self.tg)
        # 清空用户处理器的缓存
        self.user_processor.clear_batch_cache()
        logger.info(f'Telegram服务初始化成功，使用session列表: {sessionnames}')
        return True
    
    async def close_telegram_service(self) -> None:
        """关闭Telegram服务，确保完全释放连接避免数据库锁定"""
        if self.tg:
            try:
                await self.tg.close_client()
            except Exception as e:
                logger.error(f'关闭Telegram客户端时发生错误: {e}')
            finally:
                self.tg = None
                self.user_processor = None
        
        # 从活跃连接列表中移除
        try:
            _active_connections.remove(self)
        except ValueError:
            pass  # 如果不在列表中，忽略错误
    
    async def get_dialog_with_retry(self, chat_id: int, group_name: str):
        """获取dialog，失败时尝试加入群组"""
        chat = await self.tg.get_dialog(chat_id, is_more=True)
        if not chat:
            logger.info(f'群组 {group_name} dialog获取失败, 尝试加入群组')
            result = await self.tg.join_conversation(group_name)
            new_chat_id = result.get('data', {}).get('id', 0)
            if not new_chat_id:
                logger.error(f'加入群组失败: {group_name} 找不到chat_id')
                return None, chat_id
            chat_id = new_chat_id
            chat = await self.tg.get_dialog(chat_id)
            if not chat:
                logger.error(f'加入群组失败: {group_name} 无法获取dialog')
                return None, chat_id
        return chat, chat_id
    
    async def _save_chat_message(self, data: Dict[str, Any], chat_id: int) -> bool:
        """保存聊天消息到数据库"""
        message_id = str(data.get("message_id", 0))
        if not message_id or message_id == "0":
            return False
        
        # 防止重复保存
        existing = TgGroupChatHistory.query.filter_by(
            message_id=message_id, 
            chat_id=str(chat_id)
        ).first()
        
        if existing:
            return False
        
        # 跳过tg服务消息
        user_id = data.get("user_id", 0)
        if user_id == 777000:  # Telegram service
            return False
        
        try:
            # 安全转换函数
            def safe_str(value):
                if value is None:
                    return ""
                elif isinstance(value, dict):
                    import json
                    json_str = json.dumps(value, ensure_ascii=False)
                    return json_str[:500] + "..." if len(json_str) > 500 else json_str
                elif isinstance(value, (list, tuple)):
                    return str(value)[:500] + "..." if len(str(value)) > 500 else str(value)
                else:
                    return str(value)
            
            # 保存聊天记录，确保所有参数都是字符串类型
            obj = TgGroupChatHistory(
                chat_id=str(chat_id),
                message_id=message_id,
                nickname=safe_str(data.get("nick_name", "")),
                username=safe_str(data.get("user_name", "")),
                user_id=str(user_id),
                postal_time=data.get("postal_time", datetime.datetime.now(ZoneInfo('UTC'))).replace(tzinfo=None) + datetime.timedelta(hours=8),
                message=safe_str(data.get("message", "")),
                reply_to_msg_id=str(data.get("reply_to_msg_id", 0)),
                photo_path=data.get("photo", {}).get('file_path', ''),
                document_path=data.get("document", {}).get('file_path', ''),
                document_ext=data.get("document", {}).get('ext', ''),
                replies_info=safe_str(data.get('replies_info', ''))
            )
            db.session.add(obj)
            
            # 同时保存发言人信息到用户信息表
            await self.user_processor.save_user_info_from_message(data, chat_id)
            
            return True
            
        except Exception as e:
            logger.error(f'写入消息失败 {message_id}: {e}')
            return False
    
    def get_sessionnames_by_accountid(self, account_id):
        """从tg_group_session获取session名称列表，按account_id升序排序"""
        try:
            sessions = TgGroupSession.query.filter_by(user_id=str(account_id)).order_by(TgGroupSession.user_id.asc()).all()
            session_names = [session.session_name for session in sessions if session.session_name]
            
            return session_names if session_names else []
            
        except Exception as e:
            logger.error(f'获取session名称失败: {account_id}: {e}')
            return []
        
    def get_sessionnames_by_chatid(self, chat_id):
        """从tg_group_session获取session名称列表，按account_id升序排序"""
        try:
            sessions = TgGroupSession.query.filter_by(chat_id=str(chat_id)).order_by(TgGroupSession.user_id.asc()).all()
            session_names = [session.session_name for session in sessions if session.session_name]
            
            return session_names if session_names else []
            
        except Exception as e:
            logger.error(f'根据chat_id获取session名称失败: {chat_id}: {e}')
            return []
    
    def get_chat_room_list(self):
        """从tg_group获取join_success状态的群组列表,返回结果按account_id升序排序"""
        # TODO
        try:
            groups = TgGroup.query.filter_by(status=TgGroup.StatusType.JOIN_SUCCESS).all()
            chat_room_list = []
            for group in groups:
                chat_room_list.append((group.name, int(group.chat_id), group.account_id))
            return chat_room_list
        except Exception as e:
            logger.error(f'获取聊天室列表失败: {e}')
            return []
    
    async def process_message_batch(self, batch_messages, chat_id: int, batch_num: int) -> int:
        """处理消息批次，返回保存的消息数量"""
        if not batch_messages:
            return 0
        
        # 批量预处理用户信息缓存
        if self.user_processor:
            try:
                await self.user_processor.prepare_batch_user_cache(batch_messages, chat_id)
                logger.debug(f'第 {batch_num} 批次用户缓存预处理完成，消息数={len(batch_messages)}')
            except Exception as e:
                logger.error(f'批量用户缓存预处理失败: {e}')
        
        batch_saved_count = 0
        for data in batch_messages:
            if await self._save_chat_message(data, chat_id):
                batch_saved_count += 1
        
        # 提交当前批次
        db.session.commit()
        logger.info(f'第 {batch_num} 批次获取 新增 {batch_saved_count} 条消息')
        
        return batch_saved_count
    

    def update_group_status(self, chat_id: int):
        """写完数据库后,更新tg_group_status表中的字段,更新消息记录数、最早消息日期和ID、最新消息日期和ID"""
        try:
            chat_id_str = str(chat_id)
            
            # 获取或创建群组状态记录
            status = TgGroupStatus.query.filter_by(chat_id=chat_id_str).first()
            if not status:
                status = TgGroupStatus(chat_id=chat_id_str)
                db.session.add(status)
            
            # previous字段由每日备份任务统一更新，这里不再修改
            
            # 更新消息记录数
            current_records = TgGroupChatHistory.query.filter_by(chat_id=chat_id_str).count()
            status.records_now = current_records
            
            # 更新最早消息日期和ID
            earliest_message = TgGroupChatHistory.query.filter_by(
                chat_id=chat_id_str
            ).order_by(TgGroupChatHistory.postal_time.asc()).first()
            
            if earliest_message:
                status.first_record_date = earliest_message.postal_time
                status.first_record_id = earliest_message.message_id
            
            # 更新最新消息日期和ID
            latest_message = TgGroupChatHistory.query.filter_by(
                chat_id=chat_id_str
            ).order_by(TgGroupChatHistory.postal_time.desc()).first()
            
            if latest_message:
                status.last_record_date = latest_message.postal_time
                status.last_record_id = latest_message.message_id
            
            db.session.commit()
            logger.info(f'更新群组状态成功|{chat_id}|记录数: {status.records_previous} -> {status.records_now}')
            
        except Exception as e:
            logger.error(f'更新群组状态失败|{chat_id}: {e}')
            db.session.rollback() 