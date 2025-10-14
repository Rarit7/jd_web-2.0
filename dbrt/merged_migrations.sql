-- ================================================
-- JD Web 数据库迁移脚本合并文件
-- 包含除 ddl.sql 和 dml.sql 之外的所有数据库变更
-- 生成时间: 2025-10-13
-- ================================================

-- ================================================
-- 1. 标签关键词功能建表语句
-- 创建时间: 2025-09-23
-- ================================================

-- 标签关键词映射表
CREATE TABLE `tag_keyword_mapping` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tag_id` int(11) NOT NULL COMMENT '标签ID',
  `keyword` varchar(255) NOT NULL COMMENT '关键词',
  `is_active` tinyint(1) DEFAULT 1 COMMENT '是否启用',
  `auto_focus` tinyint(1) DEFAULT 0 COMMENT '是否自动加入特别关注',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tag_keyword` (`tag_id`, `keyword`),
  INDEX `idx_keyword` (`keyword`),
  INDEX `idx_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='标签关键词映射表';

-- 自动标签记录表（用于审计和去重）
-- 注: tg_user_id 使用 varchar(128) 以匹配 Telegram 用户ID 字符串类型
-- 注: 包含 detail_info JSON 字段用于存储用户昵称、聊天内容、匹配文本等详细信息
CREATE TABLE `auto_tag_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tg_user_id` varchar(128) NOT NULL COMMENT 'TG用户ID',
  `tag_id` int(11) NOT NULL COMMENT '标签ID',
  `keyword` varchar(255) NOT NULL COMMENT '触发的关键词',
  `source_type` enum('chat','nickname','desc') NOT NULL COMMENT '来源类型',
  `source_id` varchar(128) DEFAULT NULL COMMENT '来源记录ID',
  `detail_info` JSON NULL COMMENT '详细信息(JSON格式)',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_tag` (`tg_user_id`, `tag_id`),
  INDEX `idx_source` (`source_type`, `source_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='自动标签记录表';

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

-- ================================================
-- 2. 广告追踪预警系统 - 数据库建表语句
-- 创建时间: 2025-10-04
-- ================================================

-- 广告追踪表
-- 注: 包含 merchant_name 字段用于存储商家名称
CREATE TABLE `ad_tracking` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content` text NOT NULL COMMENT '原始内容（URL、@账户、Telegraph链接等）',
  `content_type` enum('url','telegram_account','t_me_invite','t_me_channel_msg','t_me_private_invite','telegraph') NOT NULL COMMENT '内容类型',
  `normalized_content` text NOT NULL COMMENT '标准化后的内容',
  `extra_info` json DEFAULT NULL COMMENT '额外信息（JSON格式，如网站类型、钓鱼检测结果、@账户类型等）',
  `merchant_name` varchar(255) DEFAULT NULL COMMENT '商家名称',
  `source_type` enum('chat','user_desc','username','nickname','group_intro') NOT NULL COMMENT '来源类型',
  `source_id` varchar(128) NOT NULL COMMENT '来源记录ID（消息ID、用户ID或群组ID）',
  `user_id` varchar(128) DEFAULT NULL COMMENT '用户ID（部分来源类型可能无用户ID）',
  `chat_id` varchar(128) DEFAULT NULL COMMENT '群组ID',
  `first_seen` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '首次发现时间',
  `last_seen` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后发现时间',
  `occurrence_count` int(11) DEFAULT 1 COMMENT '出现次数',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  INDEX `idx_content_type` (`content_type`),
  INDEX `idx_user` (`user_id`),
  INDEX `idx_chat` (`chat_id`),
  INDEX `idx_source` (`source_type`, `source_id`),
  INDEX `idx_normalized` (`normalized_content`(255)),
  INDEX `idx_first_seen` (`first_seen`),
  INDEX `idx_last_seen` (`last_seen`),
  INDEX `idx_merchant_name` (`merchant_name`(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪表';

-- 商家实体表
CREATE TABLE `ad_merchant` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `merchant_name` varchar(255) NOT NULL COMMENT '商家名称',
  `merchant_type` varchar(100) DEFAULT 'unknown' COMMENT '商家类型',
  `risk_level` enum('low','medium','high') DEFAULT 'low' COMMENT '风险等级',
  `identified_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '识别时间',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  INDEX `idx_merchant_name` (`merchant_name`(100)),
  INDEX `idx_risk_level` (`risk_level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告商家实体表';

-- 商家与广告记录关联表
CREATE TABLE `ad_merchant_tracking_relation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `merchant_id` int(11) NOT NULL COMMENT '商家ID',
  `tracking_id` int(11) NOT NULL COMMENT '广告追踪记录ID',
  `confidence_score` decimal(3,2) DEFAULT 1.00 COMMENT '关联置信度',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  INDEX `idx_merchant` (`merchant_id`),
  INDEX `idx_tracking` (`tracking_id`),
  FOREIGN KEY (`merchant_id`) REFERENCES `ad_merchant`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`tracking_id`) REFERENCES `ad_tracking`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商家与广告记录关联表';

-- 广告-标签关联表
CREATE TABLE `ad_tracking_tags` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ad_tracking_id` int(11) NOT NULL COMMENT '广告追踪记录ID',
  `tag_id` int(11) NOT NULL COMMENT '标签ID（关联tag_keyword_mapping表）',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ad_tag` (`ad_tracking_id`, `tag_id`),
  INDEX `idx_ad` (`ad_tracking_id`),
  INDEX `idx_tag` (`tag_id`),
  FOREIGN KEY (`ad_tracking_id`) REFERENCES `ad_tracking`(`id`) ON DELETE CASCADE
  -- 注意：tag_id 外键引用需要根据实际标签表名称调整
  -- FOREIGN KEY (`tag_id`) REFERENCES `tag_keyword_mapping`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪-标签关联表';

-- ================================================
-- 3. 修复 tg_user_tag 表的 tg_user_id 字段类型
-- 创建时间: 2025-10-08
-- 问题: tg_user_id 定义为 int(11)，实际应存储 Telegram 用户ID（字符串类型）
-- 解决: 修改为 varchar(128) 以匹配 tg_group_user_info.user_id 字段类型
-- 注意: 此表在 ddl.sql 中定义，需要单独执行 ALTER 语句
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

-- ================================================
-- 4. 创建私人聊天记录表
-- 执行时间: 2025-10-11
-- 说明: 优化版表结构，使用Telegram业务ID，去除冗余字段
-- ================================================

USE jd;

-- 如果表已存在则删除（谨慎使用）
-- DROP TABLE IF EXISTS `tg_person_chat_history`;

-- 创建私人聊天记录表（优化版：去除冗余字段，使用业务ID）
CREATE TABLE IF NOT EXISTS `tg_person_chat_history` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
  `chat_id` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '聊天ID（私聊中等于peer_user_id）',
  `message_id` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '消息ID',
  `owner_user_id` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '己方Telegram用户ID（关联tg_account.user_id）',
  `owner_session_name` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '己方Session名称（关联tg_account.name）',
  `peer_user_id` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '对方Telegram用户ID',
  `sender_type` ENUM('owner', 'peer') NOT NULL COMMENT '发送方类型：owner=己方，peer=对方',
  `message` TEXT NOT NULL COMMENT '消息内容',
  `postal_time` DATETIME NOT NULL DEFAULT '1970-10-30 00:00:00' COMMENT '消息发布时间（UTC+8北京时间）',
  `reply_to_msg_id` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '回复消息ID',
  `photo_path` VARCHAR(256) NOT NULL DEFAULT '' COMMENT '图片路径',
  `document_path` VARCHAR(256) NOT NULL DEFAULT '' COMMENT '文档路径',
  `document_ext` VARCHAR(16) NOT NULL DEFAULT '' COMMENT '文件后缀',
  `replies_info` TEXT NULL COMMENT '回复信息',
  `status` INT NOT NULL DEFAULT 0 COMMENT '状态',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

  KEY `idx_chat_id` (`chat_id`),
  KEY `idx_message_id` (`chat_id`, `message_id`),
  KEY `idx_owner_user` (`owner_user_id`),
  KEY `idx_owner_session` (`owner_session_name`),
  KEY `idx_peer_user` (`peer_user_id`),
  KEY `idx_postal_time` (`postal_time`),
  KEY `idx_sender_type` (`sender_type`),
  KEY `idx_owner_peer` (`owner_user_id`, `peer_user_id`),
  UNIQUE KEY `uk_chat_message` (`chat_id`, `message_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Telegram私人聊天记录表';

-- 验证表创建
SELECT 'Table tg_person_chat_history created successfully' AS result;

-- ================================================
-- 数据库迁移脚本合并完成
-- ================================================
