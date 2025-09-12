#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import asyncio
import logging
import time
from typing import List, Dict, Any

# 添加项目路径到sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jd import app, db
from jd.services.spider.tg import TgService
from jd.models.tg_group_user_info import TgGroupUserInfo
from telethon.tl.functions.users import GetFullUserRequest
from telethon.errors import UserPrivacyRestrictedError, UsernameInvalidError, UserIdInvalidError
from telethon.errors.rpcerrorlist import PeerIdInvalidError
from telethon.errors import ValueError as TelethonValueError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UserProfileUpdater:
    def __init__(self):
        self.tg_service = None
        self.updated_count = 0
        self.error_count = 0
        self.total_count = 0
        self.last_request_time = 0

    async def init_telegram_service(self):
        """初始化Telegram服务"""
        try:
            logger.info("正在初始化Telegram客户端...")
            self.tg_service = await TgService.init_tg(sessionname='111')
            if not self.tg_service:
                logger.error("Telegram客户端初始化失败")
                return False
            logger.info("Telegram客户端初始化成功")
            return True
        except Exception as e:
            logger.error(f"初始化Telegram客户端时发生错误: {e}")
            return False

    def get_unique_user_ids(self) -> List[str]:
        """获取所有去重的user_id"""
        try:
            logger.info("正在从数据库获取所有用户ID...")
            # 使用distinct()去重，只获取user_id字段
            user_ids = db.session.query(TgGroupUserInfo.user_id).distinct().all()
            # 提取user_id字符串列表
            unique_user_ids = [user_id[0] for user_id in user_ids if user_id[0]]
            logger.info(f"获取到 {len(unique_user_ids)} 个唯一用户ID")
            return unique_user_ids
        except Exception as e:
            logger.error(f"获取用户ID时发生错误: {e}")
            return []

    async def get_user_profile(self, user_id: str, max_retries: int = 3) -> str:
        """通过Telegram API获取用户个人简介，包含重试机制"""
        for attempt in range(max_retries):
            try:
                # 尝试直接获取用户实体
                user_entity = await self.tg_service.client.get_entity(int(user_id))
                
                # 使用GetFullUserRequest获取完整用户信息
                full_user = await self.tg_service.client(GetFullUserRequest(user_entity.id))
                
                # 提取个人简介
                if hasattr(full_user, 'full_user'):
                    user_about = getattr(full_user.full_user, 'about', '')
                    return user_about if user_about else ''
                
                return ''
            except (UserPrivacyRestrictedError, UsernameInvalidError, UserIdInvalidError, PeerIdInvalidError) as e:
                # 这些错误不需要重试
                logger.warning(f"用户 {user_id} 隐私限制或ID无效: {e}")
                return ''
            except TelethonValueError as e:
                if "Could not find the input entity" in str(e):
                    # 实体不存在的错误不需要重试，直接使用备用方法
                    logger.warning(f"用户 {user_id} 实体不存在，尝试通过群组成员查找: {e}")
                    return await self._get_user_profile_via_groups(user_id)
                else:
                    # 其他Telethon值错误可能需要重试
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 1  # 指数退避: 1s, 2s, 4s
                        logger.warning(f"获取用户 {user_id} 简介失败 (尝试 {attempt + 1}/{max_retries})，{wait_time}秒后重试: {e}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"获取用户 {user_id} 个人简介时发生Telethon值错误，重试已耗尽: {e}")
                        return ''
            except ValueError as e:
                if "Could not find the input entity" in str(e):
                    # 实体不存在的错误不需要重试，直接使用备用方法
                    logger.warning(f"用户 {user_id} 实体不存在，尝试通过群组成员查找: {e}")
                    return await self._get_user_profile_via_groups(user_id)
                else:
                    # 其他值错误可能需要重试
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 1  # 指数退避: 1s, 2s, 4s
                        logger.warning(f"获取用户 {user_id} 简介失败 (尝试 {attempt + 1}/{max_retries})，{wait_time}秒后重试: {e}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"获取用户 {user_id} 个人简介时发生值错误，重试已耗尽: {e}")
                        return ''
            except Exception as e:
                error_msg = str(e)
                if "Could not find the input entity" in error_msg or "PeerUser" in error_msg:
                    # 实体解析失败的错误不需要重试，直接使用备用方法
                    logger.warning(f"用户 {user_id} 实体解析失败，尝试通过群组成员查找: {e}")
                    return await self._get_user_profile_via_groups(user_id)
                else:
                    # 网络或其他临时错误可能需要重试
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 1  # 指数退避: 1s, 2s, 4s
                        logger.warning(f"获取用户 {user_id} 简介失败 (尝试 {attempt + 1}/{max_retries})，{wait_time}秒后重试: {e}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"获取用户 {user_id} 个人简介时发生未知错误，重试已耗尽: {e}")
                        return ''
        
        return ''  # 如果所有重试都失败，返回空字符串

    async def _get_user_profile_via_groups(self, user_id: str) -> str:
        """通过群组成员列表查找用户简介的备用方法"""
        try:
            # 获取用户所在的群组
            groups = self._get_user_groups(user_id)
            if not groups:
                logger.debug(f"用户 {user_id} 没有关联的群组信息")
                return ''
            
            # 尝试从每个群组的成员中找到该用户
            for group_id in groups[:3]:  # 最多尝试3个群组避免过度API调用
                try:
                    group_entity = await self.tg_service.client.get_entity(int(group_id))
                    async for participant in self.tg_service.client.iter_participants(group_entity):
                        if str(participant.id) == user_id:
                            # 找到用户，获取完整信息
                            full_user = await self.tg_service.client(GetFullUserRequest(participant.id))
                            if hasattr(full_user, 'full_user'):
                                user_about = getattr(full_user.full_user, 'about', '')
                                if user_about:
                                    logger.info(f"通过群组 {group_id} 成功获取用户 {user_id} 的个人简介")
                                    return user_about
                            return ''
                except Exception as group_error:
                    logger.debug(f"从群组 {group_id} 查找用户 {user_id} 失败: {group_error}")
                    continue
            
            logger.debug(f"无法通过群组成员列表找到用户 {user_id}")
            return ''
        except Exception as e:
            logger.error(f"通过群组查找用户 {user_id} 时发生错误: {e}")
            return ''

    def _get_user_groups(self, user_id: str) -> List[str]:
        """获取用户所在的群组ID列表"""
        try:
            # 从数据库查询该用户所在的群组
            groups = db.session.query(TgGroupUserInfo.group_id).filter(
                TgGroupUserInfo.user_id == user_id
            ).distinct().limit(5).all()  # 限制最多5个群组
            
            return [str(group[0]) for group in groups if group[0]]
        except Exception as e:
            logger.error(f"获取用户 {user_id} 群组信息时发生错误: {e}")
            return []

    def update_user_desc(self, user_id: str, desc: str) -> bool:
        """更新用户描述字段"""
        try:
            # 更新该user_id对应的所有记录的desc字段
            updated_rows = db.session.query(TgGroupUserInfo).filter(
                TgGroupUserInfo.user_id == user_id
            ).update({'desc': desc})
            
            db.session.commit()
            
            if updated_rows > 0:
                logger.info(f"用户 {user_id} 的个人简介已更新到 {updated_rows} 条记录")
                return True
            else:
                logger.warning(f"用户 {user_id} 没有找到对应记录")
                return False
                
        except Exception as e:
            logger.error(f"更新用户 {user_id} 描述时发生错误: {e}")
            db.session.rollback()
            return False

    async def process_all_users(self):
        """处理所有用户"""
        # 获取所有唯一用户ID
        user_ids = self.get_unique_user_ids()
        if not user_ids:
            logger.error("未找到任何用户ID")
            return

        self.total_count = len(user_ids)
        logger.info(f"开始处理 {self.total_count} 个用户的个人简介")

        for i, user_id in enumerate(user_ids, 1):
            logger.info(f"处理用户 {user_id} ({i}/{self.total_count})")
            
            try:
                # API限流：确保请求之间有至少1秒的间隔
                current_time = time.time()
                time_since_last = current_time - self.last_request_time
                if time_since_last < 1.0:
                    await asyncio.sleep(1.0 - time_since_last)
                
                # 获取用户个人简介
                desc = await self.get_user_profile(user_id)
                self.last_request_time = time.time()
                
                # 更新数据库
                if self.update_user_desc(user_id, desc):
                    self.updated_count += 1
                    if desc:
                        logger.info(f"用户 {user_id} 个人简介: {desc[:100]}...")
                    else:
                        logger.info(f"用户 {user_id} 没有设置个人简介")
                else:
                    self.error_count += 1
                    
            except Exception as e:
                logger.error(f"处理用户 {user_id} 时发生未预期错误: {e}")
                self.error_count += 1
            
            # 每处理10个用户输出一次进度
            if i % 10 == 0:
                logger.info(f"进度: {i}/{self.total_count}, 成功: {self.updated_count}, 错误: {self.error_count}")

    async def cleanup(self):
        """清理资源"""
        if self.tg_service and self.tg_service.client:
            await self.tg_service.client.disconnect()
            logger.info("Telegram客户端已断开连接")

    def print_summary(self):
        """输出处理总结"""
        logger.info("=" * 50)
        logger.info("处理完成！统计信息:")
        logger.info(f"总用户数: {self.total_count}")
        logger.info(f"成功更新: {self.updated_count}")
        logger.info(f"处理错误: {self.error_count}")
        logger.info("=" * 50)


async def main():
    """主函数"""
    updater = UserProfileUpdater()
    
    try:
        # 初始化Flask应用
        app.ready()
        
        with app.app_context():
            # 初始化Telegram服务
            if not await updater.init_telegram_service():
                return
            
            # 处理所有用户
            await updater.process_all_users()
            
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        await updater.cleanup()
        # 输出统计信息
        updater.print_summary()


if __name__ == "__main__":
    asyncio.run(main())