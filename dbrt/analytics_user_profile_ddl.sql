-- ================================================
-- 用户档案系统 (User Profile Analytics) - 数据库建表语句 (DDL)
-- 创建时间: 2025-01-17
-- 功能: 全息用户档案系统的左侧目录树和档案管理
-- ================================================

-- ================================================
-- 档案文件夹表 (用于左侧导航树)
-- ================================================

-- 档案文件夹表
CREATE TABLE `analytics_user_profile_folder` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL COMMENT '文件夹名称',
  `parent_id` int(11) DEFAULT NULL COMMENT '父文件夹ID（NULL表示根目录）',
  `user_id` int(11) NOT NULL COMMENT '创建者ID（关联secure_user表）',
  `sort_order` int(11) NOT NULL DEFAULT 0 COMMENT '排序值（同级文件夹排序）',
  `icon` varchar(50) DEFAULT 'Folder' COMMENT '文件夹图标名称',
  `description` varchar(500) DEFAULT NULL COMMENT '文件夹描述',
  `is_deleted` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除: 0-否, 1-是',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  INDEX `idx_parent_id` (`parent_id`),
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_sort` (`parent_id`, `sort_order`),
  INDEX `idx_deleted` (`is_deleted`),
  CONSTRAINT `fk_folder_parent` FOREIGN KEY (`parent_id`) REFERENCES `analytics_user_profile_folder` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户档案文件夹表';

-- ================================================
-- 档案主表
-- ================================================

-- 档案主表
CREATE TABLE `analytics_user_profile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tg_user_id` varchar(128) NOT NULL COMMENT 'Telegram用户ID（关联tg_group_user_info.user_id）',
  `folder_id` int(11) DEFAULT NULL COMMENT '所属文件夹ID（NULL表示根目录）',
  `profile_name` varchar(200) NOT NULL COMMENT '档案名称（可自定义，默认使用用户昵称）',
  `created_by` int(11) NOT NULL COMMENT '创建者ID（关联secure_user表）',
  `status` enum('draft','generated','archived') NOT NULL DEFAULT 'draft' COMMENT '档案状态: draft-草稿, generated-已生成, archived-已归档',
  `sort_order` int(11) NOT NULL DEFAULT 0 COMMENT '排序值（同文件夹内排序）',
  `config` json DEFAULT NULL COMMENT '自定义配置（JSON格式，存储显示面板配置等）',
  `last_refreshed_at` datetime DEFAULT NULL COMMENT '最后刷新时间',
  `is_deleted` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除: 0-否, 1-是',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  INDEX `idx_tg_user_id` (`tg_user_id`),
  INDEX `idx_folder_id` (`folder_id`),
  INDEX `idx_created_by` (`created_by`),
  INDEX `idx_status` (`status`),
  INDEX `idx_deleted` (`is_deleted`),
  INDEX `idx_sort` (`folder_id`, `sort_order`),
  CONSTRAINT `fk_profile_folder` FOREIGN KEY (`folder_id`) REFERENCES `analytics_user_profile_folder` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户档案主表';

-- ================================================
-- 索引说明
-- ================================================
-- idx_parent_id: 快速查找某文件夹下的子文件夹
-- idx_user_id: 快速查找某用户创建的所有文件夹
-- idx_sort: 复合索引，用于文件夹排序查询
-- idx_tg_user_id: 快速查找某Telegram用户的档案
-- idx_folder_id: 快速查找某文件夹下的所有档案
-- idx_status: 按档案状态筛选

-- ================================================
-- 初始化数据（可选）
-- ================================================

-- 插入示例根文件夹（由系统初始化时创建，user_id=1为系统管理员）
-- INSERT INTO `analytics_user_profile_folder` (`name`, `parent_id`, `user_id`, `sort_order`, `description`)
-- VALUES
-- ('商家', NULL, 1, 1, '商家相关用户档案'),
-- ('嫌疑人', NULL, 1, 2, '嫌疑人相关用户档案'),
-- ('买家', NULL, 1, 3, '买家相关用户档案');

-- ================================================
-- 数据库建表语句完成
-- 版本: v1.0
-- 最后更新: 2025-01-17
-- ================================================
