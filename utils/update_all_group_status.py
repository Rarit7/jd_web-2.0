#!/usr/bin/env python3
"""
批量更新所有Telegram群组的状态信息
包括：
1. 最新消息时间和消息ID
2. 对话数量（records_now）

注意：不再更新群组人数（members_now）

使用方式：
    python utils/update_all_group_status.py
    或
    python -m utils.update_all_group_status
"""

import sys
import os
import asyncio
from datetime import datetime

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func
from jd import app, db
from jd.models.tg_group import TgGroup
from jd.models.tg_group_status import TgGroupStatus
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group_session import TgGroupSession
from jd.services.spider.tg import TgService
from jd.jobs.tg_base_history_fetcher import BaseTgHistoryFetcher
from jd.utils.logging_config import get_logger

logger = get_logger('utils.update_all_group_status', {
    'component': 'telegram',
    'module': 'batch_update'
})


class GroupStatusUpdater(BaseTgHistoryFetcher):
    """批量更新群组状态的处理类"""

    def __init__(self):
        super().__init__()
        self.updated_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.invalid_count = 0  # 标记为失效的群组数量

    async def update_all_groups(self):
        """批量更新所有群组的状态信息，包括JOIN_SUCCESS和INVALID_LINK状态的群组"""
        logger.info('='*50)
        logger.info('开始批量更新群组状态信息')
        logger.info('='*50)

        # 1. 获取所有已加入的群组和已失效的群组（它们可能都有聊天记录需要统计）
        groups = TgGroup.query.filter(
            TgGroup.status.in_([TgGroup.StatusType.JOIN_SUCCESS, TgGroup.StatusType.INVALID_LINK])
        ).all()
        total_groups = len(groups)

        if total_groups == 0:
            logger.warning('没有找到需要更新的群组（状态为JOIN_SUCCESS或INVALID_LINK）')
            return

        # 统计不同状态的群组数量
        success_groups = [g for g in groups if g.status == TgGroup.StatusType.JOIN_SUCCESS]
        invalid_groups = [g for g in groups if g.status == TgGroup.StatusType.INVALID_LINK]
        logger.info(f'找到 {total_groups} 个需要更新的群组 (活跃: {len(success_groups)}, 已失效: {len(invalid_groups)})')

        # 2. 按session分组，以便批量初始化TG连接（每个群组使用其对应的session）
        # 优化：一次性查询所有session配置，避免N+1查询问题
        logger.info('批量查询所有群组的session配置...')
        chat_ids = [str(g.chat_id) for g in groups]
        all_sessions = TgGroupSession.query.filter(
            TgGroupSession.chat_id.in_(chat_ids)
        ).order_by(TgGroupSession.user_id.asc()).all()

        # 构建 chat_id -> session_names 映射
        chat_to_sessions = {}
        for session in all_sessions:
            if session.session_name:
                if session.chat_id not in chat_to_sessions:
                    chat_to_sessions[session.chat_id] = []
                chat_to_sessions[session.chat_id].append(session.session_name)

        logger.info(f'找到 {len(chat_to_sessions)} 个群组有session配置')

        # 按session分组
        groups_by_session = {}
        groups_without_session = []

        for group in groups:
            sessionnames = chat_to_sessions.get(str(group.chat_id), [])
            if not sessionnames:
                groups_without_session.append(group)
                continue

            # 只使用 default2 这个有效的 session，忽略其他 session
            valid_sessions = [s for s in sessionnames if s == 'default2']
            if not valid_sessions:
                groups_without_session.append(group)
                logger.debug(f'  群组 {group.chat_id} 没有使用有效的session (default2)，跳过')
                continue

            # 使用session名称作为key（将列表转为元组以便作为字典键）
            session_key = tuple(sorted(valid_sessions))
            if session_key not in groups_by_session:
                groups_by_session[session_key] = []
            groups_by_session[session_key].append(group)

        logger.info(f'涉及 {len(groups_by_session)} 个不同的session配置')
        print(f'DEBUG: groups_by_session 大小 = {len(groups_by_session)}', flush=True)
        if groups_without_session:
            logger.warning(f'有 {len(groups_without_session)} 个群组没有找到session配置，将跳过')
            self.skipped_count += len(groups_without_session)

        # 如果没有任何群组有session配置，直接返回
        if not groups_by_session:
            logger.warning('没有任何群组有有效的session配置，脚本结束')
            print('DEBUG: 没有session配置，退出', flush=True)
            return

        # 3. 按session遍历处理
        logger.info(f'开始遍历 {len(groups_by_session)} 个session配置...')
        print(f'DEBUG: 开始遍历 session...', flush=True)
        for session_idx, (session_key, session_groups) in enumerate(groups_by_session.items(), 1):
            sessionnames = list(session_key)
            print(f'DEBUG: 处理 session {session_idx}: {sessionnames}', flush=True)
            logger.info(f'\n处理Session [{session_idx}/{len(groups_by_session)}]: {sessionnames} (共 {len(session_groups)} 个群组)')

            # 初始化Telegram连接（设置30秒超时）
            logger.info(f'正在初始化Telegram连接: {sessionnames}')
            try:
                init_result = await asyncio.wait_for(
                    self.init_telegram_service(sessionnames),
                    timeout=30.0
                )
                if not init_result:
                    logger.error(f'Session {sessionnames} 的Telegram服务初始化失败，跳过该session的 {len(session_groups)} 个群组')
                    self.failed_count += len(session_groups)
                    continue
                logger.info(f'Telegram连接初始化成功')
            except asyncio.TimeoutError:
                logger.error(f'Session {sessionnames} 初始化超时(30秒)，跳过该session的 {len(session_groups)} 个群组')
                self.failed_count += len(session_groups)
                continue
            except Exception as e:
                logger.error(f'Session {sessionnames} 初始化异常: {e}，跳过该session的 {len(session_groups)} 个群组')
                self.failed_count += len(session_groups)
                continue

            # 4. 更新该session下的所有群组
            for group_idx, group in enumerate(session_groups, 1):
                try:
                    logger.info(f'\n  更新群组 [{group_idx}/{len(session_groups)}]: {group.title or group.name} (chat_id: {group.chat_id})')
                    # skip_member_count=True 只更新消息统计，不获取群组人数
                    await self.update_single_group(group, skip_member_count=True)
                    self.updated_count += 1

                    # 添加短暂延迟，避免请求过快
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f'  群组 {group.chat_id} 更新失败: {e}')
                    self.failed_count += 1

            # 关闭当前session的Telegram连接
            await self.close_telegram_service()
            logger.info(f'Session {sessionnames} 处理完成')

        # 5. 输出统计结果
        logger.info('\n' + '='*50)
        logger.info('批量更新完成')
        logger.info(f'总群组数: {total_groups}')
        logger.info(f'成功更新: {self.updated_count}')
        logger.info(f'更新失败: {self.failed_count}')
        logger.info(f'标记失效: {self.invalid_count}')
        logger.info(f'跳过处理: {self.skipped_count}')
        logger.info('='*50)

    async def update_single_group(self, group: TgGroup, skip_member_count=False):
        """更新单个群组的状态信息

        Args:
            group: 群组对象
            skip_member_count: 是否跳过人数更新（测试模式）
        """
        chat_id = int(group.chat_id)

        # 1. 更新消息统计（records_now, first/last record）- 所有群组都需要统计
        self.update_group_message_stats(chat_id)

        # 2. 只有状态为JOIN_SUCCESS的群组才尝试更新人数（INVALID_LINK的群组跳过）
        if group.status == TgGroup.StatusType.JOIN_SUCCESS and not skip_member_count:
            # 更新群组人数（members_now），如果失败则标记群组为已失效
            success = await self.update_group_member_count(chat_id, group.name or group.title)

            if not success:
                # 无法获取群组信息，标记为失效
                self.mark_group_as_invalid(group, '无法获取群组dialog，可能已被移出或群组已解散')
                self.invalid_count += 1
                logger.warning(f'  ⚠ 群组 {chat_id} 已标记为失效状态 (JOIN_SUCCESS -> INVALID_LINK)')
            else:
                logger.info(f'  ✓ 群组 {chat_id} 状态更新完成')
        elif group.status == TgGroup.StatusType.INVALID_LINK or skip_member_count:
            # 已失效的群组只统计消息记录，不尝试获取人数
            logger.info(f'  ✓ 群组 {chat_id} 消息统计完成 (跳过人数更新)')

    def update_group_message_stats(self, chat_id: int):
        """更新群组的消息统计信息（基于数据库记录）"""
        try:
            chat_id_str = str(chat_id)

            # 获取或创建群组状态记录
            status = TgGroupStatus.query.filter_by(chat_id=chat_id_str).first()
            if not status:
                status = TgGroupStatus(chat_id=chat_id_str)
                db.session.add(status)

            # 使用单次聚合查询获取所有统计信息
            stats = db.session.query(
                func.count(TgGroupChatHistory.id).label('total_count'),
                func.min(TgGroupChatHistory.postal_time).label('first_date'),
                func.max(TgGroupChatHistory.postal_time).label('last_date')
            ).filter(TgGroupChatHistory.chat_id == chat_id_str).first()

            if stats and stats.total_count > 0:
                status.records_now = stats.total_count
                status.first_record_date = stats.first_date
                status.last_record_date = stats.last_date

                # 获取第一条消息ID
                if stats.first_date:
                    first_msg = TgGroupChatHistory.query.filter_by(
                        chat_id=chat_id_str
                    ).filter(TgGroupChatHistory.postal_time == stats.first_date).first()
                    status.first_record_id = first_msg.message_id if first_msg else '0'

                # 获取最后一条消息ID
                if stats.last_date:
                    last_msg = TgGroupChatHistory.query.filter_by(
                        chat_id=chat_id_str
                    ).filter(TgGroupChatHistory.postal_time == stats.last_date).order_by(
                        TgGroupChatHistory.id.desc()
                    ).first()
                    status.last_record_id = last_msg.message_id if last_msg else '0'

                logger.info(f'    对话数量: {status.records_now}, 最新消息: {status.last_record_date}')
            else:
                # 没有记录时重置状态
                status.records_now = 0
                status.first_record_date = None
                status.first_record_id = '0'
                status.last_record_date = None
                status.last_record_id = '0'
                logger.info(f'    对话数量: 0 (无消息记录)')

            db.session.commit()

        except Exception as e:
            logger.error(f'    更新消息统计失败: {e}')
            try:
                db.session.rollback()
            except:
                pass

    async def update_group_member_count(self, chat_id: int, group_name: str) -> bool:
        """
        更新群组人数信息（通过Telegram API获取）

        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            chat_id_str = str(chat_id)

            # 获取dialog信息
            chat, actual_chat_id = await self.get_dialog_with_retry(chat_id, group_name)

            if not chat:
                logger.warning(f'    无法获取群组dialog，群组可能已失效')
                return False

            # 从dialog获取成员数量
            from telethon.tl.functions.channels import GetFullChannelRequest
            from telethon.tl.functions.messages import GetFullChatRequest
            from telethon.tl.types import Channel, Chat

            member_count = 0
            try:
                # chat本身就是entity，不需要访问chat.entity
                entity = chat

                # 尝试直接从entity获取participants_count
                if hasattr(entity, 'participants_count'):
                    member_count = entity.participants_count
                else:
                    # 通过完整请求获取详细信息
                    if isinstance(entity, Channel):
                        channel_full = await self.tg.client(GetFullChannelRequest(entity))
                        member_count = channel_full.full_chat.participants_count
                    elif isinstance(entity, Chat):
                        chat_full = await self.tg.client(GetFullChatRequest(entity.id))
                        member_count = chat_full.chats[0].participants_count
                    else:
                        logger.warning(f'    未知的entity类型: {type(entity)}')
                        return False
            except Exception as e:
                logger.warning(f'    获取群组信息失败: {e}')
                return False

            # 更新状态记录
            status = TgGroupStatus.query.filter_by(chat_id=chat_id_str).first()
            if status:
                status.members_now = member_count
                db.session.commit()
                logger.info(f'    群组人数: {member_count}')
            else:
                logger.warning(f'    群组状态记录不存在，无法更新人数')

            return True

        except Exception as e:
            logger.error(f'    更新群组人数失败: {e}')
            try:
                db.session.rollback()
            except:
                pass
            return False

    def mark_group_as_invalid(self, group: TgGroup, reason: str):
        """将群组标记为失效状态（INVALID_LINK）"""
        try:
            # 只有当前状态是JOIN_SUCCESS时才更新为INVALID_LINK
            if group.status == TgGroup.StatusType.JOIN_SUCCESS:
                group.status = TgGroup.StatusType.INVALID_LINK
                # 不再自动添加备注信息
                # group.remark = reason
                db.session.commit()
                logger.info(f'    已将群组 {group.chat_id} 标记为失效 (INVALID_LINK): {reason}')
        except Exception as e:
            logger.error(f'    标记群组失效状态失败: {e}')
            try:
                db.session.rollback()
            except:
                pass


async def main():
    """主函数"""
    # 初始化应用（只初始化数据库，不加载web和worker）
    app.ready(db_switch=True, web_switch=False, worker_switch=False, socketio_switch=False)

    with app.app_context():
        updater = GroupStatusUpdater()
        try:
            await updater.update_all_groups()
        except KeyboardInterrupt:
            logger.warning('\n收到中断信号，正在清理...')
        except Exception as e:
            logger.error(f'执行过程中发生错误: {e}', exc_info=True)
        finally:
            # 确保清理Telegram连接
            if updater.tg:
                await updater.close_telegram_service()


if __name__ == '__main__':
    # 运行异步主函数
    asyncio.run(main())