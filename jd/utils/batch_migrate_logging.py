#!/usr/bin/env python3
"""
批量迁移日志系统脚本
自动处理剩余的日志系统迁移任务
"""

import os
import re
from typing import Dict, List


class BatchLoggingMigrator:
    """批量日志迁移工具"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.migration_map = {
            # Telegram Jobs
            'jd/jobs/tg_file_info.py': {
                'component': 'telegram',
                'module': 'file_info'
            },
            'jd/jobs/tg_person_dialog.py': {
                'component': 'telegram',
                'module': 'person_dialog'
            },
            'jd/jobs/tg_daily_backup_manager.py': {
                'component': 'telegram',
                'module': 'daily_backup_manager'
            },

            # Telegram Tasks
            'jd/tasks/telegram/session_lock.py': {
                'component': 'telegram',
                'module': 'session_lock'
            },
            'jd/tasks/telegram/tg.py': {
                'component': 'telegram',
                'module': 'tg_tasks'
            },
            'jd/tasks/telegram/tg_daily_backup.py': {
                'component': 'telegram',
                'module': 'daily_backup'
            },
            'jd/tasks/telegram/tg_download_file.py': {
                'component': 'telegram',
                'module': 'download_file'
            },
            'jd/tasks/telegram/tg_fetch_group_info.py': {
                'component': 'telegram',
                'module': 'fetch_group_info'
            },
            'jd/tasks/telegram/tg_join_group.py': {
                'component': 'telegram',
                'module': 'join_group'
            },

            # Services
            'jd/services/spider/tg.py': {
                'component': 'spider',
                'module': 'tg_service'
            },
            'jd/services/spider/tg_download.py': {
                'component': 'spider',
                'module': 'tg_download'
            },
            'jd/services/spider/telegram_spider.py': {
                'component': 'spider',
                'module': 'telegram_spider'
            },
            'jd/services/ftp.py': {
                'component': 'service',
                'module': 'ftp'
            },
            'jd/services/proxy.py': {
                'component': 'service',
                'module': 'proxy'
            },

            # API Views
            'jd/views/api/tg/chat_history.py': {
                'component': 'api',
                'module': 'chat_history_api'
            },
            'jd/views/api/system/settings.py': {
                'component': 'api',
                'module': 'settings_api'
            },
        }

    def migrate_file(self, file_path: str) -> bool:
        """迁移单个文件"""
        full_path = os.path.join(self.project_root, file_path)

        if not os.path.exists(full_path):
            print(f"⚠️  文件不存在: {file_path}")
            return False

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查是否已经迁移
            if 'from jd.utils.logging_config import' in content:
                print(f"✅ 已迁移: {file_path}")
                return True

            # 获取组件配置
            config = self.migration_map.get(file_path, {
                'component': 'general',
                'module': os.path.basename(file_path).replace('.py', '')
            })

            # 生成logger名称
            logger_name = self._generate_logger_name(file_path)

            # 执行迁移
            new_content = self._transform_content(content, logger_name, config)

            # 写回文件
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print(f"✅ 迁移完成: {file_path}")
            return True

        except Exception as e:
            print(f"❌ 迁移失败: {file_path} - {e}")
            return False

    def _generate_logger_name(self, file_path: str) -> str:
        """生成logger名称"""
        # 将路径转换为模块名
        module_path = file_path.replace('/', '.').replace('.py', '')

        # 特殊处理
        if module_path.startswith('jd.tasks.telegram'):
            module_path = module_path.replace('jd.tasks.telegram', 'jd.tasks.tg')
        elif module_path.startswith('jd.jobs.tg_'):
            module_path = module_path.replace('jd.jobs.tg_', 'jd.jobs.tg.')

        return module_path

    def _transform_content(self, content: str, logger_name: str, config: Dict) -> str:
        """转换文件内容"""
        lines = content.split('\n')
        new_lines = []

        import_added = False
        logger_replaced = False

        for line in lines:
            # 处理import logging
            if line.strip() == 'import logging':
                if not import_added:
                    new_lines.append('from jd.utils.logging_config import get_logger')
                    import_added = True
                continue

            # 处理logger声明
            if re.match(r'^logger = logging\.getLogger\(.*\)$', line.strip()):
                if not logger_replaced:
                    component = config['component']
                    module = config['module']
                    new_lines.append(f"logger = get_logger('{logger_name}', {{'component': '{component}', 'module': '{module}'}})")
                    logger_replaced = True
                continue

            new_lines.append(line)

        # 如果没有找到import，在合适位置添加
        if not import_added:
            # 找到最后一个import的位置
            for i, line in enumerate(new_lines):
                if line.startswith('from jd.') or line.startswith('from jd '):
                    new_lines.insert(i + 1, 'from jd.utils.logging_config import get_logger')
                    break

        return '\n'.join(new_lines)

    def migrate_priority_files(self) -> Dict[str, bool]:
        """迁移高优先级文件"""
        priority_files = [
            # Phase 1: 核心Telegram模块
            'jd/jobs/tg_file_info.py',
            'jd/jobs/tg_person_dialog.py',
            'jd/jobs/tg_daily_backup_manager.py',
            'jd/tasks/telegram/session_lock.py',
            'jd/tasks/telegram/tg.py',
            'jd/tasks/telegram/tg_daily_backup.py',
            'jd/tasks/telegram/tg_download_file.py',
            'jd/tasks/telegram/tg_fetch_group_info.py',
            'jd/tasks/telegram/tg_join_group.py',
        ]

        results = {}
        for file_path in priority_files:
            results[file_path] = self.migrate_file(file_path)

        return results


def main():
    """主函数"""
    project_root = '/home/ec2-user/workspace/jd_web'
    migrator = BatchLoggingMigrator(project_root)

    print("🚀 开始批量迁移日志系统...")
    print("=" * 50)

    # 迁移高优先级文件
    results = migrator.migrate_priority_files()

    # 统计结果
    successful = sum(1 for success in results.values() if success)
    total = len(results)

    print("=" * 50)
    print(f"📊 迁移完成: {successful}/{total} 个文件成功迁移")

    if successful < total:
        print("\n❌ 失败的文件:")
        for file_path, success in results.items():
            if not success:
                print(f"  - {file_path}")

    print("\n✅ 建议下一步:")
    print("1. 测试迁移后的模块功能")
    print("2. 运行相关测试用例")
    print("3. 检查日志输出格式")
    print("4. 继续迁移剩余模块")


if __name__ == "__main__":
    main()