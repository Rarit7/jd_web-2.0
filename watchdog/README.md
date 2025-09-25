# System Watchdog & Emergency Recovery

系统监控和紧急恢复应用程序，提供完整的系统资源监控、保护和紧急恢复功能。

## 目录结构

```
watchdog/
├── README.md                    # 总体文档说明
├── src/                        # 源代码
│   ├── system_watchdog.py      # 系统监控程序
│   └── emergency_recovery.sh   # 紧急恢复脚本
├── config/                     # 配置文件
│   └── watchdog_config.json   # 监控配置
├── deploy/                     # 部署相关
│   ├── deploy_watchdog.sh      # 监控服务部署脚本
│   └── system_watchdog.service # systemd服务文件
└── docs/                       # 详细文档
    └── emergency_recovery.md   # 紧急恢复详细文档
```

## 功能特性

### 系统监控 (System Watchdog)
- 实时监控系统和应用进程资源使用
- 自动杀死超过阈值的进程
- 保护关键系统进程和SSH连接
- 自动重启应用服务
- 发送告警通知
- 生成详细监控日志

### 紧急恢复 (Emergency Recovery)
- 快速系统资源清理和优化
- 智能进程管理和清理
- 系统缓存清理
- 临时文件清理
- 服务重启和状态检查
- 系统参数优化

## 使用方法

### 系统监控使用

```bash
# 执行单次检查
python watchdog/src/system_watchdog.py --check-once

# 以守护进程模式运行
python watchdog/src/system_watchdog.py --daemon

# 杀死高资源使用进程
python watchdog/src/system_watchdog.py --kill-high-usage

# 使用自定义配置文件
python watchdog/src/system_watchdog.py --daemon --config watchdog/config/watchdog_config.json
```

### 系统服务部署

```bash
# 安装系统服务
sudo bash watchdog/deploy/deploy_watchdog.sh install

# 查看服务状态
sudo bash watchdog/deploy/deploy_watchdog.sh status

# 查看服务日志
sudo bash watchdog/deploy/deploy_watchdog.sh logs

# 重启服务
sudo bash watchdog/deploy/deploy_watchdog.sh restart

# 卸载服务
sudo bash watchdog/deploy/deploy_watchdog.sh uninstall

# 测试配置
bash watchdog/deploy/deploy_watchdog.sh test
```

### 紧急恢复使用

```bash
# 完整恢复模式（推荐）
bash watchdog/src/emergency_recovery.sh

# 仅清理进程和缓存
bash watchdog/src/emergency_recovery.sh cleanup

# 仅优化系统参数（需要root权限）
sudo bash watchdog/src/emergency_recovery.sh optimize

# 仅重启服务
bash watchdog/src/emergency_recovery.sh restart

# 仅检查服务状态
bash watchdog/src/emergency_recovery.sh check
```

## 配置说明

配置文件位于 `watchdog/config/watchdog_config.json`，包含以下主要配置项：

- `system_thresholds`: 系统资源阈值
- `process_thresholds`: 单进程资源阈值
- `monitored_processes`: 监控的应用进程
- `protected_processes`: 受保护的进程列表
- `monitoring`: 监控设置
- `emergency_thresholds`: 紧急阈值
- `logging`: 日志配置

详细配置说明请参考配置文件中的注释。

## 监控进程

默认监控以下关键进程：

- Flask Web应用
- Vite前端开发服务器
- Celery工作进程
- VS Code服务器进程
- Claude Code

## 日志

### 监控日志
监控日志保存在 `logs/watchdog.log`，包含：
- 系统资源状态
- 进程杀死记录
- 服务重启记录
- 错误和警告信息

### 恢复日志
紧急恢复日志保存在 `logs/emergency_recovery.log`，包含：
- 恢复操作时间戳
- 系统资源状态快照
- 进程清理记录
- 服务重启状态
- 操作结果和错误信息

## 详细文档

- **紧急恢复详细使用说明**: 请参考 [emergency_recovery.md](docs/emergency_recovery.md)
- **监控配置详解**: 请查看 `config/watchdog_config.json` 中的注释

## 相关工具

本系统监控应用包含两个核心组件：
1. **系统监控** - 持续监控和自动保护
2. **紧急恢复** - 快速恢复和系统优化

建议配合使用以获得最佳的系统稳定性和性能。