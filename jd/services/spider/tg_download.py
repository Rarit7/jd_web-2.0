import os
import time
import hashlib
import logging
from telethon.tl.types import DocumentAttributeFilename
from jd.jobs.tg_file_info import TgFileInfoManager

logger = logging.getLogger(__name__)


class TelegramDownloadManager:
    """
    Telegram文件下载管理器
    处理图片和文档的下载，包括配置检查和文件名冲突处理
    """
    
    def __init__(self, client):
        """
        初始化下载管理器
        :param client: Telethon客户端实例
        """
        self.client = client
    
    def _should_download_file(self, file_name, mime_type=''):
        """
        根据配置设置判断是否应该下载文件
        :param file_name: 文件名
        :param mime_type: MIME类型
        :return: 是否应该下载
        """
        from jd import app
        
        # 过滤掉sticker文件，这些文件显示为【动画表情】
        if file_name in ['sticker.webp', 'sticker.webm']:
            return False
        
        # 获取下载设置
        download_settings = app.config.get('TELEGRAM_DOWNLOAD_SETTINGS', {})
        
        # 如果设置下载所有文件，直接返回True
        if download_settings.get('download_all', False):
            return True
        
        # 获取文件扩展名
        file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
        
        # 根据MIME类型判断文件类型（优先级更高）
        if mime_type:
            if mime_type.startswith('image/'):
                return download_settings.get('download_images', True)
            elif mime_type.startswith('audio/'):
                return download_settings.get('download_audio', False)
            elif mime_type.startswith('video/'):
                return download_settings.get('download_videos', False)
        
        # 根据文件扩展名判断（MIME类型不可用或未匹配时的回退）
        if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'tif', 'svg', 'ico']:
            return download_settings.get('download_images', True)
        elif file_ext in ['mp3', 'flac', 'wav', 'ogg', 'aac', 'm4a']:
            return download_settings.get('download_audio', False)
        elif file_ext in ['mp4', 'mkv', 'webm', 'mov', 'avi', 'wmv', 'flv']:
            return download_settings.get('download_videos', False)
        elif file_ext in ['zip', 'rar', '7z', 'gz', 'bz2', 'tar', 'xz']:
            return download_settings.get('download_archives', False)
        elif file_ext in ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf', 'odt']:
            return download_settings.get('download_documents', False)
        elif file_ext in ['apk', 'exe', 'msi', 'deb', 'rpm', 'dmg', 'elf']:
            return download_settings.get('download_programs', False)
        
        # 默认情况下不下载未知文件类型
        return False

    def _calculate_file_hash(self, file_path):
        """
        计算文件的MD5哈希值
        :param file_path: 文件路径
        :return: 文件哈希值
        """
        if not os.path.exists(file_path):
            return None
        
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None

    def _get_unique_filename(self, directory_path, file_name, new_file_path=None):
        """
        生成唯一的文件名，检查文件内容哈希避免重复存储
        :param directory_path: 文件保存目录
        :param file_name: 原始文件名
        :param new_file_path: 新文件的临时路径（用于哈希比较）
        :return: 唯一的文件名或现有重复文件的文件名
        """
        original_file_path = os.path.join(directory_path, file_name)
        
        # 如果文件不存在，直接返回原文件名
        if not os.path.exists(original_file_path):
            return file_name, False  # 返回文件名和是否为重复文件的标志
        
        # 如果提供了新文件路径，计算其哈希值用于比较
        new_file_hash = None
        if new_file_path and os.path.exists(new_file_path):
            new_file_hash = self._calculate_file_hash(new_file_path)
        
        # 检查原始文件名的文件是否内容相同
        if new_file_hash:
            existing_hash = self._calculate_file_hash(original_file_path)
            if existing_hash == new_file_hash:
                # 文件内容相同，返回现有文件名，表示重复
                return file_name, True
        
        # 分离文件名和扩展名
        name_without_ext = os.path.splitext(file_name)[0]
        extension = os.path.splitext(file_name)[1]
        
        # 生成带序号的文件名，同时检查哈希
        counter = 1
        while True:
            new_file_name = f"{name_without_ext}_{counter}{extension}"
            new_file_path_check = os.path.join(directory_path, new_file_name)
            
            if not os.path.exists(new_file_path_check):
                # 文件不存在，可以使用这个文件名
                return new_file_name, False
            
            # 如果文件存在且有新文件哈希，检查内容是否相同
            if new_file_hash:
                existing_hash = self._calculate_file_hash(new_file_path_check)
                if existing_hash == new_file_hash:
                    # 找到相同内容的文件，返回现有文件名
                    return new_file_name, True
            
            counter += 1
            
            # 防止无限循环，最多尝试1000次
            if counter > 1000:
                timestamp = str(int(time.time()))
                return f"{name_without_ext}_{timestamp}{extension}", False

    async def process_photo(self, message, image_path):
        """
        处理消息中的照片
        :param message: Telegram消息对象
        :param image_path: 图片保存路径
        :return: 处理后的photo字典
        """
        photo_data = {}
        photo = message.photo
        if photo and hasattr(photo, "id"):
            file_name = f'{str(photo.id)}.jpg'
            file_path = os.path.join(image_path, file_name)
            
            # 先下载到临时文件用于哈希检查
            temp_file_path = f"{file_path}.tmp"
            need_download = not os.path.exists(file_path)
            
            if need_download:
                await self.client.download_media(message=message, file=temp_file_path, thumb=-1)
                # 检查是否有重复文件
                unique_file_name, is_duplicate = self._get_unique_filename(image_path, file_name, temp_file_path)
                
                if is_duplicate:
                    # 文件内容重复，删除临时文件，使用现有文件
                    os.remove(temp_file_path)
                else:
                    # 文件不重复，将临时文件重命名为最终文件名
                    final_file_path = os.path.join(image_path, unique_file_name)
                    os.rename(temp_file_path, final_file_path)
            else:
                unique_file_name = file_name
            
            photo_data = {
                'photo_id': photo.id,
                'access_hash': photo.access_hash,
                'file_path': f'images/{unique_file_name}'
            }
        return photo_data

    def process_peerid_by_type(self, peer_id):
        """
        将peer_id转换为通用chat_id
        :peer_id: 原始ID(-100开头表示大型群组/频道,负数(非-100开头)表示普通群组,正数表示私人/机器人)
        :return: 处理后的通用chat_id
        """
        peer_id_str = str(peer_id)
        
        # 如果peer_id以-100开头（大型群组/频道），去掉-100前缀
        if peer_id_str.startswith('-100'):
            return peer_id_str[4:]  # 去掉'-100'前缀
        # 如果是负数但不以-100开头（普通群组），去掉负号
        elif peer_id_str.startswith('-'):
            return peer_id_str[1:]  # 去掉'-'前缀
        else:
            # 正数（私人/机器人），保持原状
            return peer_id_str

    async def process_document(self, message, document_path):
        """
        处理消息中的文档
        :param message: Telegram消息对象
        :param document_path: 文档保存路径
        :return: 处理后的document字典
        """
        document_data = {}
        document = message.document
        if document and document.attributes:
            file_name = ''
            for attr in document.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    file_name = attr.file_name
                    break
            if file_name:
                unique_file_name = file_name
                mime_type = document.mime_type if hasattr(document, 'mime_type') else ''
                file_size = document.size if hasattr(document, 'size') else 0
                file_hash = ''
                video_thumb_path = ''
                final_file_path = ''
                
                logger.debug(f"Processing document: {file_name}, mime_type: {mime_type}, size: {file_size}")
                
                # 根据配置设置决定是否下载文件
                should_download = self._should_download_file(file_name, mime_type)
                logger.debug(f"Should download {file_name}: {should_download}")
                
                if should_download:
                    # 先下载到临时文件用于哈希检查
                    temp_file_path = os.path.join(document_path, f"{file_name}.tmp")
                    await self.client.download_media(message=message, file=temp_file_path)
                    logger.debug(f"Downloaded to temp file: {temp_file_path}")
                    
                    # 检查是否有重复文件
                    unique_file_name, is_duplicate = self._get_unique_filename(document_path, file_name, temp_file_path)
                    
                    if is_duplicate:
                        # 文件内容重复，删除临时文件，使用现有文件
                        os.remove(temp_file_path)
                        final_file_path = os.path.join(document_path, unique_file_name)
                        logger.debug(f"File duplicate found, using existing: {unique_file_name}")
                    else:
                        # 文件不重复，将临时文件重命名为最终文件名
                        final_file_path = os.path.join(document_path, unique_file_name)
                        os.rename(temp_file_path, final_file_path)
                        logger.debug(f"File saved as: {unique_file_name}")
                    
                    # 计算文件哈希值
                    file_hash = self._calculate_file_hash(final_file_path) or ''
                
                # 如果是视频类型，下载缩略图（无论是否下载视频文件）
                # 但跳过动画表情的缩略图下载
                if mime_type and mime_type.startswith('video/') and file_name not in ['sticker.webp', 'sticker.webm']:
                    logger.debug(f"Processing video thumbnail for: {file_name}")
                    if should_download:
                        await self._download_video_thumbnail(message, document_path, unique_file_name)
                        # 设置缩略图路径
                        name_without_ext = os.path.splitext(unique_file_name)[0]
                        video_thumb_path = f'document/thumbs/{name_without_ext}.jpg'
                    else:
                        await self._download_video_thumbnail(message, document_path, file_name)
                        # 设置缩略图路径
                        name_without_ext = os.path.splitext(file_name)[0]
                        video_thumb_path = f'thumbs/{name_without_ext}.jpg'
                
                # 获取peer_id（原始ID）
                peer_id = str(message.chat_id)
                
                # 转换peer_id为chat_id
                chat_id = self.process_peerid_by_type(peer_id)
                
                # 保存文档信息到数据库
                save_params = {
                    'peer_id': peer_id,
                    'chat_id': chat_id,
                    'message_id': str(message.id),
                    'filename_origin': file_name,
                    'file_ext_name': unique_file_name.split('.')[-1] if '.' in unique_file_name else '',
                    'mime_type': mime_type,
                    'filepath': f'document/{unique_file_name}' if should_download else '',
                    'video_thumb_path': video_thumb_path,
                    'file_hash': file_hash,
                    'file_size': file_size
                }

                logger.debug(f"Saving document info to database: message_id={message.id}, filename={file_name}")
                TgFileInfoManager.save_document_info(**save_params)
                
                document_data = {
                    'document_id': document.id,
                    'file_name': unique_file_name,  # 使用实际保存的文件名
                    'ext': unique_file_name.split('.')[-1] if '.' in unique_file_name else '',
                    'access_hash': document.access_hash,
                    'file_path': f'document/{unique_file_name}' if should_download else '',
                    'video_thumb_path': video_thumb_path,
                    'mime_type': mime_type,
                    'file_size': file_size,
                    'file_hash': file_hash
                }

        return document_data
    
    async def _download_video_thumbnail(self, message, document_path, video_filename):
        """
        下载视频缩略图
        :param message: Telegram消息对象
        :param document_path: 文档保存路径
        :param video_filename: 视频文件名
        """
        try:
            # 跳过动画表情的缩略图下载
            if video_filename in ['sticker.webp', 'sticker.webm']:
                logger.debug(f"Skipping thumbnail download for sticker: {video_filename}")
                return None
            # 创建缩略图目录
            thumbs_path = os.path.join(document_path, 'thumbs')
            os.makedirs(thumbs_path, exist_ok=True)
            
            # 生成缩略图文件名（与视频文件名保持一致，但扩展名为.jpg）
            name_without_ext = os.path.splitext(video_filename)[0]
            thumb_filename = f'{name_without_ext}.jpg'
            thumb_filepath = os.path.join(thumbs_path, thumb_filename)

            # 检查是否为视频消息并包含缩略图
            if message.video and message.video.thumbs:
                # 遍历所有缩略图，优先下载标准尺寸缩略图 (type='m')
                for i, thumb in enumerate(message.video.thumbs):
                    if thumb.type == 'm':  # 标准缩略图
                        await self.client.download_media(
                            message.video,
                            file=thumb_filepath,
                            thumb=i  # 指定缩略图索引
                        )
                        return thumb_filepath
                
                # 如果没有标准缩略图，下载第一个可用的缩略图
                if message.video.thumbs:
                    await self.client.download_media(
                        message.video,
                        file=thumb_filepath,
                        thumb=0
                    )
                    return thumb_filepath
            
        except Exception as e:
            logger.error(f"Error downloading video thumbnail for {video_filename}: {e}")
        
        return None
