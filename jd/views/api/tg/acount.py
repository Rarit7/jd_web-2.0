import time

from flask import request, session, jsonify
from flask_socketio import emit
from selenium import webdriver
from selenium.webdriver.common.by import By

from jd import db, socketio, app
from jd.models.tg_account import TgAccount
from jd.models.secure_user import SecureUser
from jd.services.role_service.role import ROLE_SUPER_ADMIN, RoleService
from jd.services.spider.tg import TgService
from jd.tasks.first.tg_app import tg_app_init
from jd.helpers.user import current_user_id

from jd.tasks.telegram.tg import login_tg_account, fetch_account_channel
from jd.jobs.tg_person_dialog import fetch_person_chat_history
from jd.tasks.telegram.tg_fetch_group_info import fetch_account_group_info
from jd.views import get_or_exception, success, APIException
from jd.views.api import api


@api.route('/tg/account/add', methods=['POST'])
def tg_account_add():
    args = request.json
    name = get_or_exception('name', request.json, 'str')
    phone = get_or_exception('phone', request.json, 'str')
    name = name.replace(' ', '')
    
    # 获取当前用户ID
    creator_id = current_user_id if current_user_id else 0
    
    obj = TgAccount.query.filter_by(phone=phone).first()
    if obj and obj.status == TgAccount.StatusType.JOIN_SUCCESS:
        return success({'message': '账户已存在且已登录成功'})
    if not obj:
        obj = TgAccount(name=name, phone=phone, creator_id=creator_id)
        db.session.add(obj)
        db.session.commit()
    else:
        # 如果账户已存在但未成功登录，重置状态为未登录，并更新创建者
        if obj.status != TgAccount.StatusType.JOIN_SUCCESS:
            TgAccount.query.filter_by(phone=phone).update({
                'status': TgAccount.StatusType.NOT_JOIN,
                'creator_id': creator_id
            })
            db.session.commit()

    return success()


@api.route('/tg/account/send_code', methods=['POST'])
def tg_account_send_phone_code():
    """登录tg发送验证码"""
    import asyncio
    import os
    from telethon import TelegramClient
    
    phone = get_or_exception('phone', request.json, 'str')
    obj = TgAccount.query.filter_by(phone=phone).first()
    if not obj:
        raise APIException('账户不存在')
    
    # 使用配置文件中的API凭证
    config_js = app.config['TG_CONFIG']
    api_id = config_js.get("api_id")
    api_hash = config_js.get("api_hash")
    
    if not api_id or not api_hash:
        raise APIException('Telegram API配置不完整')
    
    # 创建session文件路径：统一放在utils目录下
    session_dir = f'{app.static_folder}/utils'
    os.makedirs(session_dir, exist_ok=True)
    session_name = f'{session_dir}/{obj.name}-telegram.session'
    
    try:
        # 同步发送验证码
        async def send_code():
            client = TelegramClient(session_name, api_id, api_hash)
            try:
                await client.connect()
                res = await client.send_code_request(phone, force_sms=False)
                if res:
                    return res.phone_code_hash
                return None
            except Exception as e:
                app.logger.error(f'发送验证码失败: {str(e)}')
                raise e
            finally:
                if client.is_connected():
                    await client.disconnect()
        
        # 执行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            phone_code_hash = loop.run_until_complete(send_code())
            if phone_code_hash:
                # 更新账户信息
                TgAccount.query.filter_by(phone=phone).update({
                    'api_id': api_id,
                    'api_hash': api_hash,
                    'phone_code_hash': phone_code_hash
                })
                db.session.commit()
                return success({'message': '验证码已发送'})
            else:
                raise APIException('发送验证码失败')
        finally:
            loop.close()
            
    except Exception as e:
        app.logger.error(f'发送验证码异常: {str(e)}')
        raise APIException(f'发送验证码失败: {str(e)}')


