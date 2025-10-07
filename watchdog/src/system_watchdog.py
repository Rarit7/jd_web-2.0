#!/usr/bin/env python3
"""
系统资源监控和保护脚本 (System Watchdog)
监控CPU、内存、磁盘使用情况，保护系统稳定性

功能：
- 监控系统和应用进程资源使用
- 自动杀死超过阈值的进程
- 保护关键系统进程和SSH连接
- 自动重启应用服务
- 发送告警通知
- 生成监控日志

使用方法:
    python watchdog/src/system_watchdog.py --daemon
    python watchdog/src/system_watchdog.py --check-once
    python watchdog/src/system_watchdog.py --kill-high-usage
"""

import argparse
import json
import logging
import logging.handlers
import os
import psutil
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
WATCHDOG_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class SystemWatchdog:
    """系统资源监控和保护"""

    def __init__(self, config_file: Optional[str] = None):
        # 先加载配置
        self.config = self._load_config(config_file)

        # 设置独立的日志系统
        self.logger = self._setup_logger()

        # 统计信息
        self.stats = {
            'checks_performed': 0,
            'processes_killed': 0,
            'services_restarted': 0,
            'alerts_sent': 0,
            'last_check': None,
            'start_time': datetime.now().isoformat()
        }

    def _load_config(self, config_file: Optional[str] = None) -> Dict:
        """加载配置文件"""
        default_config = {
            # 系统阈值 (百分比)
            'system_thresholds': {
                'cpu_percent': 85,      # 系统CPU使用率
                'memory_percent': 80,   # 系统内存使用率
                'disk_percent': 85,     # 磁盘使用率
                'swap_percent': 70      # 交换区使用率
            },

            # 单进程阈值
            'process_thresholds': {
                'cpu_percent': 50,      # 单进程CPU使用率
                'memory_mb': 800,       # 单进程内存使用(MB)
                'memory_percent': 20    # 单进程内存占系统百分比
            },

            # 监控的应用进程
            'monitored_processes': {
                'flask': {
                    'patterns': ['python.*web.py', 'flask'],
                    'max_cpu': 40,
                    'max_memory_mb': 500,
                    'restart_cmd': 'bash start.sh -w',
                    'critical': True
                },
                'vite_frontend': {
                    'patterns': ['node.*vite', 'vite'],
                    'max_cpu': 30,
                    'max_memory_mb': 300,
                    'restart_cmd': 'cd frontend && npm run dev',
                    'critical': True
                },
                'celery_workers': {
                    'patterns': ['celery.*worker'],
                    'max_cpu': 60,
                    'max_memory_mb': 400,
                    'restart_cmd': 'bash start.sh -c',
                    'critical': True
                },
                'vscode_extensions': {
                    'patterns': ['node.*vscode.*extensionHost', 'node.*pylance'],
                    'max_cpu': 70,
                    'max_memory_mb': 1000,
                    'restart_cmd': None,  # 不自动重启
                    'critical': False
                }
            },

            # 受保护的进程 (永远不杀死)
            'protected_processes': [
                'sshd', 'systemd', 'kernel', 'init', 'kthread',
                'mysqld', 'mariadb', 'redis', 'system_watchdog'
            ],

            # 监控设置
            'monitoring': {
                'check_interval': 30,       # 检查间隔(秒)
                'grace_period': 60,         # 进程超标宽限期(秒)
                'max_kills_per_hour': 10,   # 每小时最大杀死进程数
                'enable_auto_restart': True, # 自动重启服务
                'enable_notifications': True # 启用通知
            },

            # 紧急模式阈值 (系统即将崩溃)
            'emergency_thresholds': {
                'memory_percent': 95,       # 内存使用超过95%
                'disk_percent': 95,         # 磁盘使用超过95%
                'load_average': 8.0         # 负载平均值
            },

            # 日志配置
            'logging': {
                'log_file': 'watchdog/logs/watchdog.log',
                'max_log_size_mb': 50,
                'backup_count': 3
            }
        }

        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    # 深度合并配置
                    self._deep_update(default_config, user_config)
            except Exception as e:
                print(f"配置文件加载失败: {e}, 使用默认配置")

        return default_config

    def _setup_logger(self) -> logging.Logger:
        """设置独立的日志系统"""
        logger = logging.getLogger('watchdog')
        logger.setLevel(logging.WARNING)
        logger.propagate = False  # 不传播到父logger

        # 清除已有的handler
        logger.handlers.clear()

        # 获取日志文件路径
        log_config = self.config['logging']
        log_file = log_config['log_file']

        # 如果是相对路径，相对于项目根目录
        if not os.path.isabs(log_file):
            log_file = os.path.join(PROJECT_ROOT, log_file)

        # 创建日志目录
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)

        # 文件handler - 使用RotatingFileHandler
        max_bytes = log_config['max_log_size_mb'] * 1024 * 1024
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=log_config['backup_count'],
            encoding='utf-8'
        )
        file_handler.setLevel(logging.WARNING)

        # 控制台handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)

        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> None:
        """深度更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def get_system_metrics(self) -> Dict:
        """获取系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用情况
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # 磁盘使用情况
            disk = psutil.disk_usage('/')

            # 负载平均值
            load_avg = os.getloadavg()

            # 网络连接数
            connections = len(psutil.net_connections())

            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available / (1024 * 1024),
                'swap_percent': swap.percent,
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024 * 1024 * 1024),
                'load_average': load_avg,
                'connections_count': connections,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"获取系统指标失败: {e}")
            return {}

    def get_process_info(self, pid: int) -> Optional[Dict]:
        """获取进程详细信息"""
        try:
            proc = psutil.Process(pid)

            # 获取进程基本信息
            info = {
                'pid': pid,
                'name': proc.name(),
                'cmdline': ' '.join(proc.cmdline()),
                'status': proc.status(),
                'create_time': proc.create_time(),
                'cpu_percent': proc.cpu_percent(),
                'memory_info': proc.memory_info(),
                'memory_percent': proc.memory_percent(),
                'num_threads': proc.num_threads()
            }

            # 计算运行时间
            info['runtime_hours'] = (time.time() - info['create_time']) / 3600

            return info

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def find_monitored_processes(self) -> Dict[str, List[Dict]]:
        """查找所有被监控的进程"""
        monitored = {}

        for app_name, app_config in self.config['monitored_processes'].items():
            processes = []

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])

                    # 检查是否匹配监控模式
                    for pattern in app_config['patterns']:
                        if self._match_process_pattern(cmdline, pattern):
                            proc_info = self.get_process_info(proc.info['pid'])
                            if proc_info:
                                processes.append(proc_info)
                            break

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if processes:
                monitored[app_name] = processes

        return monitored

    def _match_process_pattern(self, cmdline: str, pattern: str) -> bool:
        """匹配进程模式"""
        import re
        try:
            return bool(re.search(pattern, cmdline, re.IGNORECASE))
        except re.error:
            # 如果正则表达式无效，使用简单字符串匹配
            return pattern.lower() in cmdline.lower()

    def is_process_protected(self, proc_info: Dict, system_metrics: Optional[Dict] = None) -> bool:
        """检查进程是否受保护

        Args:
            proc_info: 进程信息
            system_metrics: 系统指标（用于条件保护判断）

        Returns:
            True 表示进程受保护，不应被杀死
        """
        name = proc_info.get('name', '').lower()
        cmdline = proc_info.get('cmdline', '').lower()

        # 检查绝对保护列表 (永远不杀死)
        for protected in self.config['protected_processes']:
            if protected.lower() in name or protected.lower() in cmdline:
                return True

        # 保护系统关键进程 (永远不杀死)
        critical_keywords = ['systemd', 'kernel', 'kthread', 'init', 'sshd']
        for keyword in critical_keywords:
            if keyword in name or keyword in cmdline:
                return True

        # 检查条件保护列表 (系统负载高时可被杀死)
        conditionally_protected = self.config.get('conditionally_protected_processes', {})
        if conditionally_protected and system_metrics:
            for pattern, thresholds in conditionally_protected.items():
                if self._match_process_pattern(cmdline, pattern) or self._match_process_pattern(name, pattern):
                    # 检查系统是否处于紧急状态
                    memory_ok = system_metrics.get('memory_percent', 0) < thresholds.get('memory_threshold_percent', 100)
                    load_ok = system_metrics.get('load_average', [0])[0] < thresholds.get('load_average_threshold', 100)

                    if memory_ok and load_ok:
                        # 系统状态良好，保护该进程
                        self.logger.info(f"条件保护生效: {name} (PID: {proc_info.get('pid')})")
                        return True
                    else:
                        # 系统处于危险状态，取消保护
                        self.logger.warning(
                            f"系统负载过高，取消条件保护: {name} (PID: {proc_info.get('pid')}), "
                            f"内存: {system_metrics.get('memory_percent', 0):.1f}% (阈值: {thresholds.get('memory_threshold_percent')}%), "
                            f"负载: {system_metrics.get('load_average', [0])[0]:.2f} (阈值: {thresholds.get('load_average_threshold')})"
                        )
                        return False

        return False

    def check_system_health(self) -> Tuple[bool, List[str]]:
        """检查系统健康状况"""
        metrics = self.get_system_metrics()
        alerts = []
        is_healthy = True

        if not metrics:
            return False, ['无法获取系统指标']

        # 检查系统阈值
        thresholds = self.config['system_thresholds']

        if metrics['cpu_percent'] > thresholds['cpu_percent']:
            alerts.append(f"CPU使用率过高: {metrics['cpu_percent']:.1f}%")
            is_healthy = False

        if metrics['memory_percent'] > thresholds['memory_percent']:
            alerts.append(f"内存使用率过高: {metrics['memory_percent']:.1f}%")
            is_healthy = False

        if metrics['disk_percent'] > thresholds['disk_percent']:
            alerts.append(f"磁盘使用率过高: {metrics['disk_percent']:.1f}%")
            is_healthy = False

        if metrics['swap_percent'] > thresholds['swap_percent']:
            alerts.append(f"交换区使用率过高: {metrics['swap_percent']:.1f}%")
            is_healthy = False

        # 检查紧急阈值
        emergency = self.config['emergency_thresholds']
        if (metrics['memory_percent'] > emergency['memory_percent'] or
            metrics['disk_percent'] > emergency['disk_percent'] or
            metrics['load_average'][0] > emergency['load_average']):
            alerts.append("⚠️ 系统进入紧急状态，需要立即处理")
            is_healthy = False

        return is_healthy, alerts

    def find_high_usage_processes(self, system_metrics: Optional[Dict] = None) -> List[Dict]:
        """查找高资源使用的进程

        Args:
            system_metrics: 系统指标，用于条件保护判断
        """
        high_usage = []
        thresholds = self.config['process_thresholds']

        # 如果没有提供系统指标，获取当前指标
        if system_metrics is None:
            system_metrics = self.get_system_metrics()

        for proc in psutil.process_iter():
            try:
                proc_info = self.get_process_info(proc.pid)
                if not proc_info:
                    continue

                # 跳过受保护的进程（传入系统指标用于条件保护判断）
                if self.is_process_protected(proc_info, system_metrics):
                    continue

                # 检查是否超过阈值
                cpu_high = proc_info['cpu_percent'] > thresholds['cpu_percent']
                memory_mb = proc_info['memory_info'].rss / (1024 * 1024)
                memory_high = (memory_mb > thresholds['memory_mb'] or
                              proc_info['memory_percent'] > thresholds['memory_percent'])

                if cpu_high or memory_high:
                    proc_info['violation_reasons'] = []
                    if cpu_high:
                        proc_info['violation_reasons'].append(f"CPU: {proc_info['cpu_percent']:.1f}%")
                    if memory_high:
                        proc_info['violation_reasons'].append(f"内存: {memory_mb:.1f}MB ({proc_info['memory_percent']:.1f}%)")

                    high_usage.append(proc_info)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # 按资源使用率排序
        high_usage.sort(key=lambda x: x['cpu_percent'] + x['memory_percent'], reverse=True)
        return high_usage

    def kill_process_safely(self, pid: int, name: str, system_metrics: Optional[Dict] = None) -> bool:
        """安全杀死进程

        Args:
            pid: 进程ID
            name: 进程名称
            system_metrics: 系统指标，用于条件保护判断
        """
        try:
            proc = psutil.Process(pid)

            # 如果没有提供系统指标，获取当前指标
            if system_metrics is None:
                system_metrics = self.get_system_metrics()

            # 最后确认不是保护进程（传入系统指标用于条件保护判断）
            proc_info = self.get_process_info(pid)
            if proc_info and self.is_process_protected(proc_info, system_metrics):
                self.logger.warning(f"跳过受保护的进程: {name} (PID: {pid})")
                return False

            # 先尝试温和终止
            proc.terminate()

            # 等待进程结束
            try:
                proc.wait(timeout=10)
                self.logger.warning(f"成功终止进程: {name} (PID: {pid})")
                return True
            except psutil.TimeoutExpired:
                # 强制杀死
                proc.kill()
                self.logger.warning(f"强制杀死进程: {name} (PID: {pid})")
                return True

        except psutil.NoSuchProcess:
            self.logger.warning(f"进程已不存在: {name} (PID: {pid})")
            return True
        except Exception as e:
            self.logger.error(f"杀死进程失败: {name} (PID: {pid}), 错误: {e}")
            return False

    def restart_service(self, service_name: str, restart_cmd: str) -> bool:
        """重启服务"""
        try:
            if not self.config['monitoring']['enable_auto_restart']:
                self.logger.warning(f"自动重启已禁用，跳过重启服务: {service_name}")
                return False

            self.logger.warning(f"重启服务: {service_name}, 命令: {restart_cmd}")

            # 切换到项目目录
            os.chdir(PROJECT_ROOT)

            # 执行重启命令
            result = subprocess.run(
                restart_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self.logger.warning(f"服务重启成功: {service_name}")
                self.stats['services_restarted'] += 1
                return True
            else:
                self.logger.error(f"服务重启失败: {service_name}, 错误: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"重启服务异常: {service_name}, 错误: {e}")
            return False

    def handle_high_usage_processes(self, system_metrics: Optional[Dict] = None) -> int:
        """处理高资源使用的进程

        Args:
            system_metrics: 系统指标，用于条件保护判断
        """
        killed_count = 0
        max_kills = self.config['monitoring']['max_kills_per_hour']

        if self.stats['processes_killed'] >= max_kills:
            self.logger.warning(f"已达到每小时最大杀死进程数限制: {max_kills}")
            return 0

        # 如果没有提供系统指标，获取当前指标
        if system_metrics is None:
            system_metrics = self.get_system_metrics()

        high_usage = self.find_high_usage_processes(system_metrics)

        for proc_info in high_usage[:5]:  # 最多处理5个进程
            if killed_count >= max_kills:
                break

            pid = proc_info['pid']
            name = proc_info['name']
            reasons = ', '.join(proc_info['violation_reasons'])

            self.logger.warning(f"发现高资源使用进程: {name} (PID: {pid}), 原因: {reasons}")

            if self.kill_process_safely(pid, name, system_metrics):
                killed_count += 1
                self.stats['processes_killed'] += 1

                # 等待一会再处理下一个
                time.sleep(2)

        return killed_count

    def check_and_restart_services(self, system_metrics: Optional[Dict] = None) -> int:
        """检查并重启关键服务

        Args:
            system_metrics: 系统指标，用于条件保护判断
        """
        restarted_count = 0
        monitored = self.find_monitored_processes()

        # 如果没有提供系统指标，获取当前指标
        if system_metrics is None:
            system_metrics = self.get_system_metrics()

        for service_name, service_config in self.config['monitored_processes'].items():
            if not service_config.get('critical', False):
                continue

            processes = monitored.get(service_name, [])

            # 检查服务是否运行
            if not processes:
                if service_config.get('restart_cmd'):
                    self.logger.warning(f"关键服务未运行: {service_name}")
                    if self.restart_service(service_name, service_config['restart_cmd']):
                        restarted_count += 1
                continue

            # 检查是否有进程超过服务特定阈值
            for proc_info in processes:
                cpu_high = proc_info['cpu_percent'] > service_config.get('max_cpu', 100)
                memory_mb = proc_info['memory_info'].rss / (1024 * 1024)
                memory_high = memory_mb > service_config.get('max_memory_mb', 1000)

                if cpu_high or memory_high:
                    self.logger.warning(f"服务 {service_name} 进程异常: PID {proc_info['pid']}, "
                                      f"CPU: {proc_info['cpu_percent']:.1f}%, 内存: {memory_mb:.1f}MB")

                    # 杀死异常进程（传入系统指标用于条件保护判断）
                    if self.kill_process_safely(proc_info['pid'], proc_info['name'], system_metrics):
                        # 等待并重启服务
                        time.sleep(5)
                        if service_config.get('restart_cmd'):
                            if self.restart_service(service_name, service_config['restart_cmd']):
                                restarted_count += 1
                        break

        return restarted_count

    def generate_report(self) -> Dict:
        """生成监控报告"""
        metrics = self.get_system_metrics()
        monitored = self.find_monitored_processes()
        high_usage = self.find_high_usage_processes()

        report = {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': metrics,
            'watchdog_stats': self.stats.copy(),
            'monitored_processes': {
                name: len(processes)
                for name, processes in monitored.items()
            },
            'high_usage_processes': len(high_usage),
            'top_processes': high_usage[:3] if high_usage else []
        }

        return report

    def run_single_check(self) -> Dict:
        """执行单次检查"""
        self.logger.info("开始系统健康检查...")

        start_time = time.time()
        self.stats['checks_performed'] += 1
        self.stats['last_check'] = datetime.now().isoformat()

        # 获取系统指标（用于条件保护判断）
        system_metrics = self.get_system_metrics()

        # 检查系统健康状况
        is_healthy, alerts = self.check_system_health()

        actions_taken = []

        if not is_healthy:
            self.logger.warning(f"系统健康检查失败: {'; '.join(alerts)}")

            # 处理高资源使用进程（传入系统指标）
            killed = self.handle_high_usage_processes(system_metrics)
            if killed > 0:
                actions_taken.append(f"杀死 {killed} 个高资源使用进程")

            # 检查并重启服务（传入系统指标）
            restarted = self.check_and_restart_services(system_metrics)
            if restarted > 0:
                actions_taken.append(f"重启 {restarted} 个服务")

        # 生成报告
        report = self.generate_report()
        report['health_check'] = {
            'is_healthy': is_healthy,
            'alerts': alerts,
            'actions_taken': actions_taken,
            'check_duration': time.time() - start_time
        }

        if actions_taken:
            self.logger.info(f"检查完成，执行了操作: {'; '.join(actions_taken)}")
        else:
            self.logger.info("系统检查完成，状态正常")

        return report

    def run_daemon(self, check_interval: Optional[int] = None):
        """运行监控守护进程"""
        interval = check_interval or self.config['monitoring']['check_interval']

        self.logger.info(f"系统监控守护进程启动，检查间隔: {interval}秒")

        try:
            while True:
                try:
                    report = self.run_single_check()

                    # 可选：保存报告到文件
                    # self._save_report(report)

                except KeyboardInterrupt:
                    self.logger.info("收到中断信号，停止监控")
                    break
                except Exception as e:
                    self.logger.error(f"监控检查异常: {e}", exc_info=True)

                time.sleep(interval)

        except Exception as e:
            self.logger.critical(f"守护进程异常退出: {e}", exc_info=True)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='系统资源监控和保护脚本')
    parser.add_argument('--daemon', action='store_true', help='以守护进程模式运行')
    parser.add_argument('--check-once', action='store_true', help='执行单次检查')
    parser.add_argument('--kill-high-usage', action='store_true', help='杀死高资源使用进程')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--interval', type=int, default=30, help='检查间隔(秒)')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行，不执行实际操作')

    args = parser.parse_args()

    # 创建监控实例
    watchdog = SystemWatchdog(config_file=args.config)

    if args.dry_run:
        watchdog.logger.info("模拟运行模式，不会执行实际的杀死或重启操作")
        # 可以添加模拟模式的逻辑

    try:
        if args.daemon:
            watchdog.run_daemon(check_interval=args.interval)
        elif args.check_once:
            report = watchdog.run_single_check()
            print(json.dumps(report, indent=2, ensure_ascii=False))
        elif args.kill_high_usage:
            killed = watchdog.handle_high_usage_processes()
            print(f"杀死了 {killed} 个高资源使用进程")
        else:
            # 默认显示系统状态
            metrics = watchdog.get_system_metrics()
            monitored = watchdog.find_monitored_processes()
            high_usage = watchdog.find_high_usage_processes()

            print("=== 系统状态 ===")
            print(f"CPU: {metrics.get('cpu_percent', 0):.1f}%")
            print(f"内存: {metrics.get('memory_percent', 0):.1f}%")
            print(f"磁盘: {metrics.get('disk_percent', 0):.1f}%")
            print(f"负载: {metrics.get('load_average', [0])[0]:.2f}")

            print(f"\n=== 监控进程 ===")
            for name, processes in monitored.items():
                print(f"{name}: {len(processes)} 个进程")

            print(f"\n=== 高资源使用进程 ===")
            for proc in high_usage[:5]:
                reasons = ', '.join(proc.get('violation_reasons', []))
                print(f"PID {proc['pid']}: {proc['name']} - {reasons}")

    except KeyboardInterrupt:
        print("\n监控已停止")
    except Exception as e:
        print(f"运行异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()