-- ================================================
-- 修复 tg_user_tag 表的 tg_user_id 字段类型
-- 问题: tg_user_id 定义为 int(11)，实际应存储 Telegram 用户ID（字符串类型）
-- 解决: 修改为 varchar(128) 以匹配 tg_group_user_info.user_id 字段类型
-- 创建时间: 2025-10-08
-- ================================================

-- 步骤1: 备份现有数据到临时表
CREATE TABLE IF NOT EXISTS `tg_user_tag_backup` LIKE `tg_user_tag`;
INSERT INTO `tg_user_tag_backup` SELECT * FROM `tg_user_tag`;

-- 步骤2: 创建映射：将 tg_group_user_info.id 映射到 user_id
-- 更新现有记录，将 tg_user_id (原为 tg_group_user_info.id) 替换为对应的 telegram user_id
UPDATE `tg_user_tag` t
JOIN `tg_group_user_info` u ON t.tg_user_id = u.id
SET t.tg_user_id = u.user_id;

-- 步骤3: 修改字段类型
ALTER TABLE `tg_user_tag`
  MODIFY COLUMN `tg_user_id` varchar(128) NOT NULL DEFAULT '' COMMENT 'Telegram用户ID';

-- 步骤4: 验证数据迁移
SELECT
    'tg_user_tag' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT tg_user_id) as unique_users
FROM `tg_user_tag`;

-- 步骤5: 如果验证通过，可以删除备份表（手动执行）
-- DROP TABLE IF EXISTS `tg_user_tag_backup`;

-- 验证修改
DESCRIBE `tg_user_tag`;
