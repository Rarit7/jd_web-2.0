-- 主流域名白名单表（Tranco Top 10k-20k）
-- 用于过滤主流网站，只处理小众域名

CREATE TABLE mainstream_domains (
    id INT PRIMARY KEY AUTO_INCREMENT,
    domain VARCHAR(255) UNIQUE NOT NULL COMMENT '域名',
    rank INT COMMENT 'Tranco排名',
    source VARCHAR(50) DEFAULT 'tranco' COMMENT '数据来源',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- 性能优化索引
    INDEX idx_domain (domain),
    INDEX idx_active (is_active, domain),  -- 覆盖索引
    INDEX idx_rank (rank)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  ROW_FORMAT=COMPRESSED  -- 压缩存储节省空间
  COMMENT='主流域名白名单（Tranco Top 10k-20k）一次性导入，月度更新';
