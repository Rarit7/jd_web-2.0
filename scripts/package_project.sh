#!/bin/bash

# SDJD_TG管理系统 - 项目打包脚本
# 根据.gitignore排除文件，创建干净的项目发布包

set -e  # 遇到错误立即退出

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_NAME="sdjd_tg_system"
VERSION=$(date +"%Y%m%d_%H%M%S")
PACKAGE_DIR="${PROJECT_DIR}/../packages"
TEMP_DIR="/tmp/${PROJECT_NAME}_packaging_$$"

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
    print_header "项目打包脚本 - 帮助信息"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help              显示此帮助信息"
    echo "  -o, --output DIR        指定输出目录 (默认: ../packages)"
    echo "  -n, --name NAME         指定包名 (默认: sdjd_tg_system)"
    echo "  -v, --version VERSION   指定版本号 (默认: 时间戳)"
    echo "  -f, --format FORMAT     打包格式 tar.gz|zip|both (默认: both)"
    echo "  -c, --clean             清理旧的打包文件"
    echo "  --include-logs          包含日志文件"
    echo "  --include-config        包含配置文件"
    echo "  --dry-run               仅显示将要打包的文件，不实际打包"
    echo ""
    echo "打包格式:"
    echo "  tar.gz                  创建 .tar.gz 压缩包"
    echo "  zip                     创建 .zip 压缩包"  
    echo "  both                    同时创建两种格式"
    echo ""
    echo "示例:"
    echo "  $0                              # 默认打包"
    echo "  $0 -f zip                       # 仅创建zip包"
    echo "  $0 -o /tmp -n myproject         # 自定义输出目录和名称"
    echo "  $0 --dry-run                    # 预览打包内容"
    echo "  $0 -c                           # 清理后重新打包"
}

# 清理函数
cleanup() {
    if [[ -d "$TEMP_DIR" ]]; then
        print_status "清理临时目录: $TEMP_DIR"
        rm -rf "$TEMP_DIR"
    fi
}

# 设置清理陷阱
trap cleanup EXIT INT TERM

# 检查依赖工具
check_dependencies() {
    print_step "检查依赖工具"
    
    local missing_tools=()
    
    # 检查tar
    if ! command -v tar &> /dev/null; then
        missing_tools+=("tar")
    fi
    
    # 检查zip
    if ! command -v zip &> /dev/null; then
        missing_tools+=("zip")
    fi
    
    # 检查git（用于处理.gitignore）
    if ! command -v git &> /dev/null; then
        print_warning "git未找到，将使用简化的文件过滤方式"
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        print_error "缺少必要工具: ${missing_tools[*]}"
        print_status "请安装缺少的工具后重新运行"
        exit 1
    fi
    
    print_success "依赖工具检查通过"
}

# 创建输出目录
create_output_dir() {
    print_step "创建输出目录"
    
    if [[ ! -d "$PACKAGE_DIR" ]]; then
        mkdir -p "$PACKAGE_DIR"
        print_status "创建输出目录: $PACKAGE_DIR"
    else
        print_status "使用现有目录: $PACKAGE_DIR"
    fi
    
    # 清理旧文件
    if $CLEAN_OLD; then
        print_status "清理旧的打包文件..."
        rm -f "$PACKAGE_DIR/${PROJECT_NAME}"*.tar.gz
        rm -f "$PACKAGE_DIR/${PROJECT_NAME}"*.zip
        print_success "旧文件清理完成"
    fi
}

# 创建临时目录并复制文件
prepare_files() {
    print_step "准备打包文件"
    
    # 创建临时目录
    mkdir -p "$TEMP_DIR"
    local target_dir="$TEMP_DIR/${PROJECT_NAME}"
    mkdir -p "$target_dir"
    
    cd "$PROJECT_DIR"
    
    # 使用git来处理.gitignore规则（如果可用）
    if command -v git &> /dev/null && [[ -f ".gitignore" ]]; then
        print_status "使用git处理.gitignore规则..."
        
        # 获取所有文件列表（排除.gitignore中的文件）
        git ls-files > "$TEMP_DIR/files_to_include.txt"
        
        # 添加未被git跟踪但不在.gitignore中的文件
        git ls-files --others --exclude-standard >> "$TEMP_DIR/files_to_include.txt" 2>/dev/null || true
        
        # 复制文件
        while IFS= read -r file; do
            if [[ -f "$file" ]]; then
                local dir_name=$(dirname "$file")
                mkdir -p "$target_dir/$dir_name"
                cp "$file" "$target_dir/$file"
            fi
        done < "$TEMP_DIR/files_to_include.txt"
        
    else
        print_warning "未使用git，使用手动文件过滤"
        
        # 手动复制文件，排除常见的不需要的文件和目录
        rsync -av \
            --exclude='__pycache__/' \
            --exclude='*.pyc' \
            --exclude='*.pyo' \
            --exclude='.git/' \
            --exclude='.gitignore' \
            --exclude='node_modules/' \
            --exclude='frontend/node_modules/' \
            --exclude='frontend/dist/' \
            --exclude='log/' \
            --exclude='static/images/' \
            --exclude='static/document/' \
            --exclude='static/send_file/' \
            --exclude='static/dist/' \
            --exclude='*.log' \
            --exclude='nohup.out' \
            --exclude='celerybeat-schedule*' \
            --exclude='.env' \
            --exclude='config.py' \
            --exclude='config_local.py' \
            --exclude='flower_db.db' \
            --exclude='jd_tg.db' \
            --exclude='.DS_Store' \
            --exclude='Thumbs.db' \
            --exclude='*.tmp' \
            --exclude='*.temp' \
            . "$target_dir/"
    fi
    
    # 手动处理特殊情况
    handle_special_files "$target_dir"
    
    print_success "文件准备完成"
}

