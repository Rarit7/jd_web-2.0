import os

# 路由前缀
API_PREFIX = '/api'

# mysql相关配置
SQLALCHEMY_ECHO = False
SQLALCHEMY_ENABLE_POOL = False
SQLALCHEMY_DATABASE_URI = 'mysql+mysqldb://jd_user:YOUR_MYSQL_PASSWORD@127.0.0.1:3306/jd?charset=utf8mb4'
SQLALCHEMY_BINDS = {}

# JWT配置
JWT_SECRET_KEY = "your-jwt-secret-key-change-this"
JWT_ACCESS_TOKEN_EXPIRES = 7 * 24 * 60 * 60

# Session密钥
SESSION_SECRET_KEY = "your-session-secret-key-change-this"

# 爬虫配置
# 注意更换cookie及代理
BAIDU_COOKIE = 'YOUR_BAIDU_COOKIE'
GOOGLE_COOKIE = 'YOUR_GOOGLE_COOKIE'
BAIDU_SPIDER_PROXIES = {}
GOOGLE_SPIDER_PROXIES = {}

# 默认爬取的页数
SPIDER_DEFAULT_PAGE = 10

# Telegram API配置
TG_CONFIG = {
    "api_id": "YOUR_TELEGRAM_API_ID",
    "api_hash": "YOUR_TELEGRAM_API_HASH",
    "sqlite_db_name": "jd_tg.db",
    "proxy": None  # {"proxy_type": "socks5", "addr": "127.0.0.1", "port": 1080}
}

# Telegram群组历史回溯功能回溯历史消息的天数
TG_HISTORY_DAYS = 30

# Telegram文档下载设置
TELEGRAM_DOWNLOAD_SETTINGS = {
    "download_all": False,        # 下载所有文件
    "download_images": True,      # 图片（jpg, bmp, png, webp, tiff, gif）
    "download_audio": True,       # 音频（mp3, flac, wav, ogg）
    "download_videos": False,     # 视频（mp4, mkv, webm, mov）
    "download_archives": True,    # 压缩包（zip, rar, 7z, gz, bz2）
    "download_documents": True,   # 文档（pdf, doc(x), xls(x), ppt(x), txt）
    "download_programs": False    # 程序（apk, exe, elf）
}

# OXYLABS代理配置（可选）
OXYLABS_USERNAME = 'YOUR_OXYLABS_USERNAME'
OXYLABS_PASSWORD = 'YOUR_OXYLABS_PASSWORD'
OXYLABS_HOST = 'pr.oxylabs.io'
OXYLABS_PORT = '7777'

# 任务队列超时时间配置（秒）
TASK_DEFAULT_TIMEOUTS = {
    'update_group_history': 3600,      # 实时增量获取
    'fetch_account_group_info': 1800,  # 账户群组信息同步
    'fetch_new_group_history': 7200,   # 历史回溯
    'manual_download_file': 3600,      # 手动下载文件
    'default': 1800                    # 默认
}

# 最大排队等待时间（秒）
TASK_MAX_WAIT_TIME = 7200  # 2小时

# Redis配置
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None  # 如果Redis设置了密码

# Celery配置
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

# 日志配置
LOG_LEVEL = 'INFO'
LOG_FILE = 'log/app.log'

# 文件上传配置
UPLOAD_FOLDER = 'static/uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# 安全配置
SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-app-secret-key-change-this-in-production'
WTF_CSRF_ENABLED = True
WTF_CSRF_SECRET_KEY = 'your-csrf-secret-key'

# 开发模式配置
DEBUG = False
TESTING = False

# 配置说明：
# 1. 请将所有 YOUR_* 占位符替换为实际值
# 2. 数据库密码需要与MariaDB安装时设置的密码一致
# 3. Telegram API需要从 https://my.telegram.org 获取
# 4. 生产环境请确保所有密钥都使用强随机值
# 5. Redis如果设置了密码，请更新REDIS_PASSWORD
