#!/bin/bash
# 紧急系统恢复脚本
# 当系统资源极度紧张时，快速恢复系统可用性

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_FILE="$PROJECT_ROOT/logs/emergency_recovery.log"

# 确保日志目录存在
mkdir -p "$PROJECT_ROOT/logs"

# 日志函数
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

# 检查是否以root权限运行（某些操作需要）
check_privileges() {
    if [[ $EUID -eq 0 ]]; then
        log_message "以root权限运行"
        return 0
    else
        log_message "以普通用户权限运行"
        return 1
    fi
}

# 获取系统资源使用情况
get_system_stats() {
    log_message "=== 系统资源使用情况 ==="

    # 内存使用
    local mem_info=$(free -m | awk 'NR==2{printf "内存使用: %s/%sMB (%.2f%%)", $3,$2,$3*100/$2}')
    log_message "$mem_info"

    # CPU使用
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    log_message "CPU使用率: ${cpu_usage}%"

    # 磁盘使用
    local disk_usage=$(df -h / | awk 'NR==2 {print $5}')
    log_message "磁盘使用率: $disk_usage"

    # 负载平均值
    local load_avg=$(uptime | awk -F'load average:' '{print $2}')
    log_message "负载平均值: $load_avg"

    # 进程数量
    local process_count=$(ps aux | wc -l)
    log_message "总进程数: $process_count"
}

