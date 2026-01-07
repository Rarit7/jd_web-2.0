"""
广告分析数据提取 Celery 任务
用于从聊天记录中批量提取价格、交易方式、地理位置等信息
"""
import logging
from celery import current_task
from datetime import datetime, timedelta

from jd import db, app
from jCelery import celery
from jd.models.ad_tracking_price import AdTrackingPrice
from jd.models.ad_tracking_transaction_method import AdTrackingTransactionMethod
from jd.models.ad_tracking_geo_location import AdTrackingGeoLocation
from jd.models.ad_tracking_dark_keyword import AdTrackingDarkKeyword
from jd.models.ad_tracking_batch_process_log import AdTrackingBatchProcessLog
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.services.keyword_extraction_service import KeywordExtractionService
from jd.services.dark_keyword_extraction_service import DarkKeywordExtractionService
from jd.services.geo_location_service import GeoLocationService
from jd.services.cache_service import CacheService

logger = logging.getLogger(__name__)


@celery.task(bind=True, queue='jd.celery.first')
def process_batch_for_analysis(
    self,
    chat_id: str,
    batch_id: str,
    config: dict
):
    """
    处理批次数据进行分析

    Args:
        self: Celery Task 实例
        chat_id: 群组ID
        batch_id: 批次ID
        config: 处理配置
            {
                'include_price': bool,                # 是否提取价格
                'include_transaction': bool,          # 是否提取交易方式
                'include_geo': bool,                  # 是否提取地理位置
                'tag_ids': list,                      # 标签ID列表 (可选)
                'limit': int,                         # 最多处理的消息数 (默认10000)
                'start_date': str (ISO格式),          # 开始日期 (可选)
                'end_date': str (ISO格式)             # 结束日期 (可选)
            }

    Returns:
        dict: 处理结果
            {
                'batch_id': str,
                'success_count': int,
                'fail_count': int,
                'total': int,
                'error': str (如果有错误)
            }
    """
    # 建立 Flask 应用上下文（Celery 任务中访问数据库需要）
    # 预初始化 matcher 缓存，确保在应用上下文中执行
    with app.app_context():
        # 预初始化提取服务的 matcher，避免后续应用上下文丢失
        logger.info(f"预初始化提取服务 matcher (batch_id={batch_id})")
        try:
            if config.get('include_transaction', False):
                from jd.services.keyword_extraction_service import KeywordExtractionService
                _ = KeywordExtractionService._build_transaction_matcher()
            if config.get('include_geo', False):
                from jd.services.geo_location_service import GeoLocationService
                _ = GeoLocationService._build_geo_matcher()
            if config.get('include_dark_keyword', False):
                from jd.services.dark_keyword_extraction_service import DarkKeywordExtractionService
                _ = DarkKeywordExtractionService._build_dark_keyword_matcher()
        except Exception as e:
            logger.warning(f"Matcher 预初始化失败: {e}")

        return _process_batch_for_analysis_impl(self, chat_id, batch_id, config)


