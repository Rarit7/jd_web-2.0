-- 广告 URL 标签日志表
-- 记录广告 URL 的自动标签匹配历史
-- 维度：URL / 域名，以替代 AutoTagLog 用于存储 URL 标签信息
-- 表名统一采用 ad_ 前缀，符合广告追踪模块命名规范

CREATE TABLE ad_url_tag_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tracking_id INT NOT NULL COMMENT '广告追踪ID (ad_tracking.id)',
    url VARCHAR(2048) NOT NULL COMMENT '完整URL',
    domain VARCHAR(255) NOT NULL COMMENT '域名',
    tag_id INT NOT NULL COMMENT '标签ID',
    keyword VARCHAR(255) NOT NULL COMMENT '触发的关键词',
    source_type ENUM('website_title', 'website_content') NOT NULL DEFAULT 'website_title'
        COMMENT '标签来源类型：网站标题/网站内容',
    detail_info JSON COMMENT '详细信息(JSON格式)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_tracking_id (tracking_id),
    INDEX idx_domain (domain),
    INDEX idx_tag_id (tag_id),
    INDEX idx_source_type (source_type),
    INDEX idx_created_at (created_at),
    UNIQUE KEY uq_tracking_tag (tracking_id, tag_id),
    FOREIGN KEY (tracking_id) REFERENCES ad_tracking(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='广告URL标签日志表（ad_前缀统一）';
