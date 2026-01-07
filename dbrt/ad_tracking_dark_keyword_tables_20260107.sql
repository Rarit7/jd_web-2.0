-- ================================================
-- 广告追踪系统 - 黑词分析相关表
-- 创建日期：2026-01-07
-- 说明：包含黑词分类、毒品配置、毒品关键词、黑词记录四个核心表
-- 注意：不使用外键约束，只使用索引
-- ================================================


-- ================================================
-- 表1：ad_tracking_dark_keyword_category（黑词分类配置表）
-- ================================================
-- 用途：存储黑词的分类（如：毒品相关、违法交易、危害品等）
-- 创建日期：2026-01-07

CREATE TABLE IF NOT EXISTS `ad_tracking_dark_keyword_category` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `name` VARCHAR(50) NOT NULL UNIQUE COMMENT '分类名称（如：毒品相关、违法交易、危害品）',
    `display_name` VARCHAR(100) DEFAULT NULL COMMENT '显示名称',
    `description` TEXT DEFAULT NULL COMMENT '分类描述',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    `priority` INT DEFAULT 0 COMMENT '优先级（用于排序，值越大优先级越高）',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_category_name` (`name`),
    KEY `idx_is_active` (`is_active`),
    KEY `idx_priority` (`priority`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪-黑词分类配置';


-- ================================================
-- 表2：ad_tracking_dark_keyword_drug（毒品配置表）
-- ================================================
-- 用途：存储具体的毒品类型（如：冰毒、海洛因、大麻等）
-- 创建日期：2026-01-07

CREATE TABLE IF NOT EXISTS `ad_tracking_dark_keyword_drug` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `category_id` INT NOT NULL COMMENT '分类ID（关联ad_tracking_dark_keyword_category）',
    `name` VARCHAR(50) NOT NULL COMMENT '毒品名称（如：冰毒、海洛因、大麻）',
    `display_name` VARCHAR(100) DEFAULT NULL COMMENT '显示名称',
    `description` TEXT DEFAULT NULL COMMENT '毒品描述',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    `priority` INT DEFAULT 0 COMMENT '优先级（用于排序，值越大优先级越高）',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_category_drug` (`category_id`, `name`),
    KEY `idx_category_id` (`category_id`),
    KEY `idx_is_active` (`is_active`),
    KEY `idx_priority` (`priority`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪-毒品配置';


-- ================================================
-- 表3：ad_tracking_dark_keyword_keyword（毒品关键词表）
-- ================================================
-- 用途：存储毒品的关键词，用于AC自动机进行高效匹配
-- 创建日期：2026-01-07

CREATE TABLE IF NOT EXISTS `ad_tracking_dark_keyword_keyword` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `drug_id` INT NOT NULL COMMENT '毒品ID（关联ad_tracking_dark_keyword_drug）',
    `keyword` VARCHAR(100) NOT NULL COMMENT '关键词（如：冰、溜冰、麻古、肉等）',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    `weight` INT DEFAULT 1 COMMENT '权重（AC自动机匹配优先级，值越大优先级越高）',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_drug_keyword` (`drug_id`, `keyword`),
    KEY `idx_drug_id` (`drug_id`),
    KEY `idx_is_active` (`is_active`),
    KEY `idx_weight` (`weight`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪-毒品关键词配置';


-- ================================================
-- 表4：ad_tracking_dark_keyword（黑词记录表）
-- ================================================
-- 用途：存储从聊天记录中提取的黑词匹配记录
-- 创建日期：2026-01-07

CREATE TABLE IF NOT EXISTS `ad_tracking_dark_keyword` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `chat_id` VARCHAR(128) NOT NULL COMMENT '群组ID',
    `message_id` VARCHAR(128) NOT NULL COMMENT '消息ID',
    `keyword` VARCHAR(100) NOT NULL COMMENT '匹配到的关键词',
    `drug_id` INT DEFAULT NULL COMMENT '毒品ID（关联ad_tracking_dark_keyword_drug）',
    `category_id` INT DEFAULT NULL COMMENT '分类ID（关联ad_tracking_dark_keyword_category）',
    `count` INT DEFAULT 1 COMMENT '该关键词在消息中出现的次数',
    `msg_date` DATE DEFAULT NULL COMMENT '消息日期',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_chat_id` (`chat_id`),
    KEY `idx_msg_date` (`msg_date`),
    KEY `idx_keyword` (`keyword`),
    KEY `idx_drug_id` (`drug_id`),
    KEY `idx_category_id` (`category_id`),
    KEY `idx_message_id` (`message_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪-黑词记录';


-- ================================================
-- 复合索引（性能优化）
-- ================================================

-- 黑词查询优化（按群组、日期、毒品聚合查询）
CREATE INDEX idx_dark_keyword_composite
ON ad_tracking_dark_keyword(chat_id, msg_date, drug_id, category_id);


-- ================================================
-- 表创建完成
-- ================================================
-- 黑词分析相关表结构已成功创建
-- 注意：初始数据需要通过单独的数据导入脚本执行