def _process_batch_for_analysis_impl(self, chat_id: str, batch_id: str, config: dict):
    """
    process_batch_for_analysis 的实现函数
    注意：此函数必须在 Flask 应用上下文中调用
    """
    batch = None
    try:
        logger.info(f"开始处理批次: batch_id={batch_id}, chat_id={chat_id}, 应用上下文活跃")

        # 获取或创建批次记录
        batch = AdTrackingBatchProcessLog.query.filter_by(batch_id=batch_id).first()
        if not batch:
            error_msg = f'批次 {batch_id} 不存在'
            logger.error(error_msg)
            return {'error': error_msg}

        # 标记开始处理
        batch.start_processing()
        db.session.commit()

        # 构建查询条件
        query = TgGroupChatHistory.query.filter_by(chat_id=chat_id)

        # 按日期范围筛选 (可选)
        if config.get('start_date'):
            try:
                start_date = datetime.fromisoformat(config['start_date'])
                query = query.filter(TgGroupChatHistory.postal_time >= start_date)
            except Exception as e:
                logger.warning(f"start_date 格式无效: {e}")

        if config.get('end_date'):
            try:
                end_date = datetime.fromisoformat(config['end_date'])
                query = query.filter(TgGroupChatHistory.postal_time <= end_date)
            except Exception as e:
                logger.warning(f"end_date 格式无效: {e}")

        # 获取聊天记录
        limit = config.get('limit', 10000)
        messages = query.order_by(TgGroupChatHistory.id).limit(limit).all()

        batch.total_messages = len(messages)
        db.session.commit()

        logger.info(f"批次 {batch_id} 获取 {len(messages)} 条消息，开始处理")

        success_count = 0
        fail_count = 0
        errors = []

        for idx, message in enumerate(messages):
            try:
                message_id = str(message.id) if message.id else None
                message_text = message.message or ''

                # 提取价格
                if config.get('include_price', False):
                    _extract_price_from_message(message, chat_id)

                # 提取交易方式
                if config.get('include_transaction', False):
                    _extract_transaction_method_from_message(message, chat_id)

                # 提取地理位置
                if config.get('include_geo', False):
                    _extract_geo_location_from_message(message, chat_id)

                # 提取黑词
                if config.get('include_dark_keyword', False):
                    _extract_dark_keyword_from_message(message, chat_id)

                success_count += 1

                # 每处理100条更新进度
                if (idx + 1) % 100 == 0:
                    batch.update_progress(success_count, fail_count, len(messages))
                    db.session.commit()

                    # 更新 Celery 任务进度
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current': idx + 1,
                            'total': len(messages),
                            'success': success_count,
                            'failed': fail_count
                        }
                    )
                    logger.info(f"批次 {batch_id} 处理进度: {idx + 1}/{len(messages)} (成功: {success_count}, 失败: {fail_count})")

            except Exception as e:
                fail_count += 1
                error_msg = f"处理消息 {idx} (ID={message.id}) 失败: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)
                # 详细记录异常类型
                logger.error(f"异常类型: {type(e).__name__}, 异常详情: {repr(e)}")

        # 标记完成
        batch.mark_as_completed()
        batch.update_progress(success_count, fail_count, len(messages))
        db.session.commit()

        # 清除相关缓存，确保前端获取最新数据
        _clear_analysis_cache(chat_id)

        logger.info(
            f"批次 {batch_id} 处理完成: 总数 {len(messages)}, "
            f"成功 {success_count}, 失败 {fail_count}"
        )

        return {
            'batch_id': batch_id,
            'chat_id': chat_id,
            'success_count': success_count,
            'fail_count': fail_count,
            'total': len(messages),
            'errors': errors[:10] if errors else []  # 返回前10个错误
        }

    except Exception as e:
        logger.error(f"批次 {batch_id} 处理异常: {str(e)}", exc_info=True)
        if batch:
            batch.mark_as_failed(str(e))
            try:
                db.session.commit()
            except Exception as commit_error:
                logger.error(f"批次状态更新失败: {commit_error}")

        return {
            'error': str(e),
            'batch_id': batch_id,
            'success_count': 0,
            'fail_count': 0,
            'total': 0
        }


def _extract_price_from_message(message: TgGroupChatHistory, chat_id: str):
    """
    从消息中提取价格

    使用优化的关键词提取服务，合并正则表达式，减少文本扫描次数：
    - 原始: 7 个独立的正则表达式遍历
    - 优化后: 2 个合并的正则表达式遍历
    - 性能提升: 7-10 倍

    Args:
        message: TgGroupChatHistory 消息对象
        chat_id: 群组ID
    """
    if not message:
        logger.debug(f"价格提取: 消息对象为 None")
        return

    message_text = message.message or ''
    if not message_text or not message_text.strip():
        logger.debug(f"价格提取: 消息 {message.id} 文本为空")
        return

    try:
        # 使用服务层提取价格
        logger.debug(f"价格提取: 开始处理消息 {message.id}, chat_id={chat_id}, 文本长度={len(message_text)}")
        prices = KeywordExtractionService.extract_prices(message_text)
        logger.debug(f"价格提取: 从消息 {message.id} 提取到 {len(prices)} 个价格")

        # 保存提取的价格
        if prices:
            for idx, price in enumerate(prices):
                try:
                    record = AdTrackingPrice(
                        chat_id=chat_id,
                        message_id=str(message.id) if message.id else None,
                        price_value=price['value'],
                        unit=price['unit'],
                        extracted_text=price['original_text'],
                        msg_date=message.postal_time.date() if message.postal_time else None
                    )
                    db.session.add(record)
                    logger.debug(f"价格提取: 添加记录 {idx+1}/{len(prices)}: {price['value']} {price['unit']}")
                except Exception as add_error:
                    logger.error(f"价格提取: 添加记录失败 {idx+1}/{len(prices)}: {add_error}")
                    raise

            # 提交数据库
            try:
                db.session.commit()
                logger.info(f"价格提取: ✅ 成功提交 {len(prices)} 个价格到数据库 (消息 {message.id})")
            except Exception as commit_error:
                logger.error(f"价格提取: ❌ 提交数据库失败 (消息 {message.id}): {commit_error}")
                db.session.rollback()
                raise
        else:
            logger.debug(f"价格提取: 消息 {message.id} 未提取到价格")

    except Exception as e:
        logger.error(f"价格提取失败 (消息 {message.id}): {str(e)}", exc_info=True)
        try:
            db.session.rollback()
        except Exception as rollback_error:
            logger.error(f"价格提取: 回滚失败: {rollback_error}")


