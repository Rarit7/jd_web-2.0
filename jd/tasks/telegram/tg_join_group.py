import logging

from jCelery import celery
from jd import db
from jd.models.tg_group import TgGroup
from jd.models.tg_group_session import TgGroupSession
from jd.models.tg_group_status import TgGroupStatus
from jd.services.spider.tg import TgService

logger = logging.getLogger(__name__)


@celery.task
def join_group(group_name, sessionname='', current_user_id=None):
    print(f'{group_name} join...')
    
    async def _join_group():
        tg = None
        try:
            tg = await TgService.init_tg(sessionname)
            if not tg:
                logger.error(f'{group_name} 群聊加入失败: session ID={sessionname} 初始化TG失败')
                return f'{group_name} join group fail'
            
            tg_group = TgGroup.query.filter(TgGroup.name == group_name).first()
            if not tg_group:
                return f'{group_name} join group fail, group not exist'
            
            # 获取当前session对应的telegram用户信息
            myself = await tg.get_me()
            telegram_user_id = str(myself.id) if myself else ''
            
            result = await tg.join_conversation(group_name)
            chat_id = result.get('data', {}).get('id', 0)
            
            if result.get('result', 'Failed') == 'Failed':
                update_info = {
                    'status': TgGroup.StatusType.JOIN_FAIL
                }
            else:
                channel_full = await tg.get_full_channel(chat_id)
                logger.info(f'{group_name} 群聊加入成功: {channel_full}')
                
                # 获取群人数
                member_count = channel_full.get('member_count', 0)
                
                update_info = {
                    'status': TgGroup.StatusType.JOIN_SUCCESS,
                    'chat_id': chat_id,
                    'desc': channel_full.get("channel_description", ''),
                    'avatar_path': channel_full.get('photo_path', ''),
                    'title': channel_full.get("title", ''),
                    'group_type': TgGroup.GroupType.CHANNEL if channel_full.get('megagroup',
                                                                                '') == 'channel' else TgGroup.GroupType.GROUP,
                    'account_id': telegram_user_id  # 1. 更新account_id为session对应的telegram数字id
                }
                
                # 2. tg_group_session表：添加新的一行数据，建立用户和群聊的关系
                existing_session = TgGroupSession.query.filter_by(
                    user_id=telegram_user_id,
                    chat_id=str(chat_id),
                    session_name=sessionname
                ).first()
                
                if not existing_session:
                    tg_group_session = TgGroupSession(
                        user_id=telegram_user_id,
                        chat_id=str(chat_id),
                        session_name=sessionname
                    )
                    db.session.add(tg_group_session)
                
                # 3. tg_group_status表：处理群组状态信息
                existing_status = TgGroupStatus.query.filter_by(chat_id=str(chat_id)).first()
                
                if not existing_status:
                    # 首次出现的chat_id，创建新记录
                    tg_group_status = TgGroupStatus(
                        chat_id=str(chat_id),
                        members_now=member_count,
                        members_previous=0,
                        records_now=0,
                        records_previous=0,
                        jdweb_user_id=current_user_id or 0,
                        jdweb_tg_id=telegram_user_id
                    )
                    db.session.add(tg_group_status)
                else:
                    # chat_id已存在，只更新群人数信息
                    TgGroupStatus.query.filter_by(chat_id=str(chat_id)).update({
                        'members_previous': existing_status.members_now,
                        'members_now': member_count
                    })
            
            tg_groups = TgGroup.query.filter(TgGroup.chat_id == chat_id).order_by(TgGroup.id.desc()).all()
            # 处理不同username加入同一群组的情况
            if len(tg_groups) > 1:
                # 更新原来的群组信息
                TgGroup.query.filter(TgGroup.chat_id == chat_id).update(update_info)
                # 删除新的群组
                _id = tg_groups[-1].id
                TgGroup.query.filter_by(id=_id).delete()
            else:
                TgGroup.query.filter_by(name=group_name, status=TgGroup.StatusType.JOIN_ONGOING).update(update_info)
            
            db.session.commit()
            return f'{group_name} join group success'
        except Exception as e:
            logger.info('join_group error: {}'.format(e))
            db.session.rollback()
            return f'{group_name} join group fail: {e}'
        finally:
            # 确保无论成功还是失败都关闭 TG 客户端连接
            if tg:
                try:
                    await tg.close_client()
                    logger.info(f'{group_name} TG客户端连接已关闭')
                except Exception as close_error:
                    logger.error(f'{group_name} 关闭TG客户端时发生错误: {close_error}')
    
    # 使用 asyncio 来运行异步函数
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_join_group())
        return result
    finally:
        loop.close()