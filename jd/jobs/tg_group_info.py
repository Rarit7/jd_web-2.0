import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from jd import db
from jd.models.tg_group import TgGroup
from jd.models.tg_group_status import TgGroupStatus
from jd.models.tg_group_info_change import TgGroupInfoChange
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group_session import TgGroupSession
from jd.services.spider.tg import TgService

logger = logging.getLogger(__name__)


class TgGroupInfoManager:
    """
    Telegram群组信息管理器
    负责获取群组信息、记录变化并更新数据库
    """
    
    @staticmethod
    async def sync_all_group_info(tg_client, session_name: str = 'default') -> Dict[str, Any]:
        """
        同步所有群组信息
        :param tg_client: TelegramAPIs客户端实例
        :param session_name: 会话名称，用于建立群组-会话关联
        :return: 同步结果统计
        """
        result = {
            'success': True,
            'message': '',
            'processed_groups': [],  # 添加处理过的群组列表
            'stats': {
                'total_groups': 0,
                'updated_groups': 0,
                'new_groups': 0,
                'member_changes': 0,
                'info_changes': 0,
                'errors': []
            }
        }
        
        try:
            logger.info("开始同步所有群组信息")
            
            # 使用异步方式获取群组列表
            async def get_all_groups():
                groups = []
                async for group_info in tg_client.get_dialog_list():
                    if group_info.get('result') == 'success':
                        groups.append(group_info.get('data', {}))
                return groups
            
            # 在客户端的事件循环中运行异步方法
            async with tg_client.client:
                groups = await get_all_groups()
            
            result['stats']['total_groups'] = len(groups)
            logger.info(f"获取到 {len(groups)} 个群组/频道")
            
            # 在异步上下文外处理群组数据，避免事件循环冲突
            import asyncio
            
            for group_data in groups:
                try:
                    # 使用同步方式处理群组数据，避免异步上下文问题
                    def process_group_sync():
                        from jd import app
                        with app.app_context():
                            return TgGroupInfoManager._process_single_group(group_data, session_name)
                    
                    # 在新的线程池中执行同步操作
                    loop = asyncio.get_event_loop()
                    group_result = await loop.run_in_executor(None, process_group_sync)
                    
                    # 将处理过的群组添加到列表中
                    chat_id = str(group_data.get('id', ''))
                    if chat_id:
                        result['processed_groups'].append(chat_id)
                    
                    # 更新统计信息
                    if group_result['is_new']:
                        result['stats']['new_groups'] += 1
                    else:
                        result['stats']['updated_groups'] += 1
                    
                    result['stats']['member_changes'] += group_result['member_changes']
                    result['stats']['info_changes'] += group_result['info_changes']
                    
                except Exception as e:
                    error_msg = f"处理群组失败 chat_id={group_data.get('id', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    result['stats']['errors'].append(error_msg)
            
            result['message'] = f"同步完成: 总计 {result['stats']['total_groups']} 个群组, " \
                              f"新增 {result['stats']['new_groups']} 个, " \
                              f"更新 {result['stats']['updated_groups']} 个, " \
                              f"成员变化 {result['stats']['member_changes']} 次, " \
                              f"信息变化 {result['stats']['info_changes']} 次"
            
            logger.info(result['message'])
            
        except Exception as e:
            result['success'] = False
            result['message'] = f"同步群组信息失败: {str(e)}"
            logger.error(result['message'])
        
        return result
    
    @staticmethod
    def _process_single_group(group_data: Dict[str, Any], session_name: str = 'default') -> Dict[str, Any]:
        """
        处理单个群组信息
        :param group_data: 群组数据
        :param session_name: 会话名称，用于建立群组-会话关联
        :return: 处理结果
        """
        result = {
            'is_new': False,
            'member_changes': 0,
            'info_changes': 0
        }
        
        chat_id = str(group_data.get('id', ''))
        if not chat_id:
            logger.warning(f"群组ID为空: {group_data}")
            return result
        
        logger.debug(f"处理群组: {chat_id} - {group_data.get('title', 'Unknown')}")
        
        # 查找现有群组记录
        existing_group = db.session.query(TgGroup).filter_by(chat_id=chat_id).first()
        
        if existing_group:
            # 更新现有群组
            result['info_changes'] = TgGroupInfoManager._update_existing_group(existing_group, group_data)
        else:
            # 创建新群组
            TgGroupInfoManager._create_new_group(group_data, session_name)
            result['is_new'] = True
        
        # 更新/创建群组状态记录（成员数量变化）
        result['member_changes'] = TgGroupInfoManager._update_group_status(group_data)
        
        return result
    
    @staticmethod
    def _update_existing_group(existing_group: TgGroup, new_data: Dict[str, Any]) -> int:
        """
        更新现有群组信息并记录变化
        :param existing_group: 现有群组记录
        :param new_data: 新的群组数据
        :return: 变化次数
        """
        changes_count = 0
        chat_id = existing_group.chat_id
        
        # 定义需要检查的字段映射
        field_mappings = [
            ('name', 'username', TgGroupInfoChange.ChangedFieldType.GROUP_NAME_INVITE_LINK),
            ('desc', 'channel_description', TgGroupInfoChange.ChangedFieldType.GROUP_DESCRIPTION),
            ('title', 'title', TgGroupInfoChange.ChangedFieldType.DISPLAY_NAME),
            ('avatar_path', 'photo_path', TgGroupInfoChange.ChangedFieldType.GROUP_AVATAR),
        ]
        
        for db_field, data_field, change_type in field_mappings:
            old_value = getattr(existing_group, db_field, '') or ''
            new_value = new_data.get(data_field, '') or ''
            
            if old_value != new_value:
                # 记录变化
                TgGroupInfoManager._record_group_info_change(
                    chat_id=chat_id,
                    changed_field=change_type,
                    old_value=old_value,
                    new_value=new_value
                )
                
                # 更新数据库字段
                setattr(existing_group, db_field, new_value)
                changes_count += 1
                
                logger.info(f"群组信息变化 {chat_id}: {db_field} '{old_value}' -> '{new_value}'")
        
        # 更新其他字段（不记录变化）
        if new_data.get('megagroup') == 'channel':
            existing_group.group_type = TgGroup.GroupType.CHANNEL
        else:
            existing_group.group_type = TgGroup.GroupType.GROUP
        
        if changes_count > 0:
            db.session.commit()
            logger.info(f"群组 {chat_id} 信息已更新，共 {changes_count} 处变化")
        
        return changes_count
    
    @staticmethod
    def _create_new_group(group_data: Dict[str, Any], session_name: str = 'default') -> None:
        """
        创建新群组记录并建立会话关联
        :param group_data: 群组数据
        :param session_name: 会话名称，用于建立群组-会话关联
        """
        chat_id = str(group_data.get('id', ''))
        
        # 确定群组类型
        if group_data.get('megagroup') == 'channel':
            group_type = TgGroup.GroupType.CHANNEL
        else:
            group_type = TgGroup.GroupType.GROUP
        
        new_group = TgGroup(
            chat_id=chat_id,
            name=group_data.get('username', '') or '',
            desc=group_data.get('channel_description', '') or '',
            title=group_data.get('title', '') or '',
            avatar_path=group_data.get('photo_path', '') or '',
            status=TgGroup.StatusType.JOIN_SUCCESS,
            group_type=group_type,
            account_id=group_data.get('account_id', '') or ''
        )
        
        db.session.add(new_group)
        db.session.flush()  # 确保获取到new_group的ID
        
        # 创建群组-会话关联记录
        try:
            # 检查是否已存在相同的会话关联
            existing_session = TgGroupSession.query.filter_by(
                chat_id=chat_id,
                session_name=session_name
            ).first()
            
            if not existing_session:
                new_session = TgGroupSession(
                    user_id=group_data.get('account_id', '') or '',
                    chat_id=chat_id,
                    session_name=session_name
                )
                db.session.add(new_session)
                logger.info(f"创建群组会话关联: chat_id={chat_id}, session_name={session_name}")
            else:
                logger.debug(f"群组会话关联已存在: chat_id={chat_id}, session_name={session_name}")
                
        except Exception as e:
            logger.error(f"创建群组会话关联失败 chat_id={chat_id}, session_name={session_name}: {e}")
            # 不影响群组创建，继续执行
        
        db.session.commit()
        
        logger.info(f"新增群组: {chat_id} - {new_group.title}")
    
    @staticmethod
    def _update_group_status(group_data: Dict[str, Any]) -> int:
        """
        更新群组状态（主要是成员数量）
        :param group_data: 群组数据
        :return: 是否有成员数量变化 (0或1)
        """
        chat_id = str(group_data.get('id', ''))
        current_members = group_data.get('member_count', 0)
        
        # 查找现有状态记录
        existing_status = db.session.query(TgGroupStatus).filter_by(chat_id=chat_id).first()
        
        if existing_status:
            # 更新现有记录 - previous字段由每日备份任务统一更新
            has_change = existing_status.members_now != current_members
            existing_status.members_now = current_members
            
            # 更新消息记录统计
            TgGroupInfoManager._update_message_stats(existing_status, chat_id)
            
            db.session.commit()
            
            if has_change:
                logger.info(f"群组 {chat_id} 成员数量变化: {existing_status.members_previous} -> {current_members}")
                return 1
            else:
                logger.debug(f"群组 {chat_id} 成员数量更新: {current_members} (无变化)")
                return 0
        else:
            # 创建新的状态记录
            new_status = TgGroupStatus(
                chat_id=chat_id,
                members_now=current_members,
                members_previous=0,
                records_now=0,
                records_previous=0
            )
            
            # 更新消息记录统计
            TgGroupInfoManager._update_message_stats(new_status, chat_id)
            
            db.session.add(new_status)
            db.session.commit()
            
            logger.info(f"新增群组状态: {chat_id}, 成员数: {current_members}")
            return 1
    
    @staticmethod
    def _update_message_stats(status_record: TgGroupStatus, chat_id: str) -> None:
        """
        更新消息统计信息
        :param status_record: 状态记录
        :param chat_id: 群组ID
        """
        try:
            # 查询消息记录统计
            message_stats = db.session.query(
                db.func.count(TgGroupChatHistory.id).label('total_count'),
                db.func.min(TgGroupChatHistory.postal_time).label('first_date'),
                db.func.max(TgGroupChatHistory.postal_time).label('last_date')
            ).filter(TgGroupChatHistory.chat_id == chat_id).first()
            
            if message_stats:
                # previous字段由每日备份任务统一更新，这里只更新now字段
                status_record.records_now = message_stats.total_count or 0
                
                # 更新时间范围
                status_record.first_record_date = message_stats.first_date
                status_record.last_record_date = message_stats.last_date
                
                # 查询最早和最新的message_id
                if message_stats.first_date:
                    first_msg = db.session.query(TgGroupChatHistory.message_id).filter(
                        TgGroupChatHistory.chat_id == chat_id,
                        TgGroupChatHistory.postal_time == message_stats.first_date
                    ).first()
                    if first_msg:
                        status_record.first_record_id = first_msg.message_id or ''
                
                if message_stats.last_date:
                    last_msg = db.session.query(TgGroupChatHistory.message_id).filter(
                        TgGroupChatHistory.chat_id == chat_id,
                        TgGroupChatHistory.postal_time == message_stats.last_date
                    ).first()
                    if last_msg:
                        status_record.last_record_id = last_msg.message_id or ''
                
        except Exception as e:
            logger.warning(f"更新消息统计失败 chat_id={chat_id}: {e}")
    
    @staticmethod
    def _record_group_info_change(chat_id: str, changed_field: int, old_value: str, new_value: str) -> None:
        """
        记录群组信息变化
        :param chat_id: 群组ID
        :param changed_field: 变化字段类型
        :param old_value: 原值
        :param new_value: 新值
        """
        try:
            change_record = TgGroupInfoChange(
                chat_id=chat_id,
                changed_fields=changed_field,
                original_value=old_value,
                new_value=new_value,
                update_time=datetime.now()
            )
            
            db.session.add(change_record)
            db.session.commit()
            
            logger.debug(f"记录群组信息变化: chat_id={chat_id}, field={changed_field}, '{old_value}' -> '{new_value}'")
            
        except Exception as e:
            logger.error(f"记录群组信息变化失败: {e}")
            db.session.rollback()
    
    @staticmethod
    async def sync_group_info_by_account(sessionname) -> Dict[str, Any]:
        """
        根据账户ID同步群组信息
        :param sessionname: session文件前缀
        :return: 同步结果
        """
        try:
            # 初始化TG服务
            tg_service = await TgService.init_tg(sessionname)
            if not tg_service:
                return {
                    'success': False,
                    'message': 'TG服务初始化失败',
                    'stats': {}
                }
            
            try:
                # 同步群组信息
                result = await TgGroupInfoManager.sync_all_group_info(tg_service, sessionname)
                return result
            finally:
                # 清理TG服务
                await tg_service.close_client()
                
        except Exception as e:
            logger.error(f"{sessionname} 同步群组信息失败: {e}")
            return {
                'success': False,
                'message': f'同步失败: {str(e)}',
                'stats': {}
            }

    @staticmethod
    def get_group_user_session(chat_id) -> List[str]:
        """
        根据群组ID获取关联的session_name列表
        :param chat_id: 群组ID
        :return: 所有关联TG账号的session_name列表
        """
        try:
            # 查询tg_group_session表中指定chat_id的所有session_name
            session_records = db.session.query(TgGroupSession.session_name).filter(
                TgGroupSession.chat_id == str(chat_id)
            ).distinct().all()
            
            # 提取session_name列表
            session_name_list = [record.session_name for record in session_records if record.session_name]
            
            logger.debug(f"群组 {chat_id} 关联的session列表: {session_name_list}")
            return session_name_list
            
        except Exception as e:
            logger.error(f"获取群组 {chat_id} 的session列表失败: {e}")
            return []

    @staticmethod
    def get_groups_by_session_name(session_name) -> List[str]:
        """
        根据session name获取关联的chat_id列表
        :param session_name: session name
        :return: 所有关联群组的chat_id列表
        """
        try:
            # 查询tg_group_session表中指定chat_id的所有session_name
            groups_records = db.session.query(TgGroupSession.chat_id).filter(
                TgGroupSession.session_name == session_name
            ).distinct().all()
            
            # 提取chat_id列表
            groups_list = [record.chat_id for record in groups_records if record.chat_id]
            
            logger.debug(f"{session_name} 关联的群组列表: {groups_list}")
            return groups_list
            
        except Exception as e:
            logger.error(f"获取 {session_name} 的群组列表失败: {e}")
            return []