-- ============================================================================
-- Ad-Analysis 模块：从 Redis 缓存迁移到 MySQL 每日统计表
-- 文件: ad_tracking_daily_stats_tables_20260110.sql
-- 描述: 创建 4 个每日统计表，支持全局统计数据预计算
-- ============================================================================

-- 表 1: 黑词每日统计表
CREATE TABLE IF NOT EXISTS `ad_tracking_dark_keyword_daily_stats` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `stat_date` DATE NOT NULL COMMENT '统计日期',
    `drug_id` INT DEFAULT NULL COMMENT '毒品ID',
    `category_id` INT DEFAULT NULL COMMENT '分类ID',
    `keyword_count` INT DEFAULT 0 COMMENT '关键词出现总次数',
    `message_count` INT DEFAULT 0 COMMENT '包含该关键词的消息数',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_dark_keyword_daily` (`stat_date`, `drug_id`, `category_id`),
    KEY `idx_stat_date` (`stat_date`),
    KEY `idx_drug_id` (`drug_id`),
    KEY `idx_category_id` (`category_id`),
    KEY `idx_daily_stats_composite` (`stat_date`, `drug_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='广告追踪-黑词每日统计';

-- 表 2: 交易方式每日统计表
CREATE TABLE IF NOT EXISTS `ad_tracking_transaction_method_daily_stats` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `stat_date` DATE NOT NULL COMMENT '统计日期',
    `method` VARCHAR(50) DEFAULT NULL COMMENT '交易方式',
    `tag_id` INT DEFAULT NULL COMMENT '标签ID',
    `record_count` INT DEFAULT 0 COMMENT '记录数量',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_transaction_method_daily` (`stat_date`, `method`, `tag_id`),
    KEY `idx_stat_date` (`stat_date`),
    KEY `idx_method` (`method`),
    KEY `idx_tag_id` (`tag_id`),
    KEY `idx_transaction_daily_composite` (`stat_date`, `method`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='广告追踪-交易方式每日统计';

-- 表 3: 价格每日统计表
CREATE TABLE IF NOT EXISTS `ad_tracking_price_daily_stats` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `stat_date` DATE NOT NULL COMMENT '统计日期',
    `unit` VARCHAR(20) DEFAULT NULL COMMENT '价格单位',
    `avg_price` DECIMAL(10, 2) DEFAULT 0.00 COMMENT '平均价格',
    `min_price` DECIMAL(10, 2) DEFAULT 0.00 COMMENT '最低价格',
    `max_price` DECIMAL(10, 2) DEFAULT 0.00 COMMENT '最高价格',
    `record_count` INT DEFAULT 0 COMMENT '记录数量',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_price_daily` (`stat_date`, `unit`),
    KEY `idx_stat_date` (`stat_date`),
    KEY `idx_unit` (`unit`),
    KEY `idx_price_daily_composite` (`stat_date`, `unit`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='广告追踪-价格每日统计';

-- 表 4: 地理位置每日统计表
CREATE TABLE IF NOT EXISTS `ad_tracking_geo_location_daily_stats` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `stat_date` DATE NOT NULL COMMENT '统计日期',
    `province` VARCHAR(50) DEFAULT NULL COMMENT '省份',
    `city` VARCHAR(50) DEFAULT NULL COMMENT '城市',
    `record_count` INT DEFAULT 0 COMMENT '记录数量',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_geo_daily` (`stat_date`, `province`, `city`),
    KEY `idx_stat_date` (`stat_date`),
    KEY `idx_province` (`province`),
    KEY `idx_city` (`city`),
    KEY `idx_geo_daily_composite` (`stat_date`, `province`, `city`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='广告追踪-地理位置每日统计';
