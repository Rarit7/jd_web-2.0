-- ============================================================================
-- JD Web - 黑词分析数据更新脚本
-- 创建日期: 2026-01-07
-- 说明: 清空并重新填充毒品配置和关键词数据
-- ============================================================================

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================================
-- 1. 清空现有数据
-- ============================================================================
TRUNCATE TABLE ad_tracking_dark_keyword_keyword;
TRUNCATE TABLE ad_tracking_dark_keyword_drug;

-- ============================================================================
-- 2. 重新插入毒品配置数据
-- 说明：category_id=1 为"毒品相关"分类（已在导出文件中定义）
-- ============================================================================
INSERT INTO ad_tracking_dark_keyword_drug (id, category_id, name, display_name, description, is_active, priority, created_at, updated_at) VALUES
(1, 1, '大麻', '大麻及制品', '大麻、大麻油、大麻种子等及其制品', 1, 10, NOW(), NOW()),
(2, 1, '上头电子烟', '上头电子烟', '含有依托咪酯等成分的电子烟', 1, 20, NOW(), NOW()),
(3, 1, '冰毒', '冰毒（甲基苯丙胺）', '甲基苯丙胺，俗称冰毒、冰', 1, 30, NOW(), NOW()),
(4, 1, 'LSD', 'LSD（麦角酸二乙酰胺）', '强效致幻剂，俗称邮票、糖纸', 1, 40, NOW(), NOW()),
(5, 1, '替来他明', '替来他明', '兽医麻醉剂，被滥用为毒品', 1, 50, NOW(), NOW()),
(6, 1, '迷幻蘑菇', '迷幻蘑菇', '含有裸盖菇素的致幻蘑菇', 1, 60, NOW(), NOW()),
(7, 1, '依托咪酯', '依托咪酯', '麻醉剂，被滥用为毒品，俗称烟粉', 1, 70, NOW(), NOW()),
(8, 1, 'MDMA', 'MDMA（摇头丸主要成分）', '亚甲基二氧甲基苯丙胺，俗称摇头丸、 Molly', 1, 80, NOW(), NOW()),
(9, 1, '大麻油', '大麻油', '大麻浓缩提取物', 1, 90, NOW(), NOW()),
(10, 1, '美托咪酯', '美托咪酯', '麻醉镇静剂', 1, 100, NOW(), NOW()),
(11, 1, '咪酯类物质', '咪酯类物质', '包括依托咪酯、美托咪酯等', 1, 110, NOW(), NOW()),
(12, 1, '制毒原料', '制毒原料', '用于制造毒品的化学品和原料', 1, 120, NOW(), NOW()),
(13, 1, '笑气', '笑气（一氧化二氮）', '一氧化二氮，俗称笑气、气球', 1, 130, NOW(), NOW()),
(14, 1, '氯胺酮衍生物', '氯胺酮衍生物', 'K粉类物质衍生物', 1, 140, NOW(), NOW()),
(15, 1, '海洛因', '海洛因（二乙酰吗啡）', '海洛因，俗称白粉、D货', 1, 150, NOW(), NOW()),
(16, 1, '大麻种子', '大麻种子', '大麻种植用种子', 1, 160, NOW(), NOW()),
(17, 1, 'DMT', 'DMT（二甲基色胺）', '强效致幻剂', 1, 170, NOW(), NOW()),
(18, 1, '可卡因', '可卡因', '古柯叶提取的兴奋剂', 1, 180, NOW(), NOW()),
(19, 1, '卡西酮', '卡西酮', '合成卡西酮类物质，俗称浴盐、喵喵', 1, 190, NOW(), NOW());

-- ============================================================================
-- 3. 插入关键词数据
-- ============================================================================

-- 大麻关键词 (drug_id=1)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(1, '大麻', 1, 3, NOW(), NOW()),
(1, '叶子', 1, 3, NOW(), NOW()),
(1, '草', 1, 2, NOW(), NOW()),
(1, 'Weed', 1, 2, NOW(), NOW()),
(1, 'hash', 1, 2, NOW(), NOW()),
(1, '哈希', 1, 2, NOW(), NOW()),
(1, 'Cannabis', 1, 2, NOW(), NOW()),
(1, '大麻脂', 1, 2, NOW(), NOW()),
(1, '大麻树脂', 1, 2, NOW(), NOW());

-- 上头电子烟关键词 (drug_id=2)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(2, '上头电子烟', 1, 3, NOW(), NOW()),
(2, '上头', 1, 2, NOW(), NOW()),
(2, '加料', 1, 2, NOW(), NOW()),
(2, '加料烟', 1, 2, NOW(), NOW()),
(2, '加料电子烟', 1, 2, NOW(), NOW()),
(2, '劲大', 1, 1, NOW(), NOW()),
(2, '特制', 1, 1, NOW(), NOW()),
(2, '特供', 1, 1, NOW(), NOW());

