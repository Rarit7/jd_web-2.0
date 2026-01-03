from flask import request, session, jsonify
import logging

from jd import db
from jd.helpers.user import current_user_id
from jd.models.result_tag import ResultTag
from jd.services.role_service.role import RoleService
from jd.services.tag import TagService
from jd.views import get_or_exception
from jd.views.api import api

logger = logging.getLogger(__name__)


@api.route('/tag/list', methods=['GET'])
def tag_list():
    try:
        tags = ResultTag.query.filter(ResultTag.status == ResultTag.StatusType.VALID).order_by(ResultTag.updated_at.desc()).all()
        data = [{
            'id': row.id,
            'name': row.title,
            'color': row.color if hasattr(row, 'color') and row.color else '#409EFF',
            'is_nsfw': row.is_nsfw if hasattr(row, 'is_nsfw') else False,
            'status': TagService.StatusMap[row.status],
            'created_at': row.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': row.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        } for row in tags]
        
        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {'data': data}
        })
    except Exception as e:
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500


@api.route('/tag/delete', methods=['DELETE', 'GET'])
def tag_delete():
    try:
        # 支持JSON请求和传统请求
        if request.method == 'DELETE' or request.headers.get('Content-Type') == 'application/json':
            data = request.get_json()
            tag_id = data.get('id') if data else request.args.get('tag_id')
        else:
            tag_id = request.args.get('tag_id')
            
        if not tag_id:
            return jsonify({
                'err_code': 1,
                'err_msg': '缺少标签ID参数',
                'payload': {}
            }), 400
            
        tag_id = int(tag_id)
        tag = ResultTag.query.filter_by(id=tag_id).first()
        if tag:
            ResultTag.query.filter_by(id=tag_id, status=ResultTag.StatusType.VALID).update(
                {'status': ResultTag.StatusType.INVALID})
            db.session.commit()
            
        return jsonify({
            'err_code': 0,
            'err_msg': '删除成功',
            'payload': {}
        })
            
    except Exception as e:
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500


@api.route('/tag/add', methods=['POST'])
def tag_add():
    try:
        # 支持JSON请求和表单请求
        if request.headers.get('Content-Type') == 'application/json':
            data = request.get_json()
            name = data.get('name')
            color = data.get('color', '#409EFF')
            is_nsfw = data.get('is_nsfw', False)
        else:
            name = request.form.get('name')
            color = request.form.get('color', '#409EFF')
            is_nsfw = request.form.get('is_nsfw', 'false').lower() == 'true'
            
        if not name or not name.strip():
            return jsonify({
                'err_code': 1,
                'err_msg': '标签名称不能为空',
                'payload': {}
            }), 400
            
        name = name.strip()
        
        # 检查是否已存在
        existing_tag = ResultTag.query.filter_by(title=name).first()
        if existing_tag:
            if existing_tag.status == ResultTag.StatusType.INVALID:
                # 重新激活已删除的标签
                existing_tag.status = ResultTag.StatusType.VALID
                existing_tag.color = color
                existing_tag.is_nsfw = is_nsfw
            else:
                return jsonify({
                    'err_code': 1,
                    'err_msg': '标签名称已存在',
                    'payload': {}
                }), 400
        else:
            # 创建新标签
            tag = ResultTag(title=name, color=color, is_nsfw=is_nsfw)
            db.session.add(tag)
        
        db.session.commit()
        
        return jsonify({
            'err_code': 0,
            'err_msg': '添加成功',
            'payload': {}
        })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500


@api.route('/tag/edit', methods=['PUT', 'POST'])
def tag_edit():
    try:
        # 支持JSON请求和表单请求
        if request.method == 'PUT' or request.headers.get('Content-Type') == 'application/json':
            data = request.get_json()
            logger.info(f"tag_edit - Received JSON data: {data}")
            if not data:
                return jsonify({
                    'err_code': 1,
                    'err_msg': '请求数据为空',
                    'payload': {}
                }), 400
            tag_id = data.get('id')
            name = data.get('name')
            color = data.get('color')
            is_nsfw = data.get('is_nsfw')
        else:
            tag_id = request.form.get('id')
            name = request.form.get('name')
            color = request.form.get('color')
            is_nsfw_str = request.form.get('is_nsfw')
            is_nsfw = is_nsfw_str.lower() == 'true' if is_nsfw_str else None

        logger.info(f"tag_edit - Parsed params: id={tag_id}, name={name}, color={color}")

        if not tag_id or not name or not name.strip():
            return jsonify({
                'err_code': 1,
                'err_msg': f'参数不完整: id={tag_id}, name={name}, color={color}',
                'payload': {}
            }), 400
            
        try:
            tag_id = int(tag_id)
        except (ValueError, TypeError):
            return jsonify({
                'err_code': 1,
                'err_msg': f'无效的标签ID: {tag_id}',
                'payload': {}
            }), 400
            
        name = name.strip()
        
        # 检查标签是否存在
        tag = ResultTag.query.filter_by(id=tag_id, status=ResultTag.StatusType.VALID).first()
        if not tag:
            return jsonify({
                'err_code': 1,
                'err_msg': '标签不存在',
                'payload': {}
            }), 404
            
        # 检查新名称是否已被其他标签使用
        existing_tag = ResultTag.query.filter(
            ResultTag.title == name,
            ResultTag.id != tag_id,
            ResultTag.status == ResultTag.StatusType.VALID
        ).first()
        
        if existing_tag:
            return jsonify({
                'err_code': 1,
                'err_msg': '标签名称已存在',
                'payload': {}
            }), 400
            
        tag.title = name
        if color is not None:
            tag.color = color
        if is_nsfw is not None:
            tag.is_nsfw = is_nsfw
        db.session.commit()
        
        return jsonify({
            'err_code': 0,
            'err_msg': '修改成功',
            'payload': {}
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500
