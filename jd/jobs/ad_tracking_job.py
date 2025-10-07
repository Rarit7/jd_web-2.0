"""
广告追踪数据处理作业

功能：
1. 从聊天记录中提取广告内容（URL、Telegram账户、t.me链接、Telegraph链接）
2. 调用 TmeSpider 服务进行内容分析
3. 整合自动标签系统
4. 将结果写入数据库

使用方式：
- 增量处理：处理指定日期的聊天记录
- 批量处理：处理历史聊天记录
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time

from jd import app, db
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group_user_info import TgGroupUserInfo
from jd.models.tg_group import TgGroup
from jd.models.ad_tracking import AdTracking
from jd.models.ad_tracking_tags import AdTrackingTags
from jd.services.spider.tme_spider import TmeSpider
from jd.jobs.auto_tagging import AutoTaggingService

logger = logging.getLogger(__name__)


class AdTrackingJob:
    """广告追踪数据处理作业"""

    def __init__(self):
        """初始化作业实例"""
        self.spider = TmeSpider()
        self.auto_tagging_service = AutoTaggingService()

    def _process_content_item(self, content: str, content_type: str,
                              source_type: str, source_id: str,
                              user_id: str = None, chat_id: str = None) -> Optional[Dict[str, Any]]:
        """
        处理单个内容项（URL、账户等）

        Args:
            content: 原始内容
            content_type: 内容类型
            source_type: 来源类型
            source_id: 来源记录ID
            user_id: 用户ID
            chat_id: 群组ID

        Returns:
            处理结果字典，如果失败返回None
        """
        try:
            # 标准化内容
            if content_type == 'url':
                normalized_content = self.spider.normalize_url(content)
            elif content_type == 'telegram_account':
                normalized_content = content.lstrip('@').lower()
            else:
                normalized_content = content.lower()

            # 获取额外信息
            extra_info = {}

            if content_type == 'url':
                # 使用智能URL处理
                result = self.spider.classify_and_process_url(content)
                if result and not result.get('error'):
                    url_type = result.get('url_type')
                    data = result.get('data', {})

                    if url_type == 'tme':
                        # t.me链接
                        content_type = self._get_tme_content_type(data.get('classification', {}))
                        extra_info = data.get('preview', {})
                    elif url_type == 'telegraph':
                        # Telegraph链接
                        content_type = 'telegraph'
                        extra_info = data
                    else:
                        # 普通URL
                        extra_info = data
                else:
                    logger.warning(f"Failed to process URL: {content}, error: {result.get('error')}")
                    # 即使处理失败，也记录基本信息
                    extra_info = {'error': result.get('error')}

            elif content_type == 'telegram_account':
                # Telegram账户深度分析
                # 1. 将 @username 转换为 t.me/username
                # 2. 爬取账户预览信息
                account_analysis = self.spider.analyze_telegram_account(content)

                if account_analysis.get('error'):
                    logger.warning(f"Telegram账户分析失败: {content}, 错误: {account_analysis.get('error')}")
                    extra_info = {
                        'account_type': 'user',
                        'tme_url': account_analysis.get('tme_url'),
                        'error': account_analysis.get('error')
                    }
                else:
                    # 从预览信息中提取账户详情
                    preview = account_analysis.get('preview', {})
                    extra_info = {
                        'account_type': preview.get('type', 'user'),  # channel/group/user
                        'tme_url': account_analysis.get('tme_url'),
                        'name': preview.get('name'),
                        'username': account_analysis.get('username'),
                        'avatar': preview.get('avatar'),
                        'desc': preview.get('desc'),
                        'members': preview.get('members')
                    }

            return {
                'content': content,
                'content_type': content_type,
                'normalized_content': normalized_content,
                'extra_info': extra_info,
                'source_type': source_type,
                'source_id': source_id,
                'user_id': user_id,
                'chat_id': chat_id
            }

        except Exception as e:
            logger.error(f"Error processing content '{content}': {str(e)}")
            return None

    def _get_tme_content_type(self, classification: Dict) -> str:
        """根据t.me链接分类结果获取content_type"""
        tme_type = classification.get('type', 'unknown')

        type_mapping = {
            'channel_msg': 't_me_channel_msg',
            'group_invite': 't_me_invite',
            'channel_invite': 't_me_invite',
            'private_invite': 't_me_private_invite',
            'user': 't_me_invite',
        }

        return type_mapping.get(tme_type, 't_me_invite')

    def _save_or_update_tracking(self, tracking_data: Dict[str, Any]) -> Optional[AdTracking]:
        """
        保存或更新广告追踪记录

        Args:
            tracking_data: 追踪数据

        Returns:
            AdTracking对象，如果失败返回None
        """
        try:
            # 查找是否存在相同的记录
            existing = AdTracking.query.filter_by(
                normalized_content=tracking_data['normalized_content'],
                source_type=tracking_data['source_type'],
                source_id=tracking_data['source_id']
            ).first()

            if existing:
                # 更新已有记录
                existing.last_seen = datetime.now()
                existing.occurrence_count += 1
                # 更新extra_info（合并新信息）
                if tracking_data.get('extra_info'):
                    if existing.extra_info:
                        existing.extra_info.update(tracking_data['extra_info'])
                    else:
                        existing.extra_info = tracking_data['extra_info']
                logger.debug(f"Updated existing tracking record: {existing.id}")
                return existing
            else:
                # 创建新记录
                new_tracking = AdTracking(
                    content=tracking_data['content'],
                    content_type=tracking_data['content_type'],
                    normalized_content=tracking_data['normalized_content'],
                    extra_info=tracking_data.get('extra_info'),
                    source_type=tracking_data['source_type'],
                    source_id=tracking_data['source_id'],
                    user_id=tracking_data.get('user_id'),
                    chat_id=tracking_data.get('chat_id'),
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    occurrence_count=1
                )
                db.session.add(new_tracking)
                logger.debug(f"Created new tracking record for: {tracking_data['content']}")
                return new_tracking

        except Exception as e:
            logger.error(f"Error saving tracking record: {str(e)}")
            return None

    def _apply_auto_tags(self, text: str, user_id: str, tracking_id: int):
        """
        应用自动标签到广告追踪记录

        Args:
            text: 文本内容
            user_id: 用户ID
            tracking_id: 广告追踪记录ID
        """
        try:
            # 使用自动标签服务处理文本
            matched_tags = self.auto_tagging_service.process_text_for_tags(
                text, user_id, 'ad_tracking', str(tracking_id)
            )

            if matched_tags:
                # 保存标签关联
                for tag_info in matched_tags:
                    # 检查是否已存在关联
                    existing = AdTrackingTags.query.filter_by(
                        ad_tracking_id=tracking_id,
                        tag_id=tag_info['tag_id']
                    ).first()

                    if not existing:
                        tag_relation = AdTrackingTags(
                            ad_tracking_id=tracking_id,
                            tag_id=tag_info['tag_id']
                        )
                        db.session.add(tag_relation)
                        logger.debug(f"Applied tag {tag_info['tag_id']} to tracking {tracking_id}")

                # 同时应用到用户（复用现有自动标签系统）
                self.auto_tagging_service.apply_auto_tags(
                    user_id, matched_tags, 'ad_tracking', str(tracking_id)
                )

        except Exception as e:
            logger.error(f"Error applying auto tags: {str(e)}")

    def process_chat_record(self, chat_record: TgGroupChatHistory) -> Dict[str, int]:
        """
        处理单条聊天记录

        Args:
            chat_record: 聊天记录对象

        Returns:
            处理统计 {'urls': count, 'accounts': count, ...}
        """
        stats = {
            'urls': 0,
            'telegram_accounts': 0,
            'total_items': 0
        }

        if not chat_record.message:
            return stats

        message_text = chat_record.message
        source_id = str(chat_record.id)
        user_id = str(chat_record.user_id) if chat_record.user_id else None
        chat_id = str(chat_record.chat_id) if chat_record.chat_id else None

        # 提取URLs
        urls = self.spider.extract_urls(message_text)
        for url in urls:
            tracking_data = self._process_content_item(
                url, 'url', 'chat', source_id, user_id, chat_id
            )
            if tracking_data:
                tracking_record = self._save_or_update_tracking(tracking_data)
                if tracking_record:
                    # 应用自动标签
                    self._apply_auto_tags(message_text, user_id, tracking_record.id)
                    stats['urls'] += 1
                    stats['total_items'] += 1

        # 提取Telegram账户
        accounts = self.spider.extract_telegram_accounts(message_text)
        for account in accounts:
            tracking_data = self._process_content_item(
                account, 'telegram_account', 'chat', source_id, user_id, chat_id
            )
            if tracking_data:
                tracking_record = self._save_or_update_tracking(tracking_data)
                if tracking_record:
                    # 应用自动标签
                    self._apply_auto_tags(message_text, user_id, tracking_record.id)
                    stats['telegram_accounts'] += 1
                    stats['total_items'] += 1

        return stats

    def process_user_info(self, user_info: TgGroupUserInfo) -> Dict[str, int]:
        """
        处理用户信息（昵称、描述）

        Args:
            user_info: 用户信息对象

        Returns:
            处理统计
        """
        stats = {
            'urls': 0,
            'telegram_accounts': 0,
            'total_items': 0
        }

        user_id = str(user_info.user_id)

        # 处理昵称
        if user_info.nickname:
            urls = self.spider.extract_urls(user_info.nickname)
            for url in urls:
                tracking_data = self._process_content_item(
                    url, 'url', 'nickname', user_id, user_id, None
                )
                if tracking_data:
                    tracking_record = self._save_or_update_tracking(tracking_data)
                    if tracking_record:
                        self._apply_auto_tags(user_info.nickname, user_id, tracking_record.id)
                        stats['urls'] += 1
                        stats['total_items'] += 1

            accounts = self.spider.extract_telegram_accounts(user_info.nickname)
            for account in accounts:
                tracking_data = self._process_content_item(
                    account, 'telegram_account', 'nickname', user_id, user_id, None
                )
                if tracking_data:
                    tracking_record = self._save_or_update_tracking(tracking_data)
                    if tracking_record:
                        self._apply_auto_tags(user_info.nickname, user_id, tracking_record.id)
                        stats['telegram_accounts'] += 1
                        stats['total_items'] += 1

        # 处理描述
        if user_info.desc:
            urls = self.spider.extract_urls(user_info.desc)
            for url in urls:
                tracking_data = self._process_content_item(
                    url, 'url', 'user_desc', user_id, user_id, None
                )
                if tracking_data:
                    tracking_record = self._save_or_update_tracking(tracking_data)
                    if tracking_record:
                        self._apply_auto_tags(user_info.desc, user_id, tracking_record.id)
                        stats['urls'] += 1
                        stats['total_items'] += 1

            accounts = self.spider.extract_telegram_accounts(user_info.desc)
            for account in accounts:
                tracking_data = self._process_content_item(
                    account, 'telegram_account', 'user_desc', user_id, user_id, None
                )
                if tracking_data:
                    tracking_record = self._save_or_update_tracking(tracking_data)
                    if tracking_record:
                        self._apply_auto_tags(user_info.desc, user_id, tracking_record.id)
                        stats['telegram_accounts'] += 1
                        stats['total_items'] += 1

        return stats

    def process_group_info(self, group: TgGroup) -> Dict[str, int]:
        """
        处理群组信息（群介绍）

        Args:
            group: 群组对象

        Returns:
            处理统计
        """
        stats = {
            'urls': 0,
            'telegram_accounts': 0,
            'total_items': 0
        }

        if not group.group_intro:
            return stats

        chat_id = str(group.chat_id)

        # 处理群组介绍
        urls = self.spider.extract_urls(group.group_intro)
        for url in urls:
            tracking_data = self._process_content_item(
                url, 'url', 'group_intro', chat_id, None, chat_id
            )
            if tracking_data:
                tracking_record = self._save_or_update_tracking(tracking_data)
                if tracking_record:
                    stats['urls'] += 1
                    stats['total_items'] += 1

        accounts = self.spider.extract_telegram_accounts(group.group_intro)
        for account in accounts:
            tracking_data = self._process_content_item(
                account, 'telegram_account', 'group_intro', chat_id, None, chat_id
            )
            if tracking_data:
                tracking_record = self._save_or_update_tracking(tracking_data)
                if tracking_record:
                    stats['telegram_accounts'] += 1
                    stats['total_items'] += 1

        return stats

    def run_daily_task(self, target_date: datetime = None) -> Dict[str, Any]:
        """
        每日增量任务：处理指定日期的聊天记录

        Args:
            target_date: 目标日期，默认为昨天

        Returns:
            执行结果统计
        """
        if target_date is None:
            target_date = datetime.now() - timedelta(days=1)

        start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        logger.info(f"Starting daily ad tracking task for {target_date.strftime('%Y-%m-%d')}")

        result = {
            'date': target_date.strftime('%Y-%m-%d'),
            'chat_records_processed': 0,
            'user_infos_processed': 0,
            'group_infos_processed': 0,
            'total_urls': 0,
            'total_accounts': 0,
            'total_items': 0,
            'errors': 0
        }

        try:
            # 处理聊天记录
            chat_records = TgGroupChatHistory.query.filter(
                TgGroupChatHistory.postal_time >= start_time,
                TgGroupChatHistory.postal_time <= end_time
            ).all()

            for record in chat_records:
                try:
                    stats = self.process_chat_record(record)
                    result['chat_records_processed'] += 1
                    result['total_urls'] += stats['urls']
                    result['total_accounts'] += stats['telegram_accounts']
                    result['total_items'] += stats['total_items']
                except Exception as e:
                    logger.error(f"Error processing chat record {record.id}: {str(e)}")
                    result['errors'] += 1

            # 处理当天更新的用户信息
            user_infos = TgGroupUserInfo.query.filter(
                TgGroupUserInfo.updated_at >= start_time,
                TgGroupUserInfo.updated_at <= end_time
            ).all()

            for user_info in user_infos:
                try:
                    stats = self.process_user_info(user_info)
                    result['user_infos_processed'] += 1
                    result['total_urls'] += stats['urls']
                    result['total_accounts'] += stats['telegram_accounts']
                    result['total_items'] += stats['total_items']
                except Exception as e:
                    logger.error(f"Error processing user info {user_info.user_id}: {str(e)}")
                    result['errors'] += 1

            # 处理当天更新的群组信息
            groups = TgGroup.query.filter(
                TgGroup.updated_at >= start_time,
                TgGroup.updated_at <= end_time
            ).all()

            for group in groups:
                try:
                    stats = self.process_group_info(group)
                    result['group_infos_processed'] += 1
                    result['total_urls'] += stats['urls']
                    result['total_accounts'] += stats['telegram_accounts']
                    result['total_items'] += stats['total_items']
                except Exception as e:
                    logger.error(f"Error processing group {group.chat_id}: {str(e)}")
                    result['errors'] += 1

            # 提交数据库
            db.session.commit()
            result['status'] = 'success'
            logger.info(f"Daily ad tracking task completed: {result}")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Daily ad tracking task failed: {str(e)}")
            result['status'] = 'failed'
            result['error'] = str(e)
            raise

        return result

    def run_historical_batch(self, batch_size: int = 1000, max_batches: int = None) -> Dict[str, Any]:
        """
        历史数据批量处理任务

        Args:
            batch_size: 每批处理数量
            max_batches: 最大批次数（None表示处理全部）

        Returns:
            执行结果统计
        """
        logger.info(f"Starting historical ad tracking batch task (batch_size={batch_size})")

        result = {
            'chat_records_processed': 0,
            'user_infos_processed': 0,
            'group_infos_processed': 0,
            'total_urls': 0,
            'total_accounts': 0,
            'total_items': 0,
            'batches_processed': 0,
            'errors': 0
        }

        try:
            # 批量处理聊天记录
            chat_offset = 0
            batch_count = 0

            while True:
                if max_batches and batch_count >= max_batches:
                    break

                chat_records = TgGroupChatHistory.query.offset(chat_offset).limit(batch_size).all()
                if not chat_records:
                    break

                for record in chat_records:
                    try:
                        stats = self.process_chat_record(record)
                        result['chat_records_processed'] += 1
                        result['total_urls'] += stats['urls']
                        result['total_accounts'] += stats['telegram_accounts']
                        result['total_items'] += stats['total_items']
                    except Exception as e:
                        logger.error(f"Error processing chat record {record.id}: {str(e)}")
                        result['errors'] += 1

                # 提交当前批次
                db.session.commit()
                chat_offset += batch_size
                batch_count += 1
                result['batches_processed'] = batch_count

                logger.info(f"Processed batch {batch_count}: {result['chat_records_processed']} chat records")
                time.sleep(0.5)  # 避免长时间占用资源

            # 批量处理用户信息
            user_offset = 0
            while True:
                if max_batches and batch_count >= max_batches:
                    break

                user_infos = TgGroupUserInfo.query.offset(user_offset).limit(batch_size).all()
                if not user_infos:
                    break

                for user_info in user_infos:
                    try:
                        stats = self.process_user_info(user_info)
                        result['user_infos_processed'] += 1
                        result['total_urls'] += stats['urls']
                        result['total_accounts'] += stats['telegram_accounts']
                        result['total_items'] += stats['total_items']
                    except Exception as e:
                        logger.error(f"Error processing user info {user_info.user_id}: {str(e)}")
                        result['errors'] += 1

                db.session.commit()
                user_offset += batch_size
                logger.info(f"Processed {result['user_infos_processed']} user infos")
                time.sleep(0.5)

            # 批量处理群组信息
            group_offset = 0
            while True:
                if max_batches and batch_count >= max_batches:
                    break

                groups = TgGroup.query.offset(group_offset).limit(batch_size).all()
                if not groups:
                    break

                for group in groups:
                    try:
                        stats = self.process_group_info(group)
                        result['group_infos_processed'] += 1
                        result['total_urls'] += stats['urls']
                        result['total_accounts'] += stats['telegram_accounts']
                        result['total_items'] += stats['total_items']
                    except Exception as e:
                        logger.error(f"Error processing group {group.chat_id}: {str(e)}")
                        result['errors'] += 1

                db.session.commit()
                group_offset += batch_size
                logger.info(f"Processed {result['group_infos_processed']} groups")
                time.sleep(0.5)

            result['status'] = 'success'
            logger.info(f"Historical ad tracking batch task completed: {result}")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Historical ad tracking batch task failed: {str(e)}")
            result['status'] = 'failed'
            result['error'] = str(e)
            raise

        return result


# 命令行入口
if __name__ == '__main__':
    import sys

    with app.app_context():
        job = AdTrackingJob()

        if len(sys.argv) > 1:
            if sys.argv[1] == 'daily':
                # 每日任务
                result = job.run_daily_task()
                print(f"Daily task result: {result}")
            elif sys.argv[1] == 'historical':
                # 历史数据批量处理
                batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
                max_batches = int(sys.argv[3]) if len(sys.argv) > 3 else None
                result = job.run_historical_batch(batch_size, max_batches)
                print(f"Historical batch result: {result}")
            else:
                print("Usage: python -m jd.jobs.ad_tracking_job [daily|historical] [batch_size] [max_batches]")
        else:
            # 默认执行每日任务
            result = job.run_daily_task()
            print(f"Daily task result: {result}")
