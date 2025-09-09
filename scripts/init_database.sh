#!/bin/bash

# SDJD_TG管理系统 - 数据库初始化脚本
# 用于创建数据库、导入表结构和初始化数据

set -e  # 遇到错误立即退出

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DDL_FILE="$PROJECT_DIR/dbrt/ddl.sql"
DML_FILE="$PROJECT_DIR/dbrt/dml.sql"

# 默认数据库配置（与setup_project.sh保持一致）
DEFAULT_DB_HOST="127.0.0.1"
DEFAULT_DB_PORT="3306"
DEFAULT_DB_NAME="jd2"
DEFAULT_DB_USER="root"
DEFAULT_DB_PASSWORD="MySecurePassword123!"

# 运行时配置变量（可通过命令行参数或环境变量覆盖）
DB_HOST="${DB_HOST:-$DEFAULT_DB_HOST}"
DB_PORT="${DB_PORT:-$DEFAULT_DB_PORT}"
DB_NAME="${DB_NAME:-$DEFAULT_DB_NAME}"
DB_USER="${DB_USER:-$DEFAULT_DB_USER}"
DB_PASSWORD="${DB_PASSWORD:-$DEFAULT_DB_PASSWORD}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help              显示此帮助信息"
    echo "  -c, --create-db         创建数据库"
    echo "  -t, --create-tables     创建数据表"
    echo "  -d, --insert-data       插入初始数据"
    echo "  -f, --force             强制执行（跳过确认）"
    echo "  -a, --all               执行所有步骤"
    echo ""
    echo "数据库配置选项:"
    echo "  --db-host HOST          数据库主机 (默认: $DEFAULT_DB_HOST)"
    echo "  --db-port PORT          数据库端口 (默认: $DEFAULT_DB_PORT)"
    echo "  --db-name NAME          数据库名称 (默认: $DEFAULT_DB_NAME)"
    echo "  --db-user USER          数据库用户 (默认: $DEFAULT_DB_USER)"
    echo "  --db-password PASS      数据库密码 (默认: $DEFAULT_DB_PASSWORD)"
    echo ""
    echo "示例:"
    echo "  $0 -a              # 执行完整初始化"
    echo "  $0 -c -t           # 仅创建数据库和表"
    echo "  $0 -d              # 仅插入初始数据"
}

# 检查MySQL客户端
check_mysql_client() {
    print_status "检查 MySQL 客户端..."
    if ! command -v mysql &> /dev/null; then
        print_error "MySQL 客户端未找到！请安装 MySQL 客户端"
        print_status "Ubuntu/Debian: sudo apt-get install mysql-client"
        print_status "CentOS/RHEL: sudo yum install mysql"
        print_status "MacOS: brew install mysql-client"
        exit 1
    fi
    print_success "MySQL 客户端已找到"
}

# 检查MySQL服务器连接
check_mysql_connection() {
    print_status "检查 MySQL 服务器连接..."
    
    # 获取密码（优先使用环境变量，然后使用默认值，最后提示输入）
    if [[ -z "$MYSQL_PASSWORD" ]]; then
        if [[ -n "$DB_PASSWORD" ]]; then
            MYSQL_PASSWORD="$DB_PASSWORD"
        else
            read -s -p "请输入 MySQL root 密码 (默认: $DEFAULT_DB_PASSWORD): " MYSQL_PASSWORD
            echo ""
            if [[ -z "$MYSQL_PASSWORD" ]]; then
                MYSQL_PASSWORD="$DB_PASSWORD"
            fi
        fi
    fi
    
    # 测试连接
    if ! mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$MYSQL_PASSWORD" -e "SELECT 1;" &> /dev/null; then
        print_error "无法连接到 MySQL 服务器"
        print_error "请检查:"
        print_error "  - MySQL 服务是否运行"
        print_error "  - 主机地址: $DB_HOST"
        print_error "  - 端口: $DB_PORT"
        print_error "  - 用户名: $DB_USER"
        print_error "  - 密码是否正确"
        exit 1
    fi
    
    print_success "MySQL 服务器连接正常"
}

