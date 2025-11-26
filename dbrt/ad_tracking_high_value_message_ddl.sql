-- ================================================
-- 广告追踪高价值信息表 - DDL
-- 创建时间: 2025-11-26
-- 描述: 存储经大模型判断的高价值聊天信息
-- ================================================

-- 广告追踪高价值信息表
CREATE TABLE `ad_tracking_high_value_message` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `chat_history_id` int(11) NOT NULL COMMENT '关联的tg_group_chat_history记录ID',
  `user_id` varchar(128) DEFAULT NULL COMMENT '用户ID',
  `username` varchar(255) DEFAULT NULL COMMENT '用户名',
  `chat_id` varchar(128) DEFAULT NULL COMMENT '群组ID',
  `group_name` varchar(255) DEFAULT NULL COMMENT '群组名称',
  `content` text NOT NULL COMMENT '聊天记录内容',
  `images` longtext COMMENT '聊天图片列表（JSON数组格式）',
  `ai_judgment` varchar(500) DEFAULT NULL COMMENT '大模型判断结果',
  `publish_time` datetime DEFAULT NULL COMMENT '消息发布时间',
  `importance_score` decimal(5,2) DEFAULT NULL COMMENT '重要程度评分（0-100）',
  `is_high_priority` tinyint(1) DEFAULT 0 COMMENT '是否为高优先级（0=否，1=是）',
  `remark` text COMMENT '备注说明',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  INDEX `idx_chat_history` (`chat_history_id`),
  INDEX `idx_user` (`user_id`),
  INDEX `idx_chat` (`chat_id`),
  INDEX `idx_publish_time` (`publish_time`),
  INDEX `idx_importance_score` (`importance_score`),
  INDEX `idx_is_high_priority` (`is_high_priority`),
  INDEX `idx_created_at` (`created_at`),
  FOREIGN KEY (`chat_history_id`) REFERENCES `tg_group_chat_history`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='广告追踪高价值信息表';
