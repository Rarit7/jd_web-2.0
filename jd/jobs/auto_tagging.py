import datetime
import logging
from typing import Dict, List, Any, Optional

from jd import db
from jd.models.tag_keyword_mapping import TagKeywordMapping
from jd.models.auto_tag_log import AutoTagLog
from jd.models.url_tag_log import UrlTagLog
from jd.models.tg_group_user_tag import TgGroupUserTag
from jd.models.tg_group_user_info import TgGroupUserInfo
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group import TgGroup
from jd.helpers.keyword_matcher import KeywordMatcherCache

logger = logging.getLogger(__name__)


class AutoTaggingService:
    """
    自动标签服务
    负责根据关键词自动为用户添加标签
    """

    def __init__(self, use_ac_automaton: bool = True):
        """
        初始化自动标签服务

        Args:
            use_ac_automaton: 是否使用AC自动机优化匹配（默认启用）
        """
        self._keyword_cache = {}  # 关键词映射缓存
        self._cache_timestamp = None  # 缓存时间戳
        self._cache_ttl = 300  # 缓存5分钟
        self._use_ac_automaton = use_ac_automaton  # 是否使用AC自动机
        self._matcher_cache = KeywordMatcherCache(cache_ttl=self._cache_ttl) if use_ac_automaton else None

    def _get_keyword_mappings(self) -> List[TagKeywordMapping]:
        """获取所有激活的关键词映射，带缓存机制"""
        current_time = datetime.datetime.now()

        # 检查缓存是否有效
        if (self._cache_timestamp and
            (current_time - self._cache_timestamp).total_seconds() < self._cache_ttl and
            self._keyword_cache):
            logger.debug("Using cached keyword mappings")
            return self._keyword_cache

        # 重新获取数据
        mappings = TagKeywordMapping.query.filter_by(is_active=True).all()
        self._keyword_cache = mappings
        self._cache_timestamp = current_time

        logger.info(f"Loaded {len(mappings)} active keyword mappings")
        return mappings

    def process_text_for_tags(self, text: str, user_id: str, source_type: str,
                             source_id: str = None) -> List[Dict[str, Any]]:
        """
        处理文本进行自动标签匹配

        Args:
            text: 要处理的文本
            user_id: 用户ID
            source_type: 来源类型 (chat, nickname, desc)
            source_id: 来源记录ID

        Returns:
            匹配到的标签信息列表
        """
        if not text or not text.strip():
            return []

        keyword_mappings = self._get_keyword_mappings()
        matched_tags = []

        # 使用AC自动机或简单匹配
        if self._use_ac_automaton and self._matcher_cache:
            # AC自动机匹配（快2倍）
            matches = self._matcher_cache.match_keywords(text, keyword_mappings)

            for match in matches:
                # 检查是否已经有此标签，避免重复
                existing_log = AutoTagLog.query.filter_by(
                    tg_user_id=user_id,
                    tag_id=match['tag_id']
                ).first()

                if not existing_log:
                    matched_tags.append(match)
                    logger.debug(f"Matched keyword '{match['keyword']}' for user {user_id}")
        else:
            # 简单匹配（兼容模式）
            for mapping in keyword_mappings:
                if mapping.keyword.lower() in text.lower():
                    # 检查是否已经有此标签，避免重复
                    existing_log = AutoTagLog.query.filter_by(
                        tg_user_id=user_id,
                        tag_id=mapping.tag_id
                    ).first()

                    if not existing_log:
                        matched_tags.append({
                            'tag_id': mapping.tag_id,
                            'keyword': mapping.keyword,
                            'auto_focus': mapping.auto_focus,
                            'mapping_id': mapping.id
                        })
                        logger.debug(f"Matched keyword '{mapping.keyword}' for user {user_id}")

        return matched_tags

    def _build_detail_info(self, source_type: str, user_id: str, keyword: str,
                          source_id: str, context_data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        构建 detail_info JSON 数据

        Args:
            source_type: 来源类型 (chat, nickname, desc, website_title)
            user_id: 用户ID (对于网站可能为空或URL)
            keyword: 触发的关键词
            source_id: 来源记录ID
            context_data: 上下文数据

        Returns:
            detail_info 字典或 None
        """
        if not context_data:
            return None

        try:
            if source_type == 'chat':
                # 聊天消息类型
                return {
                    'user_id': str(user_id),
                    'user_nickname': context_data.get('user_nickname', ''),
                    'user_username': context_data.get('user_username', ''),
                    'chat_id': str(context_data.get('chat_id', '')),
                    'chat_title': context_data.get('chat_title', ''),
                    'message_id': str(source_id) if source_id else '',
                    'message_text': (context_data.get('message_text', '') or '')[:500],  # 限制长度
                    'message_date': context_data.get('message_date', ''),
                    'matched_text': keyword
                }

            elif source_type == 'nickname':
                # 用户昵称类型
                return {
                    'user_id': str(user_id),
                    'user_nickname': context_data.get('user_nickname', ''),
                    'user_username': context_data.get('user_username', ''),
                    'nickname': context_data.get('nickname', context_data.get('user_nickname', '')),
                    'matched_text': keyword
                }

            elif source_type == 'desc':
                # 用户描述类型
                return {
                    'user_id': str(user_id),
                    'user_nickname': context_data.get('user_nickname', ''),
                    'user_username': context_data.get('user_username', ''),
                    'desc': context_data.get('desc', ''),
                    'matched_text': keyword
                }

            elif source_type == 'website_title':
                # 网站标题类型
                return {
                    'url': context_data.get('url', ''),
                    'domain': context_data.get('domain', ''),
                    'website_title': (context_data.get('website_title', '') or '')[:500],  # 限制长度
                    'matched_text': keyword
                }

            elif source_type == 'website_content':
                # 网站内容类型（预留，后续可扩展）
                return {
                    'url': context_data.get('url', ''),
                    'domain': context_data.get('domain', ''),
                    'website_title': context_data.get('website_title', ''),
                    'matched_text': keyword,
                    'content_snippet': (context_data.get('content_snippet', '') or '')[:500]
                }

        except Exception as e:
            logger.warning(f"Failed to build detail_info: {str(e)}")
            return None

        return None

    def apply_auto_tags(self, user_id: str, matched_tags: List[Dict[str, Any]],
                       source_type: str, source_id: str = None,
                       context_data: Dict[str, Any] = None, commit: bool = True) -> int:
        """
        应用自动标签

        Args:
            user_id: 用户ID
            matched_tags: 匹配到的标签信息列表
            source_type: 来源类型
            source_id: 来源记录ID
            context_data: 上下文数据，用于构建 detail_info
            commit: 是否立即提交，批量处理时设为False

        Returns:
            成功应用的标签数量
        """
        if not matched_tags:
            return 0

        applied_count = 0

        try:
            for tag_info in matched_tags:
                # 检查用户标签是否已存在
                existing_user_tag = TgGroupUserTag.query.filter_by(
                    tg_user_id=user_id,
                    tag_id=tag_info['tag_id']
                ).first()

                if not existing_user_tag:
                    # 添加用户标签
                    user_tag = TgGroupUserTag(
                        tg_user_id=user_id,
                        tag_id=tag_info['tag_id']
                    )
                    db.session.add(user_tag)

                # 构建 detail_info
                detail_info = self._build_detail_info(
                    source_type, user_id, tag_info['keyword'],
                    source_id, context_data
                )

                # 记录自动标签日志
                auto_log = AutoTagLog(
                    tg_user_id=user_id,
                    tag_id=tag_info['tag_id'],
                    keyword=tag_info['keyword'],
                    source_type=source_type,
                    source_id=source_id,
                    detail_info=detail_info
                )
                db.session.add(auto_log)

                # 如果需要自动关注
                if tag_info['auto_focus']:
                    user_info = TgGroupUserInfo.query.filter_by(user_id=user_id).first()
                    if user_info:
                        user_info.is_key_focus = True
                        logger.info(f"Auto focus enabled for user {user_id}")

                applied_count += 1
                logger.debug(f"Applied tag {tag_info['tag_id']} to user {user_id} "
                            f"via keyword '{tag_info['keyword']}'")

            if commit:
                db.session.commit()
                logger.info(f"Successfully applied {applied_count} auto tags for user {user_id}")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to apply auto tags for user {user_id}: {str(e)}")
            raise

        return applied_count

    def process_chat_message(self, message_data: Dict[str, Any]) -> int:
        """
        处理聊天消息进行自动标签

        Args:
            message_data: 消息数据字典

        Returns:
            应用的标签数量
        """
        if not message_data.get('message') or not message_data.get('user_id'):
            return 0

        try:
            matched_tags = self.process_text_for_tags(
                message_data['message'],
                message_data['user_id'],
                'chat',
                message_data.get('message_id')
            )

            if matched_tags:
                # 构建上下文数据
                context_data = {
                    'user_nickname': message_data.get('user_nickname', ''),
                    'user_username': message_data.get('user_username', ''),
                    'chat_id': message_data.get('chat_id', ''),
                    'chat_title': message_data.get('chat_title', ''),
                    'message_text': message_data.get('message', ''),
                    'message_date': message_data.get('message_date', '')
                }

                return self.apply_auto_tags(
                    message_data['user_id'],
                    matched_tags,
                    'chat',
                    message_data.get('message_id'),
                    context_data
                )

        except Exception as e:
            logger.error(f"Failed to process chat message for auto tagging: {str(e)}")

        return 0

    def process_user_info(self, user_data: Dict[str, Any]) -> int:
        """
        处理用户信息进行自动标签

        Args:
            user_data: 用户信息数据字典

        Returns:
            应用的标签数量
        """
        if not user_data.get('user_id'):
            return 0

        total_applied = 0

        # 检测用户名、昵称、描述中的关键词
        text_sources = [
            ('nickname', user_data.get('nickname', '')),
            ('desc', user_data.get('desc', ''))
        ]

        try:
            for source_type, text in text_sources:
                if text and text.strip():
                    matched_tags = self.process_text_for_tags(
                        text,
                        user_data['user_id'],
                        source_type,
                        user_data['user_id']  # 用户信息的source_id使用user_id
                    )

                    if matched_tags:
                        # 构建上下文数据
                        if source_type == 'nickname':
                            context_data = {
                                'user_nickname': text,
                                'user_username': user_data.get('username', ''),
                                'nickname': text
                            }
                        else:  # desc
                            context_data = {
                                'user_nickname': user_data.get('nickname', ''),
                                'user_username': user_data.get('username', ''),
                                'desc': text
                            }

                        applied = self.apply_auto_tags(
                            user_data['user_id'],
                            matched_tags,
                            source_type,
                            user_data['user_id'],
                            context_data
                        )
                        total_applied += applied

        except Exception as e:
            logger.error(f"Failed to process user info for auto tagging: {str(e)}")

        return total_applied

    def process_chat_history_batch(self, chat_records: List[TgGroupChatHistory],
                                  batch_commit_size: int = 100) -> Dict[str, int]:
        """
        批量处理聊天记录进行自动标签（优化版）

        优化点：
        1. 关键词映射缓存（已有）
        2. 批量提交（每batch_commit_size条）
        3. 预加载用户已有标签，减少重复查询

        Args:
            chat_records: 聊天记录列表
            batch_commit_size: 批量提交大小

        Returns:
            处理统计信息
        """
        stats = {
            'total_processed': 0,
            'total_tags_applied': 0,
            'failed_count': 0
        }

        if not chat_records:
            return stats

        # 预加载所有涉及用户的现有标签（减少N+1查询）
        user_ids = list(set([str(r.user_id) for r in chat_records if r.user_id]))
        existing_user_tags = {}

        logger.info(f"Preloading existing tags for {len(user_ids)} users")
        for user_id in user_ids:
            tags = TgGroupUserTag.query.filter_by(tg_user_id=user_id).all()
            existing_user_tags[user_id] = set([t.tag_id for t in tags])

        # 预加载已有的自动标签日志（避免重复）
        existing_logs = {}
        for user_id in user_ids:
            logs = AutoTagLog.query.filter_by(tg_user_id=user_id).all()
            existing_logs[user_id] = set([(log.tag_id, log.source_type, log.source_id) for log in logs])

        # 预加载群组信息（避免N+1查询）
        chat_ids = list(set([r.chat_id for r in chat_records if r.chat_id]))
        group_info_map = {}
        if chat_ids:
            logger.info(f"Preloading group info for {len(chat_ids)} groups")
            groups = TgGroup.query.filter(TgGroup.chat_id.in_(chat_ids)).all()
            group_info_map = {g.chat_id: g.title or '' for g in groups}

        # 批量处理
        for i, record in enumerate(chat_records):
            try:
                if record.message:
                    user_id = str(record.user_id)
                    source_id = str(record.id)

                    matched_tags = self.process_text_for_tags(
                        record.message,
                        user_id,
                        'chat',
                        source_id
                    )

                    # 过滤已存在的日志记录（避免重复）
                    if user_id in existing_logs:
                        matched_tags = [
                            t for t in matched_tags
                            if (t['tag_id'], 'chat', source_id) not in existing_logs[user_id]
                        ]

                    if matched_tags:
                        # 构建上下文数据
                        context_data = {
                            'user_nickname': record.nickname or '',
                            'user_username': record.username or '',
                            'chat_id': str(record.chat_id) if record.chat_id else '',
                            'chat_title': group_info_map.get(record.chat_id, ''),  # 使用预加载的群组名称
                            'message_text': record.message or '',
                            'message_date': record.postal_time.isoformat() if record.postal_time else ''
                        }

                        applied = self.apply_auto_tags(
                            user_id, matched_tags, 'chat', source_id,
                            context_data,
                            commit=False  # 不立即提交
                        )
                        stats['total_tags_applied'] += applied

                        # 更新内存缓存
                        for tag in matched_tags:
                            existing_user_tags.setdefault(user_id, set()).add(tag['tag_id'])
                            existing_logs.setdefault(user_id, set()).add((tag['tag_id'], 'chat', source_id))

                stats['total_processed'] += 1

                # 每batch_commit_size条提交一次
                if (i + 1) % batch_commit_size == 0:
                    try:
                        db.session.commit()
                        logger.info(f"Committed batch at {i + 1}/{len(chat_records)} records")
                    except Exception as e:
                        logger.error(f"Failed to commit batch at {i + 1}: {str(e)}")
                        db.session.rollback()
                        stats['failed_count'] += batch_commit_size

            except Exception as e:
                stats['failed_count'] += 1
                logger.error(f"Failed to process chat record {record.id}: {str(e)}")

        # 提交剩余记录
        try:
            db.session.commit()
            logger.info(f"Committed final batch")
        except Exception as e:
            logger.error(f"Failed to commit final batch: {str(e)}")
            db.session.rollback()

        logger.info(f"Batch processing completed: {stats}")
        return stats

    def process_user_info_batch(self, user_infos: List[TgGroupUserInfo],
                               batch_commit_size: int = 100) -> Dict[str, int]:
        """
        批量处理用户信息进行自动标签（优化版）

        Args:
            user_infos: 用户信息列表
            batch_commit_size: 批量提交大小

        Returns:
            处理统计信息
        """
        stats = {
            'total_processed': 0,
            'total_tags_applied': 0,
            'failed_count': 0
        }

        if not user_infos:
            return stats

        # 预加载用户标签
        user_ids = list(set([str(u.user_id) for u in user_infos if u.user_id]))
        existing_user_tags = {}

        logger.info(f"Preloading existing tags for {len(user_ids)} users")
        for user_id in user_ids:
            tags = TgGroupUserTag.query.filter_by(tg_user_id=user_id).all()
            existing_user_tags[user_id] = set([t.tag_id for t in tags])

        # 预加载自动标签日志
        existing_logs = {}
        for user_id in user_ids:
            logs = AutoTagLog.query.filter_by(tg_user_id=user_id).all()
            existing_logs[user_id] = set([(log.tag_id, log.source_type, log.source_id) for log in logs])

        for i, user_info in enumerate(user_infos):
            try:
                user_id = str(user_info.user_id)

                # 处理昵称和描述两个字段
                text_sources = [
                    ('nickname', user_info.nickname or ''),
                    ('desc', user_info.desc or '')
                ]

                for source_type, text in text_sources:
                    if not text.strip():
                        continue

                    matched_tags = self.process_text_for_tags(
                        text,
                        user_id,
                        source_type,
                        user_id
                    )

                    # 过滤已存在的日志（避免重复打标签）
                    if user_id in existing_logs:
                        matched_tags = [
                            t for t in matched_tags
                            if (t['tag_id'], source_type, user_id) not in existing_logs[user_id]
                        ]

                    if matched_tags:
                        # 构建上下文数据
                        context_data = {
                            'user_nickname': user_info.nickname or '',
                            'user_username': user_info.username or '',
                        }

                        if source_type == 'nickname':
                            context_data['nickname'] = user_info.nickname or ''
                        else:  # desc
                            context_data['desc'] = user_info.desc or ''

                        applied = self.apply_auto_tags(
                            user_id, matched_tags, source_type, user_id,
                            context_data=context_data,
                            commit=False
                        )
                        stats['total_tags_applied'] += applied

                        # 更新缓存
                        for tag in matched_tags:
                            existing_user_tags.setdefault(user_id, set()).add(tag['tag_id'])
                            existing_logs.setdefault(user_id, set()).add((tag['tag_id'], source_type, user_id))

                stats['total_processed'] += 1

                # 批量提交
                if (i + 1) % batch_commit_size == 0:
                    try:
                        db.session.commit()
                        logger.info(f"Committed batch at {i + 1}/{len(user_infos)} users")
                    except Exception as e:
                        logger.error(f"Failed to commit batch at {i + 1}: {str(e)}")
                        db.session.rollback()
                        stats['failed_count'] += batch_commit_size

            except Exception as e:
                stats['failed_count'] += 1
                logger.error(f"Failed to process user info {user_info.id}: {str(e)}")

        # 提交剩余记录
        try:
            db.session.commit()
            logger.info(f"Committed final batch")
        except Exception as e:
            logger.error(f"Failed to commit final batch: {str(e)}")
            db.session.rollback()

        logger.info(f"User info batch processing completed: {stats}")
        return stats

    def process_website_title(self, url: str, domain: str, website_title: str,
                             tracking_id: str = None, source_id: str = None) -> List[Dict[str, Any]]:
        """
        处理网站标题进行自动标签匹配

        Args:
            url: 网站URL
            domain: 域名
            website_title: 网站标题
            tracking_id: 追踪ID (用于标签关联，来自 ad_tracking.id)
            source_id: 来源记录ID (可选，默认使用tracking_id)

        Returns:
            匹配到的标签信息列表
        """
        if not website_title or not website_title.strip():
            return []

        source_id = source_id or tracking_id or url

        try:
            matched_tags = self.process_text_for_tags(
                website_title,
                tracking_id or url,  # 用tracking_id或URL作为"用户ID"
                'website_title',
                source_id
            )

            logger.debug(f"Matched {len(matched_tags)} tags for website title: {website_title[:50]}")
            return matched_tags

        except Exception as e:
            logger.error(f"Failed to process website title for auto tagging: {str(e)}")
            return []

    def apply_website_tags(self, url: str, domain: str, website_title: str,
                          matched_tags: List[Dict[str, Any]], tracking_id: int = None,
                          source_type: str = 'website_title', commit: bool = True) -> int:
        """
        应用网站标题标签到广告追踪记录

        Args:
            url: 网站URL
            domain: 域名
            website_title: 网站标题
            matched_tags: 匹配到的标签信息列表
            tracking_id: 追踪ID (ad_tracking.id，整数)
            source_type: 标签来源类型 (website_title/website_content)
            commit: 是否立即提交

        Returns:
            成功应用的标签数量
        """
        if not matched_tags or not tracking_id:
            return 0

        applied_count = 0

        try:
            for tag_info in matched_tags:
                # 检查是否已存在（避免重复）
                existing_log = UrlTagLog.query.filter_by(
                    tracking_id=tracking_id,
                    tag_id=tag_info['tag_id']
                ).first()

                if existing_log:
                    logger.debug(f"Tag {tag_info['tag_id']} already exists for tracking {tracking_id}")
                    continue

                # 构建上下文数据
                context_data = {
                    'url': url,
                    'domain': domain,
                    'website_title': website_title,
                    'matched_text': tag_info['keyword']
                }

                # 记录URL标签日志（使用新的 UrlTagLog 表）
                url_tag_log = UrlTagLog(
                    tracking_id=tracking_id,
                    url=url,
                    domain=domain,
                    tag_id=tag_info['tag_id'],
                    keyword=tag_info['keyword'],
                    source_type=source_type,
                    detail_info=self._build_detail_info(
                        source_type, str(tracking_id), tag_info['keyword'],
                        str(tracking_id), context_data
                    )
                )
                db.session.add(url_tag_log)

                applied_count += 1
                logger.debug(f"Applied tag {tag_info['tag_id']} to URL {domain} "
                            f"via keyword '{tag_info['keyword']}'")

            if commit:
                db.session.commit()
                logger.info(f"Successfully applied {applied_count} auto tags for URL {domain}")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to apply website tags for {url}: {str(e)}")
            raise

        return applied_count

    def process_and_tag_website(self, url: str, domain: str, website_title: str,
                               tracking_id: int = None, source_type: str = 'website_title') -> int:
        """
        一体化处理：从网站标题匹配标签并应用

        Args:
            url: 网站URL
            domain: 域名
            website_title: 网站标题
            tracking_id: 追踪ID (ad_tracking.id，整数)
            source_type: 标签来源类型 (website_title/website_content)

        Returns:
            成功应用的标签数量
        """
        # 第1步：匹配标签
        matched_tags = self.process_website_title(
            url, domain, website_title,
            str(tracking_id) if tracking_id else None
        )

        if not matched_tags:
            return 0

        # 第2步：应用标签
        return self.apply_website_tags(
            url, domain, website_title,
            matched_tags, tracking_id, source_type
        )

    def process_website_batch(self, websites: List[Dict[str, str]],
                             batch_commit_size: int = 100) -> Dict[str, int]:
        """
        批量处理网站标题进行自动标签（优化版）

        Args:
            websites: 网站数据列表，每个元素为：
                {
                    'url': str,
                    'domain': str,
                    'website_title': str,
                    'tracking_id': str (可选),
                    'source_id': str (可选)
                }
            batch_commit_size: 批量提交大小

        Returns:
            处理统计信息
        """
        stats = {
            'total_processed': 0,
            'total_tags_applied': 0,
            'failed_count': 0
        }

        if not websites:
            return stats

        # 预加载所有关键词映射
        keyword_mappings = self._get_keyword_mappings()
        if not keyword_mappings:
            logger.warning("No keyword mappings found")
            return stats

        logger.info(f"Starting batch processing of {len(websites)} websites")

        for i, website_data in enumerate(websites):
            try:
                url = website_data.get('url', '')
                domain = website_data.get('domain', '')
                website_title = website_data.get('website_title', '')
                tracking_id = website_data.get('tracking_id', url)  # 默认使用URL
                source_id = website_data.get('source_id', tracking_id)

                if not website_title or not website_title.strip():
                    logger.debug(f"Skipping website with empty title: {url}")
                    stats['total_processed'] += 1
                    continue

                # 匹配标签
                matched_tags = self.process_text_for_tags(
                    website_title,
                    tracking_id,
                    'website_title',
                    source_id
                )

                if matched_tags:
                    # 应用标签
                    context_data = {
                        'url': url,
                        'domain': domain,
                        'website_title': website_title
                    }

                    applied = self.apply_website_tags(
                        url, domain, website_title,
                        matched_tags, tracking_id, source_id,
                        commit=False
                    )
                    stats['total_tags_applied'] += applied

                stats['total_processed'] += 1

                # 每batch_commit_size条提交一次
                if (i + 1) % batch_commit_size == 0:
                    try:
                        db.session.commit()
                        logger.info(f"Committed batch at {i + 1}/{len(websites)} websites")
                    except Exception as e:
                        logger.error(f"Failed to commit batch at {i + 1}: {str(e)}")
                        db.session.rollback()
                        stats['failed_count'] += batch_commit_size

            except Exception as e:
                stats['failed_count'] += 1
                logger.error(f"Failed to process website {website_data.get('url', 'unknown')}: {str(e)}")

        # 提交剩余记录
        try:
            db.session.commit()
            logger.info(f"Committed final batch of websites")
        except Exception as e:
            logger.error(f"Failed to commit final batch: {str(e)}")
            db.session.rollback()

        logger.info(f"Website batch processing completed: {stats}")
        return stats

    def get_statistics(self) -> Dict[str, Any]:
        """获取自动标签统计信息"""
        try:
            # 总标签映射数
            total_mappings = TagKeywordMapping.query.filter_by(is_active=True).count()

            # 总自动标签记录数
            total_auto_tags = AutoTagLog.query.count()

            # 今日新增自动标签数
            today = datetime.date.today()
            today_auto_tags = AutoTagLog.query.filter(
                AutoTagLog.created_at >= today
            ).count()

            # 按来源类型统计
            source_type_stats = db.session.query(
                AutoTagLog.source_type,
                db.func.count(AutoTagLog.id).label('count')
            ).group_by(AutoTagLog.source_type).all()

            return {
                'total_mappings': total_mappings,
                'total_auto_tags': total_auto_tags,
                'today_auto_tags': today_auto_tags,
                'source_type_stats': [
                    {'source_type': stat.source_type, 'count': stat.count}
                    for stat in source_type_stats
                ]
            }

        except Exception as e:
            logger.error(f"Failed to get auto tagging statistics: {str(e)}")
            return {}


def main():
    """主函数，用于测试自动标签功能"""
    # 延迟导入，避免重复注册 SQLAlchemy
    from jd import app

    with app.app_context():
        service = AutoTaggingService()

        # 获取统计信息
        stats = service.get_statistics()
        print("Auto Tagging Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()