# 检查必要文件
check_files() {
    print_status "检查必要文件..."
    
    if [[ ! -f "$DDL_FILE" ]]; then
        print_error "DDL文件未找到: $DDL_FILE"
        exit 1
    fi
    print_success "DDL文件: $DDL_FILE"
    
    if [[ ! -f "$DML_FILE" ]]; then
        print_warning "DML文件未找到: $DML_FILE"
        print_warning "将跳过数据插入步骤"
        DML_FILE=""
    else
        print_success "DML文件: $DML_FILE"
    fi
}

# 创建数据库
create_database() {
    print_status "创建数据库: $DB_NAME"
    
    if ! $FORCE_MODE; then
        read -p "确定要创建数据库 '$DB_NAME' 吗? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "跳过数据库创建"
            return 0
        fi
    fi
    
    # 检查数据库是否已存在
    if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$MYSQL_PASSWORD" -e "USE $DB_NAME;" &> /dev/null; then
        print_warning "数据库 '$DB_NAME' 已存在"
        if ! $FORCE_MODE; then
            read -p "是否要删除并重新创建? (y/N): " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_status "跳过数据库创建"
                return 0
            fi
        fi
        
        print_status "删除现有数据库..."
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$MYSQL_PASSWORD" -e "DROP DATABASE IF EXISTS $DB_NAME;"
    fi
    
    # 创建数据库
    print_status "创建数据库..."
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$MYSQL_PASSWORD" << EOF
CREATE DATABASE $DB_NAME DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF
    
    print_success "数据库 '$DB_NAME' 创建成功"
}

# 创建数据表
create_tables() {
    print_status "创建数据表..."
    
    if ! $FORCE_MODE; then
        read -p "确定要执行DDL脚本创建数据表吗? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "跳过表创建"
            return 0
        fi
    fi
    
    print_status "执行DDL脚本: $DDL_FILE"
    if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$MYSQL_PASSWORD" "$DB_NAME" < "$DDL_FILE"; then
        print_success "数据表创建成功"
    else
        print_error "DDL脚本执行失败"
        exit 1
    fi
}

# 插入初始数据
insert_data() {
    if [[ -z "$DML_FILE" ]]; then
        print_warning "跳过数据插入：DML文件不存在"
        return 0
    fi
    
    print_status "插入初始数据..."
    
    if ! $FORCE_MODE; then
        read -p "确定要执行DML脚本插入初始数据吗? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "跳过数据插入"
            return 0
        fi
    fi
    
    print_status "执行DML脚本: $DML_FILE"
    if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$MYSQL_PASSWORD" "$DB_NAME" < "$DML_FILE"; then
        print_success "初始数据插入成功"
    else
        print_error "DML脚本执行失败"
        exit 1
    fi
}

# 验证数据库
verify_database() {
    print_status "验证数据库..."
    
    # 检查表数量
    local table_count
    table_count=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$MYSQL_PASSWORD" "$DB_NAME" -e "SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema='$DB_NAME';" -s -N)
    
    print_success "数据库验证通过:"
    echo "  数据库名: $DB_NAME"
    echo "  表数量: $table_count"
    
    # 显示表列表
    print_status "数据库表列表:"
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$MYSQL_PASSWORD" "$DB_NAME" -e "SHOW TABLES;" | tail -n +2 | sort | sed 's/^/  - /'
}

# 创建数据库配置模板
create_config_template() {
    print_status "创建数据库配置模板..."
    
    local config_template="$PROJECT_DIR/config_template.py"
    cat > "$config_template" << EOF
# 数据库配置模板
# 请根据实际情况修改后重命名为 config.py

import os

# 路由前缀
API_PREFIX = '/api'

# mysql相关配置
SQLALCHEMY_ECHO = False
SQLALCHEMY_ENABLE_POOL = False
SQLALCHEMY_DATABASE_URI = 'mysql+mysqldb://jd_user:YOUR_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?charset=utf8mb4'

# 其他配置...
# (从原始 config.py 复制其他配置项)
EOF
    
    print_success "配置模板已创建: $config_template"
}

