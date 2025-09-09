from flask import request, jsonify, session
from flask_jwt_extended import create_access_token

from jd import db
from jd.models.secure_user import SecureUser
from jd.views import APIException, success
from jd.views.api import api



@api.route("user/login", need_login=False, methods=["POST"])
def user_login():
    """Vue前端登录接口"""
    args = request.get_json() or request.form
    username = args.get("username")
    password = args.get("password")

    if not username or not password:
        raise APIException("用户名和密码不能为空")

    user = db.session.query(SecureUser).filter_by(username=username).one_or_none()

    if not user:
        raise APIException("账号或密码错误！")
    if not user.check_password(password):
        raise APIException("账号或密码错误！")
    
    if not user.can_login():
        raise APIException("账户已被禁用！")
    
    # 更新最后登录时间
    user.update_last_login()
    db.session.commit()
    
    # 设置session
    session['current_user_id'] = user.id
    
    # 返回用户信息 (兼容旧的角色系统格式)
    user_info = {
        "id": user.id,
        "username": user.username,
        "role_ids": [user.permission_level]  # 将权限等级映射为角色ID
    }
    
    return success(payload={"user": user_info})


@api.route("user/logout", methods=["POST"])
def user_logout():
    """Vue前端登出接口"""
    session.pop('current_user_id', None)
    return success(payload={"message": "登出成功"})


@api.route("user/info", methods=["GET"])
def get_user_info():
    """获取当前用户信息"""
    current_user_id = session.get('current_user_id')
    if not current_user_id:
        raise APIException("未登录", err_code=401, status_code=401)
    
    user = db.session.query(SecureUser).filter_by(id=current_user_id).one_or_none()
    if not user:
        raise APIException("用户不存在", err_code=401, status_code=401)
    
    user_info = {
        "id": user.id,
        "username": user.username,
        "role_ids": [user.permission_level]  # 将权限等级映射为角色ID
    }
    
    return success(payload=user_info)


@api.route("user/check-username", methods=["GET"])
def check_username():
    """检查用户名是否已被占用"""
    current_user_id = session.get('current_user_id')
    username = request.args.get('username')
    
    if not username:
        raise APIException("用户名不能为空")
    
    # 查找是否有其他用户使用此用户名
    existing_user = db.session.query(SecureUser).filter_by(username=username).first()
    
    exists = existing_user is not None
    is_different_user = existing_user and existing_user.id != current_user_id
    
    return success(payload={
        "exists": exists,
        "is_different_user": is_different_user
    })


@api.route("user/update-profile", methods=["POST"])
def update_profile():
    """更新用户资料（用户名和密码）"""
    current_user_id = session.get('current_user_id')
    
    if not current_user_id:
        raise APIException("未登录", err_code=401, status_code=401)
    
    args = request.get_json() or request.form
    new_username = args.get("username")
    new_password = args.get("password")
    
    if not new_username:
        raise APIException("用户名不能为空")
        
    if not new_password:
        raise APIException("密码不能为空")
    
    if len(new_username) < 3:
        raise APIException("用户名不能少于3位")
        
    if len(new_password) < 6:
        raise APIException("密码不能少于6位")
    
    # 获取当前用户
    user = db.session.query(SecureUser).filter_by(id=current_user_id).first()
    if not user:
        raise APIException("用户不存在")
    
    # 检查用户名是否被其他用户占用
    if new_username != user.username:
        existing_user = db.session.query(SecureUser).filter_by(username=new_username).first()
        if existing_user:
            raise APIException("用户名已被占用")
    
    # 更新用户信息
    user.username = new_username
    user.set_password(new_password)
    from datetime import datetime
    user.updated_at = datetime.now()
    
    try:
        db.session.commit()
        return success(payload={"message": "用户信息更新成功"})
    except Exception as e:
        db.session.rollback()
        raise APIException(f"更新失败：{str(e)}")