def _extract_transaction_method_from_message(message: TgGroupChatHistory, chat_id: str):
    """
    从消息中提取交易方式

    使用 AC自动机 优化的关键词提取：
    - 时间复杂度: O(n + z) 其中 n=消息文本长度，z=匹配数
    - 相比原始方案性能提升: 2-3 倍

    Args:
        message: TgGroupChatHistory 消息对象
        chat_id: 群组ID
    """
    if not message:
        logger.debug(f"交易方式提取: 消息对象为 None")
        return

    message_text = message.message or ''
    if not message_text or not message_text.strip():
        logger.debug(f"交易方式提取: 消息 {message.id} 文本为空")
        return

    try:
        # 使用 AC自动机 提取交易方式
        logger.debug(f"交易方式提取: 开始处理消息 {message.id}, chat_id={chat_id}, 文本长度={len(message_text)}")
        methods = KeywordExtractionService.extract_transaction_methods(message_text)
        logger.debug(f"交易方式提取: 从消息 {message.id} 提取到 {len(methods)} 种交易方式")

        # 保存提取的交易方式
        if methods:
            for idx, method in enumerate(methods):
                try:
                    record = AdTrackingTransactionMethod(
                        chat_id=chat_id,
                        message_id=str(message.id) if message.id else None,
                        method=method['method'],
                        msg_date=message.postal_time.date() if message.postal_time else None
                    )
                    db.session.add(record)
                    logger.debug(f"交易方式提取: 添加记录 {idx+1}/{len(methods)}: {method['method']}")
                except Exception as add_error:
                    logger.error(f"交易方式提取: 添加记录失败 {idx+1}/{len(methods)}: {add_error}")
                    raise

            # 提交数据库
            try:
                db.session.commit()
                logger.info(f"交易方式提取: ✅ 成功提交 {len(methods)} 种交易方式到数据库 (消息 {message.id})")
            except Exception as commit_error:
                logger.error(f"交易方式提取: ❌ 提交数据库失败 (消息 {message.id}): {commit_error}")
                db.session.rollback()
                raise
        else:
            logger.debug(f"交易方式提取: 消息 {message.id} 未提取到交易方式")

    except Exception as e:
        logger.error(f"交易方式提取失败 (消息 {message.id}): {str(e)}", exc_info=True)
        try:
            db.session.rollback()
        except Exception as rollback_error:
            logger.error(f"交易方式提取: 回滚失败: {rollback_error}")


