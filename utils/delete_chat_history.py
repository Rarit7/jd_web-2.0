#!/usr/bin/env python3

import logging
from jd import app, db
from jd.models.tg_group import TgGroup
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group_status import TgGroupStatus
from jd.models.tg_document_info import TgDocumentInfo


app.ready(db_switch=True, web_switch=False, worker_switch=False, socketio_switch=False)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delete_all_chat_history(chat_id):
    """
    清除以下数据表中，指定chat_id的数据：
    tg_group
    tg_group_chat_history
    tg_group_status
    tg_document_info
    """
    if not chat_id:
        logger.error("chat_id is required")
        return
    
    chat_id_str = str(chat_id)
    logger.info(f"Starting deletion process for chat_id: {chat_id_str}")
    
    with app.app_context():
        try:
            # 统计要删除的记录数
            chat_history_count = TgGroupChatHistory.query.filter_by(chat_id=chat_id_str).count()
            group_count = TgGroup.query.filter_by(chat_id=chat_id_str).count()
            status_count = TgGroupStatus.query.filter_by(chat_id=chat_id_str).count()
            document_count = TgDocumentInfo.query.filter_by(chat_id=chat_id_str).count()
            
            total_count = chat_history_count + group_count + status_count + document_count
            
            logger.info(f"Found records to delete for chat_id {chat_id_str}:")
            logger.info(f"  - tg_group_chat_history: {chat_history_count}")
            logger.info(f"  - tg_group: {group_count}")
            logger.info(f"  - tg_group_status: {status_count}")
            logger.info(f"  - tg_document_info: {document_count}")
            logger.info(f"  - Total: {total_count}")
            
            if total_count == 0:
                logger.info(f"No records found for chat_id {chat_id_str}")
                return
            
            # 删除各表中的数据
            deleted_chat_history = TgGroupChatHistory.query.filter_by(chat_id=chat_id_str).delete()
            logger.info(f"Deleted {deleted_chat_history} chat history records")
            
            deleted_group = TgGroup.query.filter_by(chat_id=chat_id_str).delete()
            logger.info(f"Deleted {deleted_group} group records")
            
            deleted_status = TgGroupStatus.query.filter_by(chat_id=chat_id_str).delete()
            logger.info(f"Deleted {deleted_status} group status records")
            
            deleted_document = TgDocumentInfo.query.filter_by(chat_id=chat_id_str).delete()
            logger.info(f"Deleted {deleted_document} document info records")
            
            # 提交事务
            db.session.commit()
            
            total_deleted = deleted_chat_history + deleted_group + deleted_status + deleted_document
            logger.info(f"Successfully deleted {total_deleted} records for chat_id {chat_id_str}")
            
            # 验证删除结果
            remaining_chat_history = TgGroupChatHistory.query.filter_by(chat_id=chat_id_str).count()
            remaining_group = TgGroup.query.filter_by(chat_id=chat_id_str).count()
            remaining_status = TgGroupStatus.query.filter_by(chat_id=chat_id_str).count()
            remaining_document = TgDocumentInfo.query.filter_by(chat_id=chat_id_str).count()
            
            remaining_total = remaining_chat_history + remaining_group + remaining_status + remaining_document
            
            if remaining_total == 0:
                logger.info(f"All records for chat_id {chat_id_str} have been successfully deleted")
            else:
                logger.warning(f"Warning: {remaining_total} records still remain for chat_id {chat_id_str}")
                
        except Exception as e:
            logger.error(f"Error deleting records for chat_id {chat_id_str}: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        logger.error("Usage: python delete_chat_history.py <chat_id>")
        logger.error("Example: python delete_chat_history.py 123456789")
        sys.exit(1)
    
    chat_id = sys.argv[1]
    logger.info("Starting chat history deletion process...")
    delete_all_chat_history(chat_id)
    logger.info("Chat history deletion process completed")