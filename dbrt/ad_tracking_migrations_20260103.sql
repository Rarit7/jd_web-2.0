-- ================================================
-- 广告追踪系统数据库迁移脚本
-- 合并日期: 2026-01-03
-- 包含内容:
--   1. 广告追踪记录表建表
--   2. 广告追踪处理批次表建表
--   3. result_tag 表添加 is_nsfw 字段
--   4. ad_tracking_records 表添加 tag_ids 字段
--   5. ad_tracking_processing_batches 表添加 task_id 字段
-- ================================================

-- ================================================
-- 1. 广告追踪记录系统 - 数据库建表语句 (DDL)
-- 创建时间: 2026-01-01
-- ================================================

-- 广告追踪记录表
CREATE TABLE IF NOT EXISTS `ad_tracking_records` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
    `channel_id` BIGINT NOT NULL COMMENT '频道ID',
    `channel_name` VARCHAR(255) NOT NULL COMMENT '频道名称',
    `message_id` BIGINT NOT NULL COMMENT '原始消息ID',
    `sender_id` BIGINT NOT NULL COMMENT '发送者ID',
    `message_text` TEXT COMMENT '消息文本',
    `image_url` VARCHAR(500) NOT NULL COMMENT '图片URL',
    `send_time` DATETIME NOT NULL COMMENT '发送时间',
    `trigger_keyword` VARCHAR(100) NOT NULL COMMENT '触发关键词',
    `trigger_tag_id` INT COMMENT '触发标签ID',
    `tag_ids` JSON COMMENT '匹配的所有标签ID列表',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_processed` BOOLEAN DEFAULT FALSE COMMENT '是否已处理',
    `process_batch_id` VARCHAR(50) COMMENT '处理批次ID',
    INDEX `idx_channel_id` (`channel_id`),
    INDEX `idx_send_time` (`send_time`),
    INDEX `idx_trigger_keyword` (`trigger_keyword`),
    INDEX `idx_process_batch_id` (`process_batch_id`),
    INDEX `idx_trigger_tag_id` (`trigger_tag_id`),
    FOREIGN KEY (`trigger_tag_id`) REFERENCES `tag_keyword_mapping`(`tag_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪记录表';

-- 广告追踪处理批次表
CREATE TABLE IF NOT EXISTS `ad_tracking_processing_batches` (
    `id` VARCHAR(50) PRIMARY KEY COMMENT '批次ID',
    `channel_id` BIGINT NOT NULL COMMENT '处理频道ID',
    `selected_tag_ids` JSON COMMENT '选中的标签ID列表',
    `status` ENUM('pending', 'processing', 'completed', 'failed', 'cancelled') DEFAULT 'pending' COMMENT '处理状态',
    `total_messages` INT DEFAULT 0 COMMENT '总消息数',
    `processed_messages` INT DEFAULT 0 COMMENT '已处理消息数',
    `created_messages` INT DEFAULT 0 COMMENT '创建的广告记录数',
    `started_at` DATETIME COMMENT '开始时间',
    `completed_at` DATETIME COMMENT '完成时间',
    `error_message` TEXT COMMENT '错误信息',
    `task_id` VARCHAR(200) COMMENT 'Celery任务ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_channel_id` (`channel_id`),
    INDEX `idx_status` (`status`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_task_id` (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪处理批次表';

-- ================================================
-- 外键关联约束
-- ================================================

-- ad_tracking_records.process_batch_id 关联到 ad_tracking_processing_batches.id
ALTER TABLE `ad_tracking_records`
ADD CONSTRAINT `fk_ad_tracking_records_process_batch`
FOREIGN KEY (`process_batch_id`) REFERENCES `ad_tracking_processing_batches`(`id`) ON DELETE SET NULL;

-- ================================================
-- 优化查询性能的复合索引
-- ================================================

-- 复合索引：用于按频道和时间范围查询广告记录
CREATE INDEX `idx_channel_sendtime` ON `ad_tracking_records` (`channel_id`, `send_time`);

-- 复合索引：用于按处理批次和状态查询
CREATE INDEX `idx_batch_status` ON `ad_tracking_processing_batches` (`id`, `status`);

-- 全文索引：用于消息文本搜索（MySQL 5.6+）
CREATE FULLTEXT INDEX `idx_message_text` ON `ad_tracking_records` (`message_text`);

-- ================================================
-- 2. 为 result_tag 表添加 NSFW 标记字段
-- 创建时间: 2026-01-02
-- 功能：支持标记标签为NSFW类型，用于群组图片模糊处理
-- ================================================

-- 检查列是否存在，不存在则添加
ALTER TABLE `result_tag`
ADD COLUMN IF NOT EXISTS `is_nsfw` TINYINT(1) NOT NULL DEFAULT 0
COMMENT 'NSFW标记：0-正常内容 1-NSFW内容'
AFTER `color`;

-- 添加索引以优化查询性能
ALTER TABLE `result_tag`
ADD INDEX IF NOT EXISTS `idx_is_nsfw` (`is_nsfw`);

-- ================================================
-- 3. 为 ad_tracking_records 表添加 tag_ids 列 (数据迁移)
-- 创建时间: 2026-01-02
-- 目的：支持一条广告记录对应多个标签
-- ================================================

-- 注：tag_ids 列已在建表时创建
-- 迁移现有数据：将 trigger_tag_id 转换为 tag_ids 数组
-- 如果 trigger_tag_id 有值，则转换为单元素数组
UPDATE `ad_tracking_records`
SET `tag_ids` = JSON_ARRAY(`trigger_tag_id`)
WHERE `trigger_tag_id` IS NOT NULL AND `tag_ids` IS NULL;

-- ================================================
-- 4. 为 ad_tracking_processing_batches 表添加 task_id 列
-- 创建时间: 2026-01-02
-- 用途: 用于修复广告追踪批次管理 API 的 500 错误
-- ================================================

-- 注：task_id 列已在建表时创建
-- 为 task_id 添加索引以优化查询性能（如不存在则添加）
-- 该索引已在建表时创建

-- ================================================
-- 验证脚本（可选，用于检查迁移是否成功）
-- ================================================

-- SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT FROM INFORMATION_SCHEMA.COLUMNS
-- WHERE TABLE_NAME = 'ad_tracking_records' AND TABLE_SCHEMA = DATABASE();

-- SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT FROM INFORMATION_SCHEMA.COLUMNS
-- WHERE TABLE_NAME = 'ad_tracking_processing_batches' AND TABLE_SCHEMA = DATABASE();

-- SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_COMMENT FROM INFORMATION_SCHEMA.COLUMNS
-- WHERE TABLE_NAME = 'result_tag' AND TABLE_SCHEMA = DATABASE() AND COLUMN_NAME = 'is_nsfw';

-- SELECT id, trigger_tag_id, tag_ids FROM ad_tracking_records LIMIT 10;

-- ================================================
-- 迁移完成
-- ================================================
