import os
import re
import logging
from flask import request, jsonify

from jd.views.api import api
from jd.views import APIException
from jd.services.role_service.role import ROLE_SUPER_ADMIN

logger = logging.getLogger(__name__)


@api.route('/system/telegram-settings', methods=['GET'], roles=[ROLE_SUPER_ADMIN])
def get_telegram_settings():
    """获取Telegram配置"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), '../../../../config.py')
        
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析TG_CONFIG
        tg_config_match = re.search(r'TG_CONFIG\s*=\s*{([^}]+)}', content, re.MULTILINE | re.DOTALL)
        tg_history_match = re.search(r'TG_HISTORY_DAYS\s*=\s*(\d+)', content)
        # 解析TELEGRAM_DOWNLOAD_SETTINGS
        download_settings_match = re.search(r'TELEGRAM_DOWNLOAD_SETTINGS\s*=\s*\{(.*?)\}', content, re.MULTILINE | re.DOTALL)
        
        if not tg_config_match:
            raise APIException('无法读取Telegram配置', 50001, 500)
        
        # 解析配置内容
        config_content = tg_config_match.group(1)
        
        # 提取各个配置项
        api_id = re.search(r'"api_id":\s*"([^"]+)"', config_content)
        api_hash = re.search(r'"api_hash":\s*"([^"]+)"', config_content)
        sqlite_db_name = re.search(r'"sqlite_db_name":\s*"([^"]+)"', config_content)
        
        # 解析代理配置
        proxy_match = re.search(r'"proxy":\s*(None|\{.*?\})', config_content, re.MULTILINE | re.DOTALL)
        proxy_config = {}
        if proxy_match:
            proxy_value = proxy_match.group(1)
            if proxy_value == 'None':
                proxy_config = {
                    'enabled': False,
                    'protocal': 'socks5',
                    'ip': '127.0.0.1',
                    'port': 7890
                }
            else:
                proxy_content = proxy_value[1:-1]  # Remove braces
                protocal = re.search(r'"protocal":\s*"([^"]+)"', proxy_content)
                ip = re.search(r'"ip":\s*"([^"]+)"', proxy_content)
                port = re.search(r'"port":\s*(\d+)', proxy_content)
                
                proxy_config = {
                    'enabled': True,
                    'protocal': protocal.group(1) if protocal else 'socks5',
                    'ip': ip.group(1) if ip else '127.0.0.1',
                    'port': int(port.group(1)) if port else 7890
                }
        
        # 解析下载设置 - 从config.py读取实际配置
        from jd import app
        config_download_settings = app.config.get('TELEGRAM_DOWNLOAD_SETTINGS', {})
        download_settings = {
            'download_all': config_download_settings.get('download_all', False),
            'download_images': config_download_settings.get('download_images', False),
            'download_audio': config_download_settings.get('download_audio', False),
            'download_videos': config_download_settings.get('download_videos', False),
            'download_archives': config_download_settings.get('download_archives', False),
            'download_documents': config_download_settings.get('download_documents', False),
            'download_programs': config_download_settings.get('download_programs', False)
        }
        
        logger.info(f"下载设置匹配结果: {download_settings_match is not None}")
        
        if download_settings_match:
            download_content = download_settings_match.group(1)
            logger.info(f"匹配到的下载设置内容: {download_content[:100]}...")
            
            # 提取各个下载设置项，覆盖从config读取的值
            download_all = re.search(r'"download_all":\s*(True|False)', download_content)
            download_images = re.search(r'"download_images":\s*(True|False)', download_content)
            download_audio = re.search(r'"download_audio":\s*(True|False)', download_content)
            download_videos = re.search(r'"download_videos":\s*(True|False)', download_content)
            download_archives = re.search(r'"download_archives":\s*(True|False)', download_content)
            download_documents = re.search(r'"download_documents":\s*(True|False)', download_content)
            download_programs = re.search(r'"download_programs":\s*(True|False)', download_content)
            
            # 只有匹配到的项才覆盖默认值
            if download_all:
                download_settings['download_all'] = download_all.group(1) == 'True'
            if download_images:
                download_settings['download_images'] = download_images.group(1) == 'True'
            if download_audio:
                download_settings['download_audio'] = download_audio.group(1) == 'True'
            if download_videos:
                download_settings['download_videos'] = download_videos.group(1) == 'True'
            if download_archives:
                download_settings['download_archives'] = download_archives.group(1) == 'True'
            if download_documents:
                download_settings['download_documents'] = download_documents.group(1) == 'True'
            if download_programs:
                download_settings['download_programs'] = download_programs.group(1) == 'True'
        
        result = {
            'api_id': api_id.group(1) if api_id else '',
            'api_hash': api_hash.group(1) if api_hash else '',
            'sqlite_db_name': sqlite_db_name.group(1) if sqlite_db_name else '',
            'proxy': proxy_config,
            'history_days': int(tg_history_match.group(1)) if tg_history_match else 60,
            'download_settings': download_settings
        }
        
        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': result
        })
        
    except Exception as e:
        logger.error(f"获取Telegram配置失败: {e}")
        raise APIException('获取配置失败', 50001, 500)


@api.route('/system/telegram-settings', methods=['POST'], roles=[ROLE_SUPER_ADMIN])
def update_telegram_settings():
    """更新Telegram配置"""
    try:
        data = request.get_json()
        
        if not data:
            raise APIException('请求数据不能为空', 40001, 400)
        
        config_path = os.path.join(os.path.dirname(__file__), '../../../../config.py')
        logger.info(f"尝试更新配置文件: {config_path}")
        logger.info(f"接收到的数据: {data}")
        
        # 检查文件是否存在和权限
        if not os.path.exists(config_path):
            logger.error(f"配置文件不存在: {config_path}")
            raise APIException('配置文件不存在', 50001, 500)
        
        if not os.access(config_path, os.R_OK | os.W_OK):
            logger.error(f"配置文件权限不足: {config_path}")
            raise APIException('配置文件权限不足', 50001, 500)
        
        # 备份原文件
        backup_path = config_path + '.backup'
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 构建新的TG_CONFIG
        proxy_data = data.get('proxy', {})
        proxy_enabled = proxy_data.get('enabled', True)
        
        if not proxy_enabled:
            proxy_str = 'None'
        else:
            proxy_str = f'''{{
        "protocal": "{proxy_data.get('protocal', 'socks5')}",
        "ip": "{proxy_data.get('ip', '127.0.0.1')}",
        "port": {proxy_data.get('port', 7890)}
    }}'''
        
        new_tg_config = f'''TG_CONFIG = {{
    "api_id": "{data.get('api_id', '')}",
    "api_hash": "{data.get('api_hash', '')}",
    "sqlite_db_name": "{data.get('sqlite_db_name', 'jd_tg.db')}",
    "proxy": {proxy_str}
}}'''
        
        # 替换TG_CONFIG - 使用更准确的模式匹配整个TG_CONFIG块
        content = re.sub(r'TG_CONFIG\s*=\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', new_tg_config, content, flags=re.MULTILINE | re.DOTALL)
        
        # 替换TG_HISTORY_DAYS
        history_days = data.get('history_days', 60)
        content = re.sub(r'TG_HISTORY_DAYS\s*=\s*\d+', f'TG_HISTORY_DAYS = {history_days}', content)
        
        # 替换TELEGRAM_DOWNLOAD_SETTINGS
        download_settings = data.get('download_settings', {})
        new_download_settings = f'''TELEGRAM_DOWNLOAD_SETTINGS = {{
    "download_all": {str(download_settings.get('download_all', False))},        # 下载所有文件
    "download_images": {str(download_settings.get('download_images', True))},      # 图片（jpg, bmp, png, webp, tiff, gif）
    "download_audio": {str(download_settings.get('download_audio', False))},      # 音频（mp3, flac, wav, ogg）
    "download_videos": {str(download_settings.get('download_videos', False))},     # 视频（mp4, mkv, webm, mov）
    "download_archives": {str(download_settings.get('download_archives', False))},   # 压缩包（zip, rar, 7z, gz, bz2）
    "download_documents": {str(download_settings.get('download_documents', False))},  # 文档（pdf, doc(x), xls(x), ppt(x), txt）
    "download_programs": {str(download_settings.get('download_programs', False))}    # 程序（apk, exe, elf）
}}'''
        
        # 检查配置文件中是否已存在 TELEGRAM_DOWNLOAD_SETTINGS
        if re.search(r'TELEGRAM_DOWNLOAD_SETTINGS\s*=', content):
            # 替换现有配置
            content = re.sub(r'TELEGRAM_DOWNLOAD_SETTINGS\s*=\s*\{.*?\}', new_download_settings, content, flags=re.MULTILINE | re.DOTALL)
            logger.info("替换现有的 TELEGRAM_DOWNLOAD_SETTINGS 配置")
        else:
            # 在 TG_HISTORY_DAYS 后添加新配置
            tg_history_pattern = r'(TG_HISTORY_DAYS\s*=\s*\d+)'
            replacement = f'\\1\n\n# Telegram文档下载设置\n{new_download_settings}'
            content = re.sub(tg_history_pattern, replacement, content)
            logger.info("添加新的 TELEGRAM_DOWNLOAD_SETTINGS 配置")
        
        logger.info(f"准备写入的内容长度: {len(content)}")
        logger.info(f"新的下载设置: {new_download_settings}")
        
        # 写入文件
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"配置文件已写入: {config_path}")
        
        # 验证写入结果
        with open(config_path, 'r', encoding='utf-8') as f:
            verify_content = f.read()
            if 'TELEGRAM_DOWNLOAD_SETTINGS' in verify_content:
                logger.info("配置文件写入验证成功")
            else:
                logger.error("配置文件写入验证失败")
        
        logger.info("Telegram配置更新成功")
        
        return jsonify({
            'err_code': 0,
            'err_msg': '配置更新成功',
            'payload': None
        })
        
    except Exception as e:
        logger.error(f"更新Telegram配置失败: {e}")
        # 如果出错，尝试恢复备份
        try:
            if os.path.exists(backup_path):
                with open(backup_path, 'r', encoding='utf-8') as f:
                    backup_content = f.read()
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(backup_content)
        except:
            pass
        raise APIException('配置更新失败', 50001, 500)