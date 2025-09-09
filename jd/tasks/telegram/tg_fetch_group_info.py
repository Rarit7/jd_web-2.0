import logging
import asyncio
from typing import Dict, Any, List

from jCelery import celery
from jd import db
from jd.jobs.tg_group_info import TgGroupInfoManager
from jd.tasks.base_task import BaseTask
from jd.models.tg_account import TgAccount
from jd.models.tg_group import TgGroup
from jd.models.tg_group_session import TgGroupSession

logger = logging.getLogger(__name__)


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
            # 查询账户信息
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
            
            # 调用群组信息同步方法
            # 使用 asyncio.run() 来执行异步方法
            result = asyncio.run(TgGroupInfoManager.sync_group_info_by_account(tg_account.name))
            
            if result['success']:
                # 同步成功后，建立账户-群组关系
                # 传递同步过程中处理的群组chat_id列表
                processed_chat_ids = result.get('processed_groups', [])
                session_result = _sync_account_group_sessions(tg_account, processed_chat_ids)
                result['session_stats'] = session_result
                
                # 填充tg_group表中缺失的account_id字段
                fill_result = _fill_missing_account_ids(tg_account, processed_chat_ids)
                result['fill_account_id_stats'] = fill_result
                
                logger.info(f"账户 {tg_account.name} 群组信息同步完成: {result['message']}")
                
                # 设置成功的错误码
                result['err_code'] = 0
                result['err_msg'] = ''
            else:
                logger.error(f"账户 {tg_account.name} 群组信息同步失败: {result['message']}")
                result['err_code'] = 1
                result['err_msg'] = result['message']
            
            # 添加账户信息到结果中
            result['account_id'] = self.account_id
            result['account_name'] = tg_account.name
            result['account_user_id'] = tg_account.user_id
            
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
    


def _fill_missing_account_ids(tg_account: TgAccount, processed_chat_ids: List[str] = None) -> Dict[str, Any]:
    """
    填充tg_group表中缺失的account_id字段
    
    Args:
        tg_account (TgAccount): TG账户对象
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
        logger.info(f"开始填充账户 {tg_account.name} 关联群组的account_id字段")
        
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
                group.account_id = tg_account.user_id
                stats['filled_groups'] += 1
                logger.info(f"填充群组 {group.name} (chat_id={group.chat_id}) 的account_id为: {tg_account.user_id}")
                
            except Exception as e:
                error_msg = f"填充群组account_id失败 chat_id={group.chat_id}: {str(e)}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        # 提交数据库变更
        if stats['filled_groups'] > 0:
            db.session.commit()
            logger.info(f"成功填充了 {stats['filled_groups']} 个群组的account_id")
        
        logger.info(f"账户 {tg_account.name} account_id填充完成: "
                   f"总计 {stats['total_groups']} 个群组, "
                   f"填充 {stats['filled_groups']} 个, "
                   f"已存在 {stats['already_filled']} 个")
        
    except Exception as e:
        error_msg = f"填充账户 {tg_account.name} 群组account_id时发生异常: {str(e)}"
        logger.error(error_msg)
        stats['errors'].append(error_msg)
        db.session.rollback()
    
    return stats


def _sync_account_group_sessions(tg_account: TgAccount, processed_chat_ids: List[str] = None) -> Dict[str, Any]:
    """
    同步账户-群组会话关系到tg_group_session表
    
    Args:
        tg_account (TgAccount): TG账户对象
        processed_chat_ids (List[str]): 要处理的群组chat_id列表，如果为None或空列表则跳过处理
        
    Returns:
        Dict[str, Any]: 同步统计结果
    """
    stats = {
        'total_groups': 0,
        'new_sessions': 0,
        'existing_sessions': 0,
        'errors': []
    }
    
    try:
        logger.info(f"开始同步账户 {tg_account.name} 的群组会话关系")
        
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
                # 检查是否已存在会话记录
                existing_session = TgGroupSession.query.filter_by(
                    user_id=tg_account.user_id,
                    chat_id=group.chat_id
                ).first()
                
                if existing_session:
                    # 更新会话名称（如果不同）
                    if existing_session.session_name != tg_account.name:
                        existing_session.session_name = tg_account.name
                        db.session.commit()
                        logger.debug(f"更新会话名称: chat_id={group.chat_id}, session_name={tg_account.name}")
                    
                    stats['existing_sessions'] += 1
                else:
                    # 创建新的会话记录
                    new_session = TgGroupSession(
                        user_id=tg_account.user_id,
                        chat_id=group.chat_id,
                        session_name=tg_account.name
                    )
                    
                    db.session.add(new_session)
                    db.session.commit()
                    
                    stats['new_sessions'] += 1
                    logger.info(f"创建新会话记录: user_id={tg_account.user_id}, chat_id={group.chat_id}, session_name={tg_account.name}")
                
            except Exception as e:
                error_msg = f"处理群组会话失败 chat_id={group.chat_id}: {str(e)}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
                db.session.rollback()
        
        logger.info(f"账户 {tg_account.name} 会话关系同步完成: "
                   f"总计 {stats['total_groups']} 个群组, "
                   f"新增 {stats['new_sessions']} 个会话, "
                   f"已存在 {stats['existing_sessions']} 个会话")
        
    except Exception as e:
        error_msg = f"同步账户 {tg_account.name} 会话关系时发生异常: {str(e)}"
        logger.error(error_msg)
        stats['errors'].append(error_msg)
    
    return stats


@celery.task
def fetch_all_accounts_group_info() -> Dict[str, Any]:
    """
    获取所有成功登录账户的群组信息
    
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
        # 查询所有成功登录的账户
        accounts = TgAccount.query.filter_by(status=TgAccount.StatusType.JOIN_SUCCESS).all()
        result['total_accounts'] = len(accounts)
        
        logger.info(f"找到 {len(accounts)} 个已成功登录的账户")
        
        for account in accounts:
            try:
                logger.info(f"处理账户: {account.name} (ID: {account.id})")
                account_result = fetch_account_group_info.apply(args=[account.id]).get()
                
                result['account_results'].append(account_result)
                
                if account_result['success']:
                    result['success_accounts'] += 1
                    logger.info(f"账户 {account.name} 处理成功")
                else:
                    result['failed_accounts'] += 1
                    logger.warning(f"账户 {account.name} 处理失败: {account_result['message']}")
                
            except Exception as e:
                error_msg = f"处理账户 {account.name} (ID: {account.id}) 时发生异常: {str(e)}"
                logger.error(error_msg)
                
                result['failed_accounts'] += 1
                result['account_results'].append({
                    'success': False,
                    'message': error_msg,
                    'account_id': account.id,
                    'account_name': account.name
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