@api.route('/tg/account/verify', methods=['POST'])
def tg_account_verify():
    """登录tg验证code"""
    import asyncio
    import os
    from telethon import TelegramClient, errors
    
    phone = get_or_exception('phone', request.json, 'str')
    code = get_or_exception('code', request.json, 'str', '')
    obj = TgAccount.query.filter_by(phone=phone).first()
    if not obj:
        raise APIException('账户不存在')
    
    # 检查是否已经发送过验证码
    if not obj.phone_code_hash:
        raise APIException('请先发送验证码')
    
    if not code:
        raise APIException('请输入验证码')
    
    # 创建session文件路径：统一放在utils目录下
    session_dir = f'{app.static_folder}/utils'
    os.makedirs(session_dir, exist_ok=True)
    session_name = f'{session_dir}/{obj.name}-telegram.session'
    
    try:
        # 同步验证登录
        async def verify_login():
            client = TelegramClient(session_name, obj.api_id, obj.api_hash)
            try:
                await client.connect()
                
                # 先尝试用验证码登录
                try:
                    user = await client.sign_in(phone=phone, code=code, phone_code_hash=obj.phone_code_hash)
                    return user, False  # 登录成功，不需要2FA
                except errors.SessionPasswordNeededError:
                    # 需要2FA密码
                    return None, True
                except Exception as e:
                    app.logger.error(f'验证码登录失败: {str(e)}')
                    raise e
                    
            finally:
                if client.is_connected():
                    await client.disconnect()
        
        # 执行异步验证
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            user, needs_2fa = loop.run_until_complete(verify_login())
            
            if needs_2fa:
                # 需要2FA验证
                TgAccount.query.filter_by(phone=phone).update({
                    'code': code,
                    'two_step': 1,
                    'status': TgAccount.StatusType.NOT_JOIN
                })
                db.session.commit()
                return success({'needs_2fa': True, 'message': '需要输入2FA密码'})
            
            elif user:
                # 登录成功
                TgAccount.query.filter_by(phone=phone).update({
                    'status': TgAccount.StatusType.JOIN_SUCCESS,
                    'username': user.username if user.username else '',
                    'user_id': str(user.id),
                    'nickname': f'{user.first_name if user.first_name else ""} {user.last_name if user.last_name else ""}',
                    'phone_code_hash': '',
                    'code': '',
                    'two_step': 0,
                })
                db.session.commit()
                return success({'needs_2fa': False, 'message': '登录成功'})
            else:
                raise APIException('登录失败')
                
        finally:
            loop.close()
            
    except Exception as e:
        # 登录失败
        TgAccount.query.filter_by(phone=phone).update({
            'status': TgAccount.StatusType.JOIN_FAIL,
            'phone_code_hash': '',
            'code': '',
        })
        db.session.commit()
        app.logger.error(f'验证登录异常: {str(e)}')
        raise APIException(f'验证失败: {str(e)}')


@api.route('/tg/account/index', methods=['GET'], roles=[ROLE_SUPER_ADMIN])
def tg_account_index():
    # Redirect to JSON endpoint - the Vue frontend should use /list instead
    return jsonify({
        'err_code': 302,
        'err_msg': 'Redirect to Vue frontend',
        'payload': {'redirect': '/tg/accounts'}
    }), 302


@api.route('/tg/account/delete', methods=['GET'])
def tg_account_delete():
    id = get_or_exception('id', request.args, 'int')
    TgAccount.query.filter_by(id=id).delete()
    db.session.commit()
    return {
        'err_code': 0,
        'err_msg': '',
        'payload': {'message': '删除成功'}
    }


@api.route('/tg/account/chat/search', methods=['POST'])
def tg_account_chat_search():
    account_id = get_or_exception('account_id', request.json, 'str')
    account_id_list = [int(i) for i in account_id.split(',')]
    tg_accounts = TgAccount.query.filter(TgAccount.id.in_(account_id_list),
                                         TgAccount.status == TgAccount.StatusType.JOIN_SUCCESS).all()
    for account in tg_accounts:
        fetch_person_chat_history.delay(account.id)

    return success({'message': '获取聊天记录任务已启动'})


@api.route('/tg/account/tow_step_check', methods=['GET'])
def tg_account_tow_step_check():
    """
    是否有2FA验证
    :return:
    """
    phone = get_or_exception('phone', request.args, 'str')
    obj = TgAccount.query.filter_by(phone=phone).first()
    if not obj:
        return success({'two_step': 0})
    if obj.user_id:
        # 不需要验证
        return success({'two_step': 2})
    return success({'two_step': obj.two_step})


@api.route('/tg/account/api_check', methods=['GET'])
def tg_account_api_check():
    """
    api_id和api_hash check
    :return:
    """
    phone = get_or_exception('phone', request.args, 'str')
    obj = TgAccount.query.filter_by(phone=phone).first()
    if not obj:
        return success({'code': 0})
    if obj.api_id and obj.api_hash:
        # 不需要验证
        return success({'code': 1})
    return success({'code': -1})


@api.route('/tg/account/update_pwd', methods=['POST'])
def tg_account_update_pwd():
    """
    有2fa验证要输入密码
    :return:
    """

    password = get_or_exception('password', request.form, 'str')
    phone = get_or_exception('phone', request.form, 'str')
    TgAccount.query.filter_by(phone=phone).update({'password': password})
    db.session.commit()
    obj = TgAccount.query.filter_by(phone=phone).first()
    login_tg_account.delay(obj.id)

    return success({'message': '密码更新成功'})


