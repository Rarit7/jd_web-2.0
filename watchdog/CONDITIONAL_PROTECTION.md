# Watchdog 条件保护机制说明

## 概述

Watchdog 系统现在支持**条件保护 (Conditional Protection)** 机制，允许某些进程在系统正常时受保护，但在系统资源紧张时可以被终止以保障系统稳定性。

## 保护级别

### 1️⃣ 永久保护 (Absolute Protection)
这些进程**永远不会**被 watchdog 终止，无论系统负载如何：

```json
"protected_processes": [
  "sshd",           // SSH 服务 - 最高优先级
  "systemd",        // 系统初始化
  "kernel",         // 内核进程
  "init",           // 初始化进程
  "kthread",        // 内核线程
  "mariadb",        // 数据库
  "mysqld",         // 数据库
  "redis",          // 缓存
  "system_watchdog",// Watchdog 自身
  "NetworkManager", // 网络管理
  "chronyd",        // 时间同步
  "dbus"            // 系统消息总线
]
```

**优先级**: 🔴 最高 - 系统核心组件

---

### 2️⃣ 条件保护 (Conditional Protection)
这些进程在系统正常时受保护，但在资源紧张时可被终止：

#### Claude Code
```json
"claude": {
  "memory_threshold_percent": 85,    // 内存 > 85% 时取消保护
  "load_average_threshold": 5.0,     // 负载 > 5.0 时取消保护
  "comment": "Claude Code - 紧急情况下可被终止以保护系统稳定性"
}
```
**优先级**: 🟡 中等 - 开发工具，保护 SSH 连接优先

#### VS Code 服务器
```json
"node.*server-main": {
  "memory_threshold_percent": 90,    // 内存 > 90% 时取消保护
  "load_average_threshold": 7.0,     // 负载 > 7.0 时取消保护
  "comment": "VS Code 服务器 - 仅极端情况下终止"
}
```
**优先级**: 🟢 较高 - IDE 核心服务

---

## 工作原理

### 决策流程

```
                    发现高资源使用进程
                            ↓
            ┌───────────────────────────────┐
            │  检查是否在永久保护列表中？    │
            └───────────┬───────────────────┘
                        │
        ┌───────────────┴────────────────┐
        │ YES                            │ NO
        ↓                                ↓
   🛡️ 永久保护                  检查是否在条件保护列表中？
   跳过终止                                ↓
                        ┌────────────────┴──────────────┐
                        │ YES                           │ NO
                        ↓                               ↓
              检查系统当前负载状态              ⚠️ 无保护，可被终止
                        ↓
        ┌───────────────┴───────────────┐
        │                               │
    负载正常                         负载过高
        ↓                               ↓
   🛡️ 临时保护                    ❌ 取消保护
   跳过终止                         允许终止
```

### 触发条件

Claude Code 会在以下情况被终止：

1. **内存使用率 ≥ 85%** 且 Claude 超过资源限制
2. **系统负载 ≥ 5.0** 且 Claude 超过资源限制
3. 满足任一条件即取消保护

### 示例场景

#### ✅ 场景 1: 系统正常
```
系统状态: 内存 37%, 负载 0.3
Claude: 使用 300MB 内存, CPU 15%
结果: ✅ Claude 受保护，不会被终止
```

#### ⚠️ 场景 2: 内存压力
```
系统状态: 内存 90%, 负载 0.3
Claude: 使用 2GB 内存, CPU 80%
结果: ❌ 取消保护，Claude 可被终止
日志: "系统负载过高，取消条件保护: claude (PID: 12345),
       内存: 90.0% (阈值: 85%), 负载: 0.30 (阈值: 5.0)"
```

#### ⚠️ 场景 3: CPU 高负载
```
系统状态: 内存 40%, 负载 6.5
Claude: 使用 500MB 内存, CPU 90%
结果: ❌ 取消保护，Claude 可被终止
日志: "系统负载过高，取消条件保护: claude (PID: 12345),
       内存: 40.0% (阈值: 85%), 负载: 6.50 (阈值: 5.0)"
```

#### 🔒 场景 4: SSH 永久保护
```
系统状态: 内存 99%, 负载 10.0
SSH: 任何资源使用
结果: ✅ SSH 永久受保护，绝不会被终止
```

---

## 配置文件

