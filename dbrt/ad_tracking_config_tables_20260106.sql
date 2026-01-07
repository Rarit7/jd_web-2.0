-- ================================================
-- 广告追踪系统 - 配置管理表
-- 创建日期：2026-01-06
-- 说明：包含交易方式配置、地理位置主数据等可管理配置表
-- ================================================


-- ================================================
-- 表1：ad_tracking_transaction_method_config（交易方式配置表）
-- ================================================
-- 用途：存储可配置的交易方式，支持实时启用/禁用，无需重启应用
-- 创建日期：2026-01-06

CREATE TABLE IF NOT EXISTS `ad_tracking_transaction_method_config` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `method_name` VARCHAR(50) NOT NULL UNIQUE COMMENT '交易方式名称（如：埋包、面交）',
    `display_name` VARCHAR(100) DEFAULT NULL COMMENT '显示名称',
    `description` TEXT DEFAULT NULL COMMENT '方式描述',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    `priority` INT DEFAULT 0 COMMENT '优先级（用于匹配顺序，值越大优先级越高）',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_method_name` (`method_name`),
    KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪-交易方式配置';


-- ================================================
-- 表2：ad_tracking_transaction_method_keyword（交易方式关键词表）
-- ================================================
-- 用途：存储交易方式的关键词，支持添加/删除/启用/禁用，用于AC自动机
-- 创建日期：2026-01-06

CREATE TABLE IF NOT EXISTS `ad_tracking_transaction_method_keyword` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `method_id` INT NOT NULL COMMENT '交易方式ID（关联ad_tracking_transaction_method_config）',
    `keyword` VARCHAR(100) NOT NULL COMMENT '关键词',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    `weight` INT DEFAULT 1 COMMENT '权重（AC自动机匹配优先级）',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_method_keyword` (`method_id`, `keyword`),
    KEY `idx_method_id` (`method_id`),
    KEY `idx_is_active` (`is_active`),
    CONSTRAINT `fk_keyword_method` FOREIGN KEY (`method_id`) REFERENCES `ad_tracking_transaction_method_config` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪-交易方式关键词配置';


-- ================================================
-- 表3：ad_tracking_geo_location_master（地理位置主数据表）
-- ================================================
-- 用途：存储中国所有地理位置数据（省、市、区县），支持坐标、别名、简称等扩展信息
-- 创建日期：2026-01-06

