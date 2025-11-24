-- =========================================================
-- 优化用户统计API的数据库索引
-- 针对getUserStats()操作的性能优化
-- 创建时间: 2025-11-24
-- =========================================================

-- 检查表是否存在，然后创建或修改索引

-- 1. 为 TgGroupChatHistory 表创建复合索引
-- 用于加速按user_id和chat_id的查询
CREATE INDEX IF NOT EXISTS idx_tg_chat_history_user_chat
ON tg_group_chat_history(user_id, chat_id, postal_time DESC);

-- 2. 为 TgGroupChatHistory 表创建user_id单列索引（支持GROUP BY）
CREATE INDEX IF NOT EXISTS idx_tg_chat_history_user_id
ON tg_group_chat_history(user_id);

-- 3. 为 TgGroupChatHistory 表的postal_time创建索引（支持时间范围查询）
CREATE INDEX IF NOT EXISTS idx_tg_chat_history_postal_time
ON tg_group_chat_history(postal_time DESC);

-- 4. 为 TgGroup 表的chat_id和status创建复合索引
-- 用于加速群组信息的JOIN操作
CREATE INDEX IF NOT EXISTS idx_tg_group_chat_id_status
ON tg_group(chat_id, status);

-- =========================================================
-- 索引说明：
-- =========================================================
-- idx_tg_chat_history_user_chat:
--   用于快速定位用户的所有消息，同时支持按chat_id分组
--   查询模式: WHERE user_id = ? AND chat_id IN (...)
--
-- idx_tg_chat_history_user_id:
--   支持快速过滤用户消息，用于GROUP BY操作
--   查询模式: WHERE user_id = ? GROUP BY chat_id
--
-- idx_tg_chat_history_postal_time:
--   支持时间范围查询和排序
--   查询模式: ORDER BY postal_time DESC
--
-- idx_tg_group_chat_id_status:
--   支持快速JOIN获取群组信息
--   查询模式: JOIN tg_group ON chat_id = ? AND status = ?

-- =========================================================
-- 验证索引是否创建成功（可选）
-- =========================================================
-- 运行以下查询查看表的所有索引：
-- SHOW INDEX FROM tg_group_chat_history;
-- SHOW INDEX FROM tg_group;
