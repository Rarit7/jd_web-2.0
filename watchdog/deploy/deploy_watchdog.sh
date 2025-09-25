#!/bin/bash
# 系统监控守护程序部署脚本
# 用于安装和管理 system_watchdog 系统服务

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
SERVICE_NAME="system-watchdog"
SERVICE_FILE="system_watchdog.service"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否以root权限运行
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要以root权限运行"
        echo "请使用: sudo $0 $@"
        exit 1
    fi
}

# 安装服务
install_service() {
    log_info "开始安装 $SERVICE_NAME 服务..."

    # 检查服务文件是否存在
    if [[ ! -f "$SCRIPT_DIR/$SERVICE_FILE" ]]; then
        log_error "服务文件 $SERVICE_FILE 不存在"
        exit 1
    fi

    # 检查 Python 脚本是否存在
    if [[ ! -f "$PROJECT_ROOT/watchdog/src/system_watchdog.py" ]]; then
        log_error "Python脚本 system_watchdog.py 不存在"
        exit 1
    fi

    # 检查配置文件是否存在
    if [[ ! -f "$PROJECT_ROOT/watchdog/config/watchdog_config.json" ]]; then
        log_error "配置文件 watchdog_config.json 不存在"
        exit 1
    fi

    # 复制服务文件到系统目录
    cp "$SCRIPT_DIR/$SERVICE_FILE" "/etc/systemd/system/$SERVICE_NAME.service"
    log_success "服务文件已复制到 /etc/systemd/system/$SERVICE_NAME.service"

    # 重新加载 systemd 配置
    systemctl daemon-reload
    log_success "systemd 配置已重新加载"

    # 启用服务（开机自启动）
    systemctl enable "$SERVICE_NAME.service"
    log_success "服务已设置为开机自启动"

    # 启动服务
    systemctl start "$SERVICE_NAME.service"
    log_success "服务已启动"

    # 检查服务状态
    if systemctl is-active --quiet "$SERVICE_NAME.service"; then
        log_success "$SERVICE_NAME 服务安装并启动成功"
        echo
        echo "服务状态:"
        systemctl status "$SERVICE_NAME.service" --no-pager -l
    else
        log_error "服务启动失败"
        echo "查看服务日志："
        echo "journalctl -u $SERVICE_NAME.service -f"
        exit 1
    fi
}

# 卸载服务
uninstall_service() {
    log_info "开始卸载 $SERVICE_NAME 服务..."

    # 停止服务
    if systemctl is-active --quiet "$SERVICE_NAME.service"; then
        systemctl stop "$SERVICE_NAME.service"
        log_success "服务已停止"
    fi

    # 禁用服务
    if systemctl is-enabled --quiet "$SERVICE_NAME.service" 2>/dev/null; then
        systemctl disable "$SERVICE_NAME.service"
        log_success "已禁用开机自启动"
    fi

    # 删除服务文件
    if [[ -f "/etc/systemd/system/$SERVICE_NAME.service" ]]; then
        rm -f "/etc/systemd/system/$SERVICE_NAME.service"
        log_success "服务文件已删除"
    fi

    # 重新加载 systemd 配置
    systemctl daemon-reload
    log_success "systemd 配置已重新加载"

    log_success "$SERVICE_NAME 服务已完全卸载"
}

# 重启服务
restart_service() {
    log_info "重启 $SERVICE_NAME 服务..."
    systemctl restart "$SERVICE_NAME.service"

    if systemctl is-active --quiet "$SERVICE_NAME.service"; then
        log_success "服务重启成功"
        systemctl status "$SERVICE_NAME.service" --no-pager -l
    else
        log_error "服务重启失败"
        exit 1
    fi
}

# 查看服务状态
status_service() {
    log_info "查看 $SERVICE_NAME 服务状态:"
    echo
    systemctl status "$SERVICE_NAME.service" --no-pager -l
}

# 查看服务日志
logs_service() {
    log_info "查看 $SERVICE_NAME 服务日志:"
    echo
    journalctl -u "$SERVICE_NAME.service" -f
}

# 测试配置
test_config() {
    log_info "测试监控配置..."

    # 切换到项目目录
    cd "$PROJECT_ROOT"

    # 激活虚拟环境（如果存在）
    if [[ -f "$HOME/miniconda3/envs/sdweb2/bin/python" ]]; then
        PYTHON_BIN="$HOME/miniconda3/envs/sdweb2/bin/python"
    else
        PYTHON_BIN="python3"
    fi

    # 运行一次性检查
    sudo -u ec2-user "$PYTHON_BIN" watchdog/src/system_watchdog.py --check-once

    if [[ $? -eq 0 ]]; then
        log_success "配置测试通过"
    else
        log_error "配置测试失败"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "系统监控守护程序部署脚本"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  install    安装并启动监控服务"
    echo "  uninstall  停止并卸载监控服务"
    echo "  restart    重启监控服务"
    echo "  status     查看服务状态"
    echo "  logs       查看服务日志（实时）"
    echo "  test       测试配置文件"
    echo "  help       显示此帮助信息"
    echo
    echo "示例:"
    echo "  sudo $0 install     # 安装服务"
    echo "  sudo $0 status      # 查看状态"
    echo "  sudo $0 logs        # 查看日志"
    echo "  sudo $0 uninstall   # 卸载服务"
}

# 主函数
main() {
    case "${1:-help}" in
        install)
            check_root
            install_service
            ;;
        uninstall)
            check_root
            uninstall_service
            ;;
        restart)
            check_root
            restart_service
            ;;
        status)
            status_service
            ;;
        logs)
            logs_service
            ;;
        test)
            test_config
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知选项: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"