def _extract_geo_location_from_message(message: TgGroupChatHistory, chat_id: str):
    """
    从消息中提取地理位置

    使用 AC自动机 优化的地理位置提取：
    - 时间复杂度: O(n + z) 其中 n=消息文本长度，z=匹配数
    - 相比原始方案性能提升: 2000-5000 倍（取决于地理位置数据规模）

    优化说明:
    1. AC自动机仅在首次使用时初始化（~50-100ms for 2000+ keywords）
    2. 后续调用使用缓存的 matcher 对象（<1ms）
    3. 单次文本扫描找到所有地理位置关键词

    Args:
        message: TgGroupChatHistory 消息对象
        chat_id: 群组ID
    """
    if not message:
        logger.debug(f"地理位置提取: 消息对象为 None")
        return

    message_text = message.message or ''
    if not message_text or not message_text.strip():
        logger.debug(f"地理位置提取: 消息 {message.id} 文本为空")
        return

    try:
        from flask import has_app_context

        # 确保应用上下文存在
        if not has_app_context():
            logger.warning(f"地理位置提取: 消息 {message.id} - 无应用上下文，尝试继续...")

        # 使用 AC自动机 提取地理位置
        logger.debug(f"地理位置提取: 开始处理消息 {message.id}, chat_id={chat_id}, 文本长度={len(message_text)}")
        locations = GeoLocationService.extract_locations(message_text, chat_id)
        logger.debug(f"地理位置提取: 从消息 {message.id} 提取到 {len(locations)} 个地理位置")

        # 保存提取的地理位置
        if locations:
            for idx, location in enumerate(locations):
                try:
                    record = AdTrackingGeoLocation(
                        chat_id=chat_id,
                        message_id=str(message.id) if message.id else None,
                        province=location.get('province'),  # 直接使用extract_locations返回的省份信息
                        city=location.get('city'),  # 直接使用extract_locations返回的城市信息
                        district=location.get('district'),  # 直接使用extract_locations返回的区县信息
                        keyword_matched=location.get('keyword_matched'),
                        latitude=location.get('latitude'),
                        longitude=location.get('longitude'),
                        msg_date=message.postal_time.date() if message.postal_time else None
                    )
                    db.session.add(record)
                    logger.debug(f"地理位置提取: 添加记录 {idx+1}/{len(locations)}: {location.get('name')} ({location.get('type')})")
                except Exception as add_error:
                    logger.error(f"地理位置提取: 添加记录失败 {idx+1}/{len(locations)}: {add_error}")
                    raise

            # 提交数据库
            try:
                db.session.commit()
                logger.info(f"地理位置提取: ✅ 成功提交 {len(locations)} 个地理位置到数据库 (消息 {message.id})")
            except Exception as commit_error:
                logger.error(f"地理位置提取: ❌ 提交数据库失败 (消息 {message.id}): {commit_error}")
                db.session.rollback()
                raise
        else:
            logger.debug(f"地理位置提取: 消息 {message.id} 未提取到地理位置")

    except Exception as e:
        logger.error(f"地理位置提取失败 (消息 {message.id}): {str(e)}", exc_info=True)
        try:
            db.session.rollback()
        except Exception as rollback_error:
            logger.error(f"地理位置提取: 回滚失败: {rollback_error}")


def _extract_dark_keyword_from_message(message: TgGroupChatHistory, chat_id: str):
    """
    从消息中提取黑词（毒品相关关键词）

    使用 AC自动机 优化的黑词提取：
    - 时间复杂度: O(n + z) 其中 n=消息文本长度，z=匹配数
    - 支持统计每个关键词在消息中出现的次数

    Args:
        message: TgGroupChatHistory 消息对象
        chat_id: 群组ID
    """
    if not message:
        logger.debug(f"黑词提取: 消息对象为 None")
        return

    message_text = message.message or ''
    if not message_text or not message_text.strip():
        logger.debug(f"黑词提取: 消息 {message.id} 文本为空")
        return

    try:
        from flask import has_app_context

        # 确保应用上下文存在
        if not has_app_context():
            logger.warning(f"黑词提取: 消息 {message.id} - 无应用上下文，尝试继续...")

        # 使用 AC自动机 提取黑词（带计数）
        logger.debug(f"黑词提取: 开始处理消息 {message.id}, chat_id={chat_id}, 文本长度={len(message_text)}")
        dark_keywords = DarkKeywordExtractionService.extract_dark_keywords_with_count(message_text)
        logger.debug(f"黑词提取: 从消息 {message.id} 提取到 {len(dark_keywords)} 个黑词")

        # 保存提取的黑词
        if dark_keywords:
            for idx, dk in enumerate(dark_keywords):
                try:
                    record = AdTrackingDarkKeyword(
                        chat_id=chat_id,
                        message_id=str(message.id) if message.id else None,
                        keyword=dk['keyword'],
                        drug_id=dk['drug_id'],
                        category_id=dk['category_id'],
                        count=dk['count'],
                        msg_date=message.postal_time.date() if message.postal_time else None
                    )
                    db.session.add(record)
                    logger.debug(f"黑词提取: 添加记录 {idx+1}/{len(dark_keywords)}: {dk['keyword']} (毒品: {dk['drug_name']}, 出现次数: {dk['count']})")
                except Exception as add_error:
                    logger.error(f"黑词提取: 添加记录失败 {idx+1}/{len(dark_keywords)}: {add_error}")
                    raise

            # 提交数据库
            try:
                db.session.commit()
                logger.info(f"黑词提取: ✅ 成功提交 {len(dark_keywords)} 个黑词到数据库 (消息 {message.id})")
            except Exception as commit_error:
                logger.error(f"黑词提取: ❌ 提交数据库失败 (消息 {message.id}): {commit_error}")
                db.session.rollback()
                raise
        else:
            logger.debug(f"黑词提取: 消息 {message.id} 未提取到黑词")

    except Exception as e:
        logger.error(f"黑词提取失败 (消息 {message.id}): {str(e)}", exc_info=True)
        try:
            db.session.rollback()
        except Exception as rollback_error:
            logger.error(f"黑词提取: 回滚失败: {rollback_error}")


