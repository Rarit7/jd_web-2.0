import asyncio
import logging

from jd.models.tg_group_status import TgGroupStatus
from jd.jobs.tg_base_history_fetcher import BaseTgHistoryFetcher


logger = logging.getLogger(__name__)


class ExsitedGroupHistoryFetcher(BaseTgHistoryFetcher):

    def __init__(self):
        super().__init__()

    
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
            logger.error(f'增量聊天记录获取|{group_name}|错误: {e}')
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
            return False, {'total_groups': 0, 'processed_groups': [], 'error_groups': []}
            
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
                    error_groups.append({
                        'group_name': group_name,
                        'chat_id': chat_id,
                        'session_names': session_names,
                        'error': 'fetch_group_new_data返回False'
                    })
                    
            except Exception as e:
                logger.error(f'处理群组 {group_name} 时发生错误: {e}')
                error_groups.append({
                    'group_name': group_name,
                    'chat_id': chat_id,
                    'session_names': session_names,
                    'error': str(e)
                })
                # 出现异常时关闭当前连接，强制下一个群组重新初始化
                if hasattr(self, 'tg') and self.tg:
                    try:
                        await self.close_telegram_service()
                        current_session_names = None  # 重置session状态
                    except Exception as close_error:
                        logger.error(f'异常处理中关闭Telegram服务失败: {close_error}')
        
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



