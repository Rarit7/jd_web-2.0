-- ================================================
-- 为 auto_tag_log 表添加 detail_info 字段
-- 目的: 减少表关联，在一个表中存储完整的上下文信息
-- 功能: 存储用户昵称、聊天内容、匹配文本等详细信息（JSON格式）
-- 创建时间: 2025-10-08
-- ================================================

-- 添加 detail_info JSON 字段
ALTER TABLE `auto_tag_log`
  ADD COLUMN `detail_info` JSON NULL COMMENT '详细信息(JSON格式)' AFTER `source_id`;

-- 验证修改
DESCRIBE `auto_tag_log`;

-- ================================================
-- detail_info 字段结构说明
-- ================================================
--
-- 聊天消息 (source_type = 'chat'):
-- {
--   "user_id": "123456789",
--   "user_nickname": "张三",
--   "user_username": "zhangsan",
--   "chat_id": "-1001234567890",
--   "chat_title": "测试群组",
--   "message_id": "98765",
--   "message_text": "我是山东人,来自青岛",
--   "message_date": "2025-10-08T10:30:00",
--   "matched_text": "山东人"
-- }
--
-- 用户昵称 (source_type = 'nickname'):
-- {
--   "user_id": "123456789",
--   "user_nickname": "张三",
--   "user_username": "zhangsan",
--   "old_nickname": "小张",
--   "new_nickname": "张三(山东)",
--   "matched_text": "山东"
-- }
--
-- 用户描述 (source_type = 'desc'):
-- {
--   "user_id": "123456789",
--   "user_nickname": "张三",
--   "user_username": "zhangsan",
--   "old_desc": "一个普通人",
--   "new_desc": "山东青岛人,从事化工行业",
--   "matched_text": "山东"
-- }
--
-- ================================================