@api.route('/tg/account/update_api_code', methods=['POST'])
def tg_account_update_api_code():
    code = get_or_exception('code', request.json, 'str')
    phone = get_or_exception('phone', request.json, 'str')
    TgAccount.query.filter_by(phone=phone).update({'api_code': code})
    db.session.commit()
    return success()


@api.route('/tg/account/group/search', methods=['POST'])
def tg_account_group_search():
    account_id = get_or_exception('account_id', request.json, 'str')
    account_id_list = [int(i) for i in account_id.split(',')]
    tg_accounts = TgAccount.query.filter(TgAccount.id.in_(account_id_list),
                                         TgAccount.status == TgAccount.StatusType.JOIN_SUCCESS).all()
    for account in tg_accounts:
        fetch_account_channel.delay(account.id)

    return success({'message': '获取频道任务已启动'})


@api.route('/tg/account/bind', methods=['POST'])
async def tg_account_bind():
    """绑定当前用户的Telegram账户"""
    try:
        # 获取当前用户ID - 先用一个测试ID
        user_id = current_user_id if current_user_id else 1
        
        app.logger.info(f"开始绑定Telegram账户，用户ID: {user_id}")
        
        # 调用init_tg进行绑定
        tg_instance = await TgService.init_tg(origin='web', username=str(user_id))
        
        if tg_instance is None:
            raise APIException('Telegram账户绑定失败，请检查网络连接和配置')
        
        app.logger.info(f"Telegram账户绑定成功，用户ID: {user_id}")
        
        return success({
            'message': f'用户 {user_id} 的Telegram账户绑定成功',
            'user_id': user_id
        })
    
    except Exception as e:
        app.logger.error(f"Telegram账户绑定失败: {str(e)}")
        return success({
            'message': f'绑定过程出现错误: {str(e)}',
            'error': True
        })


@api.route('/tg/account/bind_test', methods=['POST'])
async def tg_account_bind_test():
    """测试Telegram账户绑定API（无需登录）"""
    try:
        # 从请求中获取用户ID，如果没有则使用默认值
        args = request.get_json() or {}
        user_id = args.get('user_id', 'test_user')
        
        app.logger.info(f"开始测试绑定Telegram账户，用户ID: {user_id}")
        
        # 调用init_tg进行绑定
        tg_instance = await TgService.init_tg(origin='web', username=str(user_id))
        
        if tg_instance is None:
            return success({
                'message': 'Telegram账户绑定失败，请检查网络连接和配置',
                'success': False,
                'user_id': user_id
            })
        
        app.logger.info(f"Telegram账户绑定成功，用户ID: {user_id}")
        
        return success({
            'message': f'用户 {user_id} 的Telegram账户绑定成功',
            'success': True,
            'user_id': user_id
        })
    
    except Exception as e:
        app.logger.error(f"Telegram账户绑定失败: {str(e)}")
        return success({
            'message': f'绑定过程出现错误: {str(e)}',
            'success': False,
            'error': str(e)
        })


@api.route('/tg/account/list', methods=['GET'])
def tg_account_list():
    """获取Telegram账户列表"""
    # 查询账户列表并左连接用户表获取创建者信息
    account_list = db.session.query(TgAccount, SecureUser).outerjoin(
        SecureUser, TgAccount.creator_id == SecureUser.id
    ).order_by(TgAccount.id.desc()).all()
    
    status_map = {
        TgAccount.StatusType.JOIN_SUCCESS: '登录成功',
        TgAccount.StatusType.JOIN_FAIL: '登录失败', 
        TgAccount.StatusType.JOIN_ONGOING: '登录中',
        TgAccount.StatusType.NOT_JOIN: '未登录'
    }
    
    data = []
    for account, creator in account_list:
        # 计算账户关联的群组数量
        from jd.models.tg_group_session import TgGroupSession
        
        # 直接统计该session_name的chat_id数量
        group_count = TgGroupSession.query.filter_by(session_name=account.name).count()
        
        data.append({
            'id': account.id,
            'name': account.name,
            'phone': account.phone,
            'user_id': account.user_id,
            'username': account.username,
            'nickname': account.nickname,
            'status_text': status_map.get(account.status),
            'status': account.status,
            'two_step': account.two_step,
            'creator_id': account.creator_id,
            'creator_username': creator.username if creator else '未知用户',
            'group_count': group_count,
            'created_at': account.created_at.strftime('%Y-%m-%d %H:%M:%S') if account.created_at else '',
            'updated_at': account.updated_at.strftime('%Y-%m-%d %H:%M:%S') if account.updated_at else ''
        })
    
    return success(data)


