import logging
import os

import requests

from jd import app
from jd.models.tg_group import TgGroup
from jd.services.spider.telegram_spider import TelegramAPIs, TelegramSpider

logger = logging.getLogger(__name__)


class TgService:
    STATUS_MAP = {
        TgGroup.StatusType.NOT_JOIN: '未加入',
        TgGroup.StatusType.JOIN_SUCCESS: '已加入',
        TgGroup.StatusType.JOIN_FAIL: '加入失败',
        TgGroup.StatusType.JOIN_ONGOING: '进行中',
        TgGroup.StatusType.INVALID_LINK: '已过期'
    }

    @classmethod
    async def init_tg(cls, sessionname=''):
        tg = TelegramAPIs()
        config_js = app.config['TG_CONFIG']
        session_dir = f'{app.static_folder}/utils'
        os.makedirs(session_dir, exist_ok=True)
        
        # 统一session文件命名: {名称}-telegram.session
        if sessionname:
            session_name = f'{session_dir}/{sessionname}-telegram.session'
            logger.info(f'使用指定session文件: {sessionname}-telegram.session')
        else:
            session_name = f'{session_dir}/default-telegram.session'
            logger.info('使用默认session文件: default-telegram.session')
        
        api_id = config_js.get("api_id")
        api_hash = config_js.get("api_hash")
        proxy = config_js.get("proxy", {})
        if proxy:
            protocal = proxy.get("protocal", "socks5")
            proxy_ip = proxy.get("ip", "127.0.0.1")
            proxy_port = proxy.get("port", 7890)
            clash_proxy = (protocal, proxy_ip, proxy_port)
        else:
            clash_proxy = None
        try:
            logger.info(f'开始初始化Telegram客户端，使用session: {session_name}')
            success = await tg.init_client(
                session_name=session_name, api_id=api_id, api_hash=api_hash, proxy=clash_proxy
            )
            if not success:
                logger.error(f"Telegram客户端连接失败，session: {session_name}")
                return None
            logger.info(f'Telegram客户端初始化成功，session文件: {session_name}')
        except Exception as e:
            logger.error(f"Telegram客户端初始化失败，session: {session_name}, 错误: {e}")
            print("here", e)
            return None
        return tg
    

   
    @classmethod
    async def init_tg_with_retry(cls, sessionnames):
        '''
        带有重试机制的TG客户端初始化, 
        用列表中的sessionname逐一尝试初始化TG客户端, 如果失败则使用其他的进行尝试
        :param sessionnames: session_name列表
        :return: 初始化完成的TG客户端
        '''
        if not sessionnames:
            logger.warning("sessionnames列表为空，使用默认session")
            return await cls.init_tg()
        
        for sessionname in sessionnames:
            logger.info(f"尝试使用session: {sessionname}")
            try:
                tg = await cls.init_tg(sessionname)
                if tg is not None:
                    logger.info(f"使用session {sessionname} 初始化成功")
                    return tg
                else:
                    logger.warning(f"session {sessionname} 初始化失败，尝试下一个")
            except Exception as e:
                logger.error(f"session {sessionname} 初始化异常: {e}，尝试下一个")
                continue
        
        logger.error("所有session都初始化失败，尝试使用默认session")
        return await cls.init_tg()

