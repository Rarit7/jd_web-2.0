import datetime
import json
import logging
import os
import time
from random import randint

import requests
from bs4 import BeautifulSoup
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest, GetFullChannelRequest, GetParticipantsRequest
from telethon.tl.functions.contacts import GetContactsRequest, DeleteContactsRequest
from telethon.tl.functions.messages import CheckChatInviteRequest, ImportChatInviteRequest, GetFullChatRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import ChatInviteAlready, ChatInvite, Channel, Chat, Message, ChannelParticipantsSearch, \
    ChannelForbidden, ChannelParticipantsRecent, User

from jd import app
from .tg_download import TelegramDownloadManager

logger = logging.getLogger(__name__)


class TelegramSpider:
    """
    Telegram网页爬虫类，用于从t.me链接获取频道/群组的公开信息
    通过解析HTML页面获取头像、用户名、描述等基本信息
    """

    def __init__(self):
        """
        初始化爬虫实例
        设置请求的基本参数
        """
        self._url = ''
        self._headers = {}
        self._proxies = None

    def _send_request(self):
        """
        发送HTTP GET请求到指定URL
        
        Returns:
            dict: 解析后的页面数据，失败时返回空字典
        """
        try:
            r = requests.get(self._url, headers=self._headers, proxies=self._proxies, timeout=10)
            html = r.text
            status_code = r.status_code
            if status_code != 200:
                return {}
            return self._parse_result(html)
        except Exception as e:
            print(e)
        return {}

    def _parse_result(self, html):
        """
        解析HTML页面，提取Telegram频道/群组信息
        
        Args:
            html (str): HTML页面内容
            
        Returns:
            dict: 包含photo_url, account, username, desc的字典
        """
        soup = BeautifulSoup(html, 'html.parser')
        data = {
            'photo_url': self._get_div_text(soup, 'tgme_page_photo'),
            'account': self._get_div_text(soup, 'tgme_page_extra'),
            'username': self._get_div_text(soup, 'tgme_page_title'),
            'desc': self._get_div_text(soup, 'tgme_page_description')
        }
        return data

    def _get_div_text(self, soup, class_name):
        """
        根据CSS类名提取指定div的文本内容
        
        Args:
            soup (BeautifulSoup): BeautifulSoup解析对象
            class_name (str): CSS类名
            
        Returns:
            str: 提取的文本内容，图片类返回src属性，其他返回文本
        """
        div = soup.find_all(class_=class_name, limit=1)
        text = ''
        if div:
            if class_name == 'tgme_page_photo':
                text = div[0].img['src']
            else:
                text = div[0].text.replace('\n', '')
        return text

    def search_query(self, url=''):
        """
        搜索指定URL的Telegram频道/群组信息
        
        Args:
            url (str): t.me链接
            
        Returns:
            dict: 频道/群组的基本信息
        """
        print('start...')
        if not url:
            return {}
        self._set_params(url)
        tel_data = self._send_request()
        print('end...')
        return tel_data

    def _set_params(self, url):
        """
        设置请求参数
        
        Args:
            url (str): 目标URL
        """
        self._url = url


