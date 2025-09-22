#!/usr/bin/env python3
"""
脚本名称: compare_three_dialog_methods.py
功能描述: 对比三种方法获取对话列表：get_dialog_list、iter_dialogs、get_dialogs
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
            logger.info(f"开始使用iter_dialogs方法获取对话列表")

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


async def get_dialogs_by_get_dialogs(session_name='default2'):
    """
    使用Telethon的get_dialogs方法获取对话列表
    """
    try:
        with app.app_context():
            logger.info(f"开始使用get_dialogs方法获取对话列表")

            tg_client = await TgService.init_tg(sessionname=session_name)
            if tg_client is None:
                logger.error(f"Session '{session_name}' 初始化失败")
                return None

            raw_client = tg_client.client
            dialogs = []

            # 使用get_dialogs方法一次性获取所有对话
            # limit=None表示获取所有对话
            telegram_dialogs = await raw_client.get_dialogs(limit=None)

            for dialog in telegram_dialogs:
                entity = dialog.entity

                # 基本信息
                dialog_info = {
                    'id': entity.id,
                    'unread_count': dialog.unread_count,
                    'dialog_type': type(entity).__name__,
                    'date': dialog.date.strftime("%Y-%m-%d %H:%M:%S+%Z") if dialog.date else 'N/A',
                    'source': 'get_dialogs',
                    'is_pinned': getattr(dialog, 'pinned', False),
                    'dialog_attributes': [attr for attr in dir(dialog) if not attr.startswith('_')][:10]  # 用于调试
                }

                # 根据实体类型获取详细信息
                if isinstance(entity, Channel):
                    dialog_info.update({
                        'title': getattr(entity, 'title', ''),
                        'username': getattr(entity, 'username', None),
                        'megagroup': getattr(entity, 'megagroup', False),
                        'broadcast': getattr(entity, 'broadcast', False),
                        'group_type': 'group' if getattr(entity, 'megagroup', False) else 'channel',
                        'is_public': 1 if getattr(entity, 'username', None) else 0,
                        'verified': getattr(entity, 'verified', False),
                        'restricted': getattr(entity, 'restricted', False),
                        'scam': getattr(entity, 'scam', False),
                        'fake': getattr(entity, 'fake', False)
                    })
                elif isinstance(entity, Chat):
                    dialog_info.update({
                        'title': getattr(entity, 'title', ''),
                        'username': None,
                        'megagroup': True,
                        'group_type': 'chat',
                        'is_public': 0,
                        'participants_count': getattr(entity, 'participants_count', 0),
                        'creator': getattr(entity, 'creator', False),
                        'kicked': getattr(entity, 'kicked', False),
                        'left': getattr(entity, 'left', False)
                    })
                elif isinstance(entity, User):
                    dialog_info.update({
                        'title': f"{getattr(entity, 'first_name', '')} {getattr(entity, 'last_name', '')}".strip(),
                        'username': getattr(entity, 'username', None),
                        'group_type': 'user',
                        'is_public': 1 if getattr(entity, 'username', None) else 0,
                        'bot': getattr(entity, 'bot', False),
                        'verified': getattr(entity, 'verified', False),
                        'premium': getattr(entity, 'premium', False),
                        'phone': getattr(entity, 'phone', None)
                    })

                dialogs.append(dialog_info)

            await tg_client.close_client()
            logger.info(f"get_dialogs方法获取到 {len(dialogs)} 个对话")
            return dialogs

    except Exception as e:
        logger.error(f"get_dialogs方法执行失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return None


def analyze_three_way_differences(get_dialog_list_results, iter_dialogs_results, get_dialogs_results):
    """
    分析三种方法的差异
    """
    print("\n" + "="*80)
    print("三种对话列表方法对比分析")
    print("="*80)

    if not all([get_dialog_list_results, iter_dialogs_results, get_dialogs_results]):
        print("错误: 无法获取完整的对话列表进行对比")
        return

    # 统计数据
    get_dialog_count = len(get_dialog_list_results)
    iter_dialog_count = len(iter_dialogs_results)
    get_dialogs_count = len(get_dialogs_results)

    print(f"\n基本统计:")
    print(f"get_dialog_list方法获取:  {get_dialog_count:2d} 个对话")
    print(f"iter_dialogs方法获取:    {iter_dialog_count:2d} 个对话")
    print(f"get_dialogs方法获取:     {get_dialogs_count:2d} 个对话")

    # 创建ID集合进行对比
    get_dialog_ids = {dialog['id'] for dialog in get_dialog_list_results}
    iter_dialog_ids = {dialog['id'] for dialog in iter_dialogs_results}
    get_dialogs_ids = {dialog['id'] for dialog in get_dialogs_results}

    print(f"\n集合对比:")
    print(f"get_dialog_list与iter_dialogs共同对话: {len(get_dialog_ids & iter_dialog_ids)}")
    print(f"get_dialog_list与get_dialogs共同对话:  {len(get_dialog_ids & get_dialogs_ids)}")
    print(f"iter_dialogs与get_dialogs共同对话:    {len(iter_dialog_ids & get_dialogs_ids)}")
    print(f"三种方法共同对话:                   {len(get_dialog_ids & iter_dialog_ids & get_dialogs_ids)}")

    # 找出各种方法中独有的对话
    unique_to_get_dialog_list = get_dialog_ids - iter_dialog_ids - get_dialogs_ids
    unique_to_iter_dialogs = iter_dialog_ids - get_dialog_ids - get_dialogs_ids
    unique_to_get_dialogs = get_dialogs_ids - get_dialog_ids - iter_dialog_ids

    # 找出缺失的对话
    missing_in_get_dialog_list = (iter_dialog_ids | get_dialogs_ids) - get_dialog_ids
    missing_in_iter_dialogs = (get_dialog_ids | get_dialogs_ids) - iter_dialog_ids
    missing_in_get_dialogs = (get_dialog_ids | iter_dialog_ids) - get_dialogs_ids

    print(f"\n独有对话分析:")
    print(f"仅get_dialog_list有:  {len(unique_to_get_dialog_list)} 个")
    print(f"仅iter_dialogs有:     {len(unique_to_iter_dialogs)} 个")
    print(f"仅get_dialogs有:      {len(unique_to_get_dialogs)} 个")

    print(f"\n缺失对话分析:")
    print(f"get_dialog_list缺失:  {len(missing_in_get_dialog_list)} 个")
    print(f"iter_dialogs缺失:     {len(missing_in_iter_dialogs)} 个")
    print(f"get_dialogs缺失:      {len(missing_in_get_dialogs)} 个")

    # 详细分析get_dialogs与iter_dialogs的差异
    if missing_in_get_dialogs:
        print(f"\nget_dialogs方法中缺失的对话 ({len(missing_in_get_dialogs)} 个):")
        print("-" * 80)

        missing_dialogs = []
        for dialog_id in missing_in_get_dialogs:
            # 先在iter_dialogs中找
            dialog_info = next((d for d in iter_dialogs_results if d['id'] == dialog_id), None)
            if not dialog_info:
                # 再在get_dialog_list中找
                dialog_info = next((d for d in get_dialog_list_results if d['id'] == dialog_id), None)

            if dialog_info:
                missing_dialogs.append(dialog_info)

        # 按类型分类
        missing_by_type = {}
        for dialog_info in missing_dialogs:
            dialog_type = dialog_info.get('dialog_type', dialog_info.get('group_type', 'unknown'))
            if dialog_type not in missing_by_type:
                missing_by_type[dialog_type] = []
            missing_by_type[dialog_type].append(dialog_info)

        for dialog_type, dialogs in missing_by_type.items():
            print(f"\n{dialog_type} 类型 ({len(dialogs)} 个):")
            for i, dialog in enumerate(dialogs, 1):
                title = dialog.get('title', 'N/A')
                username = f"@{dialog.get('username')}" if dialog.get('username') else "无用户名"
                unread = dialog.get('unread_count', 0)
                print(f"  {i:2d}. {title} ({username}) - ID: {dialog['id']}, 未读: {unread}")

    # 详细分析iter_dialogs与get_dialogs的差异
    if missing_in_iter_dialogs:
        print(f"\niter_dialogs方法中缺失的对话 ({len(missing_in_iter_dialogs)} 个):")
        print("-" * 80)

        missing_dialogs = []
        for dialog_id in missing_in_iter_dialogs:
            # 先在get_dialogs中找
            dialog_info = next((d for d in get_dialogs_results if d['id'] == dialog_id), None)
            if not dialog_info:
                # 再在get_dialog_list中找
                dialog_info = next((d for d in get_dialog_list_results if d['id'] == dialog_id), None)

            if dialog_info:
                missing_dialogs.append(dialog_info)

        for i, dialog in enumerate(missing_dialogs, 1):
            title = dialog.get('title', 'N/A')
            username = f"@{dialog.get('username')}" if dialog.get('username') else "无用户名"
            unread = dialog.get('unread_count', 0)
            print(f"  {i:2d}. {title} ({username}) - ID: {dialog['id']}, 未读: {unread}")

    # 分析方法特性
    print(f"\n方法特性分析:")
    print("-" * 80)

    # 统计各方法中各类型的数量
    def count_by_type(dialogs, type_field='dialog_type'):
        types = {}
        for dialog in dialogs:
            dialog_type = dialog.get(type_field, 'unknown')
            types[dialog_type] = types.get(dialog_type, 0) + 1
        return types

    iter_types = count_by_type(iter_dialogs_results, 'dialog_type')
    get_dialogs_types = count_by_type(get_dialogs_results, 'dialog_type')
    get_dialog_list_types = count_by_type(get_dialog_list_results, 'group_type')

    print("iter_dialogs结果分类:")
    for type_name, count in sorted(iter_types.items()):
        print(f"  {type_name}: {count} 个")

    print("\nget_dialogs结果分类:")
    for type_name, count in sorted(get_dialogs_types.items()):
        print(f"  {type_name}: {count} 个")

    print("\nget_dialog_list结果分类:")
    for type_name, count in sorted(get_dialog_list_types.items()):
        print(f"  {type_name}: {count} 个")

    # 性能和特性对比
    print(f"\n性能和特性对比:")
    print("-" * 80)
    print("方法               | 数量 | 包含用户 | 额外字段        | 适用场景")
    print("-" * 80)
    print(f"get_dialog_list    | {get_dialog_count:2d}   | 否       | 成员数量等      | 业务应用，过滤用户")
    print(f"iter_dialogs       | {iter_dialog_count:2d}   | 是       | 实体详细信息    | 完整数据获取")
    print(f"get_dialogs        | {get_dialogs_count:2d}   | 是       | 置顶状态等      | 一次性批量获取")

    # 推荐使用场景
    print(f"\n推荐使用场景:")
    print("-" * 80)
    print("• get_dialog_list:  适用于业务监控，只关心群组和频道")
    print("• iter_dialogs:     适用于需要逐个处理的场景，内存友好")
    print("• get_dialogs:      适用于需要完整对话列表的场景，性能较好")

    # 保存详细对比结果
    comparison_result = {
        'timestamp': datetime.now().isoformat(),
        'session_name': 'default2',
        'statistics': {
            'get_dialog_list_count': get_dialog_count,
            'iter_dialogs_count': iter_dialog_count,
            'get_dialogs_count': get_dialogs_count,
            'common_all_three': len(get_dialog_ids & iter_dialog_ids & get_dialogs_ids),
            'missing_in_get_dialog_list': len(missing_in_get_dialog_list),
            'missing_in_iter_dialogs': len(missing_in_iter_dialogs),
            'missing_in_get_dialogs': len(missing_in_get_dialogs)
        },
        'type_distributions': {
            'iter_dialogs': iter_types,
            'get_dialogs': get_dialogs_types,
            'get_dialog_list': get_dialog_list_types
        },
        'get_dialog_list_results': get_dialog_list_results,
        'iter_dialogs_results': iter_dialogs_results,
        'get_dialogs_results': get_dialogs_results
    }

    output_file = f'three_way_dialog_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n详细对比结果已保存到: {output_file}")

    return comparison_result


async def main():
    """
    主函数：执行三方对比分析
    """
    print("Telegram三种对话列表方法对比分析工具")
    print("对比: get_dialog_list vs iter_dialogs vs get_dialogs")

    session_name = 'default2'
    if len(sys.argv) > 1:
        session_name = sys.argv[1]

    # 初始化应用
    app.ready(db_switch=False, web_switch=False, worker_switch=False, socketio_switch=False)

    print(f"\n使用session: {session_name}")
    print("开始获取三种方法的对话列表...")

    # 获取三种方法的结果
    print("\n1. 使用get_dialog_list方法...")
    get_dialog_results = await get_dialogs_by_get_dialog_list(session_name)

    print("\n2. 使用iter_dialogs方法...")
    iter_dialog_results = await get_dialogs_by_iter_dialogs(session_name)

    print("\n3. 使用get_dialogs方法...")
    get_dialogs_results = await get_dialogs_by_get_dialogs(session_name)

    # 分析差异
    if all([get_dialog_results, iter_dialog_results, get_dialogs_results]):
        analyze_three_way_differences(get_dialog_results, iter_dialog_results, get_dialogs_results)
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