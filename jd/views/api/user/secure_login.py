"""
新的安全登录接口 - 使用哈希密码验证
"""
from flask import request, session
from datetime import datetime

from jd import db
from jd.models.secure_user import SecureUser
from jd.views import APIException, success
from jd.views.api import api


@api.route("/user/secure_login", need_login=False, methods=["POST"])
def secure_user_login():
    """安全用户登录接口（使用哈希密码验证）"""
    args = request.get_json() or request.form
    username = args.get("username")
    password = args.get("password")

    if not username or not password:
        raise APIException("用户名和密码不能为空")

    # 查找用户
    user = db.session.query(SecureUser).filter_by(username=username).first()
    
    if not user:
        raise APIException("账号或密码错误！")
    
    # 检查账户状态
    if not user.is_enabled():
        raise APIException("账户已被禁用，请联系管理员")
    
    # 验证密码
    if not user.check_password(password):
        raise APIException("账号或密码错误！")
    
    # 登录成功 - 更新最后登录时间
    user.update_last_login()
    db.session.commit()
    
    # 设置session
    session['current_user_id'] = user.id
    session['user_type'] = 'secure'  # 标记使用新用户系统
    
    # 返回用户信息
    user_info = {
        "id": user.id,
        "username": user.username,
        "permission_level": user.permission_level,
        "permission_name": user.get_permission_name(),
        "role_ids": [user.permission_level],  # 兼容旧系统的role_ids
        "last_login": user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None
    }
    
    return success(payload={"user": user_info})


@api.route("/user/secure_logout", methods=["POST"])
def secure_user_logout():
    """安全用户登出接口"""
    session.pop('current_user_id', None)
    session.pop('user_type', None)
    return success(payload={"message": "登出成功"})


@api.route("/user/secure_info", methods=["GET"])
def get_secure_user_info():
    """获取当前安全用户信息"""
    current_user_id = session.get('current_user_id')
    user_type = session.get('user_type')
    
    if not current_user_id:
        raise APIException("未登录", err_code=401, status_code=401)
    
    # 查询secure_user表
    user = db.session.query(SecureUser).filter_by(id=current_user_id).first()
    if not user:
        raise APIException("用户不存在", err_code=401, status_code=401)
    
    user_info = {
        "id": user.id,
        "username": user.username,
        "permission_level": user.permission_level,
        "permission_name": user.get_permission_name(),
        "role_ids": [user.permission_level],  # 兼容旧系统
        "last_login": user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
        "user_type": "secure"
    }
    
    return success(payload=user_info)


@api.route("/user/change_password", methods=["POST"])
def change_password():
    """修改密码接口"""
    current_user_id = session.get('current_user_id')
    user_type = session.get('user_type')
    
    if not current_user_id:
        raise APIException("未登录", err_code=401, status_code=401)
    
    if user_type != 'secure':
        raise APIException("仅安全用户支持密码修改功能")
    
    args = request.get_json() or request.form
    old_password = args.get("old_password")
    new_password = args.get("new_password")
    confirm_password = args.get("confirm_password")
    
    if not all([old_password, new_password, confirm_password]):
        raise APIException("所有密码字段都不能为空")
    
    if new_password != confirm_password:
        raise APIException("新密码和确认密码不一致")
    
    if len(new_password) < 6:
        raise APIException("新密码长度不能少于6位")
    
    # 获取用户
    user = db.session.query(SecureUser).filter_by(id=current_user_id).first()
    if not user:
        raise APIException("用户不存在")
    
    # 验证旧密码
    if not user.check_password(old_password):
        raise APIException("旧密码错误")
    
    # 设置新密码
    user.set_password(new_password)
    user.updated_at = datetime.now()
    db.session.commit()
    
    return success(payload={"message": "密码修改成功"})


