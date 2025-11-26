import datetime
import signal
import asyncio
from zoneinfo import ZoneInfo
from sqlalchemy import func

from jd import db
from jd.utils.logging_config import get_logger, PerformanceLogger, async_log_performance
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group import TgGroup
from jd.models.tg_group_session import TgGroupSession
from jd.models.tg_group_status import TgGroupStatus
from jd.services.spider.tg import TgService
from jd.jobs.tg_user_info import TgUserInfoProcessor


logger = get_logger('jd.jobs.tg.base_history_fetcher', {
    'component': 'telegram',
    'module': 'history_fetcher'
})

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
signal.signal(signal.SIGTERM, lambda _signum, _frame: _cleanup_connections())
signal.signal(signal.SIGINT, lambda _signum, _frame: _cleanup_connections())


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
        # 首先确保用户处理器的待写入记录被提交
        if self.user_processor:
            try:
                self.user_processor._flush_pending_changes()
            except Exception as e:
                logger.error(f'关闭时提交用户处理器待写入记录失败: {e}')

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
    
    async def get_dialog_with_retry(self, chat_id: int, group_name: str = None):
        """获取dialog，失败时尝试加入群组（如果提供了有效的group_name）"""
        chat = await self.tg.get_dialog(chat_id, is_more=True)
        if not chat:
            # 检查group_name是否有效
            if group_name and group_name.strip():
                logger.info(f'chat_id {chat_id} (群组 {group_name}) dialog获取失败, 尝试加入群组')
                try:
                    result = await self.tg.join_conversation(group_name)
                    new_chat_id = result.get('data', {}).get('id', 0)
                    if not new_chat_id:
                        logger.error(f'加入群组失败: {group_name} 找不到chat_id')
                        # 加入失败，标记群组为失效
                        self._mark_group_as_invalid_link(chat_id, group_name, f'加入群组失败: 找不到chat_id')
                        return None, chat_id
                    chat_id = new_chat_id
                    chat = await self.tg.get_dialog(chat_id)
                    if not chat:
                        logger.error(f'加入群组失败: {group_name} 无法获取dialog')
                        # 获取dialog失败，标记群组为失效
                        self._mark_group_as_invalid_link(chat_id, group_name, f'加入群组后无法获取dialog')
                        return None, chat_id
                    else:
                        logger.info(f'成功加入群组 {group_name} 并获取dialog')
                except Exception as e:
                    logger.error(f'尝试加入群组 {group_name} 时发生错误: {e}')
                    # 加入异常，标记群组为失效
                    self._mark_group_as_invalid_link(chat_id, group_name, f'加入群组异常: {str(e)}')
                    return None, chat_id
            else:
                logger.warning(f'chat_id {chat_id} 获取失败且group_name无效 ("{group_name}")，无法自动加入群组')
                logger.info(f'建议检查：1) 账户是否已加入该群组 2) 群组是否仍然存在 3) 群组权限设置')
                # 更新群组状态为失败
                self._update_group_status_if_failed(chat_id, group_name or f"chat_id_{chat_id}")
                return None, chat_id
        else:
            logger.debug(f'成功获取 chat_id {chat_id} 的dialog')
        return chat, chat_id
    
    def _update_group_status_if_failed(self, chat_id: int, group_name: str):
        """当获取dialog失败时，更新群组状态为加入失败"""
        try:
            from jd.models.tg_group import TgGroup
            group = TgGroup.query.filter_by(chat_id=str(chat_id)).first()
            if group:
                # 只有当前状态是JOIN_SUCCESS时才更新，避免重复更新
                if group.status == TgGroup.StatusType.JOIN_SUCCESS:
                    group.status = TgGroup.StatusType.JOIN_FAIL
                    group.remark = f'Dialog获取失败，可能已被移出群组或群组不存在'
                    db.session.commit()
                    logger.info(f'更新群组 {group_name} (chat_id: {chat_id}) 状态为加入失败')
        except Exception as e:
            logger.error(f'更新群组状态失败 chat_id={chat_id}: {e}')
            try:
                db.session.rollback()
            except Exception as rollback_error:
                logger.error(f'群组状态更新回滚失败: {rollback_error}')

    def _mark_group_as_invalid_link(self, chat_id: int, group_name: str, reason: str):
        """当无法加入群组时，将群组标记为失效状态（INVALID_LINK）"""
        try:
            from jd.models.tg_group import TgGroup
            group = TgGroup.query.filter_by(chat_id=str(chat_id)).first()
            if not group:
                logger.warning(f'标记失效失败|{group_name}|群组记录不存在')
                return

            # 只有当前状态是JOIN_SUCCESS时才更新为INVALID_LINK
            if group.status == TgGroup.StatusType.JOIN_SUCCESS:
                group.status = TgGroup.StatusType.INVALID_LINK
                group.remark = reason
                db.session.commit()
                logger.info(f'标记群组为失效|{group_name}|chat_id={chat_id}，原因: {reason}')
            else:
                logger.info(f'标记失效|{group_name}|群组状态已变更|当前状态={group.status}，不再标记为失效')
        except Exception as e:
            logger.error(f'标记群组失效失败|{group_name}: {e}')
            if db.session.in_transaction():
                try:
                    db.session.rollback()
                except Exception as rollback_error:
                    logger.error(f'标记失效事务回滚失败|{group_name}: {rollback_error}')
    
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
        try:
            groups = TgGroup.query.filter_by(status=TgGroup.StatusType.JOIN_SUCCESS).all()
            chat_room_list = []
            for group in groups:
                # 直接使用数据库中的group.name作为group_name
                group_name = group.name or ""
                chat_room_list.append((group_name, int(group.chat_id), group.account_id))
            
            logger.info(f'获取到 {len(chat_room_list)} 个已加入的群组')
            return chat_room_list
        except Exception as e:
            logger.error(f'获取聊天室列表失败: {e}')
            return []
    
    
    def _safe_str(self, value):
        """安全转换函数"""
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

    def _process_postal_time(self, postal_time):
        """处理消息时间"""
        if postal_time:
            return postal_time.replace(tzinfo=None) + datetime.timedelta(hours=8)
        else:
            return datetime.datetime.now(ZoneInfo('UTC')).replace(tzinfo=None) + datetime.timedelta(hours=8)

    async def process_message_batch(self, batch_messages, chat_id: int, batch_num: int) -> int:
        """优化版本：批量处理消息，使用SQLAlchemy自动事务管理"""
        if not batch_messages:
            return 0

        # 性能监控
        perf_logger = PerformanceLogger()
        perf_logger.start('process_message_batch',
                         chat_id=chat_id,
                         batch_num=batch_num,
                         message_count=len(batch_messages))

        try:
            # 1. 批量检查重复消息
            message_ids = [str(msg.get("message_id", 0)) for msg in batch_messages if msg.get("message_id")]
            existing_ids = set()

            if message_ids:
                existing_records = TgGroupChatHistory.query.filter(
                    TgGroupChatHistory.message_id.in_(message_ids),
                    TgGroupChatHistory.chat_id == str(chat_id)
                ).with_entities(TgGroupChatHistory.message_id).all()
                existing_ids = {record.message_id for record in existing_records}

            # 2. 过滤重复和无效消息
            valid_messages = []
            for data in batch_messages:
                message_id = str(data.get("message_id", 0))
                user_id = data.get("user_id", 0)

                if (message_id and message_id != "0" and
                    message_id not in existing_ids and
                    user_id != 777000):
                    valid_messages.append(data)

            if not valid_messages:
                # 没有有效消息，直接返回
                perf_logger.end(success=True, inserted_count=0, filtered_count=len(batch_messages))
                return 0

            # 3. 批量预处理用户信息缓存
            if self.user_processor:
                try:
                    await self.user_processor.prepare_batch_user_cache(valid_messages, chat_id)
                    logger.debug(f'第 {batch_num} 批次用户缓存预处理完成，有效消息数={len(valid_messages)}')
                except Exception as e:
                    logger.error(f'批量用户缓存预处理失败: {e}')

            # 4. 批量创建消息对象
            chat_objects = []
            for data in valid_messages:
                obj = TgGroupChatHistory(
                    chat_id=str(chat_id),
                    message_id=str(data.get("message_id", 0)),
                    nickname=self._safe_str(data.get("nick_name", "")),
                    username=self._safe_str(data.get("user_name", "")),
                    user_id=str(data.get("user_id", 0)),
                    postal_time=self._process_postal_time(data.get("postal_time")),
                    message=self._safe_str(data.get("message", "")),
                    reply_to_msg_id=str(data.get("reply_to_msg_id", 0)),
                    photo_path=data.get("photo", {}).get('file_path', ''),
                    document_path=data.get("document", {}).get('file_path', ''),
                    document_ext=data.get("document", {}).get('ext', ''),
                    replies_info=self._safe_str(data.get('replies_info', ''))
                )
                chat_objects.append(obj)

            # 5. 批量插入消息记录
            if chat_objects:
                db.session.add_all(chat_objects)

            # 6. 批量处理用户信息
            if self.user_processor:
                await self.user_processor.save_user_info_from_message_batch(valid_messages, chat_id)

            # 7. 提交事务 - 依赖SQLAlchemy的自动事务管理
            db.session.commit()

            # 记录成功性能
            perf_logger.end(success=True,
                          inserted_count=len(chat_objects),
                          filtered_count=len(batch_messages) - len(valid_messages))

            logger.info(f'第 {batch_num} 批次批量插入 {len(chat_objects)} 条消息 (过滤重复 {len(batch_messages) - len(valid_messages)} 条)')
            return len(chat_objects)

        except Exception as e:
            # 检查事务状态，只在需要时回滚
            if db.session.in_transaction():
                try:
                    db.session.rollback()
                except Exception as rollback_error:
                    logger.error(f'事务回滚失败: {rollback_error}')

            # 记录失败性能
            perf_logger.end(success=False, error=str(e))
            logger.error(f'第 {batch_num} 批次批量处理失败，已回滚: {e}')
            return 0
    

    def update_group_status(self, chat_id: int):
        """优化版本：更新群组状态统计信息，减少数据库查询次数"""
        try:
            chat_id_str = str(chat_id)

            # 获取或创建群组状态记录
            status = TgGroupStatus.query.filter_by(chat_id=chat_id_str).first()
            if not status:
                status = TgGroupStatus(chat_id=chat_id_str)
                db.session.add(status)

            # previous字段由每日备份任务统一更新，这里不再修改

            # 使用单次聚合查询获取所有统计信息
            stats = db.session.query(
                func.count(TgGroupChatHistory.id).label('total_count'),
                func.min(TgGroupChatHistory.postal_time).label('first_date'),
                func.max(TgGroupChatHistory.postal_time).label('last_date')
            ).filter(TgGroupChatHistory.chat_id == chat_id_str).first()

            if stats and stats.total_count > 0:
                status.records_now = stats.total_count
                status.first_record_date = stats.first_date
                status.last_record_date = stats.last_date

                # 优化：只在需要时获取消息ID，减少查询
                # 获取第一条消息ID
                if stats.first_date and not status.first_record_id:
                    try:
                        first_msg = TgGroupChatHistory.query.filter_by(
                            chat_id=chat_id_str
                        ).filter(TgGroupChatHistory.postal_time == stats.first_date).first()
                        if first_msg:
                            status.first_record_id = first_msg.message_id
                        else:
                            status.first_record_id = 0  # 找不到消息时使用0
                    except Exception as e:
                        logger.warning(f'获取第一条消息ID失败: {e}')
                        status.first_record_id = 0  # 异常时使用0

                # 获取最后一条消息ID
                if stats.last_date:
                    try:
                        last_msg = TgGroupChatHistory.query.filter_by(
                            chat_id=chat_id_str
                        ).filter(TgGroupChatHistory.postal_time == stats.last_date).order_by(
                            TgGroupChatHistory.id.desc()
                        ).first()
                        if last_msg:
                            status.last_record_id = last_msg.message_id
                        else:
                            status.last_record_id = 0  # 找不到消息时使用0
                    except Exception as e:
                        logger.warning(f'获取最后一条消息ID失败: {e}')
                        status.last_record_id = 0   # 异常时使用0
            else:
                # 没有记录时重置状态
                status.records_now = 0
                status.first_record_date = None
                status.first_record_id = 0  # 使用0而不是None，避免数据库完整性错误
                status.last_record_date = None
                status.last_record_id = 0   # 使用0而不是None，避免数据库完整性错误

            # 提交状态更新
            db.session.commit()
            logger.info(f'群组状态更新成功|{chat_id}|记录数: {getattr(status, "records_previous", 0)} -> {status.records_now}')

        except Exception as e:
            logger.error(f'群组状态更新失败|{chat_id}: {e}')
            if db.session.in_transaction():
                try:
                    db.session.rollback()
                except Exception as rollback_error:
                    logger.error(f'状态更新回滚失败: {rollback_error}') 