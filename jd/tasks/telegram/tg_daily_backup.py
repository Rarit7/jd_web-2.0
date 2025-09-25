from jd.utils.logging_config import get_logger
from datetime import date, datetime

from jCelery import celery
from jd import app, db
from jd.models.tg_group_status import TgGroupStatus

logger = get_logger('jd.tasks.tg.tg_daily_backup', {'component': 'telegram', 'module': 'daily_backup'})


@celery.task(bind=True, queue='jd.celery.telegram')
def daily_backup_group_stats(self):
    """
    每日备份群组统计数据到previous字段
    
    该任务会：
    1. 将所有群组的 members_now 备份到 members_previous
    2. 将所有群组的 records_now 备份到 records_previous
    3. 记录备份的群组数量和时间
    
    推荐执行时间：每日凌晨 00:00
    """
    with app.app_context():
        try:
            backup_date = date.today()
            logger.info(f"开始执行每日群组数据备份任务 - {backup_date}")
            
            # 获取所有群组状态记录
            all_status = TgGroupStatus.query.all()
            
            if not all_status:
                logger.warning("未找到任何群组状态记录，跳过备份")
                return {
                    'success': True,
                    'message': '未找到任何群组状态记录',
                    'backup_count': 0,
                    'backup_date': str(backup_date)
                }
            
            backup_count = 0
            updated_groups = []
            
            for status in all_status:
                # 备份成员数据
                old_members_previous = status.members_previous
                old_records_previous = status.records_previous
                
                status.members_previous = status.members_now
                status.records_previous = status.records_now
                
                # 记录变更信息
                if (old_members_previous != status.members_now or 
                    old_records_previous != status.records_now):
                    updated_groups.append({
                        'chat_id': status.chat_id,
                        'members_backup': f"{old_members_previous} → {status.members_now}",
                        'records_backup': f"{old_records_previous} → {status.records_now}"
                    })
                
                backup_count += 1
            
            # 批量提交数据库更改
            db.session.commit()
            
            # 记录详细信息
            logger.info(f"每日数据备份完成 - 备份日期: {backup_date}, 处理群组数: {backup_count}")
            
            if updated_groups:
                logger.info(f"有数据变更的群组数: {len(updated_groups)}")
                for group_info in updated_groups[:5]:  # 只记录前5个，避免日志过长
                    logger.debug(f"群组 {group_info['chat_id']}: "
                               f"成员 {group_info['members_backup']}, "
                               f"消息 {group_info['records_backup']}")
                if len(updated_groups) > 5:
                    logger.debug(f"... 还有 {len(updated_groups) - 5} 个群组有数据变更")
            
            return {
                'success': True,
                'message': '每日群组数据备份成功',
                'backup_count': backup_count,
                'updated_count': len(updated_groups),
                'backup_date': str(backup_date),
                'task_id': self.request.id
            }
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"每日数据备份失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Celery任务失败，抛出异常以便重试
            raise Exception(error_msg)


@celery.task(bind=True, queue='jd.celery.telegram')
def backup_single_group_stats(self, chat_id):
    """
    备份单个群组的统计数据
    
    :param chat_id: 群组ID
    :return: 备份结果
    """
    with app.app_context():
        try:
            logger.info(f"开始备份单个群组数据 - chat_id: {chat_id}")
            
            # 查找指定群组
            status = TgGroupStatus.query.filter_by(chat_id=str(chat_id)).first()
            
            if not status:
                logger.warning(f"未找到群组 {chat_id} 的状态记录")
                return {
                    'success': False,
                    'message': f'未找到群组 {chat_id} 的状态记录',
                    'chat_id': chat_id
                }
            
            # 备份数据
            old_members_previous = status.members_previous
            old_records_previous = status.records_previous
            
            status.members_previous = status.members_now
            status.records_previous = status.records_now
            
            db.session.commit()
            
            logger.info(f"单个群组数据备份完成 - chat_id: {chat_id}, "
                       f"成员: {old_members_previous} → {status.members_now}, "
                       f"消息: {old_records_previous} → {status.records_now}")
            
            return {
                'success': True,
                'message': '单个群组数据备份成功',
                'chat_id': chat_id,
                'members_backup': f"{old_members_previous} → {status.members_now}",
                'records_backup': f"{old_records_previous} → {status.records_now}",
                'task_id': self.request.id
            }
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"单个群组数据备份失败 - chat_id: {chat_id}, 错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)


@celery.task(queue='jd.celery.telegram')
def get_backup_stats():
    """
    获取备份统计信息
    
    :return: 统计信息
    """
    with app.app_context():
        try:
            total_groups = TgGroupStatus.query.count()
            
            # 统计有数据的群组
            groups_with_members = TgGroupStatus.query.filter(TgGroupStatus.members_now > 0).count()
            groups_with_records = TgGroupStatus.query.filter(TgGroupStatus.records_now > 0).count()
            
            # 统计previous字段与now字段相同的群组（最近备份过的）
            synced_members = TgGroupStatus.query.filter(
                TgGroupStatus.members_previous == TgGroupStatus.members_now
            ).count()
            synced_records = TgGroupStatus.query.filter(
                TgGroupStatus.records_previous == TgGroupStatus.records_now
            ).count()
            
            stats = {
                'total_groups': total_groups,
                'groups_with_members': groups_with_members,
                'groups_with_records': groups_with_records,
                'synced_members_count': synced_members,
                'synced_records_count': synced_records,
                'last_check': datetime.now().isoformat()
            }
            
            logger.info(f"备份统计信息: {stats}")
            return stats
            
        except Exception as e:
            error_msg = f"获取备份统计信息失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)