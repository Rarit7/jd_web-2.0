import asyncio
import datetime
from zoneinfo import ZoneInfo

from jd import app, db
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.jobs.tg_base_history_fetcher import BaseTgHistoryFetcher
from jd.utils.logging_config import get_logger

logger = get_logger('jd.jobs.tg.new_history', {
    'component': 'telegram',
    'module': 'new_history'
})


class NewJoinedGroupHistoryFetcher(BaseTgHistoryFetcher):

    def __init__(self):
        super().__init__()
        self.history_days = app.config.get('TG_HISTORY_DAYS', 60)
    
    async def fetch_comprehensive_group_data(self, chat_id: int, group_name: str) -> bool:
        logger.info(f'群聊历史记录回溯|{group_name}|ID={chat_id}开始')
        
        try:
            chat, chat_id = await self.get_dialog_with_retry(chat_id, group_name)
            if not chat:
                return False
            
            # Use UTC timezone to match Telegram API datetime objects
            now_utc = datetime.datetime.now(ZoneInfo('UTC'))
            end_date = now_utc - datetime.timedelta(days=self.history_days) # n天前
            
            # 检查数据库中是否已存在聊天记录
            existing_oldest_message = TgGroupChatHistory.query.filter_by(
                chat_id=str(chat_id)
            ).order_by(TgGroupChatHistory.postal_time.asc()).first()
            
            if existing_oldest_message:
                # 如果存在聊天记录，从最老的记录时间开始往前获取
                offset_time = existing_oldest_message.postal_time.replace(tzinfo=ZoneInfo('UTC'))
                logger.info(f'群聊历史记录回溯|{group_name}|从最早时间开始获取: {offset_time.strftime("%Y-%m-%d %H:%M:%S")}')
            else:
                # 如果不存在聊天记录，从今天开始往前获取
                offset_time = now_utc
                logger.info(f'群聊历史记录回溯|{group_name}|从最新消息开始获取: {offset_time.strftime("%Y-%m-%d %H:%M:%S")}')
            
            logger.info(f'群聊历史记录回溯|{group_name}|获取 {self.history_days} 天的历史记录 从 {end_date.strftime("%Y-%m-%d")} 起')
            
            total_saved_count = 0
            batch_num = 0
            
            # 使用offset_time进行批量获取
            while offset_time > end_date:
                batch_num += 1
                logger.info(f'群聊历史记录回溯|{group_name}|第 {batch_num} 批次|从服务器拉取聊天记录')
                
                # 获取历史记录参数
                param = {
                    "limit": 100,  # 每次固定获取100条
                    "offset_date": offset_time,  # 从offset_time开始往前获取
                    "last_message_id": -1,
                }
                
                batch_messages = []
                earliest_time = offset_time
                
                # 获取当前批次的消息
                async for data in self.tg.scan_message(chat, **param):
                    batch_messages.append(data)
                    # 记录最早的消息时间
                    msg_time = data["postal_time"]
                    if msg_time < earliest_time:
                        earliest_time = msg_time
                    
                    # 如果消息时间早于end_date，停止获取
                    if msg_time < end_date:
                        break
                        
                    # 限制每批次最多100条
                    if len(batch_messages) >= 100:
                        break
                
                if not batch_messages:
                    logger.info(f'群聊历史记录回溯|{group_name}|第 {batch_num} 批次|获取完成')
                    break
                
                logger.info(f'群聊历史记录回溯|{group_name}|第 {batch_num} 批次|获取 {len(batch_messages)} 条信息')
                
                # 保存当前批次的消息
                batch_saved_count = await self.process_message_batch(batch_messages, chat_id, batch_num)
                total_saved_count += batch_saved_count
                logger.info(f'群聊历史记录回溯|{group_name}|第 {batch_num} 批次|数据库写入 {total_saved_count} 条消息')
                
                # 更新offset_time为当前批次最早的消息时间
                if earliest_time < offset_time:
                    offset_time = earliest_time
                    logger.info(f'群聊历史记录回溯|{group_name}|更新offset_time {offset_time.strftime("%Y-%m-%d %H:%M:%S")}')
                else:
                    # 如果没有更早的消息，说明已经获取完毕
                    break
                
                # 添加小延迟避免频繁请求
                await asyncio.sleep(0.5)
            
            logger.info(f'群聊历史记录回溯|{group_name}|任务完成：获取条数 {total_saved_count} ')
            
            # 更新群组状态
            self.update_group_status(chat_id)
            
            return True
            
        except Exception as e:
            logger.error(f'群聊历史记录回溯|{group_name}|错误: {e}')
            db.session.rollback()
            return False
    
    
    async def process_specific_group(self, group_name: str, chat_id: int) -> bool:
        
        try:
            # 获取群组完整数据
            return await self.fetch_comprehensive_group_data(chat_id, group_name)
            
        except Exception as e:
            logger.error(f'处理群组 {group_name} 时发生错误: {e}')
            return False
