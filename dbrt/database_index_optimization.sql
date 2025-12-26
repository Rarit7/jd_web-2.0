-- ============================================================
-- Telegram 聊天记录表 - 数据库索引优化脚本
-- 执行日期: 2025-12-25
-- 优化目标: 提升查询性能 30-40%
-- 数据库: jd
-- ============================================================
--
-- 用途: 为 Telegram 聊天记录表创建优化索引
-- 执行前:
--   1. 备份数据库
--   2. 停止应用
--   3. 确保磁盘可用空间 > 2GB
--
-- 执行方式:
--   mysql -u root -h 127.0.0.1 -P 8906 jd < database_index_optimization.sql
--
-- ============================================================

-- ============================================================
-- 步骤 1: 为 tg_document_info 添加复合索引（优化 LEFT JOIN）
-- ============================================================
-- 表: tg_document_info
-- 记录数: 5,798
-- 作用: 优化聊天记录和文档信息的 LEFT JOIN 查询
-- 索引字段: (chat_id, message_id) - 与 LEFT JOIN 条件完全匹配
-- 索引类型: BTREE（B树索引，范围查询最优）
-- 预期性能提升: 30-40%
-- 执行时间: < 1 分钟
--
-- 相关查询:
--   SELECT tgh.*, td.filename_origin
--   FROM tg_group_chat_history tgh
--   LEFT JOIN tg_document_info td
--     ON tgh.chat_id = td.chat_id AND tgh.message_id = td.message_id
--   WHERE tgh.postal_time >= ...

ALTER TABLE tg_document_info
ADD INDEX idx_chat_message (chat_id(20), message_id(20)) USING BTREE;

-- 验证语句
-- SHOW INDEX FROM tg_document_info WHERE Key_name = 'idx_chat_message';


-- ============================================================
-- 步骤 2: 为 tg_group_user_info 添加用户名索引（优化去重）
-- ============================================================
-- 表: tg_group_user_info
-- 记录数: 可变（可能数万条）
-- 作用: 优化 "SELECT ... WHERE username != ''" 的查询
-- 索引字段: username(50) - 前 50 字符用于去重查询
-- 索引类型: BTREE
-- 预期性能提升: 10-15%
-- 执行时间: < 1 分钟
--
-- 相关查询（在 chat_history.py 第 457 行）:
--   tg_group_user_info = TgGroupUserInfo.query.filter(
--       TgGroupUserInfo.username != ''
--   ).all()

ALTER TABLE tg_group_user_info
ADD INDEX idx_username (username(50)) USING BTREE;

-- 验证语句
-- SHOW INDEX FROM tg_group_user_info WHERE Key_name = 'idx_username';


-- ============================================================
-- 步骤 3: 为 tg_group_user_info 添加复合索引（优化关联查询）
-- ============================================================
-- 表: tg_group_user_info
-- 作用: 优化按 chat_id 和 user_id 的查询
-- 索引字段: (chat_id, user_id) - 常见的组合查询条件
-- 索引类型: BTREE
-- 预期性能提升: 10-20%
-- 执行时间: < 1 分钟
--
-- 相关查询（在 chat_history.py 第 406-409 行）:
--   user_infos = TgGroupUserInfo.query.filter(
--       TgGroupUserInfo.chat_id.in_(chat_ids),
--       TgGroupUserInfo.user_id.in_(user_ids)
--   ).all()

ALTER TABLE tg_group_user_info
ADD INDEX idx_chatid_userid (chat_id(20), user_id(20)) USING BTREE;

-- 验证语句
-- SHOW INDEX FROM tg_group_user_info WHERE Key_name = 'idx_chatid_userid';


-- ============================================================
-- 步骤 4: 为 tg_group_chat_history 添加时间范围查询索引
-- ============================================================
-- 表: tg_group_chat_history
-- 记录数: 1,039,251
-- 作用: 优化按 chat_id 和 postal_time 的范围查询
-- 索引字段: (chat_id, postal_time) - 支持高效的范围查询
-- 索引类型: BTREE
-- 预期性能提升: 20-30%
-- 执行时间: 5-10 分钟（因表较大）
--
-- 相关查询（在 chat_history.py 第 763-831 行）:
--   query = query.filter(TgGroupChatHistory.chat_id.in_(search_chat_id_list))
--   query = query.filter(
--       TgGroupChatHistory.postal_time.between(f_start_date, f_end_date)
--   )

ALTER TABLE tg_group_chat_history
ADD INDEX idx_chatid_time (chat_id(20), postal_time) USING BTREE;

-- 验证语句
-- SHOW INDEX FROM tg_group_chat_history WHERE Key_name = 'idx_chatid_time';


