#!/usr/bin/env python3
"""
通过session文件检查可访问的群组，并更新为已加入状态

使用方式：
    python utils/update_joined_groups_status.py
    或
    python -m utils.update_joined_groups_status
"""

import sys
import os
import asyncio

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jd import app, db
from jd.models.tg_group import TgGroup
from jd.services.spider.tg import TgService
from jd.utils.logging_config import get_logger

logger = get_logger('utils.update_joined_groups_status', {
    'component': 'telegram',
    'module': 'batch_update'
})


async def get_accessible_groups(session_name: str = 'default2'):
    """
    通过session文件获取所有可访问的群组ID

    Args:
        session_name: session文件名称

    Returns:
        set: 可访问的群组chat_id集合
    """
    accessible_groups = set()

    try:
        logger.info(f'正在通过session "{session_name}" 获取群组列表...')

        # 初始化TG服务
        tg_service = await TgService.init_tg(session_name)
        if not tg_service:
            logger.error(f'TG服务初始化失败: {session_name}')
            return accessible_groups

        try:
            # 获取所有对话
            async with tg_service.client:
                async for group_info in tg_service.get_dialog_list():
                    if group_info.get('result') == 'success':
                        data = group_info.get('data', {})
                        chat_id = str(data.get('id', ''))
                        if chat_id:
                            accessible_groups.add(chat_id)
                            logger.debug(f'  找到群组: {chat_id} - {data.get("title", "Unknown")}')

            logger.info(f'通过session "{session_name}" 找到 {len(accessible_groups)} 个可访问群组')

        finally:
            # 关闭TG服务
            await tg_service.close_client()

    except Exception as e:
        logger.error(f'获取群组列表失败: {e}', exc_info=True)

    return accessible_groups


def update_groups_status(accessible_chat_ids: set):
    """
    将可访问的群组状态更新为JOIN_SUCCESS

    Args:
        accessible_chat_ids: 可访问的群组chat_id集合
    """
    if not accessible_chat_ids:
        logger.warning('没有找到可访问的群组')
        return

    updated_count = 0
    already_joined_count = 0

    try:
        # 查询数据库中这些群组的当前状态
        groups = TgGroup.query.filter(
            TgGroup.chat_id.in_(list(accessible_chat_ids))
        ).all()

        logger.info(f'数据库中找到 {len(groups)} 个匹配的群组记录')

        for group in groups:
            if group.status != TgGroup.StatusType.JOIN_SUCCESS:
                old_status = group.status
                group.status = TgGroup.StatusType.JOIN_SUCCESS
                updated_count += 1
                logger.info(f'  更新群组状态: {group.chat_id} ({group.title or group.name}) '
                          f'{old_status} -> JOIN_SUCCESS')
            else:
                already_joined_count += 1
                logger.debug(f'  群组 {group.chat_id} 已经是JOIN_SUCCESS状态，跳过')

        if updated_count > 0:
            db.session.commit()
            logger.info(f'成功更新 {updated_count} 个群组状态为 JOIN_SUCCESS')
        else:
            logger.info('没有需要更新的群组')

        logger.info(f'统计: 已更新={updated_count}, 已是JOIN_SUCCESS={already_joined_count}')

    except Exception as e:
        logger.error(f'更新群组状态失败: {e}', exc_info=True)
        db.session.rollback()


async def main():
    """主函数"""
    logger.info('='*60)
    logger.info('开始检查并更新可访问群组的状态')
    logger.info('='*60)

    # 初始化应用
    app.ready(db_switch=True, web_switch=False, worker_switch=False, socketio_switch=False)

    with app.app_context():
        try:
            # 1. 获取可访问的群组列表
            accessible_groups = await get_accessible_groups('default2')

            if not accessible_groups:
                logger.warning('未获取到任何可访问的群组，脚本结束')
                return

            # 2. 更新数据库中群组的状态
            update_groups_status(accessible_groups)

            logger.info('='*60)
            logger.info('群组状态更新完成')
            logger.info('='*60)

        except KeyboardInterrupt:
            logger.warning('收到中断信号，正在退出...')
        except Exception as e:
            logger.error(f'执行过程中发生错误: {e}', exc_info=True)


if __name__ == '__main__':
    asyncio.run(main())