### 位置
```
/home/ec2-user/workspace/jd_web/watchdog/config/watchdog_config.json
```

### 修改阈值

如果需要调整 Claude Code 的保护阈值：

```json
"conditionally_protected_processes": {
  "claude": {
    "memory_threshold_percent": 85,  // 提高到 90 可增加保护
    "load_average_threshold": 5.0,   // 提高到 7.0 可增加保护
    "comment": "Claude Code - 紧急情况下可被终止以保护系统稳定性"
  }
}
```

**调整建议**:
- **更严格保护**: 提高阈值 (90%, 7.0)
- **更宽松保护**: 降低阈值 (80%, 4.0)
- **移除条件保护**: 将进程移回 `protected_processes` 列表

---

## 监控与日志

### 日志位置
```
/home/ec2-user/workspace/jd_web/watchdog/logs/watchdog.log
```

### 关键日志消息

#### 条件保护生效
```
2025-10-04 07:35:15 [INFO] 条件保护生效: claude (PID: 903969)
```

#### 取消条件保护
```
2025-10-04 07:35:15 [WARNING] 系统负载过高，取消条件保护: claude (PID: 903969),
内存: 90.0% (阈值: 85%), 负载: 0.30 (阈值: 5.0)
```

#### 进程被终止
```
2025-10-04 07:35:20 [WARNING] 发现高资源使用进程: claude (PID: 903969), 原因: 内存: 2048MB (80%)
2025-10-04 07:35:20 [WARNING] 成功终止进程: claude (PID: 903969)
```

---

## 测试

### 手动测试条件保护

```bash
# 执行单次检查
python3 watchdog/src/system_watchdog.py --check-once

# 查看当前系统状态
python3 watchdog/src/system_watchdog.py

# 模拟高负载测试（仅查看，不执行）
python3 watchdog/src/system_watchdog.py --dry-run
```

### 验证保护逻辑

```bash
# 运行内置测试脚本
python3 -c "
import sys
sys.path.insert(0, 'watchdog/src')
from system_watchdog import SystemWatchdog

wd = SystemWatchdog(config_file='watchdog/config/watchdog_config.json')

# 测试正常状态
metrics_normal = {'memory_percent': 37.0, 'load_average': [0.3, 0.3, 0.3]}
proc_info = {'pid': 12345, 'name': 'claude', 'cmdline': 'claude'}
print(f'正常状态保护: {wd.is_process_protected(proc_info, metrics_normal)}')

# 测试高负载状态
metrics_high = {'memory_percent': 90.0, 'load_average': [6.0, 5.0, 4.0]}
print(f'高负载状态保护: {wd.is_process_protected(proc_info, metrics_high)}')
"
```

---

## 设计理念

### 🎯 核心原则

1. **SSH 优先**: 永远保护 SSH 连接，确保远程管理能力
2. **系统稳定**: 数据库、系统服务永不终止
3. **智能取舍**: 开发工具在紧急时可牺牲以保护系统
4. **可配置性**: 通过配置文件灵活调整策略

### 🔄 优先级层次

```
Tier 0 (永不终止): SSH, 系统服务, 数据库
    ↓
Tier 1 (极端情况): VS Code Server (阈值 90%/7.0)
    ↓
Tier 2 (紧急情况): Claude Code (阈值 85%/5.0)
    ↓
Tier 3 (常规监控): 其他应用进程
```

---

## 常见问题

### Q: 为什么 Claude Code 不是永久保护？
**A**: 在内存泄漏或系统资源极度紧张时，优先保障 SSH 连接和系统稳定性。Claude 进程可以重启，但失去 SSH 连接可能导致无法远程管理系统。

### Q: 如何让 Claude 永久保护？
**A**: 将 `"claude"` 从 `conditionally_protected_processes` 移动到 `protected_processes` 列表。

### Q: watchdog 多久检查一次？
**A**: 默认 45 秒检查一次（可在配置中调整 `check_interval`）。

### Q: Claude 被终止后会自动重启吗？
**A**: 不会。需要手动重启 Claude Code。

---

## 更新日志

**2025-10-04**:
- ✅ 实现条件保护机制
- ✅ 将 Claude Code 从永久保护移至条件保护
- ✅ 添加系统负载阈值判断
- ✅ SSH 进程保持最高优先级永久保护
