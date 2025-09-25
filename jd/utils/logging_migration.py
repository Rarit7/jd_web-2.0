"""
日志系统迁移工具
自动将旧的logging系统迁移到新的统一日志系统
"""

import os
import re
from typing import List, Tuple, Dict


class LoggingMigrationTool:
    """日志系统迁移工具"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.patterns = {
            # 匹配 import logging
            'import_logging': re.compile(r'^import logging$', re.MULTILINE),

            # 匹配 logger = logging.getLogger(__name__)
            'old_logger_declaration': re.compile(r'^logger = logging\.getLogger\(__name__\)$', re.MULTILINE),

            # 匹配 logger = logging.getLogger('name')
            'old_logger_declaration_named': re.compile(r'^logger = logging\.getLogger\([\'"]([^\'"]*)[\'\"]\)$', re.MULTILINE),

            # 匹配 print() 语句
            'print_statements': re.compile(r'print\s*\(([^)]+)\)', re.MULTILINE),
        }

    def find_files_to_migrate(self) -> List[str]:
        """找出需要迁移的Python文件"""
        files_to_migrate = []

        for root, dirs, files in os.walk(os.path.join(self.project_root, 'jd')):
            # 跳过已经迁移的文件
            if 'logging_config.py' in root or '__pycache__' in root:
                continue

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    if self._needs_migration(file_path):
                        files_to_migrate.append(file_path)

        return files_to_migrate

    def _needs_migration(self, file_path: str) -> bool:
        """检查文件是否需要迁移"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查是否已经使用新日志系统
            if 'from jd.utils.logging_config import' in content:
                return False

            # 检查是否使用旧日志系统或print语句
            return (
                self.patterns['old_logger_declaration'].search(content) or
                self.patterns['old_logger_declaration_named'].search(content) or
                self.patterns['import_logging'].search(content)
            )
        except Exception:
            return False

    def generate_migration_plan(self) -> Dict[str, List[str]]:
        """生成迁移计划"""
        files_to_migrate = self.find_files_to_migrate()

        plan = {
            'telegram_jobs': [],
            'telegram_tasks': [],
            'services': [],
            'api_views': [],
            'other': []
        }

        for file_path in files_to_migrate:
            relative_path = os.path.relpath(file_path, self.project_root)

            if 'jobs/tg_' in relative_path:
                plan['telegram_jobs'].append(relative_path)
            elif 'tasks/telegram' in relative_path:
                plan['telegram_tasks'].append(relative_path)
            elif 'services/' in relative_path:
                plan['services'].append(relative_path)
            elif 'views/api' in relative_path:
                plan['api_views'].append(relative_path)
            else:
                plan['other'].append(relative_path)

        return plan

    def migrate_single_file(self, file_path: str, component_type: str = 'general') -> str:
        """迁移单个文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 确定组件类型和模块名
        relative_path = os.path.relpath(file_path, self.project_root)
        module_name = self._get_module_name(relative_path)
        component_config = self._get_component_config(relative_path)

        # 1. 替换import语句
        content = self._replace_import_statements(content)

        # 2. 替换logger声明
        content = self._replace_logger_declaration(content, module_name, component_config)

        # 3. 可选：替换print语句（谨慎操作）
        # content = self._replace_print_statements(content)

        return content

    def _get_module_name(self, relative_path: str) -> str:
        """从文件路径获取模块名"""
        return relative_path.replace('/', '.').replace('.py', '')

    def _get_component_config(self, relative_path: str) -> str:
        """根据路径确定组件配置"""
        configs = {
            'telegram': "{'component': 'telegram', 'module': '%s'}",
            'spider': "{'component': 'spider', 'module': '%s'}",
            'api': "{'component': 'api', 'module': '%s'}",
            'task': "{'component': 'task', 'module': '%s'}",
            'job': "{'component': 'job', 'module': '%s'}",
        }

        for key, config in configs.items():
            if key in relative_path.lower() or f'{key}s/' in relative_path:
                module_part = os.path.basename(relative_path).replace('.py', '')
                return config % module_part

        return "{}"

    def _replace_import_statements(self, content: str) -> str:
        """替换import语句"""
        # 替换import logging
        content = self.patterns['import_logging'].sub(
            'from jd.utils.logging_config import get_logger',
            content
        )

        return content

    def _replace_logger_declaration(self, content: str, module_name: str, component_config: str) -> str:
        """替换logger声明"""
        # 替换标准形式: logger = logging.getLogger(__name__)
        new_declaration = f"logger = get_logger('{module_name}', {component_config})"
        content = self.patterns['old_logger_declaration'].sub(new_declaration, content)

        # 替换命名形式: logger = logging.getLogger('name')
        def replace_named_logger(match):
            logger_name = match.group(1)
            return f"logger = get_logger('{logger_name}', {component_config})"

        content = self.patterns['old_logger_declaration_named'].sub(replace_named_logger, content)

        return content

    def _replace_print_statements(self, content: str) -> str:
        """替换print语句为logger.info (需要手动review)"""
        def replace_print(match):
            print_content = match.group(1)
            # 简单的print语句转换，复杂的需要手动处理
            if '"' in print_content or "'" in print_content:
                return f"logger.info({print_content})"
            else:
                return f"logger.info(f'{{{print_content}}}')"

        return self.patterns['print_statements'].sub(replace_print, content)


def generate_migration_report():
    """生成迁移报告"""
    project_root = '/home/ec2-user/workspace/jd_web'
    tool = LoggingMigrationTool(project_root)

    plan = tool.generate_migration_plan()

    report = []
    report.append("# 日志系统迁移报告")
    report.append("")
    report.append("## 📊 迁移统计")

    total_files = sum(len(files) for files in plan.values())
    report.append(f"- **总计需要迁移**: {total_files} 个文件")
    report.append("")

    report.append("## 📂 分类迁移计划")
    report.append("")

    categories = {
        'telegram_jobs': ('🤖 Telegram Jobs', '高优先级 - 核心业务逻辑'),
        'telegram_tasks': ('⚡ Telegram Tasks', '高优先级 - 异步任务'),
        'services': ('🔧 Services', '中优先级 - 服务层'),
        'api_views': ('🌐 API Views', '中优先级 - API接口'),
        'other': ('📄 Other', '低优先级 - 其他模块')
    }

    for category, files in plan.items():
        if files:
            title, priority = categories.get(category, (category, ''))
            report.append(f"### {title} ({priority})")
            report.append(f"文件数量: {len(files)}")
            report.append("")
            for file_path in sorted(files):
                report.append(f"- `{file_path}`")
            report.append("")

    report.append("## 🎯 迁移策略")
    report.append("")
    report.append("### Phase 1: 核心Telegram模块")
    report.append("优先迁移telegram_jobs和telegram_tasks，影响最大的核心业务")
    report.append("")
    report.append("### Phase 2: 服务和API层")
    report.append("迁移services和api_views，确保接口层日志统一")
    report.append("")
    report.append("### Phase 3: 其他模块")
    report.append("处理剩余模块，完成全面迁移")
    report.append("")

    report.append("## ⚠️ 注意事项")
    report.append("")
    report.append("1. **逐步迁移**: 一次迁移一个模块，测试后再继续")
    report.append("2. **保留备份**: 迁移前备份原文件")
    report.append("3. **测试验证**: 每次迁移后运行相关测试")
    report.append("4. **print语句**: 手动review和替换，避免自动化错误")

    return '\n'.join(report)


if __name__ == "__main__":
    print(generate_migration_report())