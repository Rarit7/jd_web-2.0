import asyncio
from telethon import errors

from jd import db
from jd.models.tg_group import TgGroup
from jd.models.tg_group_status import TgGroupStatus
from jd.jobs.tg_base_history_fetcher import BaseTgHistoryFetcher
from jd.utils.logging_config import get_logger


logger = get_logger('jd.jobs.tg.chat_history', {
    'component': 'telegram',
    'module': 'chat_history'
})


class ExsitedGroupHistoryFetcher(BaseTgHistoryFetcher):

    def __init__(self):
        super().__init__()


    def _is_temporary_error(self, exception) -> bool:
        """
        判断异常是否为临时性错误（需要重试）

        Args:
            exception: 捕获的异常

        Returns:
            bool: True表示临时错误，False表示永久失效
        """
        exception_type = type(exception).__name__

        # 临时错误列表（可重试）
        temporary_errors = [
            'PeerFloodError',        # Telegram速率限制
            'FloodError',            # 一般洪泛保护
            'SlowModeWaitError',     # 慢速模式
            'ConnectionError',       # 网络连接错误
            'TimeoutError',          # 超时
            'OSError',               # 操作系统级错误（包括网络）
        ]

        # 检查异常是否在临时错误列表中
        if exception_type in temporary_errors:
            return True

        # 检查异常消息中是否包含临时错误特征
        error_message = str(exception).lower()
        temporary_keywords = [
            'timeout',
            'connection',
            'temporarily',
            'temporarily unavailable',
            'temporarily blocked'
        ]

        for keyword in temporary_keywords:
            if keyword in error_message:
                return True

        return False


    def _mark_group_as_deleted(self, chat_id: int, group_name: str, reason: str):
        """
        将群组标记为失效状态（INVALID_LINK）

        Args:
            chat_id: 群组ID
            group_name: 群组名称
            reason: 标记原因
        """
        try:
            chat_id_str = str(chat_id)
            group = TgGroup.query.filter_by(chat_id=chat_id_str).first()

            if not group:
                logger.warning(f'增量聊天记录获取|{group_name}|标记失效失败|群组记录不存在')
                return

            # 只有当前状态是JOIN_SUCCESS时才更新为INVALID_LINK
            if group.status == TgGroup.StatusType.JOIN_SUCCESS:
                group.status = TgGroup.StatusType.INVALID_LINK
                db.session.commit()
                logger.info(f'增量聊天记录获取|{group_name}|已标记为失效|chat_id={chat_id}，原因: {reason}')
            else:
                logger.info(f'增量聊天记录获取|{group_name}|群组状态已变更|当前状态={group.status}，不再标记为失效')

        except Exception as e:
            logger.error(f'增量聊天记录获取|{group_name}|标记群组失效失败: {e}')
            if db.session.in_transaction():
                try:
                    db.session.rollback()
                except Exception as rollback_error:
                    logger.error(f'增量聊天记录获取|{group_name}|事务回滚失败: {rollback_error}')


    async def _retry_fetch_with_backoff(self, chat_id: int, group_name: str, max_retries: int = 3) -> tuple[bool, int]:
        """
        使用指数退避重试获取群组数据

        Args:
            chat_id: 群组ID
            group_name: 群组名称
            max_retries: 最大重试次数

        Returns:
            tuple[bool, int]: (是否成功, 新增消息数)
        """
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f'增量聊天记录获取|{group_name}|临时错误重试|第{attempt}次重试')

                # 指数退避延迟
                delay = 2 ** (attempt - 1)  # 1s, 2s, 4s
                await asyncio.sleep(delay)

                # 重新获取dialog
                chat, actual_chat_id = await self.get_dialog_with_retry(chat_id, group_name)
                if not chat:
                    logger.warning(f'增量聊天记录获取|{group_name}|第{attempt}次重试|Dialog获取失败')
                    continue

                # 尝试获取消息
                param = {
                    "limit": 100,
                    "reverse": False
                }

                batch_messages = []
                async for data in self.tg.scan_message(chat, **param):
                    batch_messages.append(data)
                    if len(batch_messages) >= 100:
                        break

                # 处理获取到的消息
                if batch_messages:
                    batch_saved_count = await self.process_message_batch(batch_messages, actual_chat_id, 1)
                    self.update_group_status(actual_chat_id)
                    logger.info(f'增量聊天记录获取|{group_name}|重试成功|获取并保存 {batch_saved_count} 条消息')
                    return True, batch_saved_count
                else:
                    logger.info(f'增量聊天记录获取|{group_name}|重试成功|无新消息')
                    return True, 0

            except Exception as e:
                if attempt == max_retries:
                    logger.warning(f'增量聊天记录获取|{group_name}|第{attempt}次重试失败|所有重试都失败了: {e}')
                else:
                    logger.warning(f'增量聊天记录获取|{group_name}|第{attempt}次重试失败|将继续重试: {e}')

        return False, 0


    # 从tg_group_status获取last_record_id作为min_id
    # 如果没有last_record_id记录，则返回-1
    def get_min_id(self, chat_id):
        try:
            status = TgGroupStatus.query.filter_by(chat_id=str(chat_id)).first()
            if status and status.last_record_id:
                return int(status.last_record_id)
            return -1
        except (ValueError, TypeError):
            return -1

    
    async def fetch_group_new_data(self, chat_id: int, group_name: str, max_batch: int = 10) -> tuple[bool, int]:
        logger.info(f'增量聊天记录获取|{group_name}|ID={chat_id}开始')
        
        try:
            chat, chat_id = await self.get_dialog_with_retry(chat_id, group_name)
            if not chat:
                return False, 0
            
            min_id = self.get_min_id(chat_id)
            total_saved_count = 0
            batch_num = 0

            # 首次运行特殊处理：获取最新100条消息
            if min_id == -1:
                logger.info(f'增量聊天记录获取|{group_name}|首次运行，获取最新100条消息')
                
                # 获取最新消息参数（不设置last_message_id，reverse=False表示从最新开始）
                param = {
                    "limit": 100,
                    "reverse": False  # 从最新消息开始往前获取
                }
                
                batch_messages = []
                batch_num = 1
                
                # 获取最新的100条消息
                async for data in self.tg.scan_message(chat, **param):
                    batch_messages.append(data)
                    if len(batch_messages) >= 100:
                        break
                
                if batch_messages:
                    logger.info(f'增量聊天记录获取|{group_name}|首次运行|获取到 {len(batch_messages)} 条最新消息')
                    
                    # 保存首次获取的消息
                    batch_saved_count = await self.process_message_batch(batch_messages, chat_id, batch_num)
                    total_saved_count += batch_saved_count
                    
                    logger.info(f'增量聊天记录获取|{group_name}|首次运行完成：保存 {total_saved_count} 条消息')
                else:
                    logger.warning(f'增量聊天记录获取|{group_name}|首次运行|未获取到任何消息')
                
                # 更新群组状态并返回
                self.update_group_status(chat_id)
                return True, total_saved_count
            
            logger.info(f'增量聊天记录获取|{group_name}|继续从min_id={min_id}开始增量获取')
            
            # 循环获取，直到不再获取到消息，或者达到10个循环（约1000条消息）
            while True:
                batch_num += 1
                if batch_num >= max_batch + 1:
                    logger.info(f'增量聊天记录获取|{group_name}|消息数到达设定上限 {max_batch * 100}, 即将暂停')
                    break
                logger.info(f'增量聊天记录获取|{group_name}|第 {batch_num} 批次|从服务器拉取聊天记录|min_id={min_id}')
                
                # 获取历史记录参数 - 每个批次开始时设置last_message_id
                param = {
                    "limit": 100,  # 每次固定获取100条
                    "last_message_id": min_id,
                    "reverse": True # 从min_id开始，往新消息获取
                }
                
                batch_messages = []
                batch_max_message_id = min_id  # 记录本批次的最大消息ID
                
                # 获取当前批次的消息
                async for data in self.tg.scan_message(chat, **param):
                    batch_messages.append(data)
                    # 记录本批次的最大消息ID，用于下一批次
                    message_id = data.get("message_id", 0)
                    if message_id and int(message_id) > batch_max_message_id:
                        batch_max_message_id = int(message_id)
                        
                    # 限制每批次最多100条
                    if len(batch_messages) >= 100:
                        break
                
                # 循环跳出条件：不再收到消息
                if not batch_messages:
                    logger.info(f'增量聊天记录获取|{group_name}|第 {batch_num} 批次|获取完成')
                    break
                
                logger.info(f'增量聊天记录获取|{group_name}|第 {batch_num} 批次|获取 {len(batch_messages)} 条信息')
                
                # 保存当前批次的消息
                batch_saved_count = await self.process_message_batch(batch_messages, chat_id, batch_num)
                total_saved_count += batch_saved_count
                logger.info(f'增量聊天记录获取|{group_name}|第 {batch_num} 批次|数据库写入 {batch_saved_count} 条消息|总计 {total_saved_count} 条')
                
                # 更新min_id为本批次的最大消息ID，用于下一批次获取
                if batch_max_message_id > min_id:
                    min_id = batch_max_message_id
                    logger.info(f'增量聊天记录获取|{group_name}|第 {batch_num} 批次|更新min_id为 {min_id}')
                
                # 添加小延迟避免频繁请求
                await asyncio.sleep(0.5)
            
            logger.info(f'增量聊天记录获取|{group_name}|任务完成：获取条数 {total_saved_count} ')

            # 更新群组状态
            self.update_group_status(chat_id)

            return True, total_saved_count

        except Exception as e:
            logger.error(f'增量聊天记录获取|{group_name}|异常发生: {type(e).__name__}: {e}')

            # 判断是否为临时错误
            if self._is_temporary_error(e):
                logger.warning(f'增量聊天记录获取|{group_name}|临时错误检测|错误类型={type(e).__name__}，尝试重试')

                # 尝试重试
                success, message_count = await self._retry_fetch_with_backoff(chat_id, group_name, max_retries=3)
                if success:
                    logger.info(f'增量聊天记录获取|{group_name}|重试恢复|最终获取 {message_count} 条消息')
                    return True, message_count
                else:
                    logger.warning(f'增量聊天记录获取|{group_name}|临时错误重试失败|但仍继续处理其他群组')
                    # 临时错误重试失败后不标记为INVALID_LINK，允许后续重试
                    return False, 0
            else:
                # 永久失效或未知错误：标记群组为失效
                logger.error(f'增量聊天记录获取|{group_name}|永久失效|将标记为INVALID_LINK')
                self._mark_group_as_deleted(chat_id, group_name, f'增量获取异常: {type(e).__name__}')
                return False, 0
    

    async def process_all_groups(self) -> tuple[bool, dict]:
        """
        修改初始化客户端的逻辑：通过chat_id获取session_name列表, 使用init_tg_with_retry初始化TG客户端
        如果当前使用的session_name也在即将处理的chat_id的关联列表里，直接使用已经初始化完成的tg客户端，避免反复初始化
        
        Returns:
            tuple[bool, dict]: (是否成功, 详细统计信息)
        """
        chat_room_list = self.get_chat_room_list()
        if not chat_room_list:
            logger.info('增量聊天记录获取|没有找到群组')
            return True, {'total_groups': 0, 'processed_groups': [], 'error_groups': [], 'success_count': 0, 'error_count': 0}
            
        success_count = 0
        current_session_names = None
        processed_groups = []
        error_groups = []
        
        for group_name, chat_id, account_id in chat_room_list:   
            # 获取当前chat_id对应的session名称列表
            session_names = self.get_sessionnames_by_chatid(chat_id)
            if not session_names:
                logger.warning(f'群组 {group_name} 找不到对应的session列表，使用account_id获取session')
                session_names = self.get_sessionnames_by_accountid(account_id)
            
            # 检查当前使用的session是否在新的session列表中
            need_reinit = True
            if current_session_names and hasattr(self, 'tg') and self.tg:
                # 如果当前session列表和新的session列表有交集，可以复用
                if set(current_session_names) & set(session_names):
                    need_reinit = False
                    logger.info(f'群组 {group_name} 复用现有TG连接')
            
            if need_reinit:
                # 关闭现有连接
                if hasattr(self, 'tg') and self.tg:
                    await self.close_telegram_service()
                
                # 使用init_tg_with_retry初始化新的连接
                from jd.services.spider.tg import TgService
                self.tg = await TgService.init_tg_with_retry(session_names)
                if not self.tg:
                    logger.error(f'群组 {group_name} 使用session列表初始化失败: {session_names}')
                    continue
                    
                # 初始化用户处理器
                from jd.jobs.tg_user_info import TgUserInfoProcessor
                self.user_processor = TgUserInfoProcessor(self.tg)
                current_session_names = session_names
                logger.info(f'群组 {group_name} 初始化TG连接成功，session列表: {session_names}')
            
            try:
                # 获取群组增量数据
                group_success, new_messages_count = await self.fetch_group_new_data(chat_id, group_name)
                if group_success:
                    success_count += 1
                    processed_groups.append({
                        'group_name': group_name,
                        'chat_id': chat_id,
                        'session_names': session_names,
                        'status': 'success',
                        'new_messages_count': new_messages_count
                    })
                else:
                    # fetch_group_new_data 返回 False，可能已标记为失效，或者是临时错误
                    error_groups.append({
                        'group_name': group_name,
                        'chat_id': chat_id,
                        'session_names': session_names,
                        'error': 'fetch_group_new_data返回False'
                    })

            except Exception as e:
                logger.error(f'增量聊天记录获取|{group_name}|进程异常: {type(e).__name__}: {e}')

                # 记录异常但继续处理其他群组
                error_groups.append({
                    'group_name': group_name,
                    'chat_id': chat_id,
                    'session_names': session_names,
                    'error': f'{type(e).__name__}: {str(e)}'
                })

                # 如果是临时错误，保持连接；如果是永久失效，关闭连接强制重新初始化
                if not self._is_temporary_error(e):
                    logger.error(f'增量聊天记录获取|{group_name}|进程异常为非临时错误，关闭连接进行重新初始化')
                    if hasattr(self, 'tg') and self.tg:
                        try:
                            await self.close_telegram_service()
                            current_session_names = None  # 重置session状态
                        except Exception as close_error:
                            logger.error(f'增量聊天记录获取|{group_name}|异常处理中关闭Telegram服务失败: {close_error}')
        
        # 最后关闭连接
        if hasattr(self, 'tg') and self.tg:
            try:
                await self.close_telegram_service()
            except Exception as e:
                logger.error(f'最终关闭Telegram服务失败: {e}')
                
        logger.info(f'处理完成，成功处理 {success_count}/{len(chat_room_list)} 个群组')
        
        # 返回详细统计信息
        stats = {
            'total_groups': len(chat_room_list),
            'success_count': success_count,
            'error_count': len(error_groups),
            'processed_groups': processed_groups,
            'error_groups': error_groups
        }
        
        return success_count > 0, stats



