#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
广告追踪测试数据插入脚本

用途：向数据库插入测试用的广告追踪数据，用于测试前端页面功能

使用方法：
    # 基础用法 - 插入100条随机测试数据
    python tests/insert_ad_tracking_test_data.py

    # 先清理后插入
    python tests/insert_ad_tracking_test_data.py --clean

    # 插入指定数量的记录
    python tests/insert_ad_tracking_test_data.py -n 200

    # 只显示统计信息
    python tests/insert_ad_tracking_test_data.py -s

    # ✨ 创建完整测试环境（推荐）
    python tests/insert_ad_tracking_test_data.py --comprehensive

功能说明：
    --comprehensive 模式会创建：
    1. 在 tg_group 表中添加群组 'test_ad_group'，ID=123456
       群组简介包含多种广告类型：
       google.com https://openai.com/zh-Hans-CN/gpt-5/ @telegramtips
       t.me/durov https://telegra.ph/api#getPageList

    2. 在 tg_group_user_info 表中添加用户 'test_ad_user'
       昵称："买手机上google.com"
       个人简介包含多种广告类型（同上）

    3. 在 tg_group_chat_history 表中添加 120 条群聊记录
       包含各种类型的广告（URL、@账户、t.me链接、Telegraph等）
       支持单一广告和复合广告

    4. 自动调用 AdTrackingJob API 提取广告信息
       写入 ad_tracking 表，支持后续前端测试

注意：这些测试数据不会自动删除，如需清理请使用 --clean 参数
"""

import sys
import os
import argparse
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jd import Application, db
from jd.models.ad_tracking import AdTracking
from jd.models.ad_tracking_tags import AdTrackingTags
from jd.models.result_tag import ResultTag
from jd.models.tg_group import TgGroup
from jd.models.tg_group_user_info import TgGroupUserInfo
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.jobs.ad_tracking_job import AdTrackingJob

# 创建并初始化应用
app = Application()
app.ready(db_switch=True, web_switch=False, worker_switch=False, socketio_switch=False)


# 测试数据模板 - 使用真实存在的域名
TEST_URLS = [
    'https://google.com/search',
    'https://baidu.com/s',
    'https://github.com/trending',
    'https://stackoverflow.com/questions',
    'https://wikipedia.org/wiki/Chemistry',
    'https://amazon.com/deals',
    'https://alibaba.com/products',
    'https://taobao.com/category',
    'https://jd.com/electronics',
    'https://reddit.com/r/programming',
]

# 测试商家名称
TEST_MERCHANTS = [
    '鑫源化工贸易',
    '华盛化学科技',
    '德诚实业',
    '永昌商贸',
    '通达化工',
    '锦绣贸易',
    '博雅科技',
    '诚信化学',
    '宏达实业',
    '金鼎贸易',
    '瑞丰化工',
    '泰和商贸',
    '恒通实业',
    '盛世化学',
    '昌盛贸易',
]

TEST_TELEGRAM_ACCOUNTS = [
    '@telegramtips',
    '@durov',
    '@telegram',
    '@telegramtips',
    '@durov',
    '@telegram',
    '@telegramtips',
    '@durov',
    '@telegram',
    '@telegramtips',
]

TEST_TME_INVITES = [
    'https://t.me/telegramtips',
    'https://t.me/durov',
    'https://t.me/telegram',
    'https://t.me/+SecretGroup456',
]

TEST_TME_CHANNELS = [
    'https://t.me/telegramtips/100',
    'https://t.me/durov/50',
    'https://t.me/telegram/200',
]

TEST_TELEGRAPH_LINKS = [
    'https://telegra.ph/Telegram-Features-01-15',
    'https://telegra.ph/Privacy-Update-02-20',
    'https://telegra.ph/API-Documentation-03-10',
]

TEST_USERS = [
    {'user_id': f'test_user_{i}', 'nickname': f'测试用户{i}'}
    for i in range(1, 21)
]

TEST_CHATS = [
    {'chat_id': f'test_chat_{i}', 'title': f'测试群组{i}'}
    for i in range(1, 11)
]

CONTENT_TYPE_TEMPLATES = {
    'url': TEST_URLS,
    'telegram_account': TEST_TELEGRAM_ACCOUNTS,
    't_me_invite': TEST_TME_INVITES,
    't_me_channel_msg': TEST_TME_CHANNELS,
    'telegraph': TEST_TELEGRAPH_LINKS,
}

SOURCE_TYPES = ['chat', 'user_desc', 'username', 'nickname', 'group_intro']

# 综合广告内容（用于测试群组简介、用户简介和聊天消息）
COMPREHENSIVE_AD_CONTENT = "google.com https://openai.com/zh-Hans-CN/gpt-5/ @telegramtips t.me/durov https://telegra.ph/api#getPageList"

# 聊天消息模板（包含各种广告类型和组合）
CHAT_MESSAGE_TEMPLATES = [
    # 单一广告类型
    "推荐一个好网站：google.com",
    "访问这里获取更多信息 https://openai.com/zh-Hans-CN/gpt-5/",
    "联系客服 @telegramtips 获取优惠",
    "加入频道 t.me/durov 了解最新动态",
    "阅读我们的文章 https://telegra.ph/api#getPageList",

    # 多种广告组合
    "购买产品请访问 example.com 或联系 @sales_bot",
    "特价促销！网址：promo-site.net 频道：t.me/deals_channel/123",
    "详情见 https://telegra.ph/Product-Details-12-01 或咨询 @customer_service",
    "全场5折！google.com | https://discount-store.com | @promo_alerts",

    # 包含中文和广告的混合消息
    "大家好，今天有个好消息分享 google.com",
    "需要化工原料的朋友可以访问 https://chemical-supplier.com/catalog",
    "我昨天买了个手机，很不错，推荐 www.sample-website.com",
    "有兴趣的加这个频道 t.me/trading_signals 获取信号",

    # 纯文本（无广告）
    "今天天气真好",
    "大家吃饭了吗？",
    "谢谢分享",
    "哈哈哈",

    # 复杂组合
    COMPREHENSIVE_AD_CONTENT,
    f"最新活动：{COMPREHENSIVE_AD_CONTENT}",
    f"联系我们：{COMPREHENSIVE_AD_CONTENT} 或打电话 400-123-4567",
]


def create_comprehensive_test_environment():
    """
    创建完整的测试环境，包括：
    1. 测试群组（test_ad_group）
    2. 测试用户（test_ad_user）
    3. 100+条聊天记录
    4. 调用API提取广告信息
    """
    print("\n" + "=" * 60)
    print("创建完整测试环境")
    print("=" * 60)

    # 1. 创建测试群组
    print("\n1. 创建测试群组...")
    test_chat_id = '-1001234567890'  # 使用负数群组ID（Telegram群组格式）
    test_group = TgGroup.query.filter_by(chat_id=test_chat_id).first()
    if test_group:
        print("  测试群组已存在，更新信息...")
        test_group.name = 'test_ad_group'
        test_group.title = '广告追踪测试群组'
        test_group.desc = COMPREHENSIVE_AD_CONTENT
        test_group.updated_at = datetime.now()
    else:
        print("  创建新的测试群组...")
        test_group = TgGroup(
            chat_id=test_chat_id,
            name='test_ad_group',
            title='广告追踪测试群组',
            desc=COMPREHENSIVE_AD_CONTENT,
            status=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.session.add(test_group)

    db.session.commit()
    print(f"  ✓ 群组创建完成: {test_group.name} (ID: {test_group.chat_id})")

    # 2. 创建测试用户
    print("\n2. 创建测试用户...")
    test_user_id = '9876543210'  # 使用纯数字用户ID
    test_user = TgGroupUserInfo.query.filter_by(
        user_id=test_user_id,
        chat_id=test_chat_id
    ).first()

    if test_user:
        print("  测试用户已存在，更新信息...")
        test_user.username = 'test_ad_user'
        test_user.nickname = '买手机上google.com'
        test_user.desc = COMPREHENSIVE_AD_CONTENT
        test_user.updated_at = datetime.now()
    else:
        print("  创建新的测试用户...")
        test_user = TgGroupUserInfo(
            user_id=test_user_id,
            chat_id=test_chat_id,
            username='test_ad_user',
            nickname='买手机上google.com',
            desc=COMPREHENSIVE_AD_CONTENT,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.session.add(test_user)

    db.session.commit()
    print(f"  ✓ 用户创建完成: {test_user.username} (ID: {test_user.user_id}, 昵称: {test_user.nickname})")

    # 3. 创建聊天记录
    print("\n3. 创建聊天记录...")
    # 先删除旧的测试聊天记录
    deleted_count = TgGroupChatHistory.query.filter(
        TgGroupChatHistory.chat_id == test_chat_id,
        TgGroupChatHistory.user_id == test_user_id
    ).delete(synchronize_session=False)
    if deleted_count > 0:
        print(f"  清理了 {deleted_count} 条旧聊天记录")

    # 创建100+条新记录
    base_date = datetime.now() - timedelta(days=30)
    message_count = 0

    for i in range(120):  # 创建120条，确保超过100
        # 随机选择消息模板
        message_text = random.choice(CHAT_MESSAGE_TEMPLATES)

        # 有些消息添加序号，增加多样性
        if random.random() < 0.3:
            message_text = f"[{i+1}] {message_text}"

        # 随机时间（过去30天内）
        msg_date = base_date + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        chat_message = TgGroupChatHistory(
            chat_id=test_chat_id,
            user_id=test_user_id,
            message_id=f'test_msg_{i}',
            message=message_text,
            postal_time=msg_date,
            created_at=msg_date
        )
        db.session.add(chat_message)
        message_count += 1

        # 每50条提交一次
        if message_count % 50 == 0:
            db.session.commit()
            print(f"  已创建 {message_count} 条聊天记录...")

    db.session.commit()
    print(f"  ✓ 聊天记录创建完成: {message_count} 条")

    # 4. 调用API提取广告信息
    print("\n4. 提取广告信息...")
    job = AdTrackingJob()

    # 处理群组简介
    print("  处理群组简介...")
    group_result = job.process_group_info(test_group)
    db.session.commit()  # 提交事务
    print(f"  ✓ 群组简介处理完成: 找到 {group_result.get('total_items', 0)} 条广告")

    # 处理用户信息
    print("  处理用户信息...")
    user_result = job.process_user_info(test_user)
    db.session.commit()  # 提交事务
    print(f"  ✓ 用户信息处理完成: 找到 {user_result.get('total_items', 0)} 条广告")

    # 处理聊天记录
    print("  处理聊天记录...")
    # 获取所有测试聊天记录
    test_messages = TgGroupChatHistory.query.filter_by(
        chat_id=test_chat_id,
        user_id=test_user_id
    ).all()

    chat_ads_count = 0
    processed_count = 0
    for message in test_messages:
        result = job.process_chat_record(message)
        if result:
            chat_ads_count += result.get('total_items', 0)
        processed_count += 1

        # 每30条提交一次并打印进度
        if processed_count % 30 == 0:
            db.session.commit()  # 提交事务
            print(f"  已处理 {processed_count}/{len(test_messages)} 条聊天记录，找到 {chat_ads_count} 条广告...")

    db.session.commit()  # 最后提交剩余的记录
    print(f"  ✓ 聊天记录处理完成: 找到 {chat_ads_count} 条广告")

    print("\n" + "=" * 60)
    print("完整测试环境创建成功！")
    print("=" * 60)

    return {
        'group': test_group,
        'user': test_user,
        'message_count': message_count,
        'ad_count': {
            'group': group_result.get('total_items', 0) if group_result else 0,
            'user': user_result.get('total_items', 0) if user_result else 0,
            'chat': chat_ads_count
        }
    }


def clean_test_data():
    """清理测试数据"""
    print("清理现有测试数据...")

    try:
        # 删除source_id以test_开头的记录
        deleted_count = AdTracking.query.filter(
            AdTracking.source_id.like('test_%')
        ).delete(synchronize_session=False)

        db.session.commit()
        print(f"已删除 {deleted_count} 条测试记录")
    except Exception as e:
        db.session.rollback()
        print(f"清理数据时出错: {e}")
        raise


def get_or_create_test_tags():
    """获取或创建测试用标签"""
    test_tag_names = ['促销', '广告', '商业推广', '诈骗可疑', '正常链接', '待审核']
    tag_ids = []

    for tag_name in test_tag_names:
        tag = ResultTag.query.filter_by(title=tag_name).first()
        if not tag:
            tag = ResultTag(
                title=tag_name,
                status=1,
                color='#409EFF'
            )
            db.session.add(tag)
            db.session.flush()
        tag_ids.append(tag.id)

    db.session.commit()
    return tag_ids


def generate_extra_info(content_type, content):
    """生成extra_info字段"""
    extra_info = {}

    if content_type == 'url':
        # 提取域名
        from urllib.parse import urlparse
        parsed = urlparse(content)
        domain = parsed.netloc or parsed.path.split('/')[0]
        extra_info = {
            'domain': domain,
            'url_type': random.choice(['general', 'ecommerce', 'social']),
            'is_phishing': random.choice([False, False, False, True]),  # 25% 概率
        }
    elif content_type == 'telegram_account':
        extra_info = {
            'account_type': random.choice(['bot', 'user', 'channel']),
            'is_verified': random.choice([True, False]),
        }
    elif content_type in ['t_me_invite', 't_me_channel_msg']:
        extra_info = {
            'link_type': 'private' if '+' in content or 'joinchat' in content else 'public',
            'is_valid': random.choice([True, True, True, False]),  # 75% 有效
        }
    elif content_type == 'telegraph':
        extra_info = {
            'article_title': content.split('/')[-1].replace('-', ' '),
            'language': random.choice(['zh', 'en']),
        }

    return extra_info


def insert_test_data(num_messages=50):
    """
    插入测试数据并调用 AdTrackingJob 提取广告

    Args:
        num_messages: 要创建的测试聊天记录数量
    """
    from jd.jobs.ad_tracking_job import AdTrackingJob

    print(f"开始创建测试数据并提取广告...")

    # 1. 创建测试群组 - 使用真实广告内容
    print("\n1. 创建测试群组...")
    test_groups = []
    group_descs = [
        '欢迎加入我们的群组！访问 https://google.com 了解更多信息',
        '最新产品发布！查看 https://github.com/trending 或联系 @telegramtips',
        '优惠活动进行中，详情见 https://baidu.com 或加入 https://t.me/durov',
        '技术交流群，推荐访问 https://stackoverflow.com 学习编程',
        '化工产品供应，联系 @telegram 或访问 https://alibaba.com'
    ]

    for i in range(1, 6):  # 创建5个测试群组
        chat_id = f'-100{1000000000 + i}'  # Telegram 群组 ID 格式：-100 开头的负数
        existing_group = TgGroup.query.filter_by(chat_id=chat_id).first()
        if not existing_group:
            group = TgGroup(
                chat_id=chat_id,
                name=f'test_group_{i}',
                title=f'测试群组{i}',
                desc=group_descs[i-1],  # 使用包含广告的简介
                status=1,
                created_at=datetime.now()
            )
            db.session.add(group)
            test_groups.append(group)
        else:
            # 更新现有群组的简介
            existing_group.desc = group_descs[i-1]
            test_groups.append(existing_group)
    db.session.commit()
    print(f"  ✓ 创建/更新了 {len(test_groups)} 个测试群组")

    # 2. 创建测试用户 - 使用真实广告内容
    print("\n2. 创建测试用户...")
    test_users = []
    user_descs = [
        '技术爱好者，关注 @telegramtips 获取最新消息和技术资讯',
        '访问 https://google.com 了解更多，或联系 @durov 咨询',
        '化工产品供应商，详情访问 https://alibaba.com 或 https://baidu.com',
        '编程学习资源分享，推荐 https://github.com 和 https://stackoverflow.com',
        '电商优惠信息发布，关注 https://jd.com 和 https://taobao.com',
        '加入我的频道 https://t.me/telegram 获取最新动态',
        '产品咨询请访问 https://amazon.com 或联系 @telegramtips',
        '技术交流群管理员，欢迎访问 https://wikipedia.org 学习知识',
        '推广专员，合作联系 @durov 或访问 https://reddit.com',
        '在线客服，咨询请访问 https://google.com 或加入 https://t.me/durov'
    ]

    for i in range(1, 11):  # 创建10个测试用户
        user_id = str(8000000000 + i)  # Telegram 用户 ID：纯数字字符串
        existing_user = TgGroupUserInfo.query.filter_by(user_id=user_id).first()
        if not existing_user:
            user = TgGroupUserInfo(
                user_id=user_id,
                chat_id=test_groups[i % len(test_groups)].chat_id,
                username=f'testuser{i}',
                nickname=f'测试用户{i}',
                desc=user_descs[i-1],
                created_at=datetime.now()
            )
            db.session.add(user)
            test_users.append(user)
        else:
            # 更新现有用户的简介
            existing_user.desc = user_descs[i-1]
            test_users.append(existing_user)
    db.session.commit()
    print(f"  ✓ 创建/更新了 {len(test_users)} 个测试用户")

    # 3. 创建测试聊天记录 - 使用多样的广告内容
    print(f"\n3. 创建 {num_messages} 条测试聊天记录...")
    test_messages = []

    # 准备多样的消息模板（包含真实广告）
    message_templates = [
        '大家好！推荐访问 https://google.com 搜索信息',
        '有兴趣的联系 @telegramtips 或访问 https://github.com',
        '最新优惠！详情见 https://baidu.com 或加入 https://t.me/durov',
        '技术交流，推荐 https://stackoverflow.com 学习',
        '化工产品咨询 @telegram 或访问 https://alibaba.com',
        '电商优惠 https://jd.com 和 https://taobao.com',
        '查看 https://amazon.com 获取产品信息',
        '学习资源 https://wikipedia.org 和 @durov',
        '社区讨论 https://reddit.com 或 @telegramtips',
        '加入频道 https://t.me/telegram 获取更新',
    ]

    for i in range(num_messages):
        user = test_users[i % len(test_users)]
        group = test_groups[i % len(test_groups)]
        message_text = message_templates[i % len(message_templates)]

        message = TgGroupChatHistory(
            chat_id=group.chat_id,
            user_id=user.user_id,
            message_id=f'test_msg_{i}',
            message=message_text,
            postal_time=datetime.now() - timedelta(days=random.randint(0, 30)),
            created_at=datetime.now()
        )
        db.session.add(message)
        db.session.flush()  # 获取ID
        test_messages.append(message)
    db.session.commit()
    print(f"  ✓ 创建了 {len(test_messages)} 条测试聊天记录")

    # 4. 调用 AdTrackingJob 提取广告
    print("\n4. 提取广告信息...")
    job = AdTrackingJob()
    total_ads = 0

    # 4.1 处理群组简介
    print("  处理群组简介...")
    group_ads = 0
    for group in test_groups:
        result = job.process_group_info(group)
        db.session.commit()  # 提交事务
        group_ads += result.get('total_items', 0)
    print(f"  ✓ 从群组简介提取了 {group_ads} 条广告")
    total_ads += group_ads

    # 4.2 处理用户信息
    print("  处理用户信息...")
    user_ads = 0
    for user in test_users:
        result = job.process_user_info(user)
        db.session.commit()  # 提交事务
        user_ads += result.get('total_items', 0)
    print(f"  ✓ 从用户信息提取了 {user_ads} 条广告")
    total_ads += user_ads

    # 4.3 处理聊天记录
    print(f"  处理 {len(test_messages)} 条聊天记录...")
    chat_ads = 0
    processed_count = 0
    for message in test_messages:
        result = job.process_chat_record(message)
        if result:
            chat_ads += result.get('total_items', 0)
        processed_count += 1

        # 每20条提交一次
        if processed_count % 20 == 0:
            db.session.commit()
            print(f"    已处理 {processed_count}/{len(test_messages)} 条，提取了 {chat_ads} 条广告...")

    db.session.commit()  # 最后提交一次
    print(f"  ✓ 从聊天记录提取了 {chat_ads} 条广告")
    total_ads += chat_ads

    print(f"\n{'='*60}")
    print(f"✓ 测试数据创建完成！")
    print(f"  - 创建群组: {len(test_groups)} 个")
    print(f"  - 创建用户: {len(test_users)} 个")
    print(f"  - 创建聊天记录: {len(test_messages)} 条")
    print(f"  - 提取广告记录: {total_ads} 条")
    print(f"{'='*60}\n")


def show_statistics():
    """显示数据统计"""
    print("\n" + "=" * 60)
    print("数据统计")
    print("=" * 60)

    total = AdTracking.query.filter(
        AdTracking.source_id.like('test_%')
    ).count()
    print(f"测试数据总数: {total}")

    # 按内容类型统计
    print("\n按内容类型分布:")
    for content_type in ['url', 'telegram_account', 't_me_invite', 't_me_channel_msg', 'telegraph']:
        count = AdTracking.query.filter(
            AdTracking.source_id.like('test_%'),
            AdTracking.content_type == content_type
        ).count()
        print(f"  {content_type}: {count}")

    # 按来源类型统计
    print("\n按来源类型分布:")
    for source_type in SOURCE_TYPES:
        count = AdTracking.query.filter(
            AdTracking.source_id.like('test_%'),
            AdTracking.source_type == source_type
        ).count()
        print(f"  {source_type}: {count}")

    # 总出现次数
    total_occurrences = db.session.query(
        db.func.sum(AdTracking.occurrence_count)
    ).filter(
        AdTracking.source_id.like('test_%')
    ).scalar() or 0
    print(f"\n累计出现次数: {total_occurrences}")

    # 涉及用户数
    unique_users = db.session.query(
        db.func.count(db.distinct(AdTracking.user_id))
    ).filter(
        AdTracking.source_id.like('test_%'),
        AdTracking.user_id.isnot(None)
    ).scalar() or 0
    print(f"涉及用户数: {unique_users}")

    # 涉及群组数
    unique_chats = db.session.query(
        db.func.count(db.distinct(AdTracking.chat_id))
    ).filter(
        AdTracking.source_id.like('test_%'),
        AdTracking.chat_id.isnot(None)
    ).scalar() or 0
    print(f"涉及群组数: {unique_chats}")

    print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='广告追踪测试数据插入工具')
    parser.add_argument('-n', '--num', type=int, default=100,
                       help='插入的记录数量（默认：100）')
    parser.add_argument('-c', '--clean', action='store_true',
                       help='插入前先清理现有测试数据')
    parser.add_argument('-s', '--stats', action='store_true',
                       help='只显示统计信息，不插入数据')
    parser.add_argument('--comprehensive', action='store_true',
                       help='创建完整测试环境（群组+用户+聊天记录+广告提取）')

    args = parser.parse_args()

    # 确保在应用上下文中运行
    ctx = app.app_context()
    ctx.push()

    try:
        if args.stats:
            # 只显示统计
            show_statistics()
        elif args.comprehensive:
            # 创建完整测试环境
            result = create_comprehensive_test_environment()
            print(f"\n测试环境摘要:")
            print(f"  群组: {result['group'].name}")
            print(f"  用户: {result['user'].username}")
            print(f"  聊天记录: {result['message_count']} 条")
            print(f"  提取的广告:")
            print(f"    - 群组简介: {result['ad_count']['group']} 条")
            print(f"    - 用户信息: {result['ad_count']['user']} 条")
            print(f"    - 聊天记录: {result['ad_count']['chat']} 条")
            print(f"    - 总计: {sum(result['ad_count'].values())} 条")
        else:
            # 清理（如果指定）
            if args.clean:
                clean_test_data()

            # 插入数据
            insert_test_data(args.num)

            # 显示统计
            show_statistics()

        print("\n✓ 完成！")
    finally:
        ctx.pop()


if __name__ == '__main__':
    main()
