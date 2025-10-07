-- ================================================
-- 广告追踪预警系统 - 数据库建表语句 (DDL)
-- 创建时间: 2025-10-04
-- ================================================

-- ================================================
-- 广告追踪核心表
-- ================================================

-- 广告追踪表
CREATE TABLE `ad_tracking` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content` text NOT NULL COMMENT '原始内容（URL、@账户、Telegraph链接等）',
  `content_type` enum('url','telegram_account','t_me_invite','t_me_channel_msg','t_me_private_invite','telegraph') NOT NULL COMMENT '内容类型',
  `normalized_content` text NOT NULL COMMENT '标准化后的内容',
  `extra_info` json DEFAULT NULL COMMENT '额外信息（JSON格式，如网站类型、钓鱼检测结果、@账户类型等）',
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
  INDEX `idx_last_seen` (`last_seen`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪表';

-- ================================================
-- 商家实体识别（未来扩展功能）
-- ================================================

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

-- ================================================
-- 广告标签关联
-- ================================================

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
