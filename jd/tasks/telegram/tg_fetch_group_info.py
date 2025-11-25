from jd.utils.logging_config import get_logger
import asyncio
import concurrent.futures
from typing import Dict, Any, List

from jCelery import celery
from jd import db
from jd.jobs.tg_group_info import TgGroupInfoManager
from jd.tasks.base_task import BaseTask
from jd.models.tg_account import TgAccount
from jd.models.tg_group import TgGroup
from jd.models.tg_group_session import TgGroupSession

logger = get_logger('jd.tasks.tg.tg_fetch_group_info', {'component': 'telegram', 'module': 'fetch_group_info'})


class FetchAccountGroupInfoTask(BaseTask):
    """获取TG账户群组信息任务"""
    
    def __init__(self, account_id: int):
        # 传递account_id作为resource_id，不传递session_id参数（这个任务不需要session绑定）
        super().__init__(resource_id=str(account_id))
        self.account_id = account_id
        # 设置立即返回模式 - 如果存在相同的account_id任务在运行，则直接返回
        self.wait_if_conflict = False
    
    def get_job_name(self) -> str:
        return 'fetch_account_group_info'
    
    def execute_task(self) -> Dict[str, Any]:
        """
        执行获取账户群组信息的任务

        Returns:
            Dict[str, Any]: 任务执行结果
        """
        logger.info(f"开始获取账户 {self.account_id} 的群组信息")

        try:
            # 查询账户信息并立即转换为 DTO（字典），避免 ORM 会话分离问题
            tg_account = TgAccount.query.filter(TgAccount.id == self.account_id).first()
            if not tg_account:
                error_msg = f"账户 {self.account_id} 不存在"
                logger.error(error_msg)
                return {
                    'err_code': 1,
                    'err_msg': error_msg,
                    'success': False,
                    'message': error_msg,
                    'account_id': self.account_id,
                    'stats': {}
                }

            if tg_account.status != TgAccount.StatusType.JOIN_SUCCESS:
                error_msg = f"账户 {tg_account.name} (ID: {self.account_id}) 状态异常，当前状态: {tg_account.status}"
                logger.error(error_msg)
                return {
                    'err_code': 1,
                    'err_msg': error_msg,
                    'success': False,
                    'message': error_msg,
                    'account_id': self.account_id,
                    'stats': {}
                }

            # 验证user_id不为空（防止数据污染）
            if not tg_account.user_id or tg_account.user_id.strip() == '':
                error_msg = f"账户 {tg_account.name} (ID: {self.account_id}) user_id为空，无法处理群组信息"
                logger.error(error_msg)
                return {
                    'err_code': 1,
                    'err_msg': error_msg,
                    'success': False,
                    'message': error_msg,
                    'account_id': self.account_id,
                    'stats': {}
                }

            # 立即将 ORM 对象转换为 DTO，提取需要的字段
            account_dto = {
                'id': tg_account.id,
                'name': tg_account.name,
                'user_id': tg_account.user_id,
                'status': tg_account.status
            }

            # 调用群组信息同步方法
            # 使用 _run_async_safely 来安全地执行异步方法
            # 传递 account_dto 而不是 ORM 对象
            result = self._run_async_safely(
                TgGroupInfoManager.sync_group_info_by_account(account_dto['name'])
            )

            if result['success']:
                # 同步成功后，建立账户-群组关系
                # 传递同步过程中处理的群组chat_id列表
                processed_chat_ids = result.get('processed_groups', [])
                session_result = _sync_account_group_sessions(account_dto, processed_chat_ids)
                result['session_stats'] = session_result

                # 填充tg_group表中缺失的account_id字段
                fill_result = _fill_missing_account_ids(account_dto, processed_chat_ids)
                result['fill_account_id_stats'] = fill_result

                logger.info(f"账户 {account_dto['name']} 群组信息同步完成: {result['message']}")

                # 设置成功的错误码
                result['err_code'] = 0
                result['err_msg'] = ''
            else:
                logger.error(f"账户 {account_dto['name']} 群组信息同步失败: {result['message']}")
                result['err_code'] = 1
                result['err_msg'] = result['message']

            # 添加账户信息到结果中
            result['account_id'] = self.account_id
            result['account_name'] = account_dto['name']
            result['account_user_id'] = account_dto['user_id']

            return result

        except Exception as e:
            error_msg = f"获取账户 {self.account_id} 群组信息时发生异常: {str(e)}"
            logger.error(error_msg)
            return {
                'err_code': 1,
                'err_msg': error_msg,
                'success': False,
                'message': error_msg,
                'account_id': self.account_id,
                'account_name': '',
                'stats': {}
            }

    @staticmethod
    def _run_async_safely(coro):
        """
        安全地运行异步协程
        处理事件循环可能已存在的情况（在Celery worker中）

        Returns:
            异步协程的执行结果
        """
        try:
            # 尝试获取当前事件循环
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 没有运行的事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        else:
            # 已有运行的事件循环，直接运行
            # 这种情况下，我们需要在线程中运行（避免冲突）
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()


