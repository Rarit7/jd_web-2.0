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
        # 批次级缓存机制
        self._user_cache = {}  # 存储已查询的用户信息 {user_id: TgGroupUserInfo对象}
        self._processed_users = set()  # 当前批次已处理的用户ID集合
        self._batch_chat_id = None  # 当前批次的chat_id
        # 统计信息
        self._cache_hits = 0  # 缓存命中次数
        self._cache_misses = 0  # 缓存未命中次数
        self._batch_count = 0  # 处理的批次数
    
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
    
    def clear_batch_cache(self):
        """清空批次缓存，在处理新批次前调用"""
        if self._cache_hits + self._cache_misses > 0:
            hit_rate = self._cache_hits / (self._cache_hits + self._cache_misses) * 100
            logger.info(f"用户缓存统计: 批次数={self._batch_count}, 命中率={hit_rate:.1f}% ({self._cache_hits}/{self._cache_hits + self._cache_misses})")
        
        self._user_cache.clear()
        self._processed_users.clear()
        self._batch_chat_id = None
        # 重置统计信息
        self._cache_hits = 0
        self._cache_misses = 0 
        self._batch_count = 0
        logger.debug("批次级用户缓存已清空")
    
    async def prepare_batch_user_cache(self, batch_messages: list, chat_id: int):
        """批量预处理用户信息缓存，减少重复数据库查询
        
        Args:
            batch_messages: 消息批次列表
            chat_id: 群组ID
        """
        if self._batch_chat_id != chat_id:
            # 新的chat_id，清空缓存
            self.clear_batch_cache()
            self._batch_chat_id = chat_id
        
        # 增加批次计数
        self._batch_count += 1
        
        # 提取批次中所有唯一的用户ID
        unique_user_ids = set()
        for msg in batch_messages:
            user_id = str(msg.get("user_id", ""))
            if user_id and user_id != "0" and user_id != "777000":
                unique_user_ids.add(user_id)
        
        # 过滤掉已缓存的用户ID
        uncached_user_ids = unique_user_ids - set(self._user_cache.keys())
        
        if not uncached_user_ids:
            logger.debug(f"批次中{len(unique_user_ids)}个用户都已缓存，跳过数据库查询")
            return
        
        logger.debug(f"批量查询用户信息: chat_id={chat_id}, 用户数={len(uncached_user_ids)}")
        
        try:
            # 批量查询数据库中已存在的用户
            existing_users = TgGroupUserInfo.query.filter(
                TgGroupUserInfo.chat_id == str(chat_id),
                TgGroupUserInfo.user_id.in_(uncached_user_ids)
            ).all()
            
            # 缓存已存在的用户
            for user in existing_users:
                self._user_cache[user.user_id] = user
            
            # 为不存在的用户ID缓存None值，避免重复查询
            cached_user_ids = {user.user_id for user in existing_users}
            for user_id in uncached_user_ids:
                if user_id not in cached_user_ids:
                    self._user_cache[user_id] = None
            
            logger.debug(f"批量用户缓存完成: 已存在={len(existing_users)}, 新用户={len(uncached_user_ids)-len(existing_users)}")
            
        except Exception as e:
            logger.error(f"批量查询用户信息失败: {e}")
            # 发生错误时，为所有用户ID缓存None，避免后续查询
            for user_id in uncached_user_ids:
                self._user_cache[user_id] = None
    
    async def save_user_info_from_message(self, data: Dict[str, Any], chat_id: int) -> None:
        """从聊天消息中提取发言人信息并保存到用户信息表"""
        # 参数验证
        if not isinstance(data, dict):
            logger.error(f"save_user_info_from_message: data参数必须是字典类型，当前类型: {type(data)}")
            return
            
        user_id = str(data.get("user_id", ""))
        if not user_id or user_id == "0" or user_id == "777000":
            return
        
        # 检查是否在当前批次中已处理过此用户
        if user_id in self._processed_users:
            logger.debug(f'用户 {user_id} 在当前批次中已处理，跳过')
            return
        
        # 标记为已处理
        self._processed_users.add(user_id)
        
        try:
            # 优先从缓存获取用户信息
            existing_user = self._user_cache.get(user_id)
            if user_id in self._user_cache:
                self._cache_hits += 1
            else:
                # 缓存中没有，单独查询（这种情况应该很少发生，因为已经有批量预处理）
                self._cache_misses += 1
                logger.debug(f'用户 {user_id} 不在缓存中，执行单独查询')
                existing_user = TgGroupUserInfo.query.filter_by(
                    chat_id=str(chat_id), 
                    user_id=user_id
                ).first()
                # 将查询结果加入缓存
                self._user_cache[user_id] = existing_user
            
            # 从消息中获取基本信息，使用安全转换函数
            nickname = self._safe_str(data.get("nick_name", ""))
            username = self._safe_str(data.get("user_name", ""))
            
            # 获取用户详细信息
            desc = ""
            avatar_path = ""
            photo_url = ""
            
            try:
                # 使用 client.get_entity 获取用户基本信息
                user_entity = await self.tg.client.get_entity(int(user_id))
                
                # 使用 GetFullUserRequest 获取完整用户信息以获取个人简介
                try:
                    from telethon.tl.functions.users import GetFullUserRequest
                    full_user = await self.tg.client(GetFullUserRequest(user_entity.id))
                    
                    # 从完整用户信息中提取个人简介
                    if hasattr(full_user, 'full_user'):
                        desc = str(getattr(full_user.full_user, 'about', '') or "")
                        if desc:
                            logger.debug(f'获取用户 {user_id} 个人简介成功: {desc[:50]}...')
                    
                except Exception as full_user_error:
                    logger.warning(f'获取用户 {user_id} 完整信息失败，尝试基本方式: {full_user_error}')
                    # 降级到基本方式获取个人简介 (可能不完整)
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
                # 更新缓存
                self._user_cache[user_id] = user_obj
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
        记录用户信息变化（带时间窗口去重）
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
            current_time = datetime.datetime.now()

            # 创建时间窗口（2小时内的相同变动将被去重）
            time_window_hours = 2
            window_start = current_time - datetime.timedelta(hours=time_window_hours)

            # 检查时间窗口内是否已存在相同的变动记录
            existing_record = TgUserInfoChange.query.filter(
                TgUserInfoChange.user_id == str(user_id),
                TgUserInfoChange.changed_fields == changed_field,
                TgUserInfoChange.original_value == (str(old_value) if old_value else ''),
                TgUserInfoChange.new_value == (str(new_value) if new_value else ''),
                TgUserInfoChange.update_time >= window_start
            ).first()

            if existing_record:
                logger.debug(f'用户 {user_id} 在 {time_window_hours} 小时内已存在相同变动记录，跳过重复记录')
                return

            # 创建新的变动记录
            change_record = TgUserInfoChange(
                user_id=str(user_id),
                changed_fields=changed_field,
                original_value=str(old_value) if old_value else '',
                new_value=str(new_value) if new_value else '',
                update_time=current_time
            )
            db.session.add(change_record)
            db.session.flush()
            logger.info(f'记录用户信息变化: user_id={user_id}, field={changed_field}, 变动: "{old_value}" -> "{new_value}"')

        except Exception as e:
            logger.error(f'记录用户信息变化失败: {e}')
            db.session.rollback()

    async def save_user_info_from_message_batch(self, batch_messages: list, chat_id: int) -> None:
        """批量处理消息中的用户信息，优化版本"""
        if not batch_messages:
            return
            
        try:
            # 提取所有用户信息，去重
            user_data_map = {}
            for data in batch_messages:
                user_id = str(data.get("user_id", ""))
                if user_id and user_id != "0" and user_id != "777000":
                    # 使用最新的用户信息（如果同一用户在批次中出现多次）
                    user_data_map[user_id] = {
                        'nickname': data.get("nick_name", ""),
                        'username': data.get("user_name", ""),
                        'user_id': user_id
                    }
            
            if not user_data_map:
                return
                
            # 批量查询现有用户
            existing_users = TgGroupUserInfo.query.filter(
                TgGroupUserInfo.chat_id == str(chat_id),
                TgGroupUserInfo.user_id.in_(user_data_map.keys())
            ).all()
            
            existing_user_map = {user.user_id: user for user in existing_users}
            
            # 批量创建新用户对象
            new_users = []
            for user_id, user_data in user_data_map.items():
                if user_id not in existing_user_map:
                    user_obj = TgGroupUserInfo(
                        chat_id=str(chat_id),
                        user_id=user_id,
                        nickname=self._safe_str(user_data['nickname']),
                        username=self._safe_str(user_data['username']),
                        desc='',
                        avatar_path='',
                        photo=''
                    )
                    new_users.append(user_obj)
                    # 更新缓存
                    self._user_cache[user_id] = user_obj
                else:
                    # 更新现有用户的基本信息（昵称和用户名）
                    existing_user = existing_user_map[user_id]
                    new_data = {
                        'nickname': user_data['nickname'],
                        'username': user_data['username'],
                        'desc': '',
                        'avatar_path': ''
                    }
                    self._update_existing_user(existing_user, new_data)
            
            # 批量添加新用户
            if new_users:
                db.session.add_all(new_users)
                logger.debug(f'批量创建 {len(new_users)} 个新用户信息记录')
                
        except Exception as e:
            logger.error(f'批量处理用户信息失败: {e}')
            db.session.rollback()