-- ============================================================
-- 步骤 5: 更新表统计信息（必须执行）
-- ============================================================
-- 更新表统计信息，使查询优化器能够做出最佳决策
-- 执行时间: 1-2 分钟

ANALYZE TABLE tg_document_info;
ANALYZE TABLE tg_group_user_info;
ANALYZE TABLE tg_group_chat_history;


-- ============================================================
-- 可选步骤 6: 为 tg_group_chat_history 添加用户 ID 索引
-- ============================================================
-- 表: tg_group_chat_history
-- 作用: 优化按 user_id 的查询（可选，取决于查询频率）
-- 索引字段: (user_id, chat_id, postal_time) - 三维度复合索引
-- 索引类型: BTREE
-- 预期性能提升: 5-10%
-- 执行时间: 5-10 分钟
-- 状态: 可选，仅在需要时执行（取消下行注释）
--
-- 相关查询（在 chat_history.py 第 797-798 行）:
--   query = query.filter(TgGroupChatHistory.user_id.in_(search_user_id_list))

-- ALTER TABLE tg_group_chat_history
-- ADD INDEX idx_userid_chatid_time (user_id(20), chat_id(20), postal_time) USING BTREE;


-- ============================================================
-- 可选步骤 7: 创建全文搜索索引（用于模糊搜索优化）
-- ============================================================
-- 表: tg_group_chat_history
-- 作用: 优化 LIKE '%content%' 模糊查询，改用全文搜索
-- 索引字段: message - 聊天消息内容
-- 索引类型: FULLTEXT
-- 预期性能提升: 80-95%（对于搜索查询）
-- 执行时间: 10-15 分钟
--
-- 注意事项:
--   1. 此步骤可选（需要修改应用代码）
--   2. 中文搜索需要配置 ngram tokenizer
--   3. 需要应用侧支持 MATCH...AGAINST 语法
--   4. 使用全文搜索的查询示例:
--      SELECT * FROM tg_group_chat_history
--      WHERE MATCH(message) AGAINST('content' IN BOOLEAN MODE)
--
-- 状态: 可选，仅在需要优化搜索时执行（取消下行注释）

-- ALTER TABLE tg_group_chat_history
-- ADD FULLTEXT INDEX ft_message (message) WITH PARSER ngram;


-- ============================================================
-- 优化完成 - 验证脚本
-- ============================================================
-- 执行以下命令验证索引是否创建成功

-- 验证 tg_document_info 的索引
-- SHOW INDEX FROM tg_document_info;

-- 验证 tg_group_user_info 的索引
-- SHOW INDEX FROM tg_group_user_info;

-- 验证 tg_group_chat_history 的索引
-- SHOW INDEX FROM tg_group_chat_history;

-- 查询所有创建的索引统计信息
-- SELECT
--     TABLE_NAME,
--     INDEX_NAME,
--     SEQ_IN_INDEX,
--     COLUMN_NAME,
--     CARDINALITY
-- FROM INFORMATION_SCHEMA.STATISTICS
-- WHERE TABLE_SCHEMA = 'jd'
--   AND TABLE_NAME IN ('tg_document_info', 'tg_group_user_info', 'tg_group_chat_history')
-- ORDER BY TABLE_NAME, INDEX_NAME;

-- 验证表大小和行数
-- SELECT
--     TABLE_NAME,
--     TABLE_TYPE,
--     ENGINE,
--     ROW_FORMAT,
--     TABLE_ROWS,
--     AVG_ROW_LENGTH,
--     DATA_LENGTH,
--     INDEX_LENGTH,
--     DATA_FREE,
--     (DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024 as TOTAL_SIZE_MB
-- FROM INFORMATION_SCHEMA.TABLES
-- WHERE TABLE_SCHEMA = 'jd'
--   AND TABLE_NAME IN ('tg_document_info', 'tg_group_user_info', 'tg_group_chat_history');

-- ============================================================
-- 脚本执行完成
-- ============================================================
--
-- 后续步骤:
--   1. 验证索引创建成功（运行上述验证脚本）
--   2. 启动应用服务
--   3. 进行功能验证和性能测试
--   4. 监控应用日志，查看是否有异常
--
-- 性能基准测试命令:
--   mysql -u root -h 127.0.0.1 -P 8906 jd -e "
--   EXPLAIN FORMAT=JSON
--   SELECT tgh.*, td.filename_origin
--   FROM tg_group_chat_history tgh
--   LEFT JOIN tg_document_info td
--     ON tgh.chat_id = td.chat_id AND tgh.message_id = td.message_id
--   WHERE tgh.postal_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)
--   LIMIT 20;
--   "
--
-- ============================================================