# 杀死高资源使用的非关键进程
kill_high_usage_processes() {
    log_message "=== 清理高资源使用进程 ==="

    # 保护的进程列表
    local protected="sshd|systemd|kernel|init|kthread|mariadb|mysqld|redis|NetworkManager|chronyd|dbus"

    # 查找高内存使用的进程（超过200MB且非保护进程）
    log_message "查找高内存使用进程..."
    ps aux --sort=-%mem | awk 'NR>1 && $6>200000' | while read line; do
        local pid=$(echo $line | awk '{print $2}')
        local user=$(echo $line | awk '{print $1}')
        local mem_mb=$(echo $line | awk '{print int($6/1024)}')
        local cmd=$(echo $line | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')

        # 检查是否为保护进程
        if echo "$cmd" | grep -qE "$protected"; then
            log_message "跳过保护进程: PID $pid ($cmd)"
            continue
        fi

        # 检查是否为当前用户的重要进程
        if [[ "$user" == "ec2-user" ]]; then
            if echo "$cmd" | grep -qE "(bash|ssh|system_watchdog)"; then
                log_message "跳过重要进程: PID $pid ($cmd)"
                continue
            fi
        fi

        log_message "杀死高内存进程: PID $pid, 内存 ${mem_mb}MB, 命令: $cmd"
        kill -TERM "$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
        sleep 1
    done

    # 查找高CPU使用的进程
    log_message "查找高CPU使用进程..."
    # 使用top命令获取CPU使用率高的进程
    top -bn1 | awk 'NR>7 && $9>50 && $9!="0.0"' | head -5 | while read line; do
        local pid=$(echo $line | awk '{print $1}')
        local cpu=$(echo $line | awk '{print $9}')
        local cmd=$(echo $line | awk '{print $12}')

        # 检查是否为保护进程
        if echo "$cmd" | grep -qE "$protected"; then
            log_message "跳过保护进程: PID $pid ($cmd)"
            continue
        fi

        log_message "杀死高CPU进程: PID $pid, CPU ${cpu}%, 命令: $cmd"
        kill -TERM "$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
        sleep 1
    done
}

# 清理系统缓存
clear_system_cache() {
    log_message "=== 清理系统缓存 ==="

    if check_privileges; then
        # 清理页面缓存
        log_message "清理页面缓存..."
        sync
        echo 1 > /proc/sys/vm/drop_caches

        # 清理目录和inode缓存
        log_message "清理目录和inode缓存..."
        echo 2 > /proc/sys/vm/drop_caches

        # 清理所有缓存
        log_message "清理所有缓存..."
        echo 3 > /proc/sys/vm/drop_caches

        log_message "系统缓存清理完成"
    else
        log_message "需要root权限清理系统缓存，跳过"
    fi
}

# 清理临时文件
clean_temp_files() {
    log_message "=== 清理临时文件 ==="

    # 清理项目临时文件
    local temp_dirs=(
        "$PROJECT_ROOT/logs/*.log.1"
        "$PROJECT_ROOT/logs/*.log.2"
        "$PROJECT_ROOT/logs/*.log.3"
        "/tmp/claude*"
        "/tmp/vscode*"
        "/tmp/npm*"
        "/tmp/pip*"
    )

    for pattern in "${temp_dirs[@]}"; do
        if ls $pattern 1> /dev/null 2>&1; then
            log_message "清理: $pattern"
            rm -rf $pattern 2>/dev/null || true
        fi
    done

    # 清理Python缓存
    find "$PROJECT_ROOT" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT" -name "*.pyc" -delete 2>/dev/null || true

    log_message "临时文件清理完成"
}

# 优化系统参数
optimize_system() {
    log_message "=== 优化系统参数 ==="

    if check_privileges; then
        # 调整虚拟内存设置
        log_message "调整虚拟内存设置..."
        echo 60 > /proc/sys/vm/swappiness
        echo 1 > /proc/sys/vm/overcommit_memory

        # 调整网络参数
        log_message "调整网络参数..."
        echo 1024 > /proc/sys/net/core/somaxconn
        echo 8192 > /proc/sys/net/core/netdev_max_backlog

        log_message "系统参数优化完成"
    else
        log_message "需要root权限优化系统参数，跳过"
    fi
}

# 重启关键服务
restart_services() {
    log_message "=== 重启关键服务 ==="

    cd "$PROJECT_ROOT"

    # 停止所有服务
    log_message "停止应用服务..."
    bash stop.sh 2>/dev/null || true
    sleep 5

    # 杀死残留进程
    log_message "清理残留进程..."
    pkill -f "python.*web.py" 2>/dev/null || true
    pkill -f "celery.*worker" 2>/dev/null || true
    pkill -f "node.*vite" 2>/dev/null || true
    sleep 3

    # 重新启动服务
    log_message "重启Flask应用..."
    bash start.sh -w &
    sleep 10

    log_message "重启Celery工作进程..."
    bash start.sh -c &
    sleep 10

    log_message "重启前端开发服务器..."
    cd frontend
    nohup npm run dev > ../log/frontend_out.txt 2>&1 &
    cd ..

    log_message "服务重启完成"
}

# 检查服务状态
check_services() {
    log_message "=== 检查服务状态 ==="

    # 检查Flask应用
    if pgrep -f "python.*web.py" > /dev/null; then
        log_message "✓ Flask应用正在运行"
    else
        log_error "✗ Flask应用未运行"
    fi

    # 检查Celery工作进程
    if pgrep -f "celery.*worker" > /dev/null; then
        log_message "✓ Celery工作进程正在运行"
    else
        log_error "✗ Celery工作进程未运行"
    fi

    # 检查前端开发服务器
    if pgrep -f "node.*vite" > /dev/null; then
        log_message "✓ 前端开发服务器正在运行"
    else
        log_error "✗ 前端开发服务器未运行"
    fi

    # 检查数据库
    if pgrep -f "mariadb\|mysqld" > /dev/null; then
        log_message "✓ 数据库服务正在运行"
    else
        log_error "✗ 数据库服务未运行"
    fi
}

# 生成恢复报告
generate_report() {
    log_message "=== 恢复操作完成 ==="
    log_message "生成时间: $(date)"
    log_message "恢复脚本: $0"
    log_message "项目目录: $PROJECT_ROOT"
    log_message "日志文件: $LOG_FILE"

    # 显示最终系统状态
    get_system_stats

    log_message "=== 恢复报告结束 ==="
    echo
    echo "紧急恢复完成！详细日志请查看: $LOG_FILE"
    echo "请监控系统状态，确认服务正常运行。"
}

# 主函数
main() {
    local mode="${1:-full}"

    log_message "========================================"
    log_message "紧急系统恢复脚本启动"
    log_message "恢复模式: $mode"
    log_message "========================================"

    # 记录初始状态
    get_system_stats

    case "$mode" in
        "cleanup")
            kill_high_usage_processes
            clear_system_cache
            clean_temp_files
            ;;
        "optimize")
            optimize_system
            ;;
        "restart")
            restart_services
            ;;
        "check")
            check_services
            ;;
        "full"|*)
            kill_high_usage_processes
            clear_system_cache
            clean_temp_files
            optimize_system
            restart_services
            sleep 10
            check_services
            ;;
    esac

    generate_report
}

# 信号处理
trap 'log_error "恢复脚本被中断"; exit 1' INT TERM

# 运行主函数
main "$@"