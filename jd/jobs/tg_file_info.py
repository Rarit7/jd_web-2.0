from jd.utils.logging_config import get_logger
from typing import Optional
from telethon.tl.types import DocumentAttributeFilename

from jd import db
from jd.models.tg_document_info import TgDocumentInfo
from jd.models.tg_group_chat_history import TgGroupChatHistory

logger = get_logger('jd.jobs.tg.file_info', {'component': 'telegram', 'module': 'file_info'})


class TgFileInfoManager:
    """
    Telegram文件信息管理器
    负责处理文档信息的数据库存储和更新
    """
    
    @staticmethod
    def save_document_info(peer_id: str, chat_id: str, message_id: str, filename_origin: str, 
                          file_ext_name: str, mime_type: str, filepath: str, 
                          video_thumb_path: str, file_hash: str, file_size: int) -> bool:
        """
        保存文档信息到数据库
        :param peer_id: 原始来源ID
        :param chat_id: 群聊ID
        :param message_id: 消息ID
        :param filename_origin: 原始文件名
        :param file_ext_name: 文件扩展名
        :param mime_type: MIME类型
        :param filepath: 文件路径
        :param video_thumb_path: 视频缩略图路径
        :param file_hash: 文件哈希值
        :param file_size: 文件大小
        :return: 保存是否成功
        """
        try:
            # 检查记录是否已存在
            existing_record = db.session.query(TgDocumentInfo).filter_by(
                chat_id=chat_id,
                message_id=message_id
            ).first()
            
            if existing_record:
                # 更新现有记录
                existing_record.peer_id = peer_id
                existing_record.filename_origin = filename_origin
                existing_record.file_ext_name = file_ext_name
                existing_record.mime_type = mime_type
                existing_record.filepath = filepath
                existing_record.video_thumb_path = video_thumb_path
                existing_record.file_hash = file_hash
                existing_record.file_size = file_size
                logger.debug(f"更新文档信息: peer_id={peer_id}, chat_id={chat_id}, message_id={message_id}, filename={filename_origin}")
            else:
                # 创建新记录
                document_info = TgDocumentInfo(
                    chat_id=chat_id,
                    message_id=message_id,
                    peer_id=peer_id,
                    filename_origin=filename_origin,
                    file_ext_name=file_ext_name,
                    mime_type=mime_type,
                    filepath=filepath,
                    video_thumb_path=video_thumb_path,
                    file_hash=file_hash,
                    file_size=file_size
                )
                db.session.add(document_info)
                logger.debug(f"新增文档信息: peer_id={peer_id}, chat_id={chat_id}, message_id={message_id}, filename={filename_origin}")
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"保存文档信息失败: chat_id={chat_id}, message_id={message_id}, error={e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_document_info(chat_id: str, message_id: str) -> Optional[TgDocumentInfo]:
        """
        根据chat_id和message_id获取文档信息
        :param chat_id: 群聊ID
        :param message_id: 消息ID
        :return: 文档信息对象或None
        """
        try:
            return db.session.query(TgDocumentInfo).filter_by(
                chat_id=chat_id,
                message_id=message_id
            ).first()
        except Exception as e:
            logger.error(f"获取文档信息失败: chat_id={chat_id}, message_id={message_id}, error={e}")
            return None
    
    @staticmethod
    def delete_document_info(chat_id: str, message_id: str) -> bool:
        """
        删除文档信息记录
        :param chat_id: 群聊ID
        :param message_id: 消息ID
        :return: 删除是否成功
        """
        try:
            document_info = db.session.query(TgDocumentInfo).filter_by(
                chat_id=chat_id,
                message_id=message_id
            ).first()
            
            if document_info:
                db.session.delete(document_info)
                db.session.commit()
                logger.info(f"删除文档信息: chat_id={chat_id}, message_id={message_id}")
                return True
            else:
                logger.warning(f"要删除的文档信息不存在: chat_id={chat_id}, message_id={message_id}")
                return False
                
        except Exception as e:
            logger.error(f"删除文档信息失败: chat_id={chat_id}, message_id={message_id}, error={e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_documents_by_chat_id(chat_id: str, limit: int = 100, offset: int = 0) -> list:
        """
        根据chat_id获取文档列表
        :param chat_id: 群聊ID
        :param limit: 限制数量
        :param offset: 偏移量
        :return: 文档信息列表
        """
        try:
            return db.session.query(TgDocumentInfo).filter_by(
                chat_id=chat_id
            ).order_by(TgDocumentInfo.created_at.desc()).limit(limit).offset(offset).all()
        except Exception as e:
            logger.error(f"获取文档列表失败: chat_id={chat_id}, error={e}")
            return []
    
    @staticmethod
    def update_chat_history_document_path(chat_id, message_id, document_path):
        """
        更新聊天历史记录中的文档路径
        :param chat_id: 群聊ID
        :param message_id: 消息ID
        :param document_path: 文档路径
        :return: 更新是否成功
        """
        try:
            # 查找对应的聊天记录
            chat_history = db.session.query(TgGroupChatHistory).filter_by(
                chat_id=str(chat_id),
                message_id=str(message_id)
            ).first()
            
            if chat_history:
                # 更新文档路径
                chat_history.document_path = document_path
                db.session.commit()
                logger.info(f"Updated chat history document_path: chat_id={chat_id}, message_id={message_id}, path={document_path}")
                return True
            else:
                logger.warning(f"Chat history record not found: chat_id={chat_id}, message_id={message_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating chat history document_path: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    async def download_file_by_message(client, chat_id, message_id, document_path):
        """
        根据chat_id和message_id下载文件
        :param client: Telethon客户端实例
        :param chat_id: 群聊ID
        :param message_id: 消息ID
        :param document_path: 文档保存路径
        :return: 下载结果字典，包含成功状态和文件信息
        """

        result = {
            'success': False,
            'message': '',
            'file_info': None,
            'file_type': None  # 'document', 'none'
        }
        
        try:
            # 使用get_messages获取消息对象
            messages = await client.get_messages(
                entity=int(chat_id),
                ids=[int(message_id)]
            )
            
            if not messages or not messages[0]:
                result['message'] = f'未找到消息: chat_id={chat_id}, message_id={message_id}'
                return result
            
            message = messages[0]
            
            # 检查消息是否包含文档
            if message.document:
                result['file_type'] = 'document'
                
                document = message.document
                if document and document.attributes:
                    file_name = ''
                    for attr in document.attributes:
                        if isinstance(attr, DocumentAttributeFilename):
                            file_name = attr.file_name
                            break
                    
                    if file_name:
                        # 检查数据库中是否已有文件记录
                        existing_doc_info = TgFileInfoManager.get_document_info(
                            chat_id=str(chat_id),
                            message_id=str(message_id)
                        )
                        
                        mime_type = document.mime_type if hasattr(document, 'mime_type') else ''
                        file_size = document.size if hasattr(document, 'size') else 0
                        
                        if existing_doc_info and existing_doc_info.filepath:
                            # 数据库中已有文件路径记录，说明已下载
                            result['success'] = True
                            result['message'] = '文档文件已下载（根据数据库记录）'
                            result['file_info'] = {
                                'file_name': existing_doc_info.filename_origin,
                                'file_path': existing_doc_info.filepath,
                                'mime_type': existing_doc_info.mime_type,
                                'file_size': existing_doc_info.file_size,
                                'file_hash': existing_doc_info.file_hash,
                                'video_thumb_path': existing_doc_info.video_thumb_path,
                                'exists': True
                            }
                        else:
                            # 数据库中无记录或无文件路径，进行下载
                            # 需要导入TelegramDownloadManager来处理下载
                            from jd.services.spider.tg_download import TelegramDownloadManager
                            download_manager = TelegramDownloadManager(client)
                            
                            document_data = await download_manager.process_document(message, document_path)
                            if document_data and document_data.get('file_path'):
                                result['success'] = True
                                result['message'] = '文档下载成功'
                                result['file_info'] = document_data
                                result['file_info']['exists'] = False
                                result['file_info']['mime_type'] = mime_type
                                result['file_info']['file_size'] = file_size
                                # filepath 字段已在 process_document 中通过 TgFileInfoManager.save_document_info 更新
                                
                                # 更新聊天历史记录中的文档路径
                                TgFileInfoManager.update_chat_history_document_path(
                                    chat_id=chat_id,
                                    message_id=message_id,
                                    document_path=document_data.get('file_path', '')
                                )
                            else:
                                result['message'] = '文档下载失败'
                                # 即使下载失败，也要确保数据库中有基本记录（但不包含filepath）
                                if not existing_doc_info:
                                    # 获取peer_id（原始ID）
                                    peer_id = str(message.chat_id)
                                    
                                    TgFileInfoManager.save_document_info(
                                        peer_id=peer_id,
                                        chat_id=str(chat_id),
                                        message_id=str(message_id),
                                        filename_origin=file_name,
                                        file_ext_name=file_name.split('.')[-1] if '.' in file_name else '',
                                        mime_type=mime_type,
                                        filepath='',  # 空字符串表示下载失败
                                        video_thumb_path='',
                                        file_hash='',
                                        file_size=file_size
                                    )
                    else:
                        result['message'] = '文档没有文件名属性'
            
            else:
                result['file_type'] = 'none'
                result['success'] = True
                result['message'] = '消息不包含文档文件'
            
        except Exception as e:
            result['message'] = f'下载文件时发生错误: {str(e)}'
            logger.error(f"Error in download_file_by_message: {e}")
        
        return result