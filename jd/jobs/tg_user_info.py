import datetime
import logging
import os
from typing import Dict, Any

from jd import app, db
from jd.models.tg_group_user_info import TgGroupUserInfo
from jd.models.tg_user_info_change import TgUserInfoChange

logger = logging.getLogger(__name__)


class TgUserInfoProcessor:
    
    def __init__(self, tg_service):
        self.tg = tg_service
    
    @staticmethod
    def _safe_str(value) -> str:
        """安全地将任何值转换为字符串，特别处理字典和列表类型"""
        if value is None:
            return ""
        elif isinstance(value, dict):
            # 如果是字典，尝试获取常见的字符串字段，或者转为JSON字符串
            if 'name' in value:
                return str(value.get('name', ''))
            elif 'value' in value:
                return str(value.get('value', ''))
            elif 'text' in value:
                return str(value.get('text', ''))
            else:
                # 作为最后的手段，转为JSON字符串，但截断长度
                import json
                json_str = json.dumps(value, ensure_ascii=False)
                return json_str[:100] + "..." if len(json_str) > 100 else json_str
        elif isinstance(value, (list, tuple)):
            # 如果是列表，转为字符串表示
            return str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
        else:
            return str(value)
    
    async def save_user_info_from_message(self, data: Dict[str, Any], chat_id: int) -> None:
        """从聊天消息中提取发言人信息并保存到用户信息表"""
        # 参数验证
        if not isinstance(data, dict):
            logger.error(f"save_user_info_from_message: data参数必须是字典类型，当前类型: {type(data)}")
            return
            
        user_id = str(data.get("user_id", ""))
        if not user_id or user_id == "0" or user_id == "777000":
            return
        
        try:
            # 检查用户信息是否已存在
            existing_user = TgGroupUserInfo.query.filter_by(
                chat_id=str(chat_id), 
                user_id=user_id
            ).first()
            
            # 从消息中获取基本信息，使用安全转换函数
            nickname = self._safe_str(data.get("nick_name", ""))
            username = self._safe_str(data.get("user_name", ""))
            
            # 获取用户详细信息
            desc = ""
            avatar_path = ""
            photo_url = ""
            
            try:
                # 使用 client.get_entity 获取用户详细信息
                user_entity = await self.tg.client.get_entity(int(user_id))
                
                # 提取个人简介 (如果有)
                if hasattr(user_entity, 'about'):
                    desc = str(user_entity.about or "")
                
                # 处理头像
                if hasattr(user_entity, 'photo') and user_entity.photo:
                    try:
                        avatar_dir = os.path.join(app.static_folder, 'images/avatar')
                        os.makedirs(avatar_dir, exist_ok=True)
                        
                        file_name = f'{user_id}.jpg'
                        file_full_path = f'{avatar_dir}/{file_name}'
                        
                        # 下载头像到本地
                        if not os.path.exists(file_full_path):
                            await self.tg.client.download_profile_photo(user_entity, file_full_path)
                            logger.debug(f'下载用户 {user_id} 头像成功: {file_name}')
                        
                        avatar_path = f'images/avatar/{file_name}'
                        
                    except Exception as e:
                        logger.warning(f'下载用户 {user_id} 头像失败: {e}')
                        
            except Exception as e:
                logger.warning(f'获取用户 {user_id} 详细信息失败: {e}')
            
            if existing_user:
                # 如果用户存在，使用新的更新方法，确保所有值都是安全的字符串
                new_data = {
                    'nickname': self._safe_str(nickname),
                    'username': self._safe_str(username),
                    'desc': self._safe_str(desc),
                    'avatar_path': self._safe_str(avatar_path)
                }
                changes_count = self._update_existing_user(existing_user, new_data)
                if changes_count > 0:
                    logger.info(f'用户信息已更新: user_id={user_id}, 变更字段数={changes_count}')
            else:
                # 创建新的用户信息记录，使用安全转换函数
                # 先记录所有参数用于调试
                params = {
                    'chat_id': self._safe_str(chat_id),
                    'user_id': self._safe_str(user_id),
                    'nickname': self._safe_str(nickname),
                    'username': self._safe_str(username),
                    'desc': self._safe_str(desc),
                    'avatar_path': self._safe_str(avatar_path),
                    'photo': self._safe_str(photo_url)
                }
                logger.debug(f'创建TgGroupUserInfo对象参数: {params}')
                
                user_obj = TgGroupUserInfo(**params)
                db.session.add(user_obj)
                logger.debug(f'新增用户信息: user_id={user_id}, nickname={nickname}, username={username}, desc={desc[:50]}...')
                
        except Exception as e:
            import traceback
            logger.error(f'保存发言人信息失败 user_id={user_id}: {e}')
            logger.error(f'完整错误栈: {traceback.format_exc()}')
            logger.error(f'输入数据内容: {data}')
            # 回滚会话以防止后续操作出现 "transaction has been rolled back" 错误
            try:
                db.session.rollback()
            except Exception as rollback_error:
                logger.error(f'回滚数据库会话失败: {rollback_error}')
    

    def _update_existing_user(self, existing_user: TgGroupUserInfo, new_data: Dict[str, Any]) -> int:
        """
        更新现有用户信息并记录变化
        为提高效率，仅在距离上次更新此用户信息1day以上时才触发此方法
        :param existing_user: 现有用户记录
        :param new_data: 新的用户数据
        :return: 变化次数
        """
        changes_count = 0
        user_id = existing_user.user_id
        
        # 检查是否需要更新（距离上次更新超过1天）
        if existing_user.updated_at:
            time_diff = datetime.datetime.now() - existing_user.updated_at
            if time_diff.total_seconds() < 86400:  # 24小时 = 86400秒
                logger.debug(f'用户 {user_id} 最近已更新，跳过检查')
                return 0
        
        # 定义需要检查的字段映射 (数据库字段, 新数据字段, 变更类型)
        field_mappings = [
            ('nickname', 'nickname', TgUserInfoChange.ChangedFieldType.DISPLAY_NAME),
            ('username', 'username', TgUserInfoChange.ChangedFieldType.USERNAME),
            ('avatar_path', 'avatar_path', TgUserInfoChange.ChangedFieldType.AVATAR),
            ('desc', 'desc', TgUserInfoChange.ChangedFieldType.BIOGRAPHY),
        ]
        
        for db_field, data_field, change_type in field_mappings:
            old_value = self._safe_str(getattr(existing_user, db_field, ''))
            new_value = self._safe_str(new_data.get(data_field, ''))
            
            if old_value != new_value and new_value:  # 只有新值不为空时才更新
                # 记录变化
                self._record_user_info_change(
                    user_id=user_id,
                    changed_field=change_type,
                    old_value=old_value,
                    new_value=new_value
                )
                
                # 更新数据库字段
                setattr(existing_user, db_field, new_value)
                changes_count += 1
                
                logger.info(f"用户信息变化 {user_id}: {db_field} '{old_value}' -> '{new_value}'")
        
        # 更新时间戳
        if changes_count > 0:
            existing_user.updated_at = datetime.datetime.now()
        
        return changes_count
    
    def _record_user_info_change(self, user_id: str, changed_field: int, old_value: str, new_value: str) -> None:
        """
        记录用户信息变化
        :param user_id: 用户ID
        :param changed_field: 变化字段类型
        :param old_value: 原值
        :param new_value: 新值
        """
        try:
            # 确保 changed_field 是整数类型
            if isinstance(changed_field, dict):
                logger.error(f'changed_field 参数不能是字典类型: {changed_field}')
                return
                
            changed_field = int(changed_field) if changed_field else 0
            
            change_record = TgUserInfoChange(
                user_id=str(user_id),
                changed_fields=changed_field,
                original_value=str(old_value) if old_value else '',
                new_value=str(new_value) if new_value else '',
                update_time=datetime.datetime.now()
            )
            db.session.add(change_record)
            db.session.flush()
            logger.debug(f'记录用户信息变化: user_id={user_id}, field={changed_field}')
        except Exception as e:
            logger.error(f'记录用户信息变化失败: {e}')
            db.session.rollback()