CREATE TABLE IF NOT EXISTS `ad_tracking_geo_location_master` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `level` INT NOT NULL COMMENT '行政级别(1=省份，2=城市，3=区县)',
    `name` VARCHAR(50) NOT NULL COMMENT '地名',
    `parent_id` INT DEFAULT NULL COMMENT '父级ID（上级行政区）',
    `code` VARCHAR(20) DEFAULT NULL UNIQUE COMMENT '行政区划代码（如：110000）',

    -- 坐标信息
    `latitude` DECIMAL(10, 8) DEFAULT NULL COMMENT '纬度',
    `longitude` DECIMAL(11, 8) DEFAULT NULL COMMENT '经度',

    -- 扩展字段
    `aliases` VARCHAR(500) DEFAULT NULL COMMENT '别名（逗号分隔，如：北京,京,燕京）',
    `short_name` VARCHAR(50) DEFAULT NULL COMMENT '简称（如：京）',
    `description` TEXT DEFAULT NULL COMMENT '描述',

    -- 状态字段
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',

    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (`id`),
    KEY `idx_level` (`level`),
    KEY `idx_name` (`name`),
    KEY `idx_parent_id` (`parent_id`),
    KEY `idx_code` (`code`),
    KEY `idx_is_active` (`is_active`),
    UNIQUE KEY `uk_level_name_parent` (`level`, `name`, `parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪-地理位置主数据';


-- ================================================
-- 视图：便于查询各级地理位置
-- ================================================

-- 省份视图
CREATE OR REPLACE VIEW v_provinces AS
SELECT `id`, `name`, `code`, `latitude`, `longitude`, `description`
FROM `ad_tracking_geo_location_master`
WHERE `level` = 1 AND `is_active` = TRUE;

-- 城市视图
CREATE OR REPLACE VIEW v_cities AS
SELECT
    g1.`id`,
    g1.`name` as `city_name`,
    g1.`code`,
    g2.`name` as `province_name`,
    g2.`id` as `province_id`,
    g1.`latitude`,
    g1.`longitude`,
    g1.`aliases`,
    g1.`short_name`
FROM `ad_tracking_geo_location_master` g1
LEFT JOIN `ad_tracking_geo_location_master` g2 ON g1.`parent_id` = g2.`id`
WHERE g1.`level` = 2 AND g1.`is_active` = TRUE;

-- 区县视图
CREATE OR REPLACE VIEW v_districts AS
SELECT
    g1.`id`,
    g1.`name` as `district_name`,
    g1.`code`,
    g3.`name` as `province_name`,
    g3.`id` as `province_id`,
    g2.`name` as `city_name`,
    g2.`id` as `city_id`,
    g1.`latitude`,
    g1.`longitude`,
    g1.`aliases`,
    g1.`short_name`
FROM `ad_tracking_geo_location_master` g1
LEFT JOIN `ad_tracking_geo_location_master` g2 ON g1.`parent_id` = g2.`id`
LEFT JOIN `ad_tracking_geo_location_master` g3 ON g2.`parent_id` = g3.`id`
WHERE g1.`level` = 3 AND g1.`is_active` = TRUE;


-- ================================================
-- 初始化默认数据（可选）
-- ================================================

-- 交易方式默认配置
INSERT INTO `ad_tracking_transaction_method_config` (`method_name`, `display_name`, `description`, `priority`)
VALUES
    ('埋包', '埋包', '地下埋藏交易方式', 10),
    ('面交', '面交（当面交易）', '当面交易方式', 20),
    ('邮寄', '邮寄（快递）', '快递邮寄方式', 30),
    ('自取', '自取', '自行取货方式', 40),
    ('物流', '物流', '物流配送方式', 50),
    ('快递', '快递', '快递配送方式', 60)
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

-- 为各交易方式添加关键词
-- 埋包相关关键词
INSERT INTO `ad_tracking_transaction_method_keyword` (`method_id`, `keyword`, `weight`)
SELECT `id`, '埋包', 3 FROM `ad_tracking_transaction_method_config` WHERE `method_name` = '埋包'
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

INSERT INTO `ad_tracking_transaction_method_keyword` (`method_id`, `keyword`, `weight`)
SELECT `id`, '埋', 2 FROM `ad_tracking_transaction_method_config` WHERE `method_name` = '埋包'
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

INSERT INTO `ad_tracking_transaction_method_keyword` (`method_id`, `keyword`, `weight`)
SELECT `id`, '地埋', 2 FROM `ad_tracking_transaction_method_config` WHERE `method_name` = '埋包'
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

-- 面交相关关键词
INSERT INTO `ad_tracking_transaction_method_keyword` (`method_id`, `keyword`, `weight`)
SELECT `id`, '面交', 3 FROM `ad_tracking_transaction_method_config` WHERE `method_name` = '面交'
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

INSERT INTO `ad_tracking_transaction_method_keyword` (`method_id`, `keyword`, `weight`)
SELECT `id`, '面', 1 FROM `ad_tracking_transaction_method_config` WHERE `method_name` = '面交'
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

INSERT INTO `ad_tracking_transaction_method_keyword` (`method_id`, `keyword`, `weight`)
SELECT `id`, '当面', 2 FROM `ad_tracking_transaction_method_config` WHERE `method_name` = '面交'
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

-- 邮寄相关关键词
INSERT INTO `ad_tracking_transaction_method_keyword` (`method_id`, `keyword`, `weight`)
SELECT `id`, '邮寄', 3 FROM `ad_tracking_transaction_method_config` WHERE `method_name` = '邮寄'
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

INSERT INTO `ad_tracking_transaction_method_keyword` (`method_id`, `keyword`, `weight`)
SELECT `id`, '寄', 1 FROM `ad_tracking_transaction_method_config` WHERE `method_name` = '邮寄'
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

-- 自取相关关键词
INSERT INTO `ad_tracking_transaction_method_keyword` (`method_id`, `keyword`, `weight`)
SELECT `id`, '自取', 3 FROM `ad_tracking_transaction_method_config` WHERE `method_name` = '自取'
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

INSERT INTO `ad_tracking_transaction_method_keyword` (`method_id`, `keyword`, `weight`)
SELECT `id`, '自', 1 FROM `ad_tracking_transaction_method_config` WHERE `method_name` = '自取'
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

-- 物流相关关键词
INSERT INTO `ad_tracking_transaction_method_keyword` (`method_id`, `keyword`, `weight`)
SELECT `id`, '物流', 2 FROM `ad_tracking_transaction_method_config` WHERE `method_name` = '物流'
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

-- 快递相关关键词
INSERT INTO `ad_tracking_transaction_method_keyword` (`method_id`, `keyword`, `weight`)
SELECT `id`, '快递', 3 FROM `ad_tracking_transaction_method_config` WHERE `method_name` = '快递'
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

INSERT INTO `ad_tracking_transaction_method_keyword` (`method_id`, `keyword`, `weight`)
SELECT `id`, '顺丰', 2 FROM `ad_tracking_transaction_method_config` WHERE `method_name` = '快递'
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

INSERT INTO `ad_tracking_transaction_method_keyword` (`method_id`, `keyword`, `weight`)
SELECT `id`, '中通', 2 FROM `ad_tracking_transaction_method_config` WHERE `method_name` = '快递'
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;

INSERT INTO `ad_tracking_transaction_method_keyword` (`method_id`, `keyword`, `weight`)
SELECT `id`, '圆通', 2 FROM `ad_tracking_transaction_method_config` WHERE `method_name` = '快递'
ON DUPLICATE KEY UPDATE `updated_at` = CURRENT_TIMESTAMP;


-- ================================================
-- 表创建完成
-- ================================================
-- 配置管理表及视图已成功创建
-- 支持实时更新交易方式和地理位置，无需重启应用
