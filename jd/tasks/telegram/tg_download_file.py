import os
import asyncio
from jd.utils.logging_config import get_logger
from jCelery import celery
from jd import app
from jd.jobs.tg_file_info import TgFileInfoManager
from jd.services.spider.tg import TgService

logger = get_logger('jd.tasks.tg.tg_download_file', {'component': 'telegram', 'module': 'download_file'})


@celery.task(bind=True, name='tg_download_file')
async def download_file_by_message_task(chat_id, message_id):
    """
    Celery任务 根据chat_id和message_id下载文件
    :param chat_id: 群聊ID
    :param message_id: 消息ID
    :return: 下载结果
    """
    logger.info(f"开始下载文件任务: chat_id={chat_id}, message_id={message_id}")
    
    try:
        # 初始化TG服务
        tg_service = await TgService.init_tg('web')
        if not tg_service:
            error_msg = 'Telegram服务初始化失败'
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'chat_id': chat_id,
                'message_id': message_id
            }
        
        try:
            # 设置文件保存路径
            document_path = os.path.join(app.static_folder, 'document')
            image_path = os.path.join(app.static_folder, 'images')
            
            # 确保目录存在
            os.makedirs(document_path, exist_ok=True)
            os.makedirs(image_path, exist_ok=True)
            
            # 定义异步下载函数
            async def download_file():
                return await TgFileInfoManager.download_file_by_message(
                    client=tg_service.client,
                    chat_id=chat_id,
                    message_id=message_id,
                    document_path=document_path,
                    image_path=image_path
                )
            
            # 在新的事件循环中运行异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(download_file())
                logger.info(f"文件下载任务完成: chat_id={chat_id}, message_id={message_id}, success={result['success']}")
                return result
            finally:
                loop.close()
            
        finally:
            # 清理TG服务
            if tg_service:
                await tg_service.close_client()
        
    except Exception as e:
        error_msg = f'文件下载任务失败: {str(e)}'
        logger.error(f"{error_msg}, chat_id={chat_id}, message_id={message_id}")
        return {
            'success': False,
            'message': error_msg,
            'chat_id': chat_id,
            'message_id': message_id,
            'error': str(e)
        }