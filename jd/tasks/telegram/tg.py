import asyncio
import datetime
import logging
import os
import time
from zoneinfo import ZoneInfo

import requests
from telethon import TelegramClient, errors

from jCelery import celery
from jd import app, db
from jd.models.tg_account import TgAccount
from jd.models.tg_group import TgGroup
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group_user_info import TgGroupUserInfo
from jd.services.spider.telegram_spider import TelegramSpider, TelegramAPIs
from jd.services.spider.tg import TgService
from jd.tasks.telegram.session_lock import with_session_lock

logger = logging.getLogger(__name__)




@celery.task
@with_session_lock(max_retries=5, check_interval=60)
async def fetch_group_user_info(chat_id, user_id, nick_name, username, sessionname):
    """
    获取群组用户的信息
    :param origin:
    :param nick_name:
    :param chat_id:
    :param user_id:
    :param username:
    :return:
    """
    def download_photo(photo_url, user_id):
        """
        从URL下载用户头像并保存到本地
        
        Args:
            photo_url (str): 头像图片的URL地址
            user_id (str): 用户ID，用作文件名
            
        Returns:
            str: 头像的相对路径
        """
        try:
            logger.info(f'开始下载用户头像: user_id={user_id}, url={photo_url}')
            response = requests.get(photo_url)
            image_path = os.path.join(app.static_folder, 'images/avatar')
            os.makedirs(image_path, exist_ok=True)
            file_path = f'{image_path}/{user_id}.jpg'
            
            # 检查请求是否成功
            if response.status_code == 200:
                # 保存图片到本地
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                logger.info(f'用户头像下载成功: user_id={user_id}, 保存路径={file_path}')
            else:
                logger.warning(f'头像下载失败，HTTP状态码: {response.status_code}, user_id={user_id}')
                file_path = ''
        except Exception as e:
            logger.error(f'用户头像下载异常: user_id={user_id}, 错误={e}')
            file_path = ''

        return f'images/avatar/{user_id}.jpg'
    
    if not user_id or not nick_name:
        return
    user_id = str(user_id)
    group_user = TgGroupUserInfo.query.filter_by(user_id=user_id).first()
    if group_user:
        # 添加不同群组中同一个用户的处理逻辑
        return
    if username:
        url = f'https://t.me/{username}'
        data = TelegramSpider().search_query(url)
        if not data:
            return
        photo_url = data['photo_url']
        file_path = ''
        if photo_url:
            # 下载图片
            file_path = download_photo(photo_url, user_id)

        obj = TgGroupUserInfo(chat_id=chat_id, user_id=user_id, nickname=nick_name,
                              username=username,
                              desc=data['desc'], photo=data['photo_url'], avatar_path=file_path)
        db.session.add(obj)
        db.session.flush()
        db.session.commit()
    else:
        tg = await TgService.init_tg(sessionname)
        try:
            async def get_chat_room_user_info(nickname):
                nickname = nickname.split(' ')
                if len(nickname) > 1:
                    nickname = nickname[0]
                user_info = await tg.get_chatroom_user_info(chat_id, nickname)
                for user in user_info:
                    uid = str(user['user_id'])
                    last_name = user["last_name"] if user["last_name"] else ''
                    n_name = f'{user["first_name"]}{last_name}'
                    g_user = TgGroupUserInfo.query.filter_by(user_id=uid).first()
                    if g_user:
                        continue
                    u = TgGroupUserInfo(chat_id=chat_id, user_id=uid, nickname=n_name,
                                        username=user['username'])
                    db.session.add(u)
                    db.session.flush()
                db.session.commit()

            async with tg.client:
                await get_chat_room_user_info(nick_name)
        finally:
            if tg:
                await tg.close_client()

    return f'群组:{chat_id}, fetch user:{nick_name} finished'


@celery.task
@with_session_lock(max_retries=5, check_interval=60)
async def fetch_group_recent_user_info(sessionname):
    tg = await TgService.init_tg(sessionname)
    try:
        async def get_chat_room_user_info(chat_id, group_name):
            join_result = await tg.join_conversation(group_name)
            print(join_result)
            user_info = await tg.get_chatroom_all_user_info(chat_id)
            for user in user_info:
                user_id = str(user["user_id"])
                last_name = user["last_name"] if user["last_name"] else ''
                n_name = f'{user["first_name"]}{last_name}'
                username = user['username']
                if not username:
                    obj = TgGroupUserInfo(chat_id=chat_id, user_id=user_id, nickname=n_name,
                                          username=username)
                    db.session.add(obj)
                    db.session.commit()
                else:
                    fetch_group_user_info(chat_id, user_id, n_name, user['username'])

        tg_groups = TgGroup.query.filter_by(status=TgGroup.StatusType.JOIN_SUCCESS).all()
        for group in tg_groups:
            async with tg.client:
                await get_chat_room_user_info(int(group.chat_id), group.name)

        return f'fetch recent users finished'
    finally:
        if tg:
            await tg.close_client()



