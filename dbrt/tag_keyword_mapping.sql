-- ================================================
-- 标签关键词功能建表语句
-- 用于支持自动标签功能
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
CREATE TABLE `auto_tag_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tg_user_id` int(11) NOT NULL COMMENT 'TG用户ID',
  `tag_id` int(11) NOT NULL COMMENT '标签ID',
  `keyword` varchar(255) NOT NULL COMMENT '触发的关键词',
  `source_type` enum('chat','nickname','desc') NOT NULL COMMENT '来源类型',
  `source_id` varchar(128) DEFAULT NULL COMMENT '来源记录ID',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_tag` (`tg_user_id`, `tag_id`),
  INDEX `idx_source` (`source_type`, `source_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='自动标签记录表';