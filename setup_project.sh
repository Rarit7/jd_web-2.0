#!/bin/bash

# SDJD_TG管理系统 - 项目一键启动脚本
# 包括环境配置、依赖安装、数据库初始化和服务启动

set -e  # 遇到错误立即退出

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="SDJD_TG管理系统"
CONDA_ENV_NAME="sdweb2"

# 默认数据库配置
DEFAULT_MYSQL_PORT="3306"
DEFAULT_MYSQL_DB_NAME="jd2"
DEFAULT_MYSQL_ROOT_PASSWORD="MySecurePassword123!"
DEFAULT_REDIS_PORT="6379"
DEFAULT_BACKEND_PORT="8931"
DEFAULT_FRONTEND_PORT="8930"

# 运行时配置变量（将通过命令行参数设置）
MYSQL_PORT="$DEFAULT_MYSQL_PORT"
MYSQL_DB_NAME="$DEFAULT_MYSQL_DB_NAME"
MYSQL_ROOT_PASSWORD="$DEFAULT_MYSQL_ROOT_PASSWORD"
REDIS_PORT="$DEFAULT_REDIS_PORT"
BACKEND_PORT="$DEFAULT_BACKEND_PORT"
FRONTEND_PORT="$DEFAULT_FRONTEND_PORT"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}${BOLD}========================================"
    echo -e "  $1"
    echo -e "========================================${NC}"
}

print_step() {
    echo -e "${BLUE}${BOLD}>>> $1${NC}"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    print_header "项目一键启动脚本 - 帮助信息"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help              显示此帮助信息"
    echo "  -e, --setup-env         仅设置conda环境"
    echo "  -m, --setup-mariadb     仅安装配置MariaDB"
    echo "  -r, --setup-redis       仅安装配置Redis"
    echo "  -d, --init-db           仅初始化数据库"
    echo "  -f, --setup-frontend    仅配置前端环境"
    echo "  -s, --start-services    仅启动服务"
    echo "  -a, --all               执行完整安装（默认）"
    echo "  --skip-confirm          跳过确认提示"
    echo "  --force                 强制执行"
    echo ""
    echo "端口和数据库配置选项:"
    echo "  --mysql-port PORT       MySQL端口 (默认: $DEFAULT_MYSQL_PORT)"
    echo "  --mysql-db NAME         MySQL数据库名称 (默认: $DEFAULT_MYSQL_DB_NAME)"
    echo "  --redis-port PORT       Redis端口 (默认: $DEFAULT_REDIS_PORT)"
    echo "  --backend-port PORT     后端服务端口 (默认: $DEFAULT_BACKEND_PORT)"
    echo "  --frontend-port PORT    前端服务端口 (默认: $DEFAULT_FRONTEND_PORT)"
    echo ""
    echo "完整流程包括:"
    echo "  1. 环境检查"
    echo "  2. Conda环境配置"
    echo "  3. Python依赖安装"
    echo "  4. MariaDB安装与配置"
    echo "  5. Redis安装与配置"
    echo "  6. 数据库初始化"
    echo "  7. 前端环境配置"
    echo "  8. 服务启动"
    echo ""
    echo "示例:"
    echo "  $0                                    # 完整安装（使用默认配置）"
    echo "  $0 -e                                 # 仅配置环境"
    echo "  $0 -m                                 # 仅安装MariaDB"
    echo "  $0 -r                                 # 仅安装Redis"
    echo "  $0 -d                                 # 仅初始化数据库"
    echo "  $0 -f                                 # 仅配置前端"
    echo "  $0 -s                                 # 仅启动服务"
    echo "  $0 -m -r -d                           # 安装数据库组件并初始化"
    echo "  $0 -a --skip-confirm                  # 完整安装且跳过确认"
    echo ""
    echo "自定义端口示例:"
    echo "  $0 --mysql-port 3307 --backend-port 8982  # 自定义MySQL和后端端口"
    echo "  $0 --mysql-db myproject --frontend-port 3000  # 自定义数据库名和前端端口"
    echo "  $0 -a --mysql-db testdb --redis-port 6380     # 完整安装并自定义数据库名和Redis端口"
}

# 检查系统环境
check_system() {
    print_step "检查系统环境"
    
    # 检查操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_status "操作系统: Linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_status "操作系统: macOS"
    else
        print_warning "未完全测试的操作系统: $OSTYPE"
    fi
    
    # 检查必要命令
    local required_commands=("curl" "git" "mkdir" "chmod")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            print_error "缺少必要命令: $cmd"
            exit 1
        fi
    done
    
    # 检查网络连接
    if ! curl -s --connect-timeout 5 http://www.google.com > /dev/null; then
        print_warning "网络连接可能存在问题，某些步骤可能失败"
    fi
    
    print_success "系统环境检查通过"
}

# 创建必要目录
create_directories() {
    print_step "创建必要目录"
    
    local directories=("log" "scripts" "static/images" "static/document" "static/send_file")
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$SCRIPT_DIR/$dir" ]]; then
            mkdir -p "$SCRIPT_DIR/$dir"
            print_status "创建目录: $dir"
        fi
    done
    
    print_success "目录结构创建完成"
}

# 检测Linux发行版
detect_linux_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        DISTRO="rhel"
    elif [ -f /etc/debian_version ]; then
        DISTRO="debian"
    else
        DISTRO="unknown"
    fi
    print_status "检测到Linux发行版: $DISTRO"
}

# 安装MariaDB
setup_mariadb() {
    print_step "安装和配置MariaDB"
    
    # 检查MariaDB是否已安装
    if command -v mysql &> /dev/null && systemctl is-active --quiet mariadb; then
        print_status "MariaDB已安装并运行"
        return 0
    fi
    
    detect_linux_distro
    
    case $DISTRO in
        "ubuntu"|"debian")
            print_status "在Ubuntu/Debian上安装MariaDB..."
            sudo apt-get update
            sudo apt-get install -y mariadb-server mariadb-client libmariadb-dev
            ;;
        "centos"|"rhel"|"fedora"|"amazon"|"amzn")
            print_status "在CentOS/RHEL/Amazon Linux上安装MariaDB..."
            sudo yum install -y mariadb-server mariadb mariadb-devel
            ;;
        *)
            print_error "不支持的Linux发行版: $DISTRO"
            return 1
            ;;
    esac
    
    # 启动MariaDB服务
    print_status "启动MariaDB服务..."
    sudo systemctl start mariadb
    sudo systemctl enable mariadb
    
    # 配置MariaDB端口
    if [[ "$MYSQL_PORT" != "3306" ]]; then
        print_status "配置MariaDB端口为: $MYSQL_PORT"
        sudo sed -i "/^\[mysqld\]/a port = $MYSQL_PORT" /etc/mysql/mariadb.conf.d/50-server.cnf 2>/dev/null || \
        sudo sed -i "/^\[mysqld\]/a port = $MYSQL_PORT" /etc/my.cnf.d/server.cnf 2>/dev/null || \
        echo -e "[mysqld]\nport = $MYSQL_PORT" | sudo tee -a /etc/my.cnf
        
        sudo systemctl restart mariadb
    fi
    
    # 安全配置MariaDB
    print_status "配置MariaDB安全设置..."
    sudo mysql -e "UPDATE mysql.user SET Password = PASSWORD('$MYSQL_ROOT_PASSWORD') WHERE User = 'root';"
    sudo mysql -e "DELETE FROM mysql.user WHERE User='';"
    sudo mysql -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
    sudo mysql -e "DROP DATABASE IF EXISTS test;"
    sudo mysql -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';"
    sudo mysql -e "FLUSH PRIVILEGES;"
    
    # 创建应用数据库和用户
    print_status "创建应用数据库: $MYSQL_DB_NAME"
    mysql -u root -p$MYSQL_ROOT_PASSWORD -e "CREATE DATABASE IF NOT EXISTS \`$MYSQL_DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    mysql -u root -p$MYSQL_ROOT_PASSWORD -e "CREATE USER IF NOT EXISTS 'jd_user'@'localhost' IDENTIFIED BY '$MYSQL_ROOT_PASSWORD';"
    mysql -u root -p$MYSQL_ROOT_PASSWORD -e "GRANT ALL PRIVILEGES ON \`$MYSQL_DB_NAME\`.* TO 'jd_user'@'localhost';"
    mysql -u root -p$MYSQL_ROOT_PASSWORD -e "FLUSH PRIVILEGES;"
    
    print_success "MariaDB安装和配置完成"
    print_status "数据库连接信息:"
    echo "  主机: localhost:$MYSQL_PORT"
    echo "  数据库: $MYSQL_DB_NAME"
    echo "  用户: root / jd_user"
    echo "  密码: $MYSQL_ROOT_PASSWORD"
}

# 安装Redis
setup_redis() {
    print_step "安装和配置Redis"
    
    # 检查Redis是否已安装
    if command -v redis-server &> /dev/null && systemctl is-active --quiet redis; then
        print_status "Redis已安装并运行"
        return 0
    fi
    
    detect_linux_distro
    
    case $DISTRO in
        "ubuntu"|"debian")
            print_status "在Ubuntu/Debian上安装Redis..."
            sudo apt-get update
            sudo apt-get install -y redis-server
            ;;
        "centos"|"rhel"|"fedora"|"amazon"|"amzn")
            print_status "在CentOS/RHEL/Amazon Linux上安装Redis..."
            sudo yum install -y redis
            ;;
        *)
            print_error "不支持的Linux发行版: $DISTRO"
            return 1
            ;;
    esac
    
    # 配置Redis
    print_status "配置Redis..."
    local redis_config="/etc/redis/redis.conf"
    if [[ ! -f "$redis_config" ]]; then
        redis_config="/etc/redis.conf"
    fi
    
    if [[ -f "$redis_config" ]]; then
        # 配置端口
        if [[ "$REDIS_PORT" != "6379" ]]; then
            sudo sed -i "s/^port 6379/port $REDIS_PORT/" "$redis_config"
        fi
        
        # 配置绑定地址
        sudo sed -i "s/^bind 127.0.0.1/bind 127.0.0.1/" "$redis_config"
        
        # 配置后台运行
        sudo sed -i "s/^daemonize no/daemonize yes/" "$redis_config"
    fi
    
    # 启动Redis服务
    print_status "启动Redis服务..."
    sudo systemctl start redis
    sudo systemctl enable redis
    
    # 测试Redis连接
    if redis-cli -p $REDIS_PORT ping | grep -q PONG; then
        print_success "Redis安装和配置完成"
        print_status "Redis连接信息:"
        echo "  主机: localhost:$REDIS_PORT"
        echo "  状态: 运行中"
    else
        print_error "Redis配置可能存在问题"
        return 1
    fi
}

# 配置conda环境
setup_conda_env() {
    print_step "配置Conda环境"
    
    local setup_env_script="$SCRIPT_DIR/scripts/setup_conda_env.sh"
    if [[ ! -f "$setup_env_script" ]]; then
        print_error "环境配置脚本未找到: $setup_env_script"
        exit 1
    fi
    
    chmod +x "$setup_env_script"
    bash "$setup_env_script"
    
    print_success "Conda环境配置完成"
}

# 初始化数据库
init_database() {
    print_step "初始化数据库"
    
    local init_db_script="$SCRIPT_DIR/scripts/init_database.sh"
    if [[ ! -f "$init_db_script" ]]; then
        print_error "数据库初始化脚本未找到: $init_db_script"
        exit 1
    fi
    
    chmod +x "$init_db_script"
    
    if $SKIP_CONFIRM; then
        bash "$init_db_script" --all --force
    else
        bash "$init_db_script" --all
    fi
    
    print_success "数据库初始化完成"
}

# 配置前端环境
setup_frontend() {
    print_step "配置前端环境"
    
    if [[ ! -d "$SCRIPT_DIR/frontend" ]]; then
        print_warning "前端目录不存在，跳过前端配置"
        return 0
    fi
    
    cd "$SCRIPT_DIR/frontend"
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js 未找到！请先安装 Node.js"
        print_status "下载地址: https://nodejs.org/"
        return 1
    fi
    
    print_status "Node.js版本: $(node --version)"
    
    # 检查npm
    if ! command -v npm &> /dev/null; then
        print_error "npm 未找到！"
        return 1
    fi
    
    print_status "npm版本: $(npm --version)"
    
    # 安装前端依赖
    if [[ ! -d "node_modules" ]] || $FORCE_MODE; then
        print_status "安装前端依赖..."
        npm install
        print_success "前端依赖安装完成"
    else
        print_status "前端依赖已存在，跳过安装"
    fi
    
    cd "$SCRIPT_DIR"
    print_success "前端环境配置完成"
}

# 配置Telegram初始化
setup_telegram() {
    print_step "配置Telegram环境"
    
    print_status "检查Telegram配置..."
    
    # 检查是否已有session文件
    if [[ -f "$SCRIPT_DIR/jd_tg.db" ]]; then
        print_success "Telegram session已存在"
        return 0
    fi
    
    print_warning "首次运行需要初始化Telegram连接"
    print_status "请在系统启动后运行以下命令进行初始化:"
    echo "  conda activate $CONDA_ENV_NAME"
    echo "  python -m scripts.job init_tg"
    echo ""
    print_status "您需要准备:"
    echo "  - Telegram账号的手机号"
    echo "  - Telegram发送的验证码"
    echo "  - 如果启用了两步验证，还需要密码"
}

# 创建配置文件
setup_config() {
    print_step "配置项目文件"
    
    local config_file="$SCRIPT_DIR/config.py"
    local config_backup="$SCRIPT_DIR/config.py.backup"
    local config_template="$SCRIPT_DIR/config_template.py"
    
    # 备份现有配置
    if [[ -f "$config_file" ]] && [[ ! -f "$config_backup" ]]; then
        cp "$config_file" "$config_backup"
        print_status "已备份现有配置文件"
    fi
    
    # 生成脱敏的配置模板
    if [[ ! -f "$config_template" ]] || $FORCE_MODE; then
        print_status "生成配置模板文件..."
        generate_config_template "$config_template"
    fi
    
    # 检查配置文件
    if [[ ! -f "$config_file" ]]; then
        print_warning "config.py不存在，正在生成默认配置..."
        generate_config_template "$config_file"
        print_success "已生成默认配置文件，请根据需要修改"
    fi
    
    print_success "配置检查完成"
}

# 生成脱敏的配置文件
generate_config_template() {
    local output_file="$1"
    
    cat > "$output_file" << EOF
import os

# 路由前缀
API_PREFIX = '/api'

# mysql相关配置
SQLALCHEMY_ECHO = False
SQLALCHEMY_ENABLE_POOL = False
SQLALCHEMY_DATABASE_URI = 'mysql+mysqldb://jd_user:YOUR_MYSQL_PASSWORD@127.0.0.1:$MYSQL_PORT/$MYSQL_DB_NAME?charset=utf8mb4'
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
REDIS_PORT = $REDIS_PORT
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
EOF

    print_status "已生成配置文件: $output_file"
}

# 启动服务
start_services() {
    print_step "启动服务"
    
    local start_script="$SCRIPT_DIR/start.sh"
    if [[ ! -f "$start_script" ]]; then
        print_error "启动脚本未找到: $start_script"
        exit 1
    fi
    
    chmod +x "$start_script"
    
    # 检查端口占用
    local ports=("$BACKEND_PORT" "$FRONTEND_PORT")
    for port in "${ports[@]}"; do
        if lsof -i ":$port" &> /dev/null; then
            print_warning "端口 $port 已被占用"
        fi
    done
    
    print_status "启动所有服务..."
    # 传递自定义端口参数给启动脚本
    if [[ "$BACKEND_PORT" != "$DEFAULT_BACKEND_PORT" ]] || [[ "$FRONTEND_PORT" != "$DEFAULT_FRONTEND_PORT" ]]; then
        print_status "使用自定义端口: 后端=$BACKEND_PORT, 前端=$FRONTEND_PORT"
        BACKEND_PORT=$BACKEND_PORT FRONTEND_PORT=$FRONTEND_PORT bash "$start_script" -a
    else
        bash "$start_script" -a
    fi
    
    print_success "服务启动完成"
}

# 验证安装
verify_installation() {
    print_step "验证安装"
    
    # 激活环境
    eval "$(conda shell.bash hook)"
    conda activate "$CONDA_ENV_NAME"
    
    # 检查Python包
    local key_packages=("flask" "celery" "telethon" "sqlalchemy")
    local missing_packages=()
    
    for package in "${key_packages[@]}"; do
        if ! python -c "import $package" &> /dev/null; then
            missing_packages+=("$package")
        fi
    done
    
    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        print_error "以下关键包未正确安装: ${missing_packages[*]}"
        return 1
    fi
    
    print_success "Python环境验证通过"
    
    # 检查前端
    if [[ -d "$SCRIPT_DIR/frontend/node_modules" ]]; then
        print_success "前端环境验证通过"
    else
        print_warning "前端环境可能存在问题"
    fi
    
    print_success "安装验证完成"
}

# 显示完成信息
show_completion_info() {
    print_header "安装完成"
    
    echo -e "${GREEN}${BOLD}🎉 恭喜！$PROJECT_NAME 安装完成！${NC}"
    echo ""
    
    print_status "服务地址:"
    echo "  📱 后端服务: http://localhost:$BACKEND_PORT"
    echo "  🎨 前端服务: http://localhost:$FRONTEND_PORT"
    echo ""
    
    print_status "常用命令:"
    echo "  # 激活环境"
    echo "  conda activate $CONDA_ENV_NAME"
    echo ""
    echo "  # 启动所有服务"
    echo "  bash start.sh -a"
    echo ""
    echo "  # 启动单独服务"
    echo "  bash start.sh -w    # Web服务"
    echo "  bash start.sh -c    # Celery服务"
    echo "  bash start.sh -f    # 前端服务"
    echo ""
    echo "  # 停止服务"
    echo "  bash stop.sh"
    echo ""
    
    print_status "默认用户账户:"
    echo "  🔐 超级管理员: admin / admin123"
    echo "  👤 普通用户: user1 / 111111"
    echo "  👤 普通用户: user2 / 111111"
    echo ""
    
    print_status "重要提示:"
    echo "  ⚠️  首次运行请初始化Telegram: python -m scripts.job init_tg"
    echo "  📝 配置文件位置: config.py"
    echo "  📊 日志文件目录: log/"
    echo "  🗄️  数据库配置: MariaDB端口$MYSQL_PORT，数据库$MYSQL_DB_NAME，用户jd_user"
    echo "  🔧 Redis配置: localhost:$REDIS_PORT"
    echo "  🔑 请更新config.py中的敏感信息（密码、API密钥等）"
    echo ""
    
    print_status "文档和支持:"
    echo "  📚 项目文档: CLAUDE.md"
    echo "  🔧 问题排查: 检查log/目录下的日志文件"
    echo ""
    
    print_success "享受使用 $PROJECT_NAME ！"
}

# 解析命令行参数
parse_args() {
    SETUP_ENV=false
    SETUP_MARIADB=false
    SETUP_REDIS=false
    INIT_DB=false
    SETUP_FRONTEND=false
    START_SERVICES=false
    SKIP_CONFIRM=false
    FORCE_MODE=false
    
    # 如果没有参数，默认执行全部
    if [[ $# -eq 0 ]]; then
        SETUP_ENV=true
        SETUP_MARIADB=true
        SETUP_REDIS=true
        INIT_DB=true
        SETUP_FRONTEND=true
        START_SERVICES=true
        return
    fi
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -e|--setup-env)
                SETUP_ENV=true
                shift
                ;;
            -m|--setup-mariadb)
                SETUP_MARIADB=true
                shift
                ;;
            -r|--setup-redis)
                SETUP_REDIS=true
                shift
                ;;
            -d|--init-db)
                INIT_DB=true
                shift
                ;;
            -f|--setup-frontend)
                SETUP_FRONTEND=true
                shift
                ;;
            -s|--start-services)
                START_SERVICES=true
                shift
                ;;
            -a|--all)
                SETUP_ENV=true
                SETUP_MARIADB=true
                SETUP_REDIS=true
                INIT_DB=true
                SETUP_FRONTEND=true
                START_SERVICES=true
                shift
                ;;
            --skip-confirm)
                SKIP_CONFIRM=true
                shift
                ;;
            --force)
                FORCE_MODE=true
                shift
                ;;
            --mysql-port)
                if [[ -z "$2" ]] || [[ "$2" =~ ^- ]]; then
                    print_error "--mysql-port 需要指定端口号"
                    exit 1
                fi
                MYSQL_PORT="$2"
                shift 2
                ;;
            --mysql-db)
                if [[ -z "$2" ]] || [[ "$2" =~ ^- ]]; then
                    print_error "--mysql-db 需要指定数据库名称"
                    exit 1
                fi
                MYSQL_DB_NAME="$2"
                shift 2
                ;;
            --redis-port)
                if [[ -z "$2" ]] || [[ "$2" =~ ^- ]]; then
                    print_error "--redis-port 需要指定端口号"
                    exit 1
                fi
                REDIS_PORT="$2"
                shift 2
                ;;
            --backend-port)
                if [[ -z "$2" ]] || [[ "$2" =~ ^- ]]; then
                    print_error "--backend-port 需要指定端口号"
                    exit 1
                fi
                BACKEND_PORT="$2"
                shift 2
                ;;
            --frontend-port)
                if [[ -z "$2" ]] || [[ "$2" =~ ^- ]]; then
                    print_error "--frontend-port 需要指定端口号"
                    exit 1
                fi
                FRONTEND_PORT="$2"
                shift 2
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 验证端口号
validate_ports() {
    local ports_to_check=("$MYSQL_PORT" "$REDIS_PORT" "$BACKEND_PORT" "$FRONTEND_PORT")
    local port_names=("MySQL" "Redis" "Backend" "Frontend")
    
    for i in "${!ports_to_check[@]}"; do
        local port="${ports_to_check[$i]}"
        local name="${port_names[$i]}"
        
        # 检查端口是否为有效数字
        if ! [[ "$port" =~ ^[0-9]+$ ]] || [[ "$port" -lt 1 ]] || [[ "$port" -gt 65535 ]]; then
            print_error "${name}端口号无效: $port (必须是1-65535之间的数字)"
            exit 1
        fi
    done
    
    # 检查端口是否重复
    local used_ports=()
    for port in "${ports_to_check[@]}"; do
        if [[ " ${used_ports[*]} " =~ " $port " ]]; then
            print_error "端口号重复: $port"
            exit 1
        fi
        used_ports+=("$port")
    done
}

# 初始化角色和用户数据
init_roles_users() {
    print_step "初始化角色和用户数据"
    
    # 检查Python环境
    eval "$(conda shell.bash hook)"
    conda activate "$CONDA_ENV_NAME"
    
    # 检查脚本是否存在
    local init_script="$PROJECT_DIR/jd/jobs/init_roles_users.py"
    if [[ ! -f "$init_script" ]]; then
        print_warning "初始化脚本未找到: $init_script"
        return 0
    fi
    
    print_status "运行角色和用户初始化脚本..."
    
    # 检查数据库连接
    if ! python -c "from jd import app, db; 
with app.app_context(): 
    try:
        result = db.session.execute(db.text('SELECT 1'))
        result.fetchone()
    except Exception as e:
        print(f'Database connection failed: {e}')
        exit(1)" &> /dev/null; then
        print_error "数据库连接失败，跳过角色用户初始化"
        print_status "提示：请确保数据库已正确初始化并且服务正在运行"
        return 0
    fi
    
    # 运行初始化脚本
    if python "$init_script"; then
        print_success "角色和用户数据初始化完成"
        echo ""
        print_status "默认用户账户:"
        echo "  🔐 超级管理员: admin / admin123"
        echo "  👤 普通用户: user1 / 111111"
        echo "  👤 普通用户: user2 / 111111"
        echo ""
    else
        print_warning "角色和用户初始化失败，请手动运行："
        echo "  conda activate $CONDA_ENV_NAME"
        echo "  python jd/jobs/init_roles_users.py"
    fi
}

# 显示配置摘要
show_config_summary() {
    print_header "配置摘要"
    echo ""
    print_status "数据库配置:"
    echo "  MySQL端口: $MYSQL_PORT"
    echo "  数据库名称: $MYSQL_DB_NAME"
    echo "  Redis端口: $REDIS_PORT"
    echo ""
    print_status "服务端口:"
    echo "  后端服务: $BACKEND_PORT"
    echo "  前端服务: $FRONTEND_PORT"
    echo ""
    
    if ! $SKIP_CONFIRM; then
        echo -n "确认使用以上配置继续安装? [y/N]: "
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY]|是)
                print_success "配置确认，开始安装..."
                ;;
            *)
                print_status "安装已取消"
                exit 0
                ;;
        esac
    fi
}

# 主函数
main() {
    # 切换到项目目录
    cd "$SCRIPT_DIR"
    
    print_header "$PROJECT_NAME - 项目一键启动脚本"
    
    # 解析参数
    parse_args "$@"
    
    # 验证端口配置
    validate_ports
    
    # 显示配置摘要（如果有自定义配置或者执行完整安装）
    if [[ "$MYSQL_PORT" != "$DEFAULT_MYSQL_PORT" ]] || [[ "$MYSQL_DB_NAME" != "$DEFAULT_MYSQL_DB_NAME" ]] || \
       [[ "$REDIS_PORT" != "$DEFAULT_REDIS_PORT" ]] || [[ "$BACKEND_PORT" != "$DEFAULT_BACKEND_PORT" ]] || \
       [[ "$FRONTEND_PORT" != "$DEFAULT_FRONTEND_PORT" ]] || \
       { $SETUP_ENV && $SETUP_MARIADB && $SETUP_REDIS && $INIT_DB && $SETUP_FRONTEND && $START_SERVICES; }; then
        show_config_summary
    fi
    
    # 系统检查
    check_system
    create_directories
    
    # 根据参数执行对应步骤
    if $SETUP_ENV; then
        setup_conda_env
    fi
    
    if $SETUP_MARIADB; then
        setup_mariadb
    fi
    
    if $SETUP_REDIS; then
        setup_redis
    fi
    
    if $SETUP_FRONTEND; then
        setup_frontend
    fi
    
    if $INIT_DB; then
        init_database
        
        # 初始化角色和用户数据（在数据库初始化后）
        init_roles_users
    fi
    
    # 配置项目
    setup_config
    setup_telegram
    
    if $START_SERVICES; then
        start_services
        
        # 等待服务启动
        sleep 5
        
        # 验证安装
        verify_installation
    fi
    
    # 显示完成信息
    show_completion_info
}

# 捕获Ctrl+C
trap 'print_error "安装被中断"; exit 1' INT

# 执行主函数
main "$@"