@api.route('/tg/account/update_api', methods=['POST'])
def tg_account_update_api():
    """更新API ID和API Hash"""
    phone = get_or_exception('phone', request.json, 'str')
    api_id = get_or_exception('api_id', request.json, 'str')
    api_hash = get_or_exception('api_hash', request.json, 'str')
    
    obj = TgAccount.query.filter_by(phone=phone).first()
    if not obj:
        raise APIException('账户不存在')
    
    TgAccount.query.filter_by(phone=phone).update({
        'api_id': api_id,
        'api_hash': api_hash
    })
    db.session.commit()
    
    return success()


@api.route('/tg/account/update_password', methods=['POST'])
def tg_account_update_password():
    """更新2FA密码并登录"""
    import asyncio
    import os
    from telethon import TelegramClient
    
    phone = get_or_exception('phone', request.json, 'str')
    password = get_or_exception('password', request.json, 'str')
    
    obj = TgAccount.query.filter_by(phone=phone).first()
    if not obj:
        raise APIException('账户不存在')
    
    if not obj.two_step:
        raise APIException('账户未启用2FA')
    
    if not password:
        raise APIException('请输入2FA密码')
    
    # 创建session文件路径：统一放在utils目录下
    session_dir = f'{app.static_folder}/utils'
    os.makedirs(session_dir, exist_ok=True)
    session_name = f'{session_dir}/{obj.name}-telegram.session'
    
    try:
        # 同步2FA登录
        async def verify_2fa():
            client = TelegramClient(session_name, obj.api_id, obj.api_hash)
            try:
                await client.connect()
                user = await client.sign_in(phone=phone, password=password)
                return user
            except Exception as e:
                app.logger.error(f'2FA登录失败: {str(e)}')
                raise e
            finally:
                if client.is_connected():
                    await client.disconnect()
        
        # 执行异步验证
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            user = loop.run_until_complete(verify_2fa())
            
            if user:
                # 登录成功
                TgAccount.query.filter_by(phone=phone).update({
                    'status': TgAccount.StatusType.JOIN_SUCCESS,
                    'username': user.username if user.username else '',
                    'user_id': str(user.id),
                    'nickname': f'{user.first_name if user.first_name else ""} {user.last_name if user.last_name else ""}',
                    'password': password,
                    'phone_code_hash': '',
                    'code': '',
                    'two_step': 1,  # 保持2FA状态
                })
                db.session.commit()
                return success({'message': '登录成功'})
            else:
                raise APIException('2FA登录失败')
                
        finally:
            loop.close()
            
    except Exception as e:
        # 登录失败
        TgAccount.query.filter_by(phone=phone).update({
            'status': TgAccount.StatusType.JOIN_FAIL
        })
        db.session.commit()
        app.logger.error(f'2FA验证异常: {str(e)}')
        raise APIException(f'2FA验证失败: {str(e)}')


@api.route('/tg/account/status/<int:account_id>', methods=['GET'])
def tg_account_status(account_id):
    """获取账户状态"""
    obj = TgAccount.query.filter_by(id=account_id).first()
    if not obj:
        raise APIException('账户不存在')
    
    status_map = {
        TgAccount.StatusType.JOIN_SUCCESS: '登录成功',
        TgAccount.StatusType.JOIN_FAIL: '登录失败',
        TgAccount.StatusType.JOIN_ONGOING: '登录中', 
        TgAccount.StatusType.NOT_JOIN: '未登录'
    }
    
    return success({
        'id': obj.id,
        'phone': obj.phone,
        'status': obj.status,
        'status_text': status_map.get(obj.status),
        'two_step': obj.two_step,
        'user_id': obj.user_id,
        'username': obj.username,
        'nickname': obj.nickname
    })


@api.route('/tg/account/check_status/<phone>', methods=['GET'])
def tg_account_check_status(phone):
    """通过手机号检查账户状态 - 用于轮询"""
    obj = TgAccount.query.filter_by(phone=phone).first()
    if not obj:
        raise APIException('账户不存在')
    
    status_map = {
        TgAccount.StatusType.JOIN_SUCCESS: '登录成功',
        TgAccount.StatusType.JOIN_FAIL: '登录失败',
        TgAccount.StatusType.JOIN_ONGOING: '登录中', 
        TgAccount.StatusType.NOT_JOIN: '未登录'
    }
    
    return success({
        'id': obj.id,
        'phone': obj.phone,
        'status': obj.status,
        'status_text': status_map.get(obj.status),
        'two_step': obj.two_step,
        'user_id': obj.user_id,
        'username': obj.username,
        'nickname': obj.nickname,
        'is_processing': obj.status == TgAccount.StatusType.JOIN_ONGOING
    })


