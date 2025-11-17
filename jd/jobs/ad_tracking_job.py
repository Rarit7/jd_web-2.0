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

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import time

from jd import app, db
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group_user_info import TgGroupUserInfo
from jd.models.tg_group import TgGroup
from jd.models.ad_tracking import AdTracking
from jd.models.ad_tracking_tags import AdTrackingTags
from jd.services.spider.tme_spider import TmeSpider
from jd.jobs.auto_tagging import AutoTaggingService
from jd.utils.logging_config import get_logger, PerformanceLogger

logger = get_logger(__name__, {
    'component': 'ad_tracking',
    'module': 'job'
})


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
                # 使用智能URL处理（统一通过 TmeSpider）
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
                        # 普通URL - 直接使用 TmeSpider.analyze_url() 获取完整信息
                        # （包括主流域名检查 + 网站信息获取）
                        website_info = self.spider.analyze_url(content)

                        if not website_info.get('error'):
                            extra_info = {
                                'domain': website_info.get('domain'),
                                'title': website_info.get('title'),
                                'status_code': website_info.get('status_code'),
                                'content_type': website_info.get('content_type'),
                                'server': website_info.get('server'),
                                'ip_address': website_info.get('ip_address'),
                                'ip_location': website_info.get('ip_location', {}),
                                'is_short_url': website_info.get('is_short_url', False),
                                'redirect_chain_length': website_info.get('redirect_chain_length', 0),
                                'phishing': website_info.get('phishing', {}),
                                'certificate': website_info.get('certificate', {}),
                                'is_mainstream': website_info.get('is_mainstream'),  # TmeSpider 已处理
                            }

                            logger.info("URL 分析完成", extra={
                                'extra_fields': {
                                    'domain': extra_info.get('domain'),
                                    'is_mainstream': extra_info.get('is_mainstream'),
                                    'status_code': extra_info.get('status_code')
                                }
                            })
                        else:
                            logger.warning("URL 分析失败", extra={
                                'extra_fields': {
                                    'url': content,
                                    'error': website_info.get('error')
                                }
                            })
                            extra_info = {'error': website_info.get('error')}
                else:
                    logger.warning("URL 处理失败", extra={
                        'extra_fields': {
                            'url': content,
                            'error': result.get('error')
                        }
                    })
                    # 即使处理失败，也尝试进行基础分析
                    extra_info = {'error': result.get('error')}

                    # 即使分类失败，也尝试提取域名
                    try:
                        parsed = urlparse(content)
                        domain = parsed.netloc.lower().strip()
                        if domain:
                            extra_info['domain'] = domain
                            # 主流域名检查通过 TmeSpider 完成
                            is_mainstream = self.spider._is_mainstream_domain(domain)
                            if is_mainstream is not None:
                                extra_info['is_mainstream'] = is_mainstream
                    except Exception as e:
                        logger.warning("域名提取失败", extra={
                            'extra_fields': {
                                'url': content,
                                'error': str(e)
                            }
                        })

            elif content_type == 'telegram_account':
                # Telegram账户深度分析
                # 1. 将 @username 转换为 t.me/username
                # 2. 爬取账户预览信息
                account_analysis = self.spider.analyze_telegram_account(content)

                if account_analysis.get('error'):
                    logger.warning("Telegram 账户分析失败", extra={
                        'extra_fields': {
                            'account': content,
                            'error': account_analysis.get('error')
                        }
                    })
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
            logger.error("处理内容失败", extra={
                'extra_fields': {
                    'content': content,
                    'content_type': content_type,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, exc_info=True)
            return None

    def _process_and_track_content(self, content_text: str, source_type: str,
                                   source_id: str, user_id: str = None,
                                   chat_id: str = None, apply_tags: bool = True,
                                   tag_source_text: str = None) -> Dict[str, int]:
        """
        通用内容处理方法 - 提取URL和账户，进行分析和追踪

        功能：
        1. 从文本中提取 URLs 和 Telegram 账户
        2. 对每个内容项进行处理和分析
        3. 保存或更新追踪记录
        4. 应用自动标签（可选）

        Args:
            content_text: 待处理的文本内容
            source_type: 来源类型 ('chat', 'nickname', 'user_desc', 'group_intro' 等)
            source_id: 来源记录ID
            user_id: 用户ID（可选）
            chat_id: 群组ID（可选）
            apply_tags: 是否应用自动标签（默认True）
            tag_source_text: 自动标签的源文本（不指定则使用content_text）

        Returns:
            处理统计 {'urls': int, 'telegram_accounts': int, 'total_items': int}
        """
        stats = {
            'urls': 0,
            'telegram_accounts': 0,
            'total_items': 0
        }

        if not content_text:
            return stats

        # 确定用于标签的源文本
        tag_source = tag_source_text or content_text

        # 提取并处理 URLs
        urls = self.spider.extract_urls(content_text)
        for url in urls:
            tracking_data = self._process_content_item(
                url, 'url', source_type, source_id, user_id, chat_id
            )
            if tracking_data:
                tracking_record = self._save_or_update_tracking(tracking_data)
                if tracking_record:
                    if apply_tags and user_id:
                        self._apply_auto_tags(tag_source, user_id, tracking_record.id)
                    stats['urls'] += 1
                    stats['total_items'] += 1

        # 提取并处理 Telegram 账户
        accounts = self.spider.extract_telegram_accounts(content_text)
        for account in accounts:
            tracking_data = self._process_content_item(
                account, 'telegram_account', source_type, source_id, user_id, chat_id
            )
            if tracking_data:
                tracking_record = self._save_or_update_tracking(tracking_data)
                if tracking_record:
                    if apply_tags and user_id:
                        self._apply_auto_tags(tag_source, user_id, tracking_record.id)
                    stats['telegram_accounts'] += 1
                    stats['total_items'] += 1

        return stats

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
                logger.debug("更新已有追踪记录", extra={
                    'extra_fields': {
                        'tracking_id': existing.id,
                        'content_type': tracking_data['content_type'],
                        'source_type': tracking_data['source_type']
                    }
                })
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
                logger.debug("创建新追踪记录", extra={
                    'extra_fields': {
                        'content': tracking_data['content'],
                        'content_type': tracking_data['content_type'],
                        'source_type': tracking_data['source_type']
                    }
                })
                return new_tracking

        except Exception as e:
            logger.error("保存追踪记录失败", extra={
                'extra_fields': {
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, exc_info=True)
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
                        logger.debug("应用标签到追踪记录", extra={
                            'extra_fields': {
                                'tag_id': tag_info['tag_id'],
                                'tracking_id': tracking_id
                            }
                        })

                # 同时应用到用户（复用现有自动标签系统）
                self.auto_tagging_service.apply_auto_tags(
                    user_id, matched_tags, 'ad_tracking', str(tracking_id)
                )

        except Exception as e:
            logger.error("应用自动标签失败", extra={
                'extra_fields': {
                    'tracking_id': tracking_id,
                    'user_id': user_id,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, exc_info=True)

    def process_chat_record(self, chat_record: TgGroupChatHistory) -> Dict[str, int]:
        """
        处理单条聊天记录

        Args:
            chat_record: 聊天记录对象

        Returns:
            处理统计 {'urls': count, 'accounts': count, 'total_items': count}
        """
        if not chat_record.message:
            return {'urls': 0, 'telegram_accounts': 0, 'total_items': 0}

        return self._process_and_track_content(
            content_text=chat_record.message,
            source_type='chat',
            source_id=str(chat_record.id),
            user_id=str(chat_record.user_id) if chat_record.user_id else None,
            chat_id=str(chat_record.chat_id) if chat_record.chat_id else None,
            apply_tags=True
        )

    def process_user_info(self, user_info: TgGroupUserInfo) -> Dict[str, int]:
        """
        处理用户信息（昵称、描述）

        Args:
            user_info: 用户信息对象

        Returns:
            处理统计 {'urls': count, 'accounts': count, 'total_items': count}
        """
        stats = {
            'urls': 0,
            'telegram_accounts': 0,
            'total_items': 0
        }

        user_id = str(user_info.user_id)

        # 处理昵称
        if user_info.nickname:
            nickname_stats = self._process_and_track_content(
                content_text=user_info.nickname,
                source_type='nickname',
                source_id=user_id,
                user_id=user_id,
                chat_id=None,
                apply_tags=True
            )
            stats['urls'] += nickname_stats['urls']
            stats['telegram_accounts'] += nickname_stats['telegram_accounts']
            stats['total_items'] += nickname_stats['total_items']

        # 处理描述
        if user_info.desc:
            desc_stats = self._process_and_track_content(
                content_text=user_info.desc,
                source_type='user_desc',
                source_id=user_id,
                user_id=user_id,
                chat_id=None,
                apply_tags=True
            )
            stats['urls'] += desc_stats['urls']
            stats['telegram_accounts'] += desc_stats['telegram_accounts']
            stats['total_items'] += desc_stats['total_items']

        return stats

    def process_group_info(self, group: TgGroup) -> Dict[str, int]:
        """
        处理群组信息（群介绍）

        Args:
            group: 群组对象

        Returns:
            处理统计 {'urls': count, 'accounts': count, 'total_items': count}
        """
        if not group.group_intro:
            return {'urls': 0, 'telegram_accounts': 0, 'total_items': 0}

        chat_id = str(group.chat_id)

        return self._process_and_track_content(
            content_text=group.group_intro,
            source_type='group_intro',
            source_id=chat_id,
            user_id=None,
            chat_id=chat_id,
            apply_tags=True  # 修复 bug：群组信息也应该应用自动标签
        )

    def tag_nonmainstream_website_titles(self, limit: int = None) -> Dict[str, int]:
        """
        为所有非主流域名网站的追踪记录标签化标题

        功能：
        1. 查询 AdTracking 表中的所有 URL 记录
        2. 检查是否为非主流域名
        3. 提取网站标题
        4. 应用自动标签
        5. 写入 UrlTagLog

        Args:
            limit: 限制处理数量（用于测试）

        Returns:
            处理统计 {'total': int, 'tagged': int, 'skipped': int, 'errors': int}
        """
        stats = {
            'total': 0,
            'tagged': 0,
            'skipped': 0,
            'errors': 0
        }

        try:
            # 查询所有 URL 类型的追踪记录
            query = AdTracking.query.filter(
                AdTracking.content_type == 'url'
            )

            if limit:
                query = query.limit(limit)

            tracking_records = query.all()
            logger.info("开始处理 URL 追踪记录", extra={
                'extra_fields': {
                    'total_records': len(tracking_records),
                    'limit': limit
                }
            })

            for record in tracking_records:
                try:
                    stats['total'] += 1

                    # 检查是否已有标签关联（避免重复）
                    existing_tags = AdTrackingTags.query.filter_by(
                        ad_tracking_id=record.id
                    ).count()

                    if existing_tags > 0:
                        logger.debug("追踪记录已有标签，跳过", extra={
                            'extra_fields': {
                                'tracking_id': record.id,
                                'tag_count': existing_tags
                            }
                        })
                        stats['skipped'] += 1
                        continue

                    # 获取追踪记录的 extra_info
                    extra_info = record.extra_info or {}

                    # 检查是否为主流域名
                    if extra_info.get('is_mainstream'):
                        logger.debug("跳过主流域名", extra={
                            'extra_fields': {
                                'tracking_id': record.id,
                                'domain': extra_info.get('domain')
                            }
                        })
                        stats['skipped'] += 1
                        continue

                    # 提取网站标题
                    website_title = extra_info.get('title')
                    if not website_title or not website_title.strip():
                        logger.debug("追踪记录无标题", extra={
                            'extra_fields': {
                                'tracking_id': record.id
                            }
                        })
                        stats['skipped'] += 1
                        continue

                    # 应用标签：第1步 - 匹配关键词
                    domain = extra_info.get('domain', '')
                    matched_tags = self.auto_tagging_service.process_website_title(
                        record.content,
                        domain,
                        website_title,
                        tracking_id=str(record.id)
                    )

                    if not matched_tags:
                        logger.debug("未找到匹配的标签", extra={
                            'extra_fields': {
                                'tracking_id': record.id,
                                'title': website_title
                            }
                        })
                        stats['skipped'] += 1
                        continue

                    # 应用标签：第2步 - 写入 UrlTagLog（不涉及 AutoTagLog）
                    tagged_count = self.auto_tagging_service.apply_website_tags(
                        record.content,
                        domain,
                        website_title,
                        matched_tags,
                        tracking_id=record.id,
                        source_type='website_title',
                        commit=False  # 批量处理，最后一起提交
                    )

                    if tagged_count > 0:
                        stats['tagged'] += tagged_count
                        logger.info("追踪记录标签应用完成", extra={
                            'extra_fields': {
                                'tracking_id': record.id,
                                'tag_count': tagged_count,
                                'domain': domain
                            }
                        })

                except Exception as e:
                    logger.error("处理追踪记录失败", extra={
                        'extra_fields': {
                            'tracking_id': record.id,
                            'error_type': type(e).__name__,
                            'error_message': str(e)
                        }
                    }, exc_info=True)
                    stats['errors'] += 1

            # 批量提交
            db.session.commit()
            logger.info("非主流 URL 标签处理完成", extra={
                'extra_fields': {
                    'total': stats['total'],
                    'tagged': stats['tagged'],
                    'skipped': stats['skipped'],
                    'errors': stats['errors']
                }
            })

        except Exception as e:
            db.session.rollback()
            logger.error("非主流 URL 标签处理失败", extra={
                'extra_fields': {
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, exc_info=True)
            raise

        return stats

    def run_daily_task(self, target_date: datetime = None) -> Dict[str, Any]:
        """
        每日增量任务：处理指定日期的聊天记录

        Args:
            target_date: 目标日期，默认为昨天

        Returns:
            执行结果统计
        """
        perf_logger = PerformanceLogger()
        perf_logger.start('daily_task')

        if target_date is None:
            target_date = datetime.now() - timedelta(days=1)

        start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        logger.info("启动每日广告追踪任务", extra={
            'extra_fields': {
                'target_date': target_date.strftime('%Y-%m-%d'),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
        })

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

            logger.info(f"查询到 {len(chat_records)} 条聊天记录", extra={
                'extra_fields': {
                    'record_count': len(chat_records),
                    'target_date': target_date.strftime('%Y-%m-%d')
                }
            })

            for record in chat_records:
                try:
                    stats = self.process_chat_record(record)
                    result['chat_records_processed'] += 1
                    result['total_urls'] += stats['urls']
                    result['total_accounts'] += stats['telegram_accounts']
                    result['total_items'] += stats['total_items']
                except Exception as e:
                    logger.error("处理聊天记录失败", extra={
                        'extra_fields': {
                            'record_id': record.id,
                            'error_type': type(e).__name__,
                            'error_message': str(e)
                        }
                    }, exc_info=True)
                    result['errors'] += 1

            # 处理当天更新的用户信息
            user_infos = TgGroupUserInfo.query.filter(
                TgGroupUserInfo.updated_at >= start_time,
                TgGroupUserInfo.updated_at <= end_time
            ).all()

            logger.info(f"查询到 {len(user_infos)} 条用户信息", extra={
                'extra_fields': {
                    'user_info_count': len(user_infos),
                    'target_date': target_date.strftime('%Y-%m-%d')
                }
            })

            for user_info in user_infos:
                try:
                    stats = self.process_user_info(user_info)
                    result['user_infos_processed'] += 1
                    result['total_urls'] += stats['urls']
                    result['total_accounts'] += stats['telegram_accounts']
                    result['total_items'] += stats['total_items']
                except Exception as e:
                    logger.error("处理用户信息失败", extra={
                        'extra_fields': {
                            'user_id': user_info.user_id,
                            'error_type': type(e).__name__,
                            'error_message': str(e)
                        }
                    }, exc_info=True)
                    result['errors'] += 1

            # 处理当天更新的群组信息
            groups = TgGroup.query.filter(
                TgGroup.updated_at >= start_time,
                TgGroup.updated_at <= end_time
            ).all()

            logger.info(f"查询到 {len(groups)} 个群组", extra={
                'extra_fields': {
                    'group_count': len(groups),
                    'target_date': target_date.strftime('%Y-%m-%d')
                }
            })

            for group in groups:
                try:
                    stats = self.process_group_info(group)
                    result['group_infos_processed'] += 1
                    result['total_urls'] += stats['urls']
                    result['total_accounts'] += stats['telegram_accounts']
                    result['total_items'] += stats['total_items']
                except Exception as e:
                    logger.error("处理群组信息失败", extra={
                        'extra_fields': {
                            'chat_id': group.chat_id,
                            'error_type': type(e).__name__,
                            'error_message': str(e)
                        }
                    }, exc_info=True)
                    result['errors'] += 1

            # 提交数据库
            db.session.commit()
            result['status'] = 'success'

            logger.info("每日广告追踪任务完成", extra={
                'extra_fields': {
                    'target_date': target_date.strftime('%Y-%m-%d'),
                    'chat_records': result['chat_records_processed'],
                    'user_infos': result['user_infos_processed'],
                    'group_infos': result['group_infos_processed'],
                    'total_urls': result['total_urls'],
                    'total_accounts': result['total_accounts'],
                    'total_items': result['total_items'],
                    'errors': result['errors'],
                    'status': result['status']
                }
            })

            perf_logger.end(success=True, **result)

        except Exception as e:
            db.session.rollback()
            logger.error("每日广告追踪任务失败", extra={
                'extra_fields': {
                    'target_date': target_date.strftime('%Y-%m-%d'),
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, exc_info=True)
            perf_logger.end(success=False, error=str(e))

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
        perf_logger = PerformanceLogger()
        perf_logger.start('historical_batch', batch_size=batch_size, max_batches=max_batches)

        logger.info("启动历史广告追踪批量处理任务", extra={
            'extra_fields': {
                'batch_size': batch_size,
                'max_batches': max_batches
            }
        })

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
                        logger.error("处理聊天记录失败", extra={
                            'extra_fields': {
                                'record_id': record.id,
                                'batch': batch_count,
                                'error_type': type(e).__name__,
                                'error_message': str(e)
                            }
                        }, exc_info=True)
                        result['errors'] += 1

                # 提交当前批次
                db.session.commit()
                chat_offset += batch_size
                batch_count += 1
                result['batches_processed'] = batch_count

                logger.info("批量处理进度", extra={
                    'extra_fields': {
                        'batch_number': batch_count,
                        'chat_records_processed': result['chat_records_processed'],
                        'total_urls': result['total_urls'],
                        'total_accounts': result['total_accounts']
                    }
                })
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
                        logger.error("处理用户信息失败", extra={
                            'extra_fields': {
                                'user_id': user_info.user_id,
                                'batch': batch_count,
                                'error_type': type(e).__name__,
                                'error_message': str(e)
                            }
                        }, exc_info=True)
                        result['errors'] += 1

                db.session.commit()
                user_offset += batch_size
                logger.info("用户信息批量处理进度", extra={
                    'extra_fields': {
                        'user_infos_processed': result['user_infos_processed'],
                        'total_urls': result['total_urls'],
                        'total_accounts': result['total_accounts']
                    }
                })
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
                        logger.error("处理群组信息失败", extra={
                            'extra_fields': {
                                'chat_id': group.chat_id,
                                'batch': batch_count,
                                'error_type': type(e).__name__,
                                'error_message': str(e)
                            }
                        }, exc_info=True)
                        result['errors'] += 1

                db.session.commit()
                group_offset += batch_size
                logger.info("群组信息批量处理进度", extra={
                    'extra_fields': {
                        'group_infos_processed': result['group_infos_processed'],
                        'total_urls': result['total_urls'],
                        'total_accounts': result['total_accounts']
                    }
                })
                time.sleep(0.5)

            result['status'] = 'success'
            logger.info("历史广告追踪批量处理任务完成", extra={
                'extra_fields': {
                    'chat_records': result['chat_records_processed'],
                    'user_infos': result['user_infos_processed'],
                    'group_infos': result['group_infos_processed'],
                    'total_urls': result['total_urls'],
                    'total_accounts': result['total_accounts'],
                    'total_items': result['total_items'],
                    'batches_processed': result['batches_processed'],
                    'errors': result['errors'],
                    'status': result['status']
                }
            })

            perf_logger.end(success=True, **result)

        except Exception as e:
            db.session.rollback()
            logger.error("历史广告追踪批量处理任务失败", extra={
                'extra_fields': {
                    'batch_size': batch_size,
                    'max_batches': max_batches,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, exc_info=True)
            perf_logger.end(success=False, error=str(e))

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