# 处理特殊文件
handle_special_files() {
    local target_dir="$1"
    
    print_status "处理特殊文件..."
    
    # 如果不包含配置文件，创建配置模板
    if ! $INCLUDE_CONFIG; then
        if [[ -f "$target_dir/config.py" ]]; then
            rm "$target_dir/config.py"
        fi
        
        # 创建配置模板
        cat > "$target_dir/config_template.py" << 'EOF'
# 配置文件模板
# 请复制此文件为 config.py 并根据实际情况修改配置

import os

# 路由前缀
API_PREFIX = '/api'

# mysql相关配置
SQLALCHEMY_ECHO = False
SQLALCHEMY_ENABLE_POOL = False
SQLALCHEMY_DATABASE_URI = 'mysql+mysqldb://用户名:密码@主机:端口/数据库名?charset=utf8mb4'

# jwt 配置
JWT_SECRET_KEY = "请修改为随机字符串"
JWT_ACCESS_TOKEN_EXPIRES = 7 * 24 * 60 * 60

SESSION_SECRET_KEY = "请修改为随机字符串"

# Telegram API配置
TG_CONFIG = {
    "api_id": "请填写您的api_id",
    "api_hash": "请填写您的api_hash",
    "sqlite_db_name": "jd_tg.db",
    "proxy": None
}

# 其他配置项请参考原始config.py文件
EOF
        print_status "创建配置模板: config_template.py"
    fi
    
    # 处理日志目录
    if ! $INCLUDE_LOGS; then
        rm -rf "$target_dir/log"
        mkdir -p "$target_dir/log"
        echo "# 日志文件将在运行时创建" > "$target_dir/log/.gitkeep"
    fi
    
    # 创建必要的空目录
    local required_dirs=(
        "static/images"
        "static/document"
        "static/send_file"
    )
    
    for dir in "${required_dirs[@]}"; do
        mkdir -p "$target_dir/$dir"
        echo "# 此目录用于存储运行时文件" > "$target_dir/$dir/.gitkeep"
    done
    
    # 确保脚本有执行权限
    find "$target_dir" -name "*.sh" -exec chmod +x {} \;
    
    print_success "特殊文件处理完成"
}

# 创建打包信息文件
create_package_info() {
    local target_dir="$1"
    
    print_status "创建打包信息文件..."
    
    cat > "$target_dir/PACKAGE_INFO.txt" << EOF
========================================
SDJD_TG管理系统 - 发布包信息
========================================

包名称: ${PROJECT_NAME}
版本号: ${VERSION}
打包时间: $(date '+%Y-%m-%d %H:%M:%S')
打包主机: $(hostname)

========================================
安装说明
========================================

1. 解压包到目标目录
2. 阅读 SETUP_GUIDE.md 了解详细安装步骤
3. 运行一键安装脚本: bash setup_project.sh
4. 根据提示配置数据库和Telegram连接

========================================
主要文件说明
========================================

setup_project.sh       - 一键安装脚本
start.sh               - 服务启动脚本
stop.sh                - 服务停止脚本
SETUP_GUIDE.md         - 详细安装指南
config_template.py     - 配置文件模板
requirements.txt       - Python依赖列表
dbrt/ddl.sql          - 数据库建表脚本

========================================
重要提示
========================================

- 首次运行前请复制config_template.py为config.py并修改配置
- 确保MySQL和Redis服务已启动
- 需要有效的Telegram API credentials
- 推荐使用conda环境管理Python依赖

========================================
技术支持
========================================

详细文档请参考项目中的CLAUDE.md和SETUP_GUIDE.md文件。

EOF

    print_success "打包信息文件创建完成"
}

# 显示打包内容预览
show_package_contents() {
    local target_dir="$1"
    
    print_step "打包内容预览"
    
    echo "主要文件和目录:"
    find "$target_dir" -type f | head -20 | sort | sed 's|'"$target_dir"'/||g' | sed 's/^/  /'
    
    if [[ $(find "$target_dir" -type f | wc -l) -gt 20 ]]; then
        echo "  ... (还有 $(( $(find "$target_dir" -type f | wc -l) - 20 )) 个文件)"
    fi
    
    echo ""
    echo "统计信息:"
    echo "  文件总数: $(find "$target_dir" -type f | wc -l)"
    echo "  目录总数: $(find "$target_dir" -type d | wc -l)"
    echo "  总大小: $(du -sh "$target_dir" | cut -f1)"
    echo ""
}