@api.route('/tg/account/fetch_group_info', methods=['POST'])
def tg_account_fetch_group_info():
    """获取账户群组信息并建立会话关系"""
    account_id = get_or_exception('account_id', request.json, 'int')
    
    # 检查账户是否存在
    account = TgAccount.query.filter_by(id=account_id).first()
    if not account:
        raise APIException('账户不存在')
    
    if account.status != TgAccount.StatusType.JOIN_SUCCESS:
        raise APIException('账户未成功登录，无法获取群组信息')
    
    try:
        # 异步调用群组信息获取任务
        task = fetch_account_group_info.delay(account_id)
        
        return success({
            'message': f'已开始获取账户 {account.name} 的群组信息',
            'account_id': account_id,
            'account_name': account.name,
            'task_id': task.id
        })
        
    except Exception as e:
        raise APIException(f'启动群组信息获取任务失败: {str(e)}')


@api.route('/tg/account/fetch_group_info_batch', methods=['POST'])
def tg_account_fetch_group_info_batch():
    """批量获取多个账户的群组信息"""
    account_ids = get_or_exception('account_ids', request.json, 'str')
    account_id_list = [int(i) for i in account_ids.split(',') if i.strip()]
    
    if not account_id_list:
        raise APIException('请选择要获取群组信息的账户')
    
    # 检查所有账户状态
    accounts = TgAccount.query.filter(
        TgAccount.id.in_(account_id_list),
        TgAccount.status == TgAccount.StatusType.JOIN_SUCCESS
    ).all()
    
    if not accounts:
        raise APIException('没有找到可用的已登录账户')
    
    try:
        task_results = []
        for account in accounts:
            # 异步调用每个账户的群组信息获取任务
            task = fetch_account_group_info.delay(account.id)
            task_results.append({
                'account_id': account.id,
                'account_name': account.name,
                'task_id': task.id
            })
        
        return success({
            'message': f'已开始获取 {len(accounts)} 个账户的群组信息',
            'total_accounts': len(accounts),
            'tasks': task_results
        })
        
    except Exception as e:
        raise APIException(f'启动批量群组信息获取任务失败: {str(e)}')


@api.route('/tg/account/<int:account_id>/groups', methods=['GET'])
def tg_account_groups(account_id):
    """获取账户关联的群组列表"""
    # 检查账户是否存在
    account = TgAccount.query.filter_by(id=account_id).first()
    if not account:
        raise APIException('账户不存在')
    
    try:
        from jd.models.tg_group import TgGroup
        from jd.models.tg_group_session import TgGroupSession

        # 仅通过tg_group_session表进行关联查询，这是正确的多对多关系
        groups_query = db.session.query(TgGroup, TgGroupSession).join(
            TgGroupSession,
            TgGroup.chat_id == TgGroupSession.chat_id
        ).filter(
            TgGroupSession.user_id == account.user_id
        ).order_by(TgGroup.updated_at.desc())

        groups_data = []
        for group, session in groups_query.all():
            groups_data.append({
                'id': group.id,
                'name': group.name,
                'title': group.title,
                'chat_id': group.chat_id,
                'status': group.status,
                'status_text': get_group_status_text(group.status),
                'desc': group.desc,
                'group_type': group.group_type,
                'group_type_text': '频道' if group.group_type == TgGroup.GroupType.CHANNEL else '群组',
                'session_name': session.session_name,
                'created_at': group.created_at.strftime('%Y-%m-%d %H:%M:%S') if group.created_at else '',
                'updated_at': group.updated_at.strftime('%Y-%m-%d %H:%M:%S') if group.updated_at else ''
            })
        
        return success({
            'groups': groups_data,
            'total_count': len(groups_data),
            'account_info': {
                'id': account.id,
                'name': account.name,
                'user_id': account.user_id,
                'nickname': account.nickname
            }
        })
        
    except Exception as e:
        raise APIException(f'获取群组列表失败: {str(e)}')


def get_group_status_text(status):
    """获取群组状态文本"""
    status_map = {
        0: '未加入',
        1: '已加入', 
        2: '加入失败',
        3: '加入中'
    }
    return status_map.get(status, '未知')