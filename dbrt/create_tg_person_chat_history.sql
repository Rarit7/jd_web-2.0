-- 私人聊天记录表创建脚本
-- 执行时间：2025-10-11
-- 说明：优化版表结构，使用Telegram业务ID，去除冗余字段

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
DESCRIBE tg_person_chat_history;