# 创建压缩包
create_archives() {
    local target_dir="$1"
    local package_base="${PROJECT_NAME}-${VERSION}"
    
    print_step "创建压缩包"
    
    cd "$TEMP_DIR"
    
    # 创建tar.gz包
    if [[ "$FORMAT" == "tar.gz" ]] || [[ "$FORMAT" == "both" ]]; then
        print_status "创建 tar.gz 包..."
        tar -czf "$PACKAGE_DIR/${package_base}.tar.gz" "$PROJECT_NAME"
        print_success "已创建: ${package_base}.tar.gz"
    fi
    
    # 创建zip包
    if [[ "$FORMAT" == "zip" ]] || [[ "$FORMAT" == "both" ]]; then
        print_status "创建 zip 包..."
        zip -r "$PACKAGE_DIR/${package_base}.zip" "$PROJECT_NAME" > /dev/null
        print_success "已创建: ${package_base}.zip"
    fi
}

# 显示完成信息
show_completion_info() {
    local package_base="${PROJECT_NAME}-${VERSION}"
    
    print_header "打包完成"
    
    echo -e "${GREEN}${BOLD}🎉 项目打包完成！${NC}"
    echo ""
    
    print_status "输出目录: $PACKAGE_DIR"
    echo ""
    
    print_status "生成的文件:"
    if [[ "$FORMAT" == "tar.gz" ]] || [[ "$FORMAT" == "both" ]]; then
        if [[ -f "$PACKAGE_DIR/${package_base}.tar.gz" ]]; then
            local size=$(du -h "$PACKAGE_DIR/${package_base}.tar.gz" | cut -f1)
            echo "  📦 ${package_base}.tar.gz ($size)"
        fi
    fi
    
    if [[ "$FORMAT" == "zip" ]] || [[ "$FORMAT" == "both" ]]; then
        if [[ -f "$PACKAGE_DIR/${package_base}.zip" ]]; then
            local size=$(du -h "$PACKAGE_DIR/${package_base}.zip" | cut -f1)
            echo "  📦 ${package_base}.zip ($size)"
        fi
    fi
    
    echo ""
    print_status "使用方法:"
    echo "  1. 将压缩包传输到目标服务器"
    echo "  2. 解压: tar -xzf ${package_base}.tar.gz  或  unzip ${package_base}.zip"
    echo "  3. 进入目录: cd ${PROJECT_NAME}"
    echo "  4. 运行安装: bash setup_project.sh"
    echo ""
    
    print_success "打包任务完成！"
}

# 解析命令行参数
parse_args() {
    # 设置默认值
    PACKAGE_DIR="${PROJECT_DIR}/../packages"
    FORMAT="both"
    CLEAN_OLD=false
    INCLUDE_LOGS=false
    INCLUDE_CONFIG=false
    DRY_RUN=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -o|--output)
                PACKAGE_DIR="$2"
                shift 2
                ;;
            -n|--name)
                PROJECT_NAME="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -f|--format)
                FORMAT="$2"
                if [[ "$FORMAT" != "tar.gz" && "$FORMAT" != "zip" && "$FORMAT" != "both" ]]; then
                    print_error "无效的格式: $FORMAT"
                    show_help
                    exit 1
                fi
                shift 2
                ;;
            -c|--clean)
                CLEAN_OLD=true
                shift
                ;;
            --include-logs)
                INCLUDE_LOGS=true
                shift
                ;;
            --include-config)
                INCLUDE_CONFIG=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 转换相对路径为绝对路径
    if [[ ! -d "$PACKAGE_DIR" ]]; then
        mkdir -p "$PACKAGE_DIR"
    fi
    PACKAGE_DIR=$(cd "$PACKAGE_DIR" && pwd)
}

# 主函数
main() {
    print_header "SDJD_TG管理系统 - 项目打包工具"
    
    # 解析参数
    parse_args "$@"
    
    print_status "打包配置:"
    echo "  项目名称: $PROJECT_NAME"
    echo "  版本号: $VERSION"
    echo "  输出目录: $PACKAGE_DIR"
    echo "  打包格式: $FORMAT"
    echo "  包含日志: $([ "$INCLUDE_LOGS" = true ] && echo "是" || echo "否")"
    echo "  包含配置: $([ "$INCLUDE_CONFIG" = true ] && echo "是" || echo "否")"
    echo ""
    
    # 检查依赖
    check_dependencies
    
    # 创建输出目录
    create_output_dir
    
    # 准备文件
    prepare_files
    
    # 处理特殊文件
    local target_dir="$TEMP_DIR/${PROJECT_NAME}"
    create_package_info "$target_dir"
    
    # 显示内容预览
    show_package_contents "$target_dir"
    
    # 如果是dry-run，到这里就结束
    if $DRY_RUN; then
        print_success "预览完成（干运行模式）"
        exit 0
    fi
    
    # 创建压缩包
    create_archives "$target_dir"
    
    # 显示完成信息
    show_completion_info
}

# 执行主函数
main "$@"