class TelegramAPIs(object):
    """
    Telegram API客户端类，提供完整的Telegram API功能
    包括群组管理、消息获取、用户信息查询、文件下载等核心功能
    """

    def __init__(self):
        """
        初始化API客户端实例
        """
        self.client = None
        self.download_manager = None
        self.session_lock_file = None

    async def init_client(self, session_name, api_id, api_hash, proxy=None):
        """
        初始化Telegram客户端连接
        
        Args:
            session_name (str): session文件路径，用于保持登录状态
            api_id (str): Telegram API ID
            api_hash (str): Telegram API Hash
            proxy (tuple, optional): 代理配置，格式为(协议, IP, 端口)
        """
        import asyncio
        import fcntl
        import os
        
        # 创建session文件锁，防止多进程同时访问
        lock_file_path = f"{session_name}.lock"
        lock_file = None
        
        try:
            # 尝试获取文件锁
            lock_file = open(lock_file_path, 'w')
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            logger.info(f"获取session文件锁成功: {lock_file_path}")
            
            # 处理proxy参数
            client_kwargs = {}
            if proxy:
                client_kwargs['proxy'] = proxy
                
            # 设置Telethon日志等级为WARNING，减少冗余日志输出
            logging.getLogger('telethon').setLevel(logging.WARNING)
            
            # 禁用Telethon的自动保存以减少文件操作冲突
            client_kwargs['device_model'] = 'Server'
            client_kwargs['system_version'] = '1.0'
            client_kwargs['app_version'] = '1.0'
            client_kwargs['lang_code'] = 'en'
            client_kwargs['auto_reconnect'] = False  # 禁用自动重连
            
            self.client = TelegramClient(session_name, api_id, api_hash, **client_kwargs)
            self.session_lock_file = lock_file  # 保存锁文件引用
            
            # 连接并启动客户端
            await self.client.connect()
            if not await self.client.is_user_authorized():
                logger.error(f"Session {session_name} 未授权，需要重新登录")
                return False
            
            # 初始化下载管理器
            self.download_manager = TelegramDownloadManager(self.client)
            logger.info(f"Telegram客户端初始化成功: {session_name}")
            return True
            
        except BlockingIOError:
            if lock_file:
                lock_file.close()
            
            # 实现固定间隔重试策略，减少日志噪音
            max_retries = 5
            retry_interval = 60.0  # 1分钟间隔
            
            for retry_count in range(max_retries):
                wait_time = retry_interval  # 固定1分钟间隔
                
                if retry_count == 0:
                    logger.info(f"Session文件 {session_name} 被占用，等待 {wait_time:.1f}s 后重试")
                else:
                    logger.debug(f"Session文件 {session_name} 重试 {retry_count + 1}/{max_retries}，等待 {wait_time:.1f}s")
                
                await asyncio.sleep(wait_time)
                
                # 尝试重新获取锁
                try:
                    lock_file = open(lock_file_path, 'w')
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    logger.info(f"Session文件锁获取成功: {lock_file_path} (重试 {retry_count + 1} 次后)")
                    
                    # 继续初始化客户端的逻辑
                    client_kwargs = {}
                    if proxy:
                        client_kwargs['proxy'] = proxy
                        
                    logging.getLogger('telethon').setLevel(logging.WARNING)
                    client_kwargs['device_model'] = 'Server'
                    client_kwargs['system_version'] = '1.0'
                    client_kwargs['app_version'] = '1.0'
                    client_kwargs['lang_code'] = 'en'
                    client_kwargs['auto_reconnect'] = False
                    
                    self.client = TelegramClient(session_name, api_id, api_hash, **client_kwargs)
                    self.session_lock_file = lock_file
                    
                    await self.client.connect()
                    if not await self.client.is_user_authorized():
                        logger.error(f"Session {session_name} 未授权，需要重新登录")
                        return False
                    
                    self.download_manager = TelegramDownloadManager(self.client)
                    logger.info(f"Telegram客户端初始化成功: {session_name}")
                    return True
                    
                except BlockingIOError:
                    if lock_file:
                        lock_file.close()
                    continue  # 继续下一次重试
                except Exception as inner_e:
                    logger.error(f"重试过程中发生错误: {inner_e}")
                    if lock_file:
                        lock_file.close()
                    raise inner_e
            
            # 所有重试都失败了
            total_wait_time = max_retries * retry_interval
            logger.error(f"Session文件 {session_name} 在 {max_retries} 次重试({total_wait_time/60:.0f}分钟)后仍被占用，初始化失败")
            return False
            
        except Exception as e:
            logger.error(f"Telegram客户端初始化失败: {e}")
            if lock_file:
                lock_file.close()
            raise e


    async def close_client(self):
        """
        关闭Telegram客户端连接
        释放网络资源和文件锁
        """
        if self.client:
            try:
                if self.client.is_connected():
                    await self.client.disconnect()
                # 等待一小段时间确保连接完全关闭
                import asyncio
                await asyncio.sleep(0.1)
                logger.info('Telegram客户端连接已关闭')
            except Exception as e:
                logger.error(f'关闭Telegram客户端时发生错误: {e}')
            finally:
                self.client = None
        
        # 释放session文件锁
        if hasattr(self, 'session_lock_file') and self.session_lock_file:
            try:
                import fcntl
                fcntl.flock(self.session_lock_file.fileno(), fcntl.LOCK_UN)
                self.session_lock_file.close()
                logger.info('Session文件锁已释放')
            except Exception as lock_error:
                logger.warning(f'释放session文件锁时发生错误: {lock_error}')
            finally:
                self.session_lock_file = None

    def _ensure_directory(self, path):
        """
        确保指定目录存在，不存在则创建
        
        Args:
            path (str): 目录路径
        """
        os.makedirs(path, exist_ok=True)

    async def _download_avatar(self, chat, avatar_path):
        """
        下载频道/群组头像到本地
        
        Args:
            chat: Telegram聊天对象（频道或群组）
            avatar_path (str): 头像保存的本地目录
            
        Returns:
            str: 头像的相对路径，如果没有头像则返回空字符串
        """
        photo_path = ''
        photo = chat.photo
        if photo and hasattr(photo, "photo_id"):
            file_full_path = f'{avatar_path}/{str(photo.photo_id)}.jpg'
            photo_path = f'images/avatar/{str(photo.photo_id)}.jpg'
            if not os.path.exists(file_full_path):              
                await self.client.download_profile_photo(entity=chat, file=file_full_path)
        return photo_path

    def _parse_message_sender(self, message):
        """
        解析消息发送者的详细信息
        
        Args:
            message: Telegram消息对象
            
        Returns:
            dict: 包含user_id, user_name, nick_name的发送者信息字典
        """
        sender_info = {
            "user_id": 0,
            "user_name": "",
            "nick_name": ""
        }
        
        try:
            if message.sender:
                sender_info["user_id"] = message.sender.id
                if isinstance(message.sender, ChannelForbidden):
                    username = ""
                else:
                    username = message.sender.username
                    username = username if username else ""
                sender_info["user_name"] = username
                
                if isinstance(message.sender, Channel) or isinstance(message.sender, ChannelForbidden):
                    first_name = message.sender.title
                    last_name = ""
                else:
                    first_name = message.sender.first_name
                    last_name = message.sender.last_name
                    first_name = first_name if first_name else ""
                    last_name = " " + last_name if last_name else ""
                sender_info["nick_name"] = "{0}{1}".format(first_name, last_name)
        except Exception as e:
            logger.warning(f'无法获取发送者信息 message_id:{message.id}, user_id:{getattr(message, "from_id", "unknown")}: {e}')
            # 设置默认值，继续处理消息
            if hasattr(message, 'from_id') and message.from_id:
                if hasattr(message.from_id, 'user_id'):
                    sender_info["user_id"] = message.from_id.user_id
                else:
                    sender_info["user_id"] = 0
            else:
                sender_info["user_id"] = 0
        
        return sender_info

    async def join_conversation(self, invite):
        """
        加入Telegram频道或群组
        
        支持两种加入方式：
        1. 公开群组/频道：使用username（如：@channelname）
        2. 私有群组/频道：使用邀请链接的hash部分
        
        Args:
            invite (str): 频道/群组的username或邀请链接hash
            
        Returns:
            dict: 加入结果，格式为：
                {
                    "data": {"id": chat_id, "group_name": invite},
                    "result": "Done/Failed", 
                    "reason": "错误原因"
                }
        
        Note:
            - 无法通过纯数字ID直接加入频道/群组
            - 更换username后，旧username将失效
        """
        # 每个加组的操作都休眠10秒先，降低速率
        time.sleep(5)
        chat_id = 0
        result = "Failed"
        result_json = {
            "data": {"id": chat_id, "group_name": invite},
            "result": result,
            "reason": "",
        }
        try:
            # Checking a link without joining
            # 检测私有频道或群组时，由于传入的是hash，可能会失败(已测试，除非是被禁止的，否则也会成功)
            updates = await self.client(CheckChatInviteRequest(invite))
            if isinstance(updates, ChatInviteAlready):
                chat_id = updates.chat.id
                result = "Done"
            elif isinstance(updates, ChatInvite):
                # Joining a private chat or channel
                updates = await self.client(ImportChatInviteRequest(invite))
                chat_id = updates.chats[0].id
                result = "Done"
        except Exception as e:
            try:
                # Joining a public chat or channel
                updates = await self.client(JoinChannelRequest(invite))
                result = "Done"
            except Exception as ee:
                result_json["reason"] = str(ee)
                return result_json
            chat_id = updates.chats[0].id
        result_json["data"]["id"] = chat_id
        result_json["result"] = result

        return result_json

    def delete_all_dialog(self, is_all=0):
        """
        批量删除对话框
        
        根据条件删除不同类型的对话：
        - 删除已删除账户的对话
        - 删除特定模式的用户对话（包含数字组合的用户名）
        - 可选择删除所有群组/频道对话
        
        Args:
            is_all (int): 是否删除所有对话，0=仅删除特定条件，1=删除所有
        """
        for dialog in self.client.get_dialogs():
            # like "4721 4720"、"5909 5908"
            name = dialog.name
            is_new_user = False
            if " " in name and ("1" in name or "3" in name or "6" in name):
                is_new_user = True
            # 退出频道或群组
            if is_all and hasattr(dialog.entity, "title"):
                chat = dialog.entity
                self.client.delete_dialog(chat)
                print("已离开<{}>群组".format(dialog.entity.title))
            # 删除delete account
            elif dialog.name == "":
                chat = dialog.entity
                self.client.delete_dialog(chat)
                print("已删除Deleted Account用户对话框")
            elif is_new_user:
                chat = dialog.entity
                self.client.delete_dialog(chat)
                print("已删除{}用户对话框".format(dialog.name))
            elif is_all:
                chat = dialog.entity
                self.client.delete_dialog(chat)
                print("已删除{}用户对话框".format(dialog.name))
            else:
                pass

    async def get_me(self):
        """
        获取当前登录账户的详细信息
        
        Returns:
            User: 当前账户的完整信息对象，包含ID、用户名、姓名等
        """
        myself = await self.client.get_me()
        return myself

    def get_contacts(self):
        """
        获取当前账户的所有联系人列表
        
        Returns:
            ContactsContacts: 联系人列表对象，包含用户信息和联系人数量
        """
        contacts = self.client(GetContactsRequest(0))
        return contacts

    def delete_contact(self, ids):
        """
        批量删除指定的联系人
        
        Args:
            ids (list): 要删除的联系人ID列表
        """
        self.client(DeleteContactsRequest(ids))

    async def get_dialog_list(self):
        """
        获取当前账户已加入的所有频道和群组列表
        
        自动下载并保存频道/群组头像，提取详细信息包括：
        - 基本信息：ID、标题、用户名
        - 统计信息：成员数量、未读消息数
        - 媒体信息：头像路径
        - 分类信息：频道/群组类型、公开/私有状态
        
        Yields:
            dict: 每个频道/群组的详细信息，格式为：
                {
                    "result": "success",
                    "reason": "ok", 
                    "data": {
                        "id": int,
                        "title": str,
                        "username": str,
                        "megagroup": "channel/group",
                        "member_count": int,
                        "channel_description": str,
                        "is_public": int,
                        "join_date": str,
                        "unread_count": int,
                        "group_type": str,
                        "photo_path": str
                    }
                }
        """
        avatar_path = os.path.join(app.static_folder, 'images/avatar')
        self._ensure_directory(avatar_path)
        async for dialog in self.client.iter_dialogs():
            # 确保每次数据的准确性
            result_json = {"result": "success", "reason": "ok", 'data': {}}
            photo_path = ''
            # 只爬取频道或群组，排除个人
            if hasattr(dialog.entity, "title"):
                chat = dialog.entity
                if isinstance(chat, Channel):
                    channel_full = await self.client(GetFullChannelRequest(chat))
                    member_count = channel_full.full_chat.participants_count
                    channel_description = channel_full.full_chat.about
                    username = await self._process_channel_username(chat, channel_full)
                    megagroup = channel_full.chats[0].megagroup
                    group_type = 'channel' if not megagroup else 'group'
                    photo_path = await self._download_avatar(chat, avatar_path)
                elif isinstance(chat, Chat):
                    channel_full = await self.client(GetFullChatRequest(chat.id))
                    member_count = channel_full.chats[0].participants_count
                    channel_description = channel_full.full_chat.about
                    username = None
                    megagroup = True
                    group_type = 'chat'
                else:
                    yield result_json
                    continue

                out = {
                    "id": chat.id,
                    "title": chat.title,
                    "username": username,
                    # 'democracy': channel_full.chats[0].democracy,
                    "megagroup": "channel" if not megagroup else "group",
                    "member_count": member_count,
                    "channel_description": channel_description,
                    "is_public": 1 if username else 0,
                    "join_date": chat.date.strftime("%Y-%m-%d %H:%M:%S+%Z"),
                    "unread_count": dialog.unread_count,
                    'group_type': group_type,
                    'photo_path': photo_path
                }
                result_json["data"] = out
                yield result_json

    async def _process_channel_username(self, chat, channel_full):
        """
        稳定获取频道/群组用户名的方法
        
        优先级：
        1. chat.username (传统单用户名)
        2. channel_full.chats[0].username (备用单用户名)
        3. usernames列表中editable=True的主用户名
        4. usernames列表中第一个active=True的用户名
        5. usernames列表中第一个用户名（最后备用）
        """
        # 方法1: 直接从chat实体获取传统用户名
        username = chat.username
        if username:
            return username
            
        # 方法2: 从完整频道信息获取传统用户名
        username = channel_full.chats[0].username
        if username:
            return username
            
        # 方法3: 处理多用户名系统 - 优先检查chat对象的usernames
        usernames_list = None
        if hasattr(chat, "usernames") and chat.usernames:
            usernames_list = chat.usernames
        elif hasattr(channel_full.full_chat, "usernames") and channel_full.full_chat.usernames:
            usernames_list = channel_full.full_chat.usernames
        
        if usernames_list:
            # 优先返回可编辑的主用户名 (editable=True)
            for u in usernames_list:
                if (hasattr(u, 'editable') and u.editable and 
                    hasattr(u, 'active') and u.active):
                    return u.username
            
            # 备用1: 返回第一个活跃的用户名
            for u in usernames_list:
                if hasattr(u, 'active') and u.active:
                    return u.username
            
            # 备用2: 返回列表中第一个用户名
            if usernames_list:
                return usernames_list[0].username
                
        return None


    async def get_person_dialog_list(self):
        """
        获取所有个人聊天对话列表
        
        只返回与个人用户的对话，排除群组和频道
        
        Returns:
            list: 个人对话列表，每个元素包含：
                {
                    "id": int,           # 用户ID
                    "username": str,     # 用户名
                    "user_id": int,      # 用户ID（重复）
                    "unread_count": int  # 未读消息数
                }
        """
        result = []
        async for dialog in self.client.iter_dialogs():
            # 确保每次数据的准确性
            chat = dialog.entity
            if isinstance(chat, User):
                channel_full = await self.client(GetFullUserRequest(chat.id))
                username = channel_full.users[0].username or ''
                user_id = channel_full.users[0].id
            else:
                continue

            out = {
                "id": chat.id,
                "username": username,
                "user_id": user_id,
                "unread_count": dialog.unread_count,
            }
            result.append(out)
        return result

    async def get_dialog(self, chat_id, is_more=False):
        """
        根据chat_id获取对话实体对象
        
        提供两种获取方式：
        1. 直接方式：使用get_entity()方法（推荐，速度快）
        2. 遍历方式：遍历所有对话找到匹配的ID（兜底方案）
        
        Args:
            chat_id (int): 群组/频道的唯一ID
            is_more (bool): 是否使用遍历方式，默认False使用直接方式
            
        Returns:
            Chat/Channel/User: Telegram实体对象，可用于后续API调用
        """
        # 方法一
        if is_more:
            chat = None
            async for dialog in self.client.iter_dialogs():
                if dialog.entity.id == chat_id:
                    chat = dialog.entity
                    break
        # 方法二
        else:
            chat = await self.client.get_entity(chat_id)

        return chat


    async def scan_message(self, chat, **kwargs):
        """
        扫描指定频道/群组的历史消息
        
        完整处理消息内容，包括：
        - 文本内容提取
        - 发送者信息解析  
        - 媒体文件下载（图片、文档）
        - 回复和转发信息处理
        - 智能限流防止被封
        
        Args:
            chat: Telegram聊天实体对象
            **kwargs: 扫描参数
                - limit (int): 消息数量限制
                - last_message_id (int): 起始消息ID
                - offset_date (datetime, optional): 起始日期
                - reverse (bool, optional): 遍历方向，默认False（新到旧），True为旧到新
                
        Yields:
            dict: 每条消息的详细信息，包含：
                - message_id: 消息ID
                - user_id, user_name, nick_name: 发送者信息
                - chat_id: 所属聊天ID
                - postal_time: 发送时间
                - message: 消息文本内容
                - photo: 图片信息（已下载）
                - document: 文档信息（已下载）
                - reply_to_msg_id: 回复的消息ID
                - from_name, from_time: 转发来源信息
                - replies_info: 回复统计信息
        """
        tick = 0
        waterline = randint(5, 20)
        limit = kwargs.get("limit", 100)
        min_id = kwargs.get("last_message_id", -1)
        # 默认只能从最远开始爬取
        offset_date = kwargs.get("offset_date", None)
        reverse = kwargs.get("reverse", False)
        count = 0
        image_path = os.path.join(app.static_folder, 'images')
        self._ensure_directory(image_path)
        document_path = os.path.join(app.static_folder, 'document')
        self._ensure_directory(document_path)
        async for message in self.client.iter_messages(
                chat,
                limit=limit,
                offset_date=offset_date,
                offset_id=min_id,
                wait_time=1,
                reverse=reverse,
        ):

            if isinstance(message, Message):
                logger.debug(f'message | chat_id:{chat.id}, info:{message.to_dict()}')
                content = ""
                try:
                    content = message.message
                except Exception as e:
                    print(e)
                m = dict()
                m["message_id"] = message.id
                m["reply_to_msg_id"] = 0
                m["from_name"] = ""
                m["from_time"] = datetime.datetime.fromtimestamp(657224281)
                
                # 使用公共方法解析发送者信息
                sender_info = self._parse_message_sender(message)
                m.update(sender_info)
                if message.is_reply:
                    m["reply_to_msg_id"] = message.reply_to_msg_id
                if message.forward:
                    m["from_name"] = message.forward.from_name
                    m["from_time"] = message.forward.date
                m["chat_id"] = chat.id
                m["postal_time"] = message.date
                m["message"] = content
                # 处理照片
                m['photo'] = await self.download_manager.process_photo(message, image_path)
                # 处理文档
                m['document'] = await self.download_manager.process_document(message, document_path)
                m['replies_info'] = {}
                if message.replies:
                    try:
                        m['replies_info'] = message.replies.to_dict()
                    except Exception as e:
                        print(e)
                tick += 1
                if tick >= waterline:
                    tick = 0
                    waterline = randint(5, 10)
                    time.sleep(waterline)
                count += 1
                yield m


    async def get_chatroom_user_info(self, chat_id, nick_name):
        """
        在指定频道/群组中搜索特定昵称的用户信息
        
        Args:
            chat_id (int): 频道/群组ID
            nick_name (str): 要搜索的用户昵称
            
        Returns:
            list: 匹配的用户信息列表，每个元素包含：
                {
                    "user_id": int,        # 用户ID
                    "username": str,       # 用户名
                    "first_name": str,     # 名字
                    "last_name": str       # 姓氏
                }
                
        Note:
            搜索结果数量随机限制在5-10个，避免触发限流
        """
        chat = await self.get_dialog(chat_id)
        result = []
        try:
            participants = await self.client(
                GetParticipantsRequest(
                    chat,
                    filter=ChannelParticipantsSearch(nick_name),
                    offset=0,
                    limit=randint(5, 10),
                    hash=0,
                )
            )
        except Exception as e:
            print("查找《{}》用户失败，失败原因：{}".format(nick_name, str(e)))
            return []

        if not participants.users:
            print("未找到《{}》用户。".format(nick_name))
            return []

        for entity in participants.users:
            user_info = entity.to_dict()
            result.append({'user_id': user_info['id'],
                           'username': user_info['username'],
                           'first_name': user_info['first_name'],
                           'last_name': user_info['last_name']})
            print(f'{nick_name}:{user_info}')

        return result

    async def get_chatroom_all_user_info(self, chat_id):
        """
        获取指定频道/群组的所有用户信息
        
        获取最近活跃的用户列表，适用于分析群组成员构成
        
        Args:
            chat_id (int): 频道/群组ID
            
        Returns:
            list: 用户信息列表，每个元素包含：
                {
                    "user_id": int,        # 用户ID
                    "username": str,       # 用户名
                    "first_name": str,     # 名字
                    "last_name": str       # 姓氏
                }
                
        Note:
            - 限制返回最近的50个活跃用户
            - 大型群组可能无法获取完整用户列表（API限制）
        """
        chat = await self.get_dialog(chat_id)
        result = []
        try:
            participants = await self.client(
                GetParticipantsRequest(
                    chat,
                    filter=ChannelParticipantsRecent(),
                    offset=0,
                    limit=50,
                    hash=0,
                )
            )
        except Exception as e:
            print("查找《{}》用户失败，失败原因：{}".format(chat_id, str(e)))
            return []

        if not participants.users:
            print("未找到《{}》用户。".format(chat_id))
            return []

        for entity in participants.users:
            user_info = entity.to_dict()
            result.append({'user_id': user_info['id'],
                           'username': user_info['username'],
                           'first_name': user_info['first_name'],
                           'last_name': user_info['last_name']})

        return result

    async def get_full_channel(self, chat_id):
        """
        获取指定频道/群组的完整详细信息
        
        获取比基本信息更详细的数据，包括描述、统计信息等
        同时下载并保存头像文件
        
        Args:
            chat_id (int): 频道/群组ID
            
        Returns:
            dict: 详细信息字典，包含：
                {
                    "id": int,                    # 频道/群组ID
                    "title": str,                 # 标题
                    "username": str,              # 用户名
                    "megagroup": str,             # "channel" 或 "group"
                    "member_count": int,          # 成员数量
                    "channel_description": str,   # 描述信息
                    "is_public": int,            # 是否公开 (1/0)
                    "join_date": str,            # 加入日期
                    "photo_path": str            # 头像本地路径
                }
                
        Note:
            如果频道不存在或无权访问，返回空字典
        """
        avatar_path = os.path.join(app.static_folder, 'images/avatar')
        self._ensure_directory(avatar_path)
        chat = await self.get_dialog(chat_id)
        if not chat:
            return {}
        channel_full = await self.client(GetFullChannelRequest(chat))
        if not channel_full:
            return {}
        member_count = channel_full.full_chat.participants_count
        channel_description = channel_full.full_chat.about
        username = channel_full.chats[0].username
        megagroup = channel_full.chats[0].megagroup
        photo_path = await self._download_avatar(chat, avatar_path)
        out = {
            "id": chat.id,
            "title": chat.title,
            "username": username,
            "megagroup": "channel" if not megagroup else "group",
            "member_count": member_count,
            "channel_description": channel_description,
            "is_public": 1 if username else 0,
            "join_date": chat.date.strftime("%Y-%m-%d %H:%M:%S+%Z"),
            'photo_path': photo_path
        }
        return out


def test_tg_spider():
    """
    测试TelegramSpider网页爬虫功能
    
    测试多个t.me链接的数据抓取，并根据账户类型进行分类：
    - 个人账户：account字段包含'@'
    - 群组账户：account字段包含'subscribers' 
    - 其他账户：不符合上述条件的账户
    """
    spider = TelegramSpider()
    url_list = ['https://t.me/feixingmeiluo', 'https://t.me/huaxuerou', 'https://t.me/ppo995']
    for url in url_list:
        data = spider.search_query(url)
        if data:
            if '@' in data['account']:
                print(f'个人账户：{url}, data:{data}')
            elif 'subscribers' in data['account']:
                print(f'群组账户：{url}, data:{data}')
            else:
                print(f'其他账户：{url}, data:{data}')
        else:
            print(f'{url}, 无数据')


if __name__ == '__main__':
    app.ready(db_switch=False, web_switch=False, worker_switch=False)
    tg = TelegramAPIs()
    config_js = app.config['TG_CONFIG']
    session_name = f'{app.static_folder}/utils/default-telegram.session'
    api_id = config_js.get("api_id")
    api_hash = config_js.get("api_hash")
    proxy = config_js.get("proxy", {})
    clash_proxy = None
    # 配置代理
    # if proxy:
    #     protocal = proxy.get("protocal", "socks5")
    #     proxy_ip = proxy.get("ip", "127.0.0.1")
    #     proxy_port = proxy.get("port", 7890)
    #     clash_proxy = (protocal, proxy_ip, proxy_port)
    tg.init_client(
        session_name=session_name, api_id=api_id, api_hash=api_hash, proxy=clash_proxy
    )


