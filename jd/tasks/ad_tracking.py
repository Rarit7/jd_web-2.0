from celery import current_task
from jd import db
from jd.tasks.base_task import BaseTask
from jCelery import celery
from jd.models.ad_tracking_record import AdTrackingRecord
from jd.models.ad_tracking_processing_batch import AdTrackingProcessingBatch
from jd.models.tag_keyword_mapping import TagKeywordMapping
from jd.models.tg_group_chat_history import TgGroupChatHistory
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


class AdTrackingTask(BaseTask):
    """广告追踪任务基类"""

    name = 'jd.celery.ad_tracking'


@celery.task(bind=True, queue='jd.celery.first')
def process_channel_for_ad_tracking(self, channel_id, tag_ids, batch_id=None):
    """
    处理频道中的聊天记录，提取广告内容

    Args:
        channel_id: 频道ID
        tag_ids: 标签ID列表
        batch_id: 处理批次ID（如果为None，则创建新的）
    """
    if batch_id is None:
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        # 获取或创建处理批次记录
        batch = AdTrackingProcessingBatch.query.get(batch_id)
        if not batch:
            # 如果批次不存在，创建新的
            batch = AdTrackingProcessingBatch(
                id=batch_id,
                channel_id=channel_id,
                selected_tag_ids=json.dumps(tag_ids)
            )
            db.session.add(batch)
            db.session.commit()
        else:
            # 批次已存在，确保状态为pending
            batch.status = AdTrackingProcessingBatch.Status.PENDING
            db.session.commit()

        logger.info(f"开始处理频道 {channel_id}，批次ID: {batch_id}")

        # 获取频道对应的chat_id
        from jd.models.tg_group import TgGroup
        channel = TgGroup.query.get(channel_id)
        if not channel:
            raise Exception(f"频道 {channel_id} 不存在")

        # 获取频道下的所有聊天记录
        # 使用chat_id查询消息，因为TgGroupChatHistory中存储的是chat_id而不是channel_id
        messages = TgGroupChatHistory.query.filter_by(
            chat_id=channel.chat_id
        ).order_by(TgGroupChatHistory.postal_time).all()

        batch.total_messages = len(messages)
        db.session.commit()

        logger.info(f"频道 {channel_id} 共有 {len(messages)} 条消息")

        # 获取标签关键词映射
        # 现在 tag_ids 是 ResultTag 的 ID（标签ID）
        # 需要获取每个标签对应的所有关键字
        tag_keywords = {}  # {tag_id: [keywords]}
        for tag_id in tag_ids:
            # 根据 ResultTag ID 获取对应的所有关键字
            keywords = db.session.query(TagKeywordMapping.keyword).filter_by(
                tag_id=tag_id,
                is_active=True
            ).all()
            # 转换为列表
            tag_keywords[tag_id] = [k[0].lower() for k in keywords]

        logger.info(f"标签关键词映射: {tag_keywords}")

        processed_count = 0
        created_records = 0

        # 处理每条消息
        for message in messages:
            try:
                # 更新进度
                processed_count += 1
                batch.processed_messages = processed_count
                db.session.commit()

                # 发送心跳
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': processed_count,
                        'total': batch.total_messages,
                        'batch_id': batch_id
                    }
                )

                # 处理消息
                message_created = _process_message(message, tag_keywords, batch_id, channel_id, channel.name)
                if message_created:
                    created_records += 1

                logger.info(f"已处理 {processed_count}/{batch.total_messages} 条消息，创建 {created_records} 条记录")

            except Exception as e:
                logger.error(f"处理消息失败: {message.id}, 错误: {str(e)}")
                # 继续处理下一条消息，不中断整个任务

        # 更新批次完成状态
        batch.status = AdTrackingProcessingBatch.Status.COMPLETED
        batch.completed_at = datetime.now()
        batch.created_messages = created_records
        db.session.commit()

        logger.info(f"频道处理完成: {channel_id}, 批次: {batch_id}, "
                   f"处理 {len(messages)} 条消息，创建 {created_records} 条广告记录")

        return {
            'batch_id': batch_id,
            'status': 'completed',
            'processed_messages': processed_count,
            'created_records': created_records,
            'message': f'处理完成，共创建 {created_records} 条广告记录'
        }

    except Exception as e:
        logger.error(f"处理频道失败: {channel_id}, 错误: {str(e)}")

        # 更新批次为失败状态
        if 'batch' in locals():
            batch.status = AdTrackingProcessingBatch.Status.FAILED
            batch.error_message = str(e)
            batch.completed_at = datetime.now()
            db.session.commit()

        raise Exception(f"处理频道失败: {str(e)}")