-- 冰毒关键词 (drug_id=3)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(3, '冰毒', 1, 3, NOW(), NOW()),
(3, '冰', 1, 2, NOW(), NOW()),
(3, '溜冰', 1, 3, NOW(), NOW()),
(3, '肉', 1, 2, NOW(), NOW()),
(3, '溜肉', 1, 3, NOW(), NOW()),
(3, '吃药', 1, 2, NOW(), NOW()),
(3, '肉肉', 1, 2, NOW(), NOW()),
(3, '猪肉', 1, 2, NOW(), NOW()),
(3, '溜肉肉', 1, 2, NOW(), NOW()),
(3, '甲基苯丙胺', 1, 3, NOW(), NOW()),
(3, '麻古', 1, 2, NOW(), NOW()),
(3, '溜麻古', 1, 2, NOW(), NOW()),
(3, '冰片', 1, 2, NOW(), NOW());

-- LSD关键词 (drug_id=4)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(4, 'LSD', 1, 3, NOW(), NOW()),
(4, '邮票', 1, 3, NOW(), NOW()),
(4, '糖纸', 1, 3, NOW(), NOW()),
(4, '贴纸', 1, 2, NOW(), NOW()),
(4, '迷幻贴', 1, 2, NOW(), NOW()),
(4, '酸', 1, 2, NOW(), NOW()),
(4, '麦角酸', 1, 2, NOW(), NOW()),
(4, '指压剂', 1, 2, NOW(), NOW());

-- 替来他明关键词 (drug_id=5)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(5, '替来他明', 1, 3, NOW(), NOW()),
(5, '替胺', 1, 2, NOW(), NOW()),
(5, 'Tilamine', 1, 2, NOW(), NOW()),
(5, '兽医粉', 1, 2, NOW(), NOW()),
(5, 'K粉代', 1, 2, NOW(), NOW());

-- 迷幻蘑菇关键词 (drug_id=6)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(6, '迷幻蘑菇', 1, 3, NOW(), NOW()),
(6, '魔法蘑菇', 1, 3, NOW(), NOW()),
(6, '蘑菇', 1, 2, NOW(), NOW()),
(6, '裸盖菇', 1, 2, NOW(), NOW()),
(6, '迷幻菇', 1, 2, NOW(), NOW()),
(6, '神菇', 1, 2, NOW(), NOW()),
(6, 'psilocybin', 1, 2, NOW(), NOW()),
(6, '裸盖菇素', 1, 2, NOW(), NOW());

-- 依托咪酯关键词 (drug_id=7)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(7, '依托咪酯', 1, 3, NOW(), NOW()),
(7, '烟粉', 1, 3, NOW(), NOW()),
(7, '咪酯', 1, 2, NOW(), NOW()),
(7, 'Etomidate', 1, 2, NOW(), NOW()),
(7, '粉末', 1, 1, NOW(), NOW()),
(7, '白面', 1, 1, NOW(), NOW());

-- MDMA关键词 (drug_id=8)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(8, 'MDMA', 1, 3, NOW(), NOW()),
(8, '摇头丸', 1, 3, NOW(), NOW()),
(8, '摇头', 1, 2, NOW(), NOW()),
(8, 'Molly', 1, 3, NOW(), NOW()),
(8, 'Ecstasy', 1, 3, NOW(), NOW()),
(8, 'E仔', 1, 2, NOW(), NOW()),
(8, '亚当', 1, 2, NOW(), NOW()),
(8, '快乐丸', 1, 2, NOW(), NOW()),
(8, '爱他死', 1, 2, NOW(), NOW());

-- 大麻油关键词 (drug_id=9)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(9, '大麻油', 1, 3, NOW(), NOW()),
(9, '哈希油', 1, 2, NOW(), NOW()),
(9, '蜂蜜油', 1, 2, NOW(), NOW()),
(9, 'BHO', 1, 2, NOW(), NOW()),
(9, 'dabs', 1, 2, NOW(), NOW()),
(9, 'wax', 1, 2, NOW(), NOW()),
(9, 'shatter', 1, 2, NOW(), NOW());

-- 美托咪酯关键词 (drug_id=10)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(10, '美托咪酯', 1, 3, NOW(), NOW()),
(10, 'Medetomidine', 1, 2, NOW(), NOW()),
(10, '美咪', 1, 2, NOW(), NOW());

-- 咪酯类物质关键词 (drug_id=11)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(11, '咪酯类', 1, 3, NOW(), NOW()),
(11, '咪酯', 1, 2, NOW(), NOW()),
(11, '咪脂', 1, 2, NOW(), NOW()),
(11, '烟油', 1, 2, NOW(), NOW()),
(11, '加烟油', 1, 2, NOW(), NOW());

