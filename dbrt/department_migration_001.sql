-- ============================================================
-- 部门管理功能数据库迁移脚本
-- 版本: v1.0
-- 日期: 2025-12-07
-- 说明: 创建部门表、部门-TG账户关联表，修改用户表添加部门字段
-- ============================================================

-- ============================================================
-- Step 1: 创建部门表 (department)
-- ============================================================
CREATE TABLE IF NOT EXISTS `department` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '部门ID',
  `name` VARCHAR(100) NOT NULL UNIQUE COMMENT '部门名称',
  `description` VARCHAR(500) DEFAULT NULL COMMENT '部门描述',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用: 1=启用, 0=禁用',
  INDEX idx_name (name),
  INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='部门表';

-- 插入默认全局部门（ID=0）
-- 注意：先插入一条记录获取自增ID，然后更新为0
INSERT INTO `department` (name, description, is_active)
VALUES ('全局部门', '超级管理员所属部门，可查看所有群组', 1);

-- 将刚插入的记录ID改为0（需要临时禁用自增）
SET @dept_id = LAST_INSERT_ID();
UPDATE `department` SET id = 0 WHERE id = @dept_id;

-- ============================================================
-- Step 2: 创建部门-TG账户关联表 (department_tg_account)
-- ============================================================
CREATE TABLE IF NOT EXISTS `department_tg_account` (
  `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
  `department_id` INT NOT NULL COMMENT '部门ID',
  `tg_user_id` VARCHAR(128) NOT NULL COMMENT 'TG账户的user_id（与tg_account.user_id关联）',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` INT DEFAULT NULL COMMENT '创建人(secure_user.id)',
  UNIQUE KEY uk_dept_tg (department_id, tg_user_id) COMMENT '部门-TG账户唯一约束',
  INDEX idx_department (department_id),
  INDEX idx_tg_user (tg_user_id),
  CONSTRAINT `fk_dept_tg_department`
    FOREIGN KEY (`department_id`) REFERENCES `department`(`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_dept_tg_creator`
    FOREIGN KEY (`created_by`) REFERENCES `secure_user`(`id`)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='部门与TG账户关联表';

-- ============================================================
-- Step 3: 修改用户表 (secure_user) 添加部门字段
-- ============================================================
-- 检查字段是否已存在，避免重复执行报错
SET @column_exists = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'secure_user'
    AND COLUMN_NAME = 'department_id'
);

-- 如果字段不存在，则添加
SET @sql = IF(
  @column_exists = 0,
  'ALTER TABLE `secure_user` ADD COLUMN `department_id` INT DEFAULT 0 COMMENT ''所属部门ID，0为全局部门''',
  'SELECT ''department_id column already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加外键约束（如果字段是新添加的）
SET @fk_exists = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'secure_user'
    AND CONSTRAINT_NAME = 'fk_user_department'
);

SET @sql = IF(
  @fk_exists = 0 AND @column_exists = 0,
  'ALTER TABLE `secure_user` ADD CONSTRAINT `fk_user_department`
    FOREIGN KEY (`department_id`) REFERENCES `department`(`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE',
  'SELECT ''fk_user_department already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加索引
SET @index_exists = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'secure_user'
    AND INDEX_NAME = 'idx_department_id'
);

SET @sql = IF(
  @index_exists = 0,
  'CREATE INDEX idx_department_id ON secure_user(department_id)',
  'SELECT ''idx_department_id already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 为permission_level添加索引（如果不存在）
SET @index_exists = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'secure_user'
    AND INDEX_NAME = 'idx_permission_level'
);

SET @sql = IF(
  @index_exists = 0,
  'CREATE INDEX idx_permission_level ON secure_user(permission_level)',
  'SELECT ''idx_permission_level already exists'' AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================================
-- Step 4: 数据迁移 - 调整权限等级和分配部门
-- ============================================================
-- 注意：根据设计方案调整权限等级
-- 原有：1=超级管理员, 2=普通用户
-- 新设计：0=超级管理员, 1=部门管理员, 2=普通用户

-- 4.1 将所有超级管理员（permission_level=1）改为0，并分配到全局部门
UPDATE `secure_user`
SET permission_level = 0, department_id = 0
WHERE permission_level = 1;

-- 4.2 将所有普通用户（permission_level=2）暂时分配到全局部门
-- 后续可由超级管理员手动调整到具体部门
UPDATE `secure_user`
SET department_id = 0
WHERE permission_level = 2 OR permission_level > 2;

-- ============================================================
-- Step 5: 创建示例部门（可选）
-- ============================================================
-- 取消下面的注释以创建示例部门
-- INSERT INTO `department` (name, description, is_active) VALUES
-- ('销售部', '销售相关的Telegram群组监控', 1),
-- ('市场部', '市场推广相关的Telegram群组监控', 1),
-- ('技术部', '技术交流相关的Telegram群组监控', 1);

-- ============================================================
-- Step 6: 验证迁移结果
-- ============================================================
-- 检查部门表
SELECT '=== 部门表检查 ===' AS status;
SELECT * FROM department;

-- 检查用户表的部门分配
SELECT '=== 用户部门分配检查 ===' AS status;
SELECT
  id,
  username,
  permission_level,
  department_id,
  CASE permission_level
    WHEN 0 THEN '超级管理员'
    WHEN 1 THEN '部门管理员'
    WHEN 2 THEN '普通用户'
    ELSE '未知权限'
  END as permission_name
FROM secure_user
ORDER BY permission_level, id;

-- 检查索引是否创建成功
SELECT '=== 索引检查 ===' AS status;
SELECT
  TABLE_NAME,
  INDEX_NAME,
  COLUMN_NAME
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN ('secure_user', 'department', 'department_tg_account')
ORDER BY TABLE_NAME, INDEX_NAME;

-- ============================================================
-- 迁移完成提示
-- ============================================================
SELECT '=== 迁移完成 ===' AS status,
       '请检查上述输出确认数据迁移正确' AS message;

-- ============================================================
-- 回滚脚本（如需回滚，请谨慎执行）
-- ============================================================
-- DROP TABLE IF EXISTS `department_tg_account`;
-- DROP TABLE IF EXISTS `department`;
-- ALTER TABLE `secure_user` DROP FOREIGN KEY `fk_user_department`;
-- ALTER TABLE `secure_user` DROP INDEX `idx_department_id`;
-- ALTER TABLE `secure_user` DROP INDEX `idx_permission_level`;
-- ALTER TABLE `secure_user` DROP COLUMN `department_id`;
-- UPDATE `secure_user` SET permission_level = 1 WHERE permission_level = 0;