def _process_message(message, tag_keywords, batch_id, channel_id, channel_name):
    """
    处理单条消息

    Args:
        message: TgGroupChatHistory 消息对象
        tag_keywords: 标签关键词映射 {tag_id: [keyword]}
        batch_id: 批次ID
        channel_id: 频道ID
        channel_name: 频道名称

    Returns:
        bool: 是否创建了广告记录（现在总是True，因为无条件创建）
    """
    created_count = 0

    # 处理文本消息
    if message.message and not message.photo_path:
        created_count = _process_text_message(message, tag_keywords, batch_id, channel_id, channel_name)

    # 处理图片消息
    elif message.photo_path:
        created_count = _process_photo_message(message, tag_keywords, batch_id, channel_id, channel_name)

    # 总是返回True，因为已经无条件创建记录
    return created_count > 0


def _process_text_message(message, tag_keywords, batch_id, channel_id, channel_name):
    """
    处理文本消息 - 每条消息只创建一条记录

    逻辑：用户选择频道进行处理时，意味着用户认为该频道的所有消息都是广告。
    - 一条消息只创建一条 AdTrackingRecord
    - 该记录包含所有匹配的标签ID（存储在 tag_ids JSON 字段中）
    - 如果选择了标签，则记录匹配的所有标签ID
    - 如果没有选择标签，则 tag_ids 为 NULL

    tag_keywords: {tag_id: [keywords]}，其中tag_id是ResultTag的ID
    """
    text = message.message or ""
    text_lower = text.lower()
    created_count = 0

    # 查找匹配的标签ID列表
    matched_tag_ids = []
    if tag_keywords:
        for tag_id, keywords in tag_keywords.items():
            # 检查消息是否包含该标签的任何关键字
            for keyword in keywords:
                if keyword in text_lower:
                    matched_tag_ids.append(tag_id)
                    break  # 找到一个关键字就认为匹配，不需要再检查该标签的其他关键字

    # 为这条消息创建一条记录（而不是为每个标签创建一条）
    record = AdTrackingRecord(
        channel_id=channel_id,
        channel_name=channel_name,
        message_id=int(message.message_id) if message.message_id else 0,
        sender_id=int(message.user_id) if message.user_id else 0,
        message_text=text,
        image_url="",  # 文本消息没有图片
        send_time=message.postal_time,
        trigger_keyword="",  # 无关键词匹配，只表示用户主观判定
        trigger_tag_id=matched_tag_ids[0] if matched_tag_ids else None,  # 保留以支持向后兼容
        tag_ids=matched_tag_ids if matched_tag_ids else None,  # 新字段：所有匹配的标签ID
        process_batch_id=batch_id,
        is_processed=False
    )
    db.session.add(record)
    created_count = 1

    # 提交广告记录到数据库
    db.session.commit()

    # 更新处理批次
    batch = AdTrackingProcessingBatch.query.get(batch_id)
    if batch:
        batch.created_messages += created_count

    return created_count


def _process_photo_message(message, tag_keywords, batch_id, channel_id, channel_name):
    """
    处理图片消息 - 每条消息只创建一条记录

    逻辑：用户选择频道进行处理时，意味着用户认为该频道的所有消息都是广告。
    - 一条消息只创建一条 AdTrackingRecord
    - 该记录包含所有匹配的标签ID（存储在 tag_ids JSON 字段中）

    tag_keywords: {tag_id: [keywords]}，其中tag_id是ResultTag的ID
    """
    # 查找同一时间窗口内的文本消息（用于获取消息文本）
    time_window = timedelta(minutes=5)  # 5分钟时间窗口

    text_message = TgGroupChatHistory.query.filter(
        TgGroupChatHistory.chat_id == message.chat_id,
        TgGroupChatHistory.user_id == message.user_id,
        TgGroupChatHistory.postal_time.between(
            message.postal_time - time_window,
            message.postal_time + time_window
        ),
        TgGroupChatHistory.message.isnot(None),
        TgGroupChatHistory.id != message.id
    ).first()

    text = text_message.message if text_message else ""
    text_lower = text.lower()
    created_count = 0

    # 查找匹配的标签ID列表
    matched_tag_ids = []
    if tag_keywords:
        for tag_id, keywords in tag_keywords.items():
            # 检查消息是否包含该标签的任何关键字
            for keyword in keywords:
                if keyword in text_lower:
                    matched_tag_ids.append(tag_id)
                    break  # 找到一个关键字就认为匹配，不需要再检查该标签的其他关键字

    # 为这条消息创建一条记录（而不是为每个标签创建一条）
    record = AdTrackingRecord(
        channel_id=channel_id,
        channel_name=channel_name,
        message_id=int(message.message_id) if message.message_id else 0,
        sender_id=int(message.user_id) if message.user_id else 0,
        message_text=text,
        image_url=message.photo_path or "",  # 使用图片路径
        send_time=message.postal_time,
        trigger_keyword="",  # 无关键词匹配，只表示用户主观判定
        trigger_tag_id=matched_tag_ids[0] if matched_tag_ids else None,  # 保留以支持向后兼容
        tag_ids=matched_tag_ids if matched_tag_ids else None,  # 新字段：所有匹配的标签ID
        process_batch_id=batch_id,
        is_processed=False
    )
    db.session.add(record)
    created_count = 1

    # 提交广告记录到数据库
    db.session.commit()

    # 更新处理批次
    batch = AdTrackingProcessingBatch.query.get(batch_id)
    if batch:
        batch.created_messages += created_count

    return created_count