-- 制毒原料关键词 (drug_id=12)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(12, '制毒原料', 1, 3, NOW(), NOW()),
(12, '麻黄素', 1, 3, NOW(), NOW()),
(12, '麻黄碱', 1, 3, NOW(), NOW()),
(12, '伪麻黄碱', 1, 3, NOW(), NOW()),
(12, '苯丙酮', 1, 3, NOW(), NOW()),
(12, '前体', 1, 2, NOW(), NOW()),
(12, '原料', 1, 1, NOW(), NOW()),
(12, '化学品', 1, 1, NOW(), NOW()),
(12, '试剂', 1, 1, NOW(), NOW());

-- 笑气关键词 (drug_id=13)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(13, '笑气', 1, 3, NOW(), NOW()),
(13, '气球', 1, 3, NOW(), NOW()),
(13, '一氧化二氮', 1, 3, NOW(), NOW()),
(13, 'N2O', 1, 2, NOW(), NOW()),
(13, '笑气瓶', 1, 2, NOW(), NOW()),
(13, '气弹', 1, 2, NOW(), NOW()),
(13, '奶油枪', 1, 2, NOW(), NOW()),
(13, '打气', 1, 2, NOW(), NOW()),
(13, '吸气球', 1, 2, NOW(), NOW());

-- 氯胺酮衍生物关键词 (drug_id=14)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(14, '氯胺酮衍生物', 1, 3, NOW(), NOW()),
(14, 'K粉衍生物', 1, 3, NOW(), NOW()),
(14, '类K', 1, 2, NOW(), NOW()),
(14, '新K', 1, 2, NOW(), NOW()),
(14, '脱K', 1, 2, NOW(), NOW()),
(14, '2-oxo-PCE', 1, 2, NOW(), NOW()),
(14, 'DCK', 1, 2, NOW(), NOW());

-- 海洛因关键词 (drug_id=15)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(15, '海洛因', 1, 3, NOW(), NOW()),
(15, '白粉', 1, 3, NOW(), NOW()),
(15, 'D货', 1, 3, NOW(), NOW()),
(15, 'D', 1, 2, NOW(), NOW()),
(15, 'H', 1, 2, NOW(), NOW()),
(15, '二乙酰吗啡', 1, 3, NOW(), NOW()),
(15, '四号', 1, 2, NOW(), NOW()),
(15, '土', 1, 2, NOW(), NOW()),
(15, '白面', 1, 2, NOW(), NOW()),
(15, '粉', 1, 1, NOW(), NOW());

-- 大麻种子关键词 (drug_id=16)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(16, '大麻种子', 1, 3, NOW(), NOW()),
(16, '大麻籽', 1, 3, NOW(), NOW()),
(16, '种子', 1, 1, NOW(), NOW()),
(16, '麻籽', 1, 2, NOW(), NOW()),
(16, '草籽', 1, 2, NOW(), NOW()),
(16, 'CBD种子', 1, 2, NOW(), NOW());

-- DMT关键词 (drug_id=17)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(17, 'DMT', 1, 3, NOW(), NOW()),
(17, '二甲基色胺', 1, 3, NOW(), NOW()),
(17, '灵魂之旅', 1, 2, NOW(), NOW()),
(17, '精神礼', 1, 2, NOW(), NOW()),
(17, '死藤水', 1, 2, NOW(), NOW()),
(17, 'ayahuasca', 1, 2, NOW(), NOW()),
(17, '5-MeO-DMT', 1, 2, NOW(), NOW());

-- 可卡因关键词 (drug_id=18)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(18, '可卡因', 1, 3, NOW(), NOW()),
(18, '古柯碱', 1, 3, NOW(), NOW()),
(18, 'Coke', 1, 3, NOW(), NOW()),
(18, 'Cocaine', 1, 3, NOW(), NOW()),
(18, '雪', 1, 2, NOW(), NOW()),
(18, '白金', 1, 2, NOW(), NOW()),
(18, '黄金', 1, 2, NOW(), NOW()),
(18, '可乐', 1, 1, NOW(), NOW());

-- 卡西酮关键词 (drug_id=19)
INSERT INTO ad_tracking_dark_keyword_keyword (drug_id, keyword, is_active, weight, created_at, updated_at) VALUES
(19, '卡西酮', 1, 3, NOW(), NOW()),
(19, '浴盐', 1, 3, NOW(), NOW()),
(19, '喵喵', 1, 3, NOW(), NOW()),
(19, 'Meow', 1, 2, NOW(), NOW()),
(19, 'Mephedrone', 1, 2, NOW(), NOW()),
(19, 'MCAT', 1, 2, NOW(), NOW()),
(19, '4-MMC', 1, 2, NOW(), NOW()),
(19, '甲卡西酮', 1, 2, NOW(), NOW()),
(19, '丧尸药', 1, 2, NOW(), NOW()),
(19, '长治筋', 1, 2, NOW(), NOW());

-- 恢复外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- 数据更新完成
-- ============================================================================
-- 共插入 19 种毒品配置
-- 共插入约 180+ 个关键词
-- ============================================================================
