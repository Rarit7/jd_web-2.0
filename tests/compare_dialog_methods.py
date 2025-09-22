#!/usr/bin/env python3
"""
脚本名称: compare_dialog_methods.py
功能描述: 对比get_dialog_list和原始iter_dialogs方法的结果，分析是否存在缺漏
作者: Claude Code
创建时间: 2025-09-22
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jd.services.spider.tg import TgService
from jd import app
from telethon.tl.types import Channel, Chat, User

# 配置日志输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_dialogs_by_get_dialog_list(session_name='default2'):
    """
    使用get_dialog_list方法获取对话列表
    """
    try:
        with app.app_context():
            logger.info(f"开始使用get_dialog_list方法获取对话列表")

            tg_client = await TgService.init_tg(sessionname=session_name)
            if tg_client is None:
                logger.error(f"Session '{session_name}' 初始化失败")
                return None

            dialogs = []
            async for dialog_info in tg_client.get_dialog_list():
                if dialog_info.get('data'):
                    dialogs.append({
                        'id': dialog_info['data']['id'],
                        'title': dialog_info['data'].get('title', ''),
                        'username': dialog_info['data'].get('username'),
                        'group_type': dialog_info['data'].get('group_type', ''),
                        'megagroup': dialog_info['data'].get('megagroup', ''),
                        'member_count': dialog_info['data'].get('member_count', 0),
                        'unread_count': dialog_info['data'].get('unread_count', 0),
                        'is_public': dialog_info['data'].get('is_public', 0),
                        'join_date': dialog_info['data'].get('join_date', ''),
                        'source': 'get_dialog_list'
                    })

            await tg_client.close_client()
            logger.info(f"get_dialog_list方法获取到 {len(dialogs)} 个对话")
            return dialogs

    except Exception as e:
        logger.error(f"get_dialog_list方法执行失败: {e}")
        return None


async def get_dialogs_by_iter_dialogs(session_name='default2'):
    """
    使用原始iter_dialogs方法获取对话列表
    """
    try:
        with app.app_context():
            logger.info(f"开始使用原始iter_dialogs方法获取对话列表")

            tg_client = await TgService.init_tg(sessionname=session_name)
            if tg_client is None:
                logger.error(f"Session '{session_name}' 初始化失败")
                return None

            raw_client = tg_client.client
            dialogs = []

            async for dialog in raw_client.iter_dialogs():
                entity = dialog.entity

                # 基本信息
                dialog_info = {
                    'id': entity.id,
                    'unread_count': dialog.unread_count,
                    'dialog_type': type(entity).__name__,
                    'date': dialog.date.strftime("%Y-%m-%d %H:%M:%S+%Z") if dialog.date else 'N/A',
                    'source': 'iter_dialogs'
                }

                # 根据实体类型获取详细信息
                if isinstance(entity, Channel):
                    dialog_info.update({
                        'title': getattr(entity, 'title', ''),
                        'username': getattr(entity, 'username', None),
                        'megagroup': getattr(entity, 'megagroup', False),
                        'broadcast': getattr(entity, 'broadcast', False),
                        'group_type': 'group' if getattr(entity, 'megagroup', False) else 'channel',
                        'is_public': 1 if getattr(entity, 'username', None) else 0
                    })
                elif isinstance(entity, Chat):
                    dialog_info.update({
                        'title': getattr(entity, 'title', ''),
                        'username': None,
                        'megagroup': True,
                        'group_type': 'chat',
                        'is_public': 0,
                        'participants_count': getattr(entity, 'participants_count', 0)
                    })
                elif isinstance(entity, User):
                    dialog_info.update({
                        'title': f"{getattr(entity, 'first_name', '')} {getattr(entity, 'last_name', '')}".strip(),
                        'username': getattr(entity, 'username', None),
                        'group_type': 'user',
                        'is_public': 1 if getattr(entity, 'username', None) else 0,
                        'bot': getattr(entity, 'bot', False)
                    })

                dialogs.append(dialog_info)

            await tg_client.close_client()
            logger.info(f"iter_dialogs方法获取到 {len(dialogs)} 个对话")
            return dialogs

    except Exception as e:
        logger.error(f"iter_dialogs方法执行失败: {e}")
        return None


def analyze_differences(get_dialog_list_results, iter_dialogs_results):
    """
    分析两种方法的差异
    """
    print("\n" + "="*80)
    print("对话列表方法对比分析")
    print("="*80)

    if not get_dialog_list_results or not iter_dialogs_results:
        print("错误: 无法获取完整的对话列表进行对比")
        return

    # 统计数据
    get_dialog_count = len(get_dialog_list_results)
    iter_dialog_count = len(iter_dialogs_results)

    print(f"\n基本统计:")
    print(f"get_dialog_list方法获取: {get_dialog_count} 个对话")
    print(f"iter_dialogs方法获取:   {iter_dialog_count} 个对话")
    print(f"差异: {abs(get_dialog_count - iter_dialog_count)} 个对话")

    # 创建ID集合进行对比
    get_dialog_ids = {dialog['id'] for dialog in get_dialog_list_results}
    iter_dialog_ids = {dialog['id'] for dialog in iter_dialogs_results}

    # 找出缺失的对话
    missing_in_get_dialog = iter_dialog_ids - get_dialog_ids
    missing_in_iter_dialog = get_dialog_ids - iter_dialog_ids

    print(f"\n缺失分析:")
    print(f"get_dialog_list中缺失的对话: {len(missing_in_get_dialog)} 个")
    print(f"iter_dialogs中缺失的对话:   {len(missing_in_iter_dialog)} 个")

    # 详细分析get_dialog_list中缺失的对话
    if missing_in_get_dialog:
        print(f"\nget_dialog_list方法中缺失的对话 ({len(missing_in_get_dialog)} 个):")
        print("-" * 80)

        # 按类型分类
        missing_by_type = {}
        for dialog_id in missing_in_get_dialog:
            # 找到对应的对话信息
            dialog_info = next((d for d in iter_dialogs_results if d['id'] == dialog_id), None)
            if dialog_info:
                dialog_type = dialog_info['dialog_type']
                if dialog_type not in missing_by_type:
                    missing_by_type[dialog_type] = []
                missing_by_type[dialog_type].append(dialog_info)

        for dialog_type, dialogs in missing_by_type.items():
            print(f"\n{dialog_type} 类型 ({len(dialogs)} 个):")
            for i, dialog in enumerate(dialogs, 1):
                title = dialog.get('title', 'N/A')
                username = f"@{dialog.get('username')}" if dialog.get('username') else "无用户名"
                unread = dialog.get('unread_count', 0)

                # 分析可能的原因
                reason = []
                if dialog_type == 'User':
                    reason.append("个人对话")
                if unread == 0:
                    reason.append("无未读消息")
                if not dialog.get('title'):
                    reason.append("无标题")

                reason_str = f" [可能原因: {', '.join(reason)}]" if reason else ""

                print(f"  {i:2d}. {title} ({username}) - ID: {dialog['id']}, 未读: {unread}{reason_str}")

    # 详细分析iter_dialogs中缺失的对话
    if missing_in_iter_dialog:
        print(f"\niter_dialogs方法中缺失的对话 ({len(missing_in_iter_dialog)} 个):")
        print("-" * 80)
        for dialog_id in missing_in_iter_dialog:
            dialog_info = next((d for d in get_dialog_list_results if d['id'] == dialog_id), None)
            if dialog_info:
                title = dialog_info.get('title', 'N/A')
                username = f"@{dialog_info.get('username')}" if dialog_info.get('username') else "无用户名"
                print(f"  - {title} ({username}) - ID: {dialog_id}")

    # 分析get_dialog_list的过滤逻辑
    print(f"\nget_dialog_list过滤逻辑分析:")
    print("-" * 80)

    # 统计iter_dialogs中各类型的数量
    iter_types = {}
    for dialog in iter_dialogs_results:
        dialog_type = dialog['dialog_type']
        if dialog_type not in iter_types:
            iter_types[dialog_type] = 0
        iter_types[dialog_type] += 1

    # 统计get_dialog_list中各类型的数量
    get_types = {}
    for dialog in get_dialog_list_results:
        group_type = dialog.get('group_type', 'unknown')
        if group_type not in get_types:
            get_types[group_type] = 0
        get_types[group_type] += 1

    print("iter_dialogs结果分类:")
    for type_name, count in sorted(iter_types.items()):
        print(f"  {type_name}: {count} 个")

    print("\nget_dialog_list结果分类:")
    for type_name, count in sorted(get_types.items()):
        print(f"  {type_name}: {count} 个")

    # 分析过滤规则
    print(f"\n过滤规则分析:")
    user_dialogs_count = iter_types.get('User', 0)
    if user_dialogs_count > 0 and 'user' not in get_types:
        print(f"✓ get_dialog_list过滤了所有 {user_dialogs_count} 个用户对话")

    # 检查是否有hasattr(dialog.entity, "title")的过滤逻辑
    dialogs_without_title = 0
    for dialog in iter_dialogs_results:
        if not dialog.get('title') or dialog.get('title').strip() == '':
            dialogs_without_title += 1

    if dialogs_without_title > 0:
        print(f"✓ 有 {dialogs_without_title} 个对话没有标题，可能被get_dialog_list过滤")

    # 共同对话的详细对比
    common_ids = get_dialog_ids & iter_dialog_ids
    if common_ids:
        print(f"\n共同对话详细对比 ({len(common_ids)} 个):")
        print("-" * 80)

        differences_found = False
        for dialog_id in list(common_ids)[:5]:  # 只显示前5个的详细对比
            get_dialog = next((d for d in get_dialog_list_results if d['id'] == dialog_id), None)
            iter_dialog = next((d for d in iter_dialogs_results if d['id'] == dialog_id), None)

            if get_dialog and iter_dialog:
                print(f"\n对话ID: {dialog_id}")
                print(f"  标题: {get_dialog.get('title', 'N/A')}")

                # 比较关键字段
                fields_to_compare = ['username', 'unread_count', 'group_type']
                for field in fields_to_compare:
                    get_val = get_dialog.get(field, 'N/A')
                    iter_val = iter_dialog.get(field, 'N/A')
                    if get_val != iter_val:
                        print(f"  {field}差异: get_dialog_list='{get_val}' vs iter_dialogs='{iter_val}'")
                        differences_found = True

        if not differences_found:
            print("  前5个共同对话的关键字段完全一致")

    # 保存详细对比结果
    comparison_result = {
        'timestamp': datetime.now().isoformat(),
        'session_name': 'default2',
        'statistics': {
            'get_dialog_list_count': get_dialog_count,
            'iter_dialogs_count': iter_dialog_count,
            'missing_in_get_dialog_list': len(missing_in_get_dialog),
            'missing_in_iter_dialogs': len(missing_in_iter_dialog),
            'common_dialogs': len(common_ids)
        },
        'missing_in_get_dialog_list': [d for d in iter_dialogs_results if d['id'] in missing_in_get_dialog],
        'missing_in_iter_dialogs': [d for d in get_dialog_list_results if d['id'] in missing_in_iter_dialog],
        'get_dialog_list_results': get_dialog_list_results,
        'iter_dialogs_results': iter_dialogs_results
    }

    output_file = f'dialog_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n详细对比结果已保存到: {output_file}")

    return comparison_result


async def main():
    """
    主函数：执行对比分析
    """
    print("Telegram对话列表方法对比分析工具")
    print("对比get_dialog_list方法与原始iter_dialogs方法的结果")

    session_name = 'default2'
    if len(sys.argv) > 1:
        session_name = sys.argv[1]

    # 初始化应用
    app.ready(db_switch=False, web_switch=False, worker_switch=False, socketio_switch=False)

    print(f"\n使用session: {session_name}")
    print("开始获取两种方法的对话列表...")

    # 获取两种方法的结果
    print("\n1. 使用get_dialog_list方法...")
    get_dialog_results = await get_dialogs_by_get_dialog_list(session_name)

    print("\n2. 使用原始iter_dialogs方法...")
    iter_dialog_results = await get_dialogs_by_iter_dialogs(session_name)

    # 分析差异
    if get_dialog_results and iter_dialog_results:
        analyze_differences(get_dialog_results, iter_dialog_results)
    else:
        print("错误: 无法获取完整的对话列表进行对比")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"程序执行失败: {e}")
        sys.exit(1)