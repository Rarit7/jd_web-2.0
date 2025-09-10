import logging
from typing import Dict, Any

from jd.jobs.tg_chat_history import ExsitedGroupHistoryFetcher
from jd.tasks.base_task import AsyncBaseTask
from jCelery import celery

logger = logging.getLogger(__name__)


class TgHistoryTask(AsyncBaseTask):
    """Telegram群组聊天历史获取任务"""
    
    def __init__(self, session_name: str = None):
        # 这个任务是全局性的历史获取，不针对特定资源
        # 但需要使用实际的session来避免与其他Telegram任务冲突
        # 如果没有指定session，使用常用的默认session名称，确保能与其他任务正确排队
        actual_session = session_name or 'default2'  # 使用实际的session名称而非虚拟名称
        super().__init__(resource_id='', session_id=actual_session)
        # 设置冲突处理策略：同名任务或session冲突时排队等待，避免session争抢
        self.wait_if_conflict = True
    
    def get_job_name(self) -> str:
        return 'update_group_history'
    
    def generate_result_summary(self, result: Dict[str, Any]) -> str:
        """生成update_group_history任务的友好结果摘要"""
        if not result:
            return "任务完成，无结果数据"
            
        err_code = result.get('err_code', 0)
        if err_code != 0:
            return f"任务失败: {result.get('err_msg', '未知错误')}"
        
        payload = result.get('payload', {})
        if not payload:
            return "任务成功"
        
        # 提取统计信息
        stats = payload.get('statistics', {})
        duration = payload.get('duration_seconds', 0)
        
        # 格式化持续时间
        if duration > 0:
            if duration >= 60:
                duration_text = f"{duration/60:.1f}分钟"
            else:
                duration_text = f"{duration:.1f}秒"
        else:
            duration_text = "未知"
        
        # 提取群组和消息统计
        total_groups = stats.get('total_groups', 0)
        success_count = stats.get('success_count', 0)
        error_count = stats.get('error_count', 0)
        
        # 计算新增消息数（需要从processed_groups中提取）
        processed_groups = stats.get('processed_groups', [])
        total_new_messages = 0
        for group in processed_groups:
            if isinstance(group, dict):
                total_new_messages += group.get('new_messages_count', 0)
        
        # 构建结果摘要
        if total_groups > 0:
            result_parts = [f"任务成功，处理群 {success_count}/{total_groups} 个"]
            
            if total_new_messages > 0:
                result_parts.append(f"新增 {total_new_messages} 条消息记录")
            else:
                result_parts.append("无新消息")
            
            if error_count > 0:
                result_parts.append(f"{error_count} 个群组处理失败")
                
            result_parts.append(f"耗时 {duration_text}")
            
            return "，".join(result_parts)
        else:
            return f"任务成功，无群组处理，耗时 {duration_text}"
    
    async def execute_async_task(self) -> Dict[str, Any]:
        """执行Telegram历史获取任务"""
        import datetime
        from zoneinfo import ZoneInfo
        
        start_time = datetime.datetime.now(ZoneInfo('UTC'))
        logger.info('开始Telegram聊天实时获取任务...')
        
        fetcher = ExsitedGroupHistoryFetcher()
        try:
            # process_all_groups会根据每个群组自动选择合适的session并初始化
            # 执行历史获取任务，现在返回详细统计信息
            success, stats = await fetcher.process_all_groups()
            end_time = datetime.datetime.now(ZoneInfo('UTC'))
            
            if success:
                logger.info('Telegram聊天历史获取任务完成')
                return {
                    'err_code': 0,
                    'err_msg': '',
                    'payload': {
                        'status': 'completed',
                        'success': True,
                        'start_time': start_time.isoformat(),
                        'end_time': end_time.isoformat(),
                        'duration_seconds': (end_time - start_time).total_seconds(),
                        'session_name': self.session_id,
                        'statistics': stats
                    }
                }
            else:
                logger.warning('Telegram聊天历史获取任务未成功完成')
                return {
                    'err_code': 1,
                    'err_msg': 'Telegram聊天历史获取任务未成功完成',
                    'payload': {
                        'status': 'failed',
                        'success': False,
                        'start_time': start_time.isoformat(),
                        'end_time': end_time.isoformat(),
                        'duration_seconds': (end_time - start_time).total_seconds(),
                        'session_name': self.session_id,
                        'statistics': stats
                    }
                }
                
        except Exception as e:
            end_time = datetime.datetime.now(ZoneInfo('UTC'))
            error_msg = f'异步任务执行错误: {e}'
            logger.error(error_msg)
            return {
                'err_code': 1,
                'err_msg': error_msg,
                'payload': {
                    'status': 'error',
                    'success': False,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': (end_time - start_time).total_seconds(),
                    'session_name': self.session_id,
                    'exception': str(e),
                    'statistics': None
                }
            }
        finally:
            # 确保Telegram服务被关闭
            if fetcher:
                await fetcher.close_telegram_service()


@celery.task
def fetch_tg_history_job(session_name: str = None):
    """使用重构后的ExsitedGroupHistoryFetcher获取Telegram群组聊天历史
    
    Args:
        session_name: 可选的session名称，用于区分不同的历史获取任务
    """
    task = TgHistoryTask(session_name=session_name)
    return task.start_task()



if __name__ == '__main__':
    # 直接运行脚本进行测试
    from jd import app
    app.ready(db_switch=True, web_switch=False, worker_switch=True)
    fetch_tg_history_job()
