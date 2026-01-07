-- ================================================
-- 广告追踪系统 - 新增数据表
-- 创建日期：2025-01-05
-- 说明：包含地理位置、价格、交易方式和批次处理四个核心表
-- 注意：不使用外键约束，只使用索引
-- ================================================


-- ================================================
-- 表1：ad_tracking_geo_location（地理位置记录表）
-- ================================================
-- 用途：存储从聊天记录中提取的地理位置信息
-- 创建日期：2025-01-05

CREATE TABLE IF NOT EXISTS `ad_tracking_geo_location` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `chat_id` VARCHAR(128) NOT NULL COMMENT '群组ID',
    `message_id` VARCHAR(128) NOT NULL COMMENT '消息ID',
    `province` VARCHAR(50) DEFAULT NULL COMMENT '省份',
    `city` VARCHAR(50) DEFAULT NULL COMMENT '城市',
    `district` VARCHAR(50) DEFAULT NULL COMMENT '区县',
    `keyword_matched` VARCHAR(100) DEFAULT NULL COMMENT '匹配的关键词',
    `latitude` DECIMAL(10, 8) DEFAULT NULL COMMENT '纬度',
    `longitude` DECIMAL(11, 8) DEFAULT NULL COMMENT '经度',
    `msg_date` DATE DEFAULT NULL COMMENT '消息日期',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_province` (`province`),
    KEY `idx_city` (`city`),
    KEY `idx_msg_date` (`msg_date`),
    KEY `idx_chat_id` (`chat_id`),
    KEY `idx_message_id` (`message_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪-地理位置记录';


-- ================================================
-- 表2：ad_tracking_price（价格记录表）
-- ================================================
-- 用途：存储从聊天记录中通过正则提取的价格信息
-- 创建日期：2025-01-05

CREATE TABLE IF NOT EXISTS `ad_tracking_price` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `chat_id` VARCHAR(128) NOT NULL COMMENT '群组ID',
    `message_id` VARCHAR(128) NOT NULL COMMENT '消息ID',
    `price_value` DECIMAL(10, 2) DEFAULT NULL COMMENT '价格数值',
    `unit` VARCHAR(20) DEFAULT NULL COMMENT '价格单位',
    `extracted_text` VARCHAR(200) DEFAULT NULL COMMENT '提取的原始文本',
    `msg_date` DATE DEFAULT NULL COMMENT '消息日期',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_chat_id` (`chat_id`),
    KEY `idx_msg_date` (`msg_date`),
    KEY `idx_unit` (`unit`),
    KEY `idx_message_id` (`message_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪-价格记录';


-- ================================================
-- 表3：ad_tracking_transaction_method（交易方式记录表）
-- ================================================
-- 用途：存储识别到的交易方式（埋包、面交、邮寄等）
-- 创建日期：2025-01-05

CREATE TABLE IF NOT EXISTS `ad_tracking_transaction_method` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `chat_id` VARCHAR(128) NOT NULL COMMENT '群组ID',
    `message_id` VARCHAR(128) NOT NULL COMMENT '消息ID',
    `method` VARCHAR(50) DEFAULT NULL COMMENT '交易方式',
    `tag_id` INT DEFAULT NULL COMMENT '标签ID',
    `msg_date` DATE DEFAULT NULL COMMENT '消息日期',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_method` (`method`),
    KEY `idx_msg_date` (`msg_date`),
    KEY `idx_chat_id` (`chat_id`),
    KEY `idx_tag_id` (`tag_id`),
    KEY `idx_message_id` (`message_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪-交易方式记录';


-- ================================================
-- 表4：ad_tracking_batch_process_log（批次处理日志表）
-- ================================================
-- 用途：记录管理页面手动处理的批次信息，用于跟踪和重现处理历史
-- 创建日期：2025-01-05

CREATE TABLE IF NOT EXISTS `ad_tracking_batch_process_log` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `batch_id` VARCHAR(36) NOT NULL COMMENT '批次ID（UUID）',
    `chat_id` VARCHAR(128) NOT NULL COMMENT '群组ID',
    `selected_tags` JSON DEFAULT NULL COMMENT '选中的标签（JSON数组）',
    `selected_geo_tag` INT DEFAULT NULL COMMENT '选中的地理位置标签ID',
    `selected_method_tag` INT DEFAULT NULL COMMENT '选中的交易方式标签ID',
    `include_price` BOOLEAN DEFAULT FALSE COMMENT '是否包含价格提取',
    `total_messages` INT DEFAULT 0 COMMENT '总消息数',
    `success_count` INT DEFAULT 0 COMMENT '成功处理数',
    `fail_count` INT DEFAULT 0 COMMENT '失败处理数',
    `progress` INT DEFAULT 0 COMMENT '处理进度（百分比）',
    `status` ENUM('processing', 'success', 'failed') DEFAULT 'processing' COMMENT '处理状态',
    `start_time` DATETIME DEFAULT NULL COMMENT '开始时间',
    `end_time` DATETIME DEFAULT NULL COMMENT '结束时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_batch_id` (`batch_id`),
    KEY `idx_chat_id` (`chat_id`),
    KEY `idx_status` (`status`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪-批次处理日志';


-- ================================================
-- 复合索引（性能优化）
-- ================================================

-- 地理位置查询优化（按群组、日期、地区聚合查询）
CREATE INDEX idx_geo_tracking_composite
ON ad_tracking_geo_location(chat_id, msg_date, province, city);

-- 价格查询优化（按群组、日期、单位聚合查询）
CREATE INDEX idx_price_tracking_composite
ON ad_tracking_price(chat_id, msg_date, unit);

-- 交易方式查询优化（按群组、日期、方式聚合查询）
CREATE INDEX idx_transaction_method_composite
ON ad_tracking_transaction_method(chat_id, msg_date, method);


-- ================================================
-- 索引创建完成
-- ================================================
-- 所有表和索引已成功创建
-- 可以开始使用这些表进行广告追踪数据的存储和查询
