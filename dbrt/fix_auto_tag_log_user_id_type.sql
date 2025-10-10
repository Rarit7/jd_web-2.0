-- ================================================
-- 修复 auto_tag_log 表的 tg_user_id 字段类型
-- 问题: tg_user_id 定义为 int(11)，但实际存储的是 Telegram 用户ID（字符串类型）
-- 解决: 修改为 varchar(128) 以匹配其他表的 user_id 字段类型
-- 创建时间: 2025-10-08
-- ================================================

-- 1. 删除依赖于 tg_user_id 的唯一索引
ALTER TABLE `auto_tag_log` DROP INDEX `uk_user_tag`;

-- 2. 修改 tg_user_id 字段类型为 varchar(128)
ALTER TABLE `auto_tag_log`
  MODIFY COLUMN `tg_user_id` varchar(128) NOT NULL COMMENT 'TG用户ID';

-- 3. 重新创建唯一索引
ALTER TABLE `auto_tag_log`
  ADD UNIQUE KEY `uk_user_tag` (`tg_user_id`, `tag_id`);

-- 验证修改
DESCRIBE `auto_tag_log`;
