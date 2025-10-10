from jd.utils.logging_config import get_logger

from jCelery import celery
from jd import db
from jd.models.tg_group import TgGroup
from jd.models.tg_group_session import TgGroupSession
from jd.models.tg_group_status import TgGroupStatus
from jd.services.spider.tg import TgService

logger = get_logger('jd.tasks.tg.tg_join_group', {'component': 'telegram', 'module': 'join_group'})


@celery.task
def join_group(group_name, sessionname='', current_user_id=None):
    logger.info(f'{sessionname} 尝试加入群组: {group_name} ...')

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
            if not myself or not myself.id:
                logger.error(f'{group_name} 群聊加入失败: 无法获取当前用户信息, session={sessionname}')
                return f'{group_name} join group fail: Cannot get user info'

            telegram_user_id = str(myself.id)

            result = await tg.join_conversation(group_name)

            # 调试日志：查看join_conversation的完整返回结果
            logger.info(f'{group_name} join_conversation返回结果: {result}')

            # 获取chat_id（Telethon 返回的正整数格式）
            # Telethon 会自动处理正负格式，统一使用正整数存储
            raw_chat_id = result.get('data', {}).get('id', '')

            if raw_chat_id:
                # 确保是整数类型
                chat_id = int(raw_chat_id) if isinstance(raw_chat_id, str) else raw_chat_id
            else:
                chat_id = ''
            
            if result.get('result', 'Failed') == 'Failed':
                # 根据错误信息判断失败原因
                error_message = result.get("reason", "Unknown error")

                # 检查是否是无效链接的常见错误信息
                if any(keyword in error_message.lower() for keyword in [
                    'expired', 'not valid anymore', '已过期', '不再有效',
                    'not found', 'invalid', 'does not exist', 'username not found',
                    'chat not found', 'peer not found', 'cannot find', '找不到', '无效'
                ]):
                    status = TgGroup.StatusType.INVALID_LINK
                    # 区分过期和其他无效情况
                    if any(k in error_message.lower() for k in ['expired', '已过期', 'not valid anymore']):
                        status_desc = 'invite link expired'
                    else:
                        status_desc = 'invalid link'
                else:
                    status = TgGroup.StatusType.JOIN_FAIL
                    status_desc = 'join failed'

                update_info = {
                    'status': status
                }
                # 当加入失败时，直接更新原记录，不进行chat_id相关的查询
                TgGroup.query.filter_by(name=group_name, status=TgGroup.StatusType.JOIN_ONGOING).update(update_info)
                db.session.commit()
                return f'{group_name} {status_desc}: {error_message}'
            else:
                # 检查chat_id是否有效
                if not chat_id or chat_id == '':
                    update_info = {
                        'status': TgGroup.StatusType.INVALID_LINK
                    }
                    TgGroup.query.filter_by(name=group_name, status=TgGroup.StatusType.JOIN_ONGOING).update(update_info)
                    db.session.commit()
                    return f'{group_name} invalid link: Invalid chat_id'

                # 尝试从join_conversation返回的结果中获取群组详细信息
                channel_full = result.get('data', {}).get('full_info')

                # 如果join_conversation已经返回了完整信息，直接使用
                if channel_full:
                    logger.info(f'{group_name} 群聊加入成功，已获取完整信息: {channel_full}')
                    member_count = channel_full.get('member_count', 0)
                else:
                    # 如果没有完整信息，尝试单独获取
                    logger.warning(f'{group_name} join_conversation未返回完整信息，尝试单独获取')
                    try:
                        channel_full = await tg.get_full_channel(chat_id)
                        logger.info(f'{group_name} 群聊加入成功: {channel_full}')
                        member_count = channel_full.get('member_count', 0)
                    except Exception as get_channel_error:
                        # get_full_channel失败，说明虽然join_conversation返回了chat_id，但实际无法访问该群组
                        error_msg = str(get_channel_error)
                        logger.error(f'{group_name} 获取群组详情失败: {error_msg}, chat_id={chat_id}')

                        # 判断失败类型
                        if any(keyword in error_msg.lower() for keyword in [
                            'cannot find', 'not found', 'no such', 'does not exist', '找不到', '不存在'
                        ]):
                            status = TgGroup.StatusType.INVALID_LINK
                            status_desc = 'invalid link'
                        else:
                            status = TgGroup.StatusType.JOIN_FAIL
                            status_desc = 'join failed'

                        TgGroup.query.filter_by(name=group_name, status=TgGroup.StatusType.JOIN_ONGOING).update({
                            'status': status
                        })
                        db.session.commit()
                        return f'{group_name} {status_desc}: {error_msg}'

                # 将chat_id转换为字符串用于数据库存储（保持正整数格式）
                chat_id_str = str(chat_id)

                update_info = {
                    'status': TgGroup.StatusType.JOIN_SUCCESS,
                    'chat_id': chat_id_str,
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
                    chat_id=chat_id_str,
                    session_name=sessionname
                ).first()

                if not existing_session:
                    tg_group_session = TgGroupSession(
                        user_id=telegram_user_id,
                        chat_id=chat_id_str,
                        session_name=sessionname
                    )
                    db.session.add(tg_group_session)

                # 3. tg_group_status表：处理群组状态信息
                existing_status = TgGroupStatus.query.filter_by(chat_id=chat_id_str).first()

                if not existing_status:
                    # 首次出现的chat_id，创建新记录
                    tg_group_status = TgGroupStatus(
                        chat_id=chat_id_str,
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
                    TgGroupStatus.query.filter_by(chat_id=chat_id_str).update({
                        'members_previous': existing_status.members_now,
                        'members_now': member_count
                    })

            # 只有当chat_id有效时才进行基于chat_id的查询和处理
            if chat_id and chat_id != '':
                tg_groups = TgGroup.query.filter(TgGroup.chat_id == chat_id_str).order_by(TgGroup.id.desc()).all()
                # 处理不同username加入同一群组的情况
                if len(tg_groups) > 1:
                    # 更新原来的群组信息
                    TgGroup.query.filter(TgGroup.chat_id == chat_id_str).update(update_info)
                    # 删除新的群组
                    _id = tg_groups[-1].id
                    TgGroup.query.filter_by(id=_id).delete()
                else:
                    TgGroup.query.filter_by(name=group_name, status=TgGroup.StatusType.JOIN_ONGOING).update(update_info)
            else:
                # 如果chat_id无效，只更新原来的记录状态
                TgGroup.query.filter_by(name=group_name, status=TgGroup.StatusType.JOIN_ONGOING).update({
                    'status': TgGroup.StatusType.INVALID_LINK
                })
            
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