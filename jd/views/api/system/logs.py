import os
from flask import request
from jd.views.api import api
from jd.services.role_service.role import ROLE_SUPER_ADMIN


@api.route('/system/logs/<log_filename>', methods=['GET'], need_login=False)
def get_log_content(log_filename):
    """
    获取指定日志文件的内容（最新50行）
    """
    try:
        # 安全检查：只允许读取特定的日志文件
        allowed_logs = {
            'celery_out.txt',
            'celery_telegram_out.txt', 
            'celery_beat.txt',
            'flask_out.txt',
            'frontend_out.txt'
        }
        
        if log_filename not in allowed_logs:
            return {
                'err_code': 1,
                'err_msg': f'不允许访问的日志文件: {log_filename}',
                'payload': {}
            }
        
        # 构建日志文件路径 - 从项目根目录找log目录
        current_dir = os.path.dirname(__file__)  # /path/to/jd/views/api/system
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))  # 项目根目录
        log_dir = os.path.join(project_root, 'log')
        log_path = os.path.join(log_dir, log_filename)
        
        # 检查文件是否存在
        if not os.path.exists(log_path):
            return {
                'err_code': 0,
                'err_msg': '',
                'payload': {
                    'content': f'日志文件不存在: {log_filename}',
                    'lines': 0
                }
            }
        
        # 读取文件最后50行
        lines = []
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 读取所有行
                all_lines = f.readlines()
                # 取最后50行
                lines = all_lines[-50:] if len(all_lines) > 50 else all_lines
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            try:
                with open(log_path, 'r', encoding='gbk', errors='ignore') as f:
                    all_lines = f.readlines()
                    lines = all_lines[-50:] if len(all_lines) > 50 else all_lines
            except:
                with open(log_path, 'r', encoding='latin1', errors='ignore') as f:
                    all_lines = f.readlines()
                    lines = all_lines[-50:] if len(all_lines) > 50 else all_lines
        
        # 组合内容
        content = ''.join(lines) if lines else '日志文件为空'
        
        return {
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'content': content,
                'lines': len(lines)
            }
        }
        
    except Exception as e:
        return {
            'err_code': 1,
            'err_msg': f'读取日志文件失败: {str(e)}',
            'payload': {}
        }


@api.route('/system/logs/list', methods=['GET'], need_login=False)
def get_log_list():
    """
    获取可用的日志文件列表
    """
    try:
        # 构建日志文件路径 - 从项目根目录找log目录
        current_dir = os.path.dirname(__file__)  # /path/to/jd/views/api/system
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))  # 项目根目录
        log_dir = os.path.join(project_root, 'log')
        
        # 定义日志文件映射
        log_files = [
            {
                'filename': 'celery_out.txt',
                'label': 'Celery Worker 日志',
                'exists': os.path.exists(os.path.join(log_dir, 'celery_out.txt'))
            },
            {
                'filename': 'celery_telegram_out.txt',
                'label': 'Celery Telegram 日志', 
                'exists': os.path.exists(os.path.join(log_dir, 'celery_telegram_out.txt'))
            },
            {
                'filename': 'celery_beat.txt',
                'label': 'Celery Beat 日志',
                'exists': os.path.exists(os.path.join(log_dir, 'celery_beat.txt'))
            },
            {
                'filename': 'flask_out.txt',
                'label': 'Flask 后端日志',
                'exists': os.path.exists(os.path.join(log_dir, 'flask_out.txt'))
            },
            {
                'filename': 'frontend_out.txt',
                'label': '前端开发日志',
                'exists': os.path.exists(os.path.join(log_dir, 'frontend_out.txt'))
            }
        ]
        
        return {
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'log_files': log_files
            }
        }
        
    except Exception as e:
        return {
            'err_code': 1,
            'err_msg': f'获取日志文件列表失败: {str(e)}',
            'payload': {}
        }