@celery.task
def fetch_account_group_info(account_id: int) -> Dict[str, Any]:
    """
    获取指定账户的全部群聊和频道信息，并建立账户-群组关系
    
    Args:
        account_id (int): TG账户ID
        
    Returns:
        Dict[str, Any]: 任务执行结果
    """
    # 使用改进后的BaseTask来执行任务
    task = FetchAccountGroupInfoTask(account_id)
    return task.start_task()
    


def _fill_missing_account_ids(account_dto: Dict[str, Any], processed_chat_ids: List[str] = None) -> Dict[str, Any]:
    """
    填充tg_group表中缺失的account_id字段

    Args:
        account_dto (Dict[str, Any]): TG账户数据（字典，包含 id, name, user_id 等）
        processed_chat_ids (List[str]): 要处理的群组chat_id列表，如果为None或空列表则处理所有群组

    Returns:
        Dict[str, Any]: 填充统计结果
    """
    stats = {
        'total_groups': 0,
        'filled_groups': 0,
        'already_filled': 0,
        'errors': []
    }

    try:
        logger.info(f"开始填充账户 {account_dto['name']} 关联群组的account_id字段")
        
        # 构建查询条件
        if processed_chat_ids:
            # 如果提供了chat_id列表，只处理这些群组
            query = TgGroup.query.filter(TgGroup.chat_id.in_(processed_chat_ids))
            logger.info(f"处理指定的 {len(processed_chat_ids)} 个群组")
        else:
            # 如果没有提供列表，处理所有account_id为空的群组
            query = TgGroup.query.filter(
                db.or_(TgGroup.account_id == '', TgGroup.account_id.is_(None))
            )
            logger.info("处理所有account_id为空的群组")
        
        groups = query.all()
        stats['total_groups'] = len(groups)
        
        if not groups:
            logger.info("没有找到需要填充account_id的群组")
            return stats
        
        logger.info(f"找到 {len(groups)} 个需要填充account_id的群组")
        
        for group in groups:
            try:
                # 检查account_id是否为空
                if group.account_id and group.account_id.strip():
                    stats['already_filled'] += 1
                    logger.debug(f"群组 {group.name} (chat_id={group.chat_id}) 的account_id已存在: {group.account_id}")
                    continue
                
                # 填充account_id为当前账户的TG数字ID
                group.account_id = account_dto['user_id']
                stats['filled_groups'] += 1
                logger.info(f"填充群组 {group.name} (chat_id={group.chat_id}) 的account_id为: {account_dto['user_id']}")
                
            except Exception as e:
                error_msg = f"填充群组account_id失败 chat_id={group.chat_id}: {str(e)}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        # 提交数据库变更
        if stats['filled_groups'] > 0:
            db.session.commit()
            logger.info(f"成功填充了 {stats['filled_groups']} 个群组的account_id")
        
        logger.info(f"账户 {account_dto['name']} account_id填充完成: "
                   f"总计 {stats['total_groups']} 个群组, "
                   f"填充 {stats['filled_groups']} 个, "
                   f"已存在 {stats['already_filled']} 个")

    except Exception as e:
        error_msg = f"填充账户 {account_dto['name']} 群组account_id时发生异常: {str(e)}"
        logger.error(error_msg)
        stats['errors'].append(error_msg)
        db.session.rollback()

    return stats


def _sync_account_group_sessions(account_dto: Dict[str, Any], processed_chat_ids: List[str] = None) -> Dict[str, Any]:
    """
    同步账户-群组会话关系到tg_group_session表

    Args:
        account_dto (Dict[str, Any]): TG账户数据（字典，包含 id, name, user_id 等）
        processed_chat_ids (List[str]): 要处理的群组chat_id列表，如果为None或空列表则跳过处理

    Returns:
        Dict[str, Any]: 同步统计结果
    """
    stats = {
        'total_groups': 0,
        'new_sessions': 0,
        'existing_sessions': 0,
        'updated_empty_sessions': 0,
        'merged_duplicate_sessions': 0,
        'errors': []
    }

    try:
        logger.info(f"开始同步账户 {account_dto['name']} 的群组会话关系")
        
        # 如果没有提供processed_chat_ids或列表为空，直接返回
        if not processed_chat_ids:
            logger.warning(f"未提供processed_chat_ids或列表为空，跳过会话关联处理")
            stats['total_groups'] = 0
            return stats
        
        # 使用提供的chat_id列表查询群组
        logger.info(f"使用提供的chat_id列表: {len(processed_chat_ids)} 个群组")
        groups = TgGroup.query.filter(TgGroup.chat_id.in_(processed_chat_ids)).all()
        logger.info(f"从数据库查询到 {len(groups)} 个匹配的群组")
        
        stats['total_groups'] = len(groups)
        logger.info(f"将为 {len(groups)} 个群组创建会话关联")
        
        for group in groups:
            try:
                # 首先检查是否存在空user_id的历史记录
                empty_user_session = TgGroupSession.query.filter(
                    db.or_(
                        TgGroupSession.user_id == '',
                        TgGroupSession.user_id.is_(None)
                    ),
                    TgGroupSession.chat_id == group.chat_id
                ).first()

                if empty_user_session:
                    # 在修复前，检查修复后是否会与现有记录重复
                    potential_duplicate = TgGroupSession.query.filter_by(
                        user_id=account_dto['user_id'],
                        chat_id=group.chat_id
                    ).first()

                    if potential_duplicate:
                        # 如果修复后会重复，删除空记录，保留正常记录
                        db.session.delete(empty_user_session)
                        # 更新正常记录的session_name（如果需要）
                        if potential_duplicate.session_name != account_dto['name']:
                            potential_duplicate.session_name = account_dto['name']
                        db.session.commit()

                        stats['merged_duplicate_sessions'] += 1
                        logger.info(f"删除空user_id记录并保留正常记录: chat_id={group.chat_id}, user_id={account_dto['user_id']}")
                    else:
                        # 修复空user_id记录
                        empty_user_session.user_id = account_dto['user_id']
                        empty_user_session.session_name = account_dto['name']
                        db.session.commit()

                        stats['updated_empty_sessions'] += 1
                        logger.info(f"修复空user_id记录: chat_id={group.chat_id}, 设置user_id={account_dto['user_id']}, session_name={account_dto['name']}")

                    continue

                # 检查是否已存在正常的会话记录
                existing_session = TgGroupSession.query.filter_by(
                    user_id=account_dto['user_id'],
                    chat_id=group.chat_id
                ).first()

                if existing_session:
                    # 更新会话名称（如果不同）
                    if existing_session.session_name != account_dto['name']:
                        existing_session.session_name = account_dto['name']
                        db.session.commit()
                        logger.debug(f"更新会话名称: chat_id={group.chat_id}, session_name={account_dto['name']}")

                    stats['existing_sessions'] += 1
                else:
                    # 创建新的会话记录
                    new_session = TgGroupSession(
                        user_id=account_dto['user_id'],
                        chat_id=group.chat_id,
                        session_name=account_dto['name']
                    )

                    db.session.add(new_session)
                    db.session.commit()

                    stats['new_sessions'] += 1
                    logger.info(f"创建新会话记录: user_id={account_dto['user_id']}, chat_id={group.chat_id}, session_name={account_dto['name']}")

            except Exception as e:
                error_msg = f"处理群组会话失败 chat_id={group.chat_id}: {str(e)}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
                db.session.rollback()
        
        logger.info(f"账户 {account_dto['name']} 会话关系同步完成: "
                   f"总计 {stats['total_groups']} 个群组, "
                   f"新增 {stats['new_sessions']} 个会话, "
                   f"已存在 {stats['existing_sessions']} 个会话, "
                   f"修复空user_id记录 {stats['updated_empty_sessions']} 个, "
                   f"合并重复记录 {stats['merged_duplicate_sessions']} 个")

    except Exception as e:
        error_msg = f"同步账户 {account_dto['name']} 会话关系时发生异常: {str(e)}"
        logger.error(error_msg)
        stats['errors'].append(error_msg)

    return stats


@celery.task(name='jd.tasks.telegram.tg_fetch_group_info.fetch_all_accounts_group_info', bind=False, queue='jd.celery.telegram')
def fetch_all_accounts_group_info() -> Dict[str, Any]:
    """
    获取所有成功登录账户的群组信息

    Note: 这是一个串行处理任务，逐个处理账户以避免资源冲突
    使用 DTO 模式避免 SQLAlchemy 会话分离错误

    Returns:
        Dict[str, Any]: 批量任务执行结果
    """
    logger.info("开始批量获取所有账户的群组信息")

    result = {
        'success': True,
        'message': '',
        'total_accounts': 0,
        'success_accounts': 0,
        'failed_accounts': 0,
        'account_results': []
    }

    try:
        # 步骤 1: 查询所有成功登录的账户并立即转换为 DTO（字典）
        # 这避免了后续操作中 ORM 对象的会话分离问题
        account_dtos = [
            {
                'id': acc.id,
                'name': acc.name,
                'user_id': acc.user_id,
                'status': acc.status
            }
            for acc in TgAccount.query.filter_by(status=TgAccount.StatusType.JOIN_SUCCESS).all()
        ]
        result['total_accounts'] = len(account_dtos)

        logger.info(f"找到 {len(account_dtos)} 个已成功登录的账户")

        # 步骤 2: 使用 DTO 处理，不依赖 ORM 对象
        for account_dto in account_dtos:
            try:
                logger.info(f"处理账户: {account_dto['name']} (ID: {account_dto['id']})")

                # 直接调用任务函数，而不使用apply().get()
                # 这避免了Celery中不允许的阻塞操作
                task = FetchAccountGroupInfoTask(account_dto['id'])
                account_result = task.start_task()

                result['account_results'].append(account_result)

                if account_result.get('success', False):
                    result['success_accounts'] += 1
                    logger.info(f"账户 {account_dto['name']} 处理成功")
                else:
                    result['failed_accounts'] += 1
                    logger.warning(f"账户 {account_dto['name']} 处理失败: {account_result.get('message', 'Unknown error')}")

            except Exception as e:
                error_msg = f"处理账户 {account_dto['name']} (ID: {account_dto['id']}) 时发生异常: {str(e)}"
                logger.error(error_msg)

                result['failed_accounts'] += 1
                result['account_results'].append({
                    'success': False,
                    'message': error_msg,
                    'account_id': account_dto['id'],
                    'account_name': account_dto['name']
                })

        # 生成汇总信息
        result['message'] = f"批量处理完成: 总计 {result['total_accounts']} 个账户, " \
                           f"成功 {result['success_accounts']} 个, " \
                           f"失败 {result['failed_accounts']} 个"

        logger.info(result['message'])

    except Exception as e:
        result['success'] = False
        result['message'] = f"批量获取群组信息失败: {str(e)}"
        logger.error(result['message'])

    return result

