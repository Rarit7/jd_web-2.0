-- 为 ad_tracking 表添加 merchant_name 字段
-- 执行时间: 2025-10-06

ALTER TABLE `ad_tracking`
ADD COLUMN `merchant_name` varchar(255) DEFAULT NULL COMMENT '商家名称' AFTER `extra_info`,
ADD INDEX `idx_merchant_name` (`merchant_name`(100));