def _clear_analysis_cache(chat_id: str):
    """
    清除分析相关的所有缓存

    当批处理完成后，清除缓存确保前端获取最新数据。
    缓存键模式:
    - dark_keywords:{chat_id}:* 或 dark_keywords:all:*
    - transaction_methods:{chat_id}:* 或 transaction_methods:all:*
    - price_trend:{chat_id}:* 或 price_trend:all:*
    - geo_heatmap:{chat_id}:* 或 geo_heatmap:all:*

    注意：需要同时清除特定群组缓存和全局缓存，因为全局统计数据也受影响

    Args:
        chat_id: 群组ID
    """
    try:
        # 清除特定群组的缓存
        patterns = [
            f'dark_keywords:{chat_id}:*',
            f'transaction_methods:{chat_id}:*',
            f'price_trend:{chat_id}:*',
            f'geo_heatmap:{chat_id}:*'
        ]

        # 同时清除全局缓存（因为全表统计数据也受影响）
        global_patterns = [
            'dark_keywords:all:*',
            'transaction_methods:all:*',
            'price_trend:all:*',
            'geo_heatmap:all:*'
        ]

        all_patterns = patterns + global_patterns

        for pattern in all_patterns:
            count = CacheService.clear_pattern(pattern)
            if count > 0:
                logger.info(f"清除缓存: {pattern} ({count} 条)")

    except Exception as e:
        logger.warning(f"清除缓存失败: {str(e)}")
        # 不抛出异常，缓存清除失败不影响任务的整体成功


@celery.task(bind=True, queue='jd.celery.first')
def process_messages_for_chat(
    self,
    chat_id: str,
    days: int = 7,
    include_price: bool = True,
    include_transaction: bool = True,
    include_geo: bool = True,
    include_dark_keyword: bool = True
):
    """
    处理指定群组的最近N天的消息

    这是一个简化版本的任务，不需要批次ID，直接处理指定群组的消息。

    Args:
        self: Celery Task 实例
        chat_id: 群组ID
        days: 处理最近多少天的消息 (默认7)
        include_price: 是否提取价格 (默认True)
        include_transaction: 是否提取交易方式 (默认True)
        include_geo: 是否提取地理位置 (默认True)
        include_dark_keyword: 是否提取黑词 (默认True)

    Returns:
        dict: 处理结果
    """
    # 建立 Flask 应用上下文（Celery 任务中访问数据库需要）
    with app.app_context():
        return _process_messages_for_chat_impl(
            self, chat_id, days, include_price, include_transaction, include_geo, include_dark_keyword
        )


def _process_messages_for_chat_impl(
    self,
    chat_id: str,
    days: int,
    include_price: bool,
    include_transaction: bool,
    include_geo: bool,
    include_dark_keyword: bool
):
    """process_messages_for_chat 的实现函数"""
    try:
        start_date = datetime.now() - timedelta(days=days)
        logger.info(f"开始处理群组 {chat_id} 最近 {days} 天的消息")

        # 查询消息
        messages = TgGroupChatHistory.query.filter(
            TgGroupChatHistory.chat_id == chat_id,
            TgGroupChatHistory.postal_time >= start_date
        ).order_by(TgGroupChatHistory.id).all()

        logger.info(f"群组 {chat_id} 获取 {len(messages)} 条消息")

        success_count = 0
        fail_count = 0

        for idx, message in enumerate(messages):
            try:
                if include_price:
                    _extract_price_from_message(message, chat_id)

                if include_transaction:
                    _extract_transaction_method_from_message(message, chat_id)

                if include_geo:
                    _extract_geo_location_from_message(message, chat_id)

                if include_dark_keyword:
                    _extract_dark_keyword_from_message(message, chat_id)

                success_count += 1

                # 每处理100条更新进度
                if (idx + 1) % 100 == 0:
                    self.update_state(
                        state='PROGRESS',
                        meta={'current': idx + 1, 'total': len(messages)}
                    )
                    logger.info(f"群组 {chat_id} 处理进度: {idx + 1}/{len(messages)}")

            except Exception as e:
                fail_count += 1
                logger.error(f"处理消息 {idx} 失败: {str(e)}")

        # 清除缓存
        _clear_analysis_cache(chat_id)

        logger.info(f"群组 {chat_id} 处理完成: 成功 {success_count}, 失败 {fail_count}")

        return {
            'chat_id': chat_id,
            'days': days,
            'success_count': success_count,
            'fail_count': fail_count,
            'total': len(messages)
        }

    except Exception as e:
        logger.error(f"处理群组 {chat_id} 异常: {str(e)}", exc_info=True)
        return {
            'error': str(e),
            'chat_id': chat_id,
            'success_count': 0,
            'fail_count': 0
        }


@celery.task(bind=True, queue='jd.celery.first')
def process_all_chats(
    self,
    days: int = 1,
    include_price: bool = True,
    include_transaction: bool = True,
    include_geo: bool = True,
    include_dark_keyword: bool = True
):
    """
    处理所有群组的消息

    Args:
        self: Celery Task 实例
        days: 处理最近多少天的消息 (默认1)
        include_price: 是否提取价格
        include_transaction: 是否提取交易方式
        include_geo: 是否提取地理位置
        include_dark_keyword: 是否提取黑词

    Returns:
        dict: 处理结果
    """
    # 建立 Flask 应用上下文（Celery 任务中访问数据库需要）
    with app.app_context():
        return _process_all_chats_impl(
            self, days, include_price, include_transaction, include_geo, include_dark_keyword
        )


def _process_all_chats_impl(
    self,
    days: int,
    include_price: bool,
    include_transaction: bool,
    include_geo: bool,
    include_dark_keyword: bool
):
    """process_all_chats 的实现函数"""
    try:
        # 获取所有有消息的群组ID
        from sqlalchemy import func
        chat_ids = db.session.query(
            func.distinct(TgGroupChatHistory.chat_id)
        ).filter(
            TgGroupChatHistory.postal_time >= datetime.now() - timedelta(days=days)
        ).all()

        chat_ids = [row[0] for row in chat_ids if row[0]]
        logger.info(f"发现 {len(chat_ids)} 个有消息的群组")

        results = []
        for idx, chat_id in enumerate(chat_ids):
            try:
                result = process_messages_for_chat.apply_async(
                    args=[chat_id, days, include_price, include_transaction, include_geo, include_dark_keyword],
                    queue='jd.celery.first'
                )
                results.append({
                    'chat_id': chat_id,
                    'task_id': result.id
                })

                # 更新进度
                if (idx + 1) % 10 == 0:
                    self.update_state(
                        state='PROGRESS',
                        meta={'current': idx + 1, 'total': len(chat_ids)}
                    )

            except Exception as e:
                logger.error(f"提交群组 {chat_id} 任务失败: {str(e)}")

        logger.info(f"已提交 {len(results)} 个群组的处理任务")

        return {
            'total_chats': len(chat_ids),
            'submitted_tasks': len(results),
            'tasks': results
        }

    except Exception as e:
        logger.error(f"处理所有群组异常: {str(e)}", exc_info=True)
        return {'error': str(e)}