@celery.task
def fetch_account_channel(account_id, origin='celery'):
    tg_account = TgAccount.query.filter(TgAccount.id == account_id).first()
    if not tg_account:
        return

    tg = TelegramAPIs()
    session_dir = f'{app.static_folder}/utils'
    session_name = f'{session_dir}/{tg_account.name}-telegram.session'
    logger.info(f'使用session文件获取频道列表: {tg_account.name}-telegram.session')
    if not os.path.exists(session_name):
        logger.warning(f'Session文件不存在: {session_name}')
    else:
        logger.info(f'Session文件存在: {session_name}')
    try:
        logger.info(f'开始初始化Telegram客户端获取频道，账户: {tg_account.name}')
        tg.init_client(
            session_name=session_name, api_id=tg_account.api_id, api_hash=tg_account.api_hash
        )
        logger.info(f'Telegram客户端初始化成功，准备获取频道列表，账户: {tg_account.name}')
    except Exception as e:
        logger.error(f'获取频道列表时Telegram客户端初始化失败，账户: {tg_account.name}, 错误: {e}')
        return

    async def get_channel():
        async for result in tg.get_dialog_list():
            data = result.get('data', {})
            print(data)
            chat_id = str(data.get('id', ''))
            if not chat_id:
                continue
            tg_group = TgGroup.query.filter(TgGroup.chat_id == chat_id).first()
            if tg_group:
                TgGroup.query.filter(TgGroup.chat_id == chat_id).update({
                    'account_id': tg_account.user_id,
                    'desc': data.get('channel_description', ''),
                    'avatar_path': data.get('photo_path', ''),
                    'chat_id': chat_id,
                    'title': data.get("title", ''),
                    'group_type': TgGroup.GroupType.CHANNEL if data.get('megagroup',
                                                                        '') == 'channel' else TgGroup.GroupType.GROUP,
                })
            else:
                obj = TgGroup(
                    account_id=tg_account.user_id,
                    chat_id=chat_id,
                    name=data.get('username', ''),
                    desc=data.get('channel_description', ''),
                    status=TgGroup.StatusType.JOIN_SUCCESS,
                    avatar_path=data.get('photo_path', ''),
                    title=data.get("title", ''),
                    group_type=TgGroup.GroupType.CHANNEL if data.get('megagroup',
                                                                     '') == 'channel' else TgGroup.GroupType.GROUP,
                )
                db.session.add(obj)
            db.session.commit()

    try:
        with tg.client:
            tg.client.loop.run_until_complete(get_channel())
    finally:
        if tg:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(tg.close_client())
                loop.close()
            except Exception as close_error:
                logger.error(f'关闭TG客户端失败: {close_error}')



def login_tg_account(account_id, origin='celery'):
    tg_account = TgAccount.query.filter(TgAccount.id == account_id).first()
    if not tg_account:
        return
    session_name = get_session_name(tg_account.name, origin)
    api_id = tg_account.api_id
    api_hash = tg_account.api_hash
    phone = tg_account.phone
    code = tg_account.code
    if not api_id or not api_hash or not phone or not code:
        return

    async def start_login():
        if not client.is_connected():
            await client.connect()
        user = None
        try:
            if tg_account.two_step:
                user = await client.sign_in(phone=phone, password=tg_account.password)
            else:
                user = await client.sign_in(phone=phone, code=code, phone_code_hash=tg_account.phone_code_hash)
        except errors.SessionPasswordNeededError:
            TgAccount.query.filter(TgAccount.id == tg_account.id).update({'two_step': 1})
            db.session.commit()
            if client.is_connected():
                client.disconnect()
            return
        except Exception as e:
            logger.info('add_account error: {}'.format(e))
            if client.is_connected():
                client.disconnect()
            return
        print('user', user)
        if user:
            TgAccount.query.filter(TgAccount.id == tg_account.id).update({
                'status': TgAccount.StatusType.JOIN_SUCCESS,
                'username': user.username if user.username else '',
                'user_id': user.id,
                'nickname': f'{user.first_name if user.first_name else ""} {user.last_name if user.last_name else ""}',
                'phone_code_hash': '',
                'code': '',
                'api_code': '',
                'two_step': 0,
            })
        else:
            TgAccount.query.filter(TgAccount.id == tg_account.id).update({
                'status': TgAccount.StatusType.JOIN_FAIL,
                'phone_code_hash': '',
                'code': '',
                'api_code': '',
                'two_step': 0,
            })

        if client.is_connected():
            client.disconnect()

    client = TelegramClient(session_name, api_id, api_hash)

    for i in range(3):
        try:
            client.loop.run_until_complete(start_login())
            break
        except Exception as e:
            print('login error:', e)
            time.sleep(1)

    db.session.commit()
    return


def get_session_name(name, origin):
    session_dir = f'{app.static_folder}/utils'
    os.makedirs(session_dir, exist_ok=True)
    session_name = f'{session_dir}/{name}-telegram.session'
    logger.info(f'构建session文件路径: {name}-telegram.session, 来源: {origin}')
    if os.path.exists(session_name):
        logger.info(f'Session文件存在: {session_name}')
    else:
        logger.info(f'Session文件不存在: {session_name}')
    return session_name


if __name__ == '__main__':
    app.ready(db_switch=True, web_switch=False, worker_switch=True)
    # 验证码登录
    # login_tg_account(24)
    # 密码登录
    login_tg_account(24)