@celery.task(bind=True, queue='jd.celery.first')
def batch_reprocess_records(self, record_ids, tag_ids=None):
    """
    批量重新处理广告记录

    Args:
        record_ids: 需要重新处理的记录ID列表
        tag_ids: 可选的新标签ID列表
    """
    try:
        batch_id = f"reprocess_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 创建处理批次
        batch = AdTrackingProcessingBatch.create_batch(0, tag_ids or [])
        batch_id = batch.id

        # 获取原始消息
        records = AdTrackingRecord.query.filter(
            AdTrackingRecord.id.in_(record_ids)
        ).all()

        if not records:
            return {
                'batch_id': batch_id,
                'status': 'completed',
                'message': '没有找到需要重新处理的记录'
            }

        # 重新处理
        processed_count = 0
        created_records = 0

        for record in records:
            try:
                processed_count += 1
                batch.processed_messages = processed_count

                # 如果提供了新的标签，使用新标签
                if tag_ids:
                    # 这里需要根据新的标签重新匹配
                    # 简化处理：直接更新触发标签
                    record.trigger_tag_id = tag_ids[0]

                # 标记为已重新处理
                record.is_processed = True
                db.session.commit()

                created_records += 1

            except Exception as e:
                logger.error(f"重新处理记录失败: {record.id}, 错误: {str(e)}")

        # 更新批次状态
        batch.status = AdTrackingProcessingBatch.Status.COMPLETED
        batch.completed_at = datetime.now()
        batch.created_messages = created_records
        db.session.commit()

        return {
            'batch_id': batch_id,
            'status': 'completed',
            'processed_records': processed_count,
            'updated_records': created_records
        }

    except Exception as e:
        logger.error(f"批量重新处理失败: {str(e)}")
        raise


@celery.task(bind=True, queue='jd.celery.first')
def cleanup_duplicate_records(self, days=7):
    """
    清理重复的广告记录

    Args:
        days: 保留最近几天的记录
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)

        # 查找重复记录（相同的channel_id, message_id, trigger_keyword）
        duplicates = db.session.query(
            AdTrackingRecord.channel_id,
            AdTrackingRecord.message_id,
            AdTrackingRecord.trigger_keyword,
            db.func.count(AdTrackingRecord.id).label('count')
        ).filter(
            AdTrackingRecord.created_at >= cutoff_date
        ).group_by(
            AdTrackingRecord.channel_id,
            AdTrackingRecord.message_id,
            AdTrackingRecord.trigger_keyword
        ).having(
            db.func.count(AdTrackingRecord.id) > 1
        ).all()

        deleted_count = 0

        for duplicate in duplicates:
            # 获取重复的记录，保留最新的（ID最大的）
            records = AdTrackingRecord.query.filter(
                AdTrackingRecord.channel_id == duplicate.channel_id,
                AdTrackingRecord.message_id == duplicate.message_id,
                AdTrackingRecord.trigger_keyword == duplicate.trigger_keyword
            ).order_by(AdTrackingRecord.id.desc()).all()

            # 删除除最新外的所有记录
            for record in records[1:]:
                db.session.delete(record)
                deleted_count += 1

        db.session.commit()

        return {
            'status': 'completed',
            'deleted_count': deleted_count,
            'duplicates_found': len(duplicates)
        }

    except Exception as e:
        logger.error(f"清理重复记录失败: {str(e)}")
        raise