# 显示完成信息
show_completion_info() {
    print_success "=== 数据库初始化完成 ==="
    echo ""
    print_status "数据库信息:"
    echo "  主机: $DB_HOST:$DB_PORT"
    echo "  数据库: $DB_NAME"
    echo "  用户: $DB_USER"
    echo ""
    print_status "下一步:"
    echo "  1. 检查并更新 config.py 中的数据库连接配置"
    echo "  2. 启动服务: bash start.sh -a"
    echo "  3. 访问系统: http://localhost:8931"
    echo ""
    print_warning "重要提示:"
    echo "  - 请确保MySQL服务正在运行"
    echo "  - 请确保数据库连接配置正确"
    echo "  - 建议定期备份数据库"
}

# 解析命令行参数
parse_args() {
    CREATE_DB=false
    CREATE_TABLES=false
    INSERT_DATA=false
    FORCE_MODE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--create-db)
                CREATE_DB=true
                shift
                ;;
            -t|--create-tables)
                CREATE_TABLES=true
                shift
                ;;
            -d|--insert-data)
                INSERT_DATA=true
                shift
                ;;
            -f|--force)
                FORCE_MODE=true
                shift
                ;;
            -a|--all)
                CREATE_DB=true
                CREATE_TABLES=true
                INSERT_DATA=true
                shift
                ;;
            --db-host)
                if [[ -z "$2" ]] || [[ "$2" =~ ^- ]]; then
                    print_error "--db-host 需要指定主机地址"
                    exit 1
                fi
                DB_HOST="$2"
                shift 2
                ;;
            --db-port)
                if [[ -z "$2" ]] || [[ "$2" =~ ^- ]]; then
                    print_error "--db-port 需要指定端口号"
                    exit 1
                fi
                DB_PORT="$2"
                shift 2
                ;;
            --db-name)
                if [[ -z "$2" ]] || [[ "$2" =~ ^- ]]; then
                    print_error "--db-name 需要指定数据库名称"
                    exit 1
                fi
                DB_NAME="$2"
                shift 2
                ;;
            --db-user)
                if [[ -z "$2" ]] || [[ "$2" =~ ^- ]]; then
                    print_error "--db-user 需要指定用户名"
                    exit 1
                fi
                DB_USER="$2"
                shift 2
                ;;
            --db-password)
                if [[ -z "$2" ]] || [[ "$2" =~ ^- ]]; then
                    print_error "--db-password 需要指定密码"
                    exit 1
                fi
                DB_PASSWORD="$2"
                shift 2
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 如果没有指定任何操作，显示帮助
    if ! $CREATE_DB && ! $CREATE_TABLES && ! $INSERT_DATA; then
        show_help
        exit 0
    fi
}

# 主函数
main() {
    echo "========================================"
    echo "  SDJD_TG管理系统 - 数据库初始化脚本"
    echo "========================================"
    echo ""
    
    # 解析参数
    parse_args "$@"
    
    print_status "数据库配置:"
    echo "  主机: $DB_HOST:$DB_PORT"
    echo "  数据库: $DB_NAME"
    echo "  用户: $DB_USER"
    echo ""
    
    # 预检查
    check_mysql_client
    check_mysql_connection
    check_files
    
    # 执行操作
    if $CREATE_DB; then
        create_database
    fi
    
    if $CREATE_TABLES; then
        create_tables
    fi
    
    if $INSERT_DATA; then
        insert_data
    fi
    
    # 验证和完成
    verify_database
    create_config_template
    show_completion_info
}

# 执行主函数
main "$@"