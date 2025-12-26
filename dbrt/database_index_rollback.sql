-- ============================================================
-- Telegram 聊天记录表 - 数据库索引回滚脚本
-- 执行日期: 2025-12-25
-- 用途: 回滚之前创建的所有优化索引
-- 数据库: jd
-- ============================================================
--
-- 注意事项:
--   1. 此脚本用于紧急情况，回滚所有优化索引
--   2. 回滚不会影响数据，仅删除索引
--   3. 索引删除速度很快（< 1 分钟）
--   4. 删除后查询性能会降低，应及时恢复
--
-- 执行方式:
--   mysql -u root -h 127.0.0.1 -P 8906 jd < database_index_rollback.sql
--
-- ============================================================

-- ============================================================
-- 步骤 1: 删除 tg_document_info 的优化索引
-- ============================================================
-- 删除复合索引 idx_chat_message

ALTER TABLE tg_document_info
DROP INDEX idx_chat_message;

-- 验证删除成功
-- SHOW INDEX FROM tg_document_info;


-- ============================================================
-- 步骤 2: 删除 tg_group_user_info 的优化索引
-- ============================================================
-- 删除用户名索引 idx_username

ALTER TABLE tg_group_user_info
DROP INDEX idx_username;

-- 删除复合索引 idx_chatid_userid

ALTER TABLE tg_group_user_info
DROP INDEX idx_chatid_userid;

-- 验证删除成功
-- SHOW INDEX FROM tg_group_user_info;


-- ============================================================
-- 步骤 3: 删除 tg_group_chat_history 的优化索引
-- ============================================================
-- 删除时间范围查询索引 idx_chatid_time

ALTER TABLE tg_group_chat_history
DROP INDEX idx_chatid_time;

-- 删除可选的用户 ID 索引（如果存在）
-- ALTER TABLE tg_group_chat_history
-- DROP INDEX idx_userid_chatid_time;

-- 删除可选的全文搜索索引（如果存在）
-- ALTER TABLE tg_group_chat_history
-- DROP INDEX ft_message;

-- 验证删除成功
-- SHOW INDEX FROM tg_group_chat_history;


-- ============================================================
-- 步骤 4: 更新表统计信息
-- ============================================================
-- 更新表统计信息，使查询优化器重新计算执行计划

ANALYZE TABLE tg_document_info;
ANALYZE TABLE tg_group_user_info;
ANALYZE TABLE tg_group_chat_history;


-- ============================================================
-- 回滚完成 - 验证脚本
-- ============================================================
-- 执行以下命令验证索引是否已删除

-- 验证 tg_document_info 的索引
-- SHOW INDEX FROM tg_document_info;
-- 预期: 仅显示 PRIMARY KEY

-- 验证 tg_group_user_info 的索引
-- SHOW INDEX FROM tg_group_user_info;
-- 预期: 仅显示 PRIMARY KEY

-- 验证 tg_group_chat_history 的索引
-- SHOW INDEX FROM tg_group_chat_history;
-- 预期: 仅显示 PRIMARY KEY

-- 检查索引使用情况
-- SELECT
--     OBJECT_NAME,
--     COUNT_READ,
--     COUNT_WRITE,
--     COUNT_FETCH,
--     COUNT_INSERT,
--     COUNT_UPDATE,
--     COUNT_DELETE
-- FROM INFORMATION_SCHEMA.TABLE_IO_WAITS_SUMMARY_BY_INDEX_USAGE
-- WHERE OBJECT_SCHEMA = 'jd'
--   AND OBJECT_NAME IN ('tg_document_info', 'tg_group_user_info', 'tg_group_chat_history');

-- ============================================================
-- 回滚脚本执行完成
-- ============================================================
--
-- 后续步骤:
--   1. 验证索引删除成功（运行上述验证脚本）
--   2. 启动应用服务
--   3. 监控应用性能和日志
--
-- 注意:
--   回滚后查询性能会恢复到优化前的水平，请尽快诊断问题并重新执行优化
--
-- ============================================================
