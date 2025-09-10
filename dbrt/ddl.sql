-- ================================================
-- SDJD_TG管理系统 - 完整数据库建表语句 (DDL)
-- 更新时间: 2025-09-08
-- ================================================

-- ================================================
-- 用户权限管理系统
-- ================================================


-- 安全用户表 (新的安全认证系统)
CREATE TABLE `secure_user`
(
    `id`               int          NOT NULL AUTO_INCREMENT,
    `username`         varchar(80)  NOT NULL COMMENT '用户名',
    `password_hash`    varchar(128) NOT NULL COMMENT '密码哈希值',
    `salt`             varchar(32)  NOT NULL COMMENT '密码盐值',
    `permission_level` int          NOT NULL DEFAULT 2 COMMENT '权限等级: 1=超级管理员, 2=普通用户',
    `status`           int          NOT NULL DEFAULT 1 COMMENT '状态: 0=禁用, 1=启用',
    `last_login`       datetime              DEFAULT NULL COMMENT '最后登录时间',
    `created_at`       datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`       datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `created_by`       int                   DEFAULT NULL COMMENT '创建者用户ID',
    PRIMARY KEY (`id`),
    UNIQUE KEY `udx_username` (`username`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='安全用户表';

-- 角色表
CREATE TABLE `role`
(
    `id`         int(11) unsigned NOT NULL AUTO_INCREMENT,
    `name`       varchar(31)      NOT NULL DEFAULT '',
    `detail`     varchar(255)     NOT NULL DEFAULT '' COMMENT '角色描述',
    `status`     tinyint(4)       NOT NULL DEFAULT '0' COMMENT '0-无效，1-有效',
    `created_at` timestamp        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` timestamp        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `u_name` (`name`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='角色';

-- 权限表
CREATE TABLE `permission`
(
    `id`         int(11) unsigned NOT NULL AUTO_INCREMENT,
    `name`       varchar(31)      NOT NULL DEFAULT '',
    `perm_key`   varchar(255)     NOT NULL DEFAULT '' COMMENT '权限标识',
    `level`      tinyint(4)       NOT NULL DEFAULT '0' COMMENT '几级，1-一级菜单，2-二级菜单，3-三级功能/页面，4-四级功能；与type字段结合使用',
    `type`       tinyint(4)       NOT NULL DEFAULT '0' COMMENT '类型，1-菜单，2-功能，3-页面',
    `parent_id`  int(11)          NOT NULL DEFAULT '0' COMMENT '父级权限ID',
    `priority`   int(11)          NOT NULL DEFAULT '0' COMMENT '排序值，越小越靠前',
    `status`     tinyint(4)       NOT NULL DEFAULT '0' COMMENT '-1-被删除，0-禁用，1-开启',
    `created_at` timestamp        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` timestamp        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `u_perm_key` (`perm_key`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='权限';

-- 角色权限关联表
CREATE TABLE `role_permission`
(
    `id`            int(11) unsigned NOT NULL AUTO_INCREMENT,
    `role_id`       int(11)          NOT NULL DEFAULT '0',
    `permission_id` int(11)          NOT NULL DEFAULT '0',
    `status`        tinyint(4)       NOT NULL DEFAULT '0' COMMENT '0-无效，1-有效',
    `created_at`    timestamp        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`    timestamp        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `u_role_perm` (`role_id`, `permission_id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='角色-权限';

-- 用户角色关联表
CREATE TABLE `user_role`
(
    `id`         int(11) unsigned NOT NULL AUTO_INCREMENT,
    `user_id`    int(11)          NOT NULL DEFAULT '0',
    `role_id`    int(11)          NOT NULL DEFAULT '0',
    `status`     tinyint(4)       NOT NULL DEFAULT '0' COMMENT '0-无效，1-有效',
    `created_at` timestamp        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` timestamp        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `u_member_role` (`user_id`, `role_id`),
    KEY `idx_role` (`role_id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='用户-角色';

-- ================================================
-- 黑词管理系统
-- ================================================

-- 黑词关键词表
CREATE TABLE `black_keyword`
(
    `id`         int          NOT NULL AUTO_INCREMENT,
    `keyword`    varchar(126) NOT NULL DEFAULT '' COMMENT '关键词',
    `status`     int          NOT NULL DEFAULT 0 COMMENT '状态',
    `is_delete`  int          NOT NULL DEFAULT 0 COMMENT '0-正常 1-已删除',
    `created_at` timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` timestamp    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='黑词表';

-- 黑词搜索队列表
CREATE TABLE `keyword_search_queue`
(
    `id`          int         NOT NULL AUTO_INCREMENT,
    `batch_id`    varchar(64) NOT NULL DEFAULT '' COMMENT '批次id',
    `search_type` int         NOT NULL DEFAULT 1 COMMENT '1-baidu 2-google',
    `keyword`     varchar(80) NOT NULL DEFAULT '' COMMENT '黑词',
    `status`      int         NOT NULL DEFAULT 0 COMMENT '状态 0-待处理 1-处理中 2-已处理',
    `page`        int         NOT NULL DEFAULT 10 COMMENT '所需页码',
    `created_at`  datetime    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`  datetime    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `idx_batch_id` (`batch_id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='黑词搜索队列';

-- 黑词搜索结果表
CREATE TABLE `keyword_search`
(
    `id`          int         NOT NULL AUTO_INCREMENT,
    `batch_id`    varchar(64) NOT NULL DEFAULT '' COMMENT '批次id',
    `search_type` int         NOT NULL DEFAULT 1 COMMENT '1-baidu 2-google',
    `keyword`     varchar(80) NOT NULL DEFAULT '' COMMENT '黑词',
    `result`      text COMMENT '黑词搜索结果',
    `page`        int         NOT NULL DEFAULT 1 COMMENT '页数',
    `status`      int         NOT NULL DEFAULT 0 COMMENT '状态 0-待处理 1-处理中 2-已处理',
    `created_at`  datetime    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`  datetime    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `udx_keyword` (`keyword`),
    KEY `udx_batch_id` (`batch_id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='黑词搜索结果';

-- 黑词搜索结果解析表
CREATE TABLE `keyword_search_parse_result`
(
    `id`         int          NOT NULL AUTO_INCREMENT,
    `keyword`    varchar(80)  NOT NULL DEFAULT '' COMMENT '黑词',
    `url`        varchar(1024) NOT NULL DEFAULT '' COMMENT 'url',
    `account`    varchar(1024) NOT NULL DEFAULT '' COMMENT '账户内容相关',
    `desc`       varchar(1024) NOT NULL DEFAULT '' COMMENT '描述',
    `is_delete`  int          NOT NULL DEFAULT 0 COMMENT '0-未删除 1-已删除',
    `created_at` datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_keyword` (`keyword`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='黑词搜索结果解析';

-- 黑词解析结果标签关联表
CREATE TABLE `keyword_search_parse_result_tag`
(
    `id`         int      NOT NULL AUTO_INCREMENT,
    `parse_id`   int      NOT NULL DEFAULT 0 COMMENT 'keyword_search_parse_result.id',
    `tag_id`     int      NOT NULL DEFAULT 0 COMMENT '标签id',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_parse_tag` (`parse_id`, `tag_id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='黑词解析结果-标签';

-- ================================================
-- 标签管理系统
-- ================================================

-- 结果标签表
CREATE TABLE `result_tag`
(
    `id`         int         NOT NULL AUTO_INCREMENT,
    `title`      varchar(32) NOT NULL DEFAULT '' COMMENT '标签名称',
    `color`      varchar(7)  NOT NULL DEFAULT '#409EFF' COMMENT '标签颜色',
    `status`     int         NOT NULL DEFAULT 0 COMMENT '状态 0-正常 1-无效',
    `created_at` datetime    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_title` (`title`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='标签';

-- ================================================
-- Telegram 群组管理系统
-- ================================================

-- TG账号表
CREATE TABLE `tg_account`
(
    `id`               int          NOT NULL AUTO_INCREMENT,
    `creator_id`       int          NOT NULL DEFAULT 0 COMMENT '创建者用户ID',
    `name`             varchar(32)  NOT NULL DEFAULT '' COMMENT '连接名称',
    `phone`            varchar(32)  NOT NULL DEFAULT '' COMMENT '手机号',
    `user_id`          varchar(128) NOT NULL DEFAULT '' COMMENT '用户ID',
    `username`         varchar(128) NOT NULL DEFAULT '' COMMENT '用户名',
    `nickname`         varchar(128) NOT NULL DEFAULT '' COMMENT '昵称',
    `api_id`           varchar(32)  NOT NULL DEFAULT '' COMMENT 'Telegram API ID',
    `api_hash`         varchar(64)  NOT NULL DEFAULT '' COMMENT 'Telegram API Hash',
    `phone_code_hash`  varchar(128) NOT NULL DEFAULT '' COMMENT '手机验证码哈希',
    `code`             varchar(16)  NOT NULL DEFAULT '' COMMENT '验证码',
    `api_code`         varchar(16)  NOT NULL DEFAULT '' COMMENT 'API验证码',
    `password`         varchar(128) NOT NULL DEFAULT '' COMMENT '2FA密码',
    `two_step`         int          NOT NULL DEFAULT 0 COMMENT '0:未开启 1-开启',
    `status`           int          NOT NULL DEFAULT 0 COMMENT '0:未加入 1-加入成功 2-加入失败',
    `created_at`       datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`       datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `udx_phone` (`phone`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='tg账号';

-- TG群组表
CREATE TABLE `tg_group`
(
    `id`          int          NOT NULL AUTO_INCREMENT,
    `name`        varchar(20)  NOT NULL DEFAULT '' COMMENT '群组标识名称',
    `chat_id`     varchar(128) NOT NULL DEFAULT '' COMMENT '群组id',
    `status`      int          NOT NULL DEFAULT 0 COMMENT '0-未加入 1-加入成功 2-加入失败',
    `desc`        varchar(1024) NOT NULL DEFAULT '' COMMENT '描述',
    `title`       varchar(1024) NOT NULL DEFAULT '' COMMENT '群组名称',
    `account_id`  varchar(128) NOT NULL DEFAULT '' COMMENT 'TG账户数字ID',
    `avatar_path` varchar(1024) NOT NULL DEFAULT '' COMMENT '头像本地地址',
    `remark`      varchar(128) NOT NULL DEFAULT '' COMMENT '备注',
    `group_type`  int          NOT NULL DEFAULT 1 COMMENT '1-群组 2-频道',
    `created_at`  datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`  datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `udx_name` (`name`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='tg群组表';

-- TG群组状态表
CREATE TABLE `tg_group_status`
(
    `id`                  int          NOT NULL AUTO_INCREMENT,
    `chat_id`             varchar(128) NOT NULL COMMENT '群聊id',
    `members_now`         int          NOT NULL DEFAULT 0 COMMENT '群人数(最新)',
    `members_previous`    int          NOT NULL DEFAULT 0 COMMENT '群人数(先前)',
    `records_now`         int          NOT NULL DEFAULT 0 COMMENT '数据库中此群消息记录数(最新)',
    `records_previous`    int          NOT NULL DEFAULT 0 COMMENT '数据库中此群消息记录数(先前)',
    `first_record_date`   datetime              DEFAULT NULL COMMENT '最早消息日期',
    `first_record_id`     varchar(128) NOT NULL DEFAULT '' COMMENT '最早消息message_id',
    `last_record_date`    datetime              DEFAULT NULL COMMENT '最新消息日期',
    `last_record_id`      varchar(128) NOT NULL DEFAULT '' COMMENT '最新消息message_id',
    `jdweb_user_id`       int          NOT NULL DEFAULT 0 COMMENT '添加此群的用户id',
    `jdweb_tg_id`         varchar(128) NOT NULL DEFAULT '' COMMENT '添加此群的用户的telegram_id',
    `created_at`          datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='tg群组状态';

-- TG群组会话表
CREATE TABLE `tg_group_session`
(
    `id`           int          NOT NULL AUTO_INCREMENT,
    `user_id`      varchar(128) NOT NULL DEFAULT '' COMMENT 'telegram账户id',
    `chat_id`      varchar(128) NOT NULL DEFAULT '' COMMENT '群聊id',
    `session_name` varchar(128) NOT NULL DEFAULT '' COMMENT '连接名称',
    `created_at`   datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`   datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='tg群组会话';

-- TG群组聊天记录表
CREATE TABLE `tg_group_chat_history`
(
    `id`             int          NOT NULL AUTO_INCREMENT,
    `chat_id`        varchar(128) NOT NULL DEFAULT '' COMMENT '聊天室id',
    `message_id`     varchar(128) NOT NULL DEFAULT '' COMMENT '消息id',
    `user_id`        varchar(128) NOT NULL DEFAULT '' COMMENT '用户id',
    `username`       varchar(128) NOT NULL DEFAULT '' COMMENT '用户名',
    `nickname`       varchar(128) NOT NULL DEFAULT '' COMMENT '用户昵称',
    `postal_time`    datetime     NOT NULL DEFAULT '1970-10-30 00:00:00',
    `reply_to_msg_id` varchar(128) NOT NULL DEFAULT '' COMMENT '回复的消息id',
    `message`        text         NOT NULL COMMENT '消息',
    `photo_path`     varchar(256) NOT NULL DEFAULT '' COMMENT '图片路径',
    `document_path`  varchar(256) NOT NULL DEFAULT '' COMMENT '视频/文件路径',
    `document_ext`   varchar(16)  NOT NULL DEFAULT '' COMMENT '文件后缀',
    `status`         int          NOT NULL DEFAULT 0 COMMENT '状态',
    `replies_info`   text         DEFAULT NULL COMMENT '回复信息',
    `created_at`     datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`     datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='tg群组聊天记录';

-- TG群组用户信息表
CREATE TABLE `tg_group_user_info`
(
    `id`           int           NOT NULL AUTO_INCREMENT,
    `chat_id`      varchar(128)  NOT NULL DEFAULT '' COMMENT '群组id',
    `user_id`      varchar(128)  NOT NULL DEFAULT '' COMMENT '用户id',
    `username`     varchar(128)  NOT NULL DEFAULT '' COMMENT '用户名',
    `nickname`     varchar(128)  NOT NULL DEFAULT '' COMMENT '用户昵称',
    `desc`         varchar(1024) NOT NULL DEFAULT '' COMMENT '描述信息',
    `photo`        varchar(1024) NOT NULL DEFAULT '' COMMENT '头像地址',
    `avatar_path`  varchar(1024) NOT NULL DEFAULT '' COMMENT '头像本地地址',
    `remark`       varchar(128)  NOT NULL DEFAULT '' COMMENT '备注',
    `is_key_focus` boolean       NOT NULL DEFAULT FALSE COMMENT '是否重点关注对象',
    `status`       int           NOT NULL DEFAULT 0,
    `created_at`   datetime      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`   datetime      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='tg群组用户信息';

-- TG用户信息变更记录表
CREATE TABLE `tg_user_info_change`
(
    `id`              int          NOT NULL AUTO_INCREMENT,
    `user_id`         varchar(128) NOT NULL DEFAULT '' COMMENT '用户id',
    `changed_fields`  int          NOT NULL DEFAULT 0 COMMENT '变更字段(1-显示名称 2-用户名 3-头像 4-个人简介)',
    `original_value`  text         DEFAULT NULL COMMENT '原信息',
    `new_value`       text         DEFAULT NULL COMMENT '变更后信息',
    `update_time`     datetime     DEFAULT CURRENT_TIMESTAMP COMMENT '变更时间',
    PRIMARY KEY (`id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='tg用户信息变更记录';

-- TG群组信息变更记录表
CREATE TABLE `tg_group_info_change`
(
    `id`              int          NOT NULL AUTO_INCREMENT,
    `chat_id`         varchar(128) NOT NULL DEFAULT '' COMMENT '群聊id',
    `changed_fields`  int          NOT NULL DEFAULT 0 COMMENT '变更字段(1-显示名称 2-群组名/邀请链接 3-群头像 4-群组简介)',
    `original_value`  text         DEFAULT NULL COMMENT '原信息',
    `new_value`       text         DEFAULT NULL COMMENT '变更后信息',
    `update_time`     datetime     DEFAULT CURRENT_TIMESTAMP COMMENT '变更时间',
    PRIMARY KEY (`id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='tg群组信息变更记录';

-- TG文档信息表
CREATE TABLE `tg_document_info`
(
    `chat_id`           varchar(128) NOT NULL COMMENT '群聊id',
    `message_id`        varchar(128) NOT NULL COMMENT '消息id',
    `peer_id`           varchar(128) NOT NULL DEFAULT '' COMMENT '原始来源id',
    `filename_origin`   varchar(256) NOT NULL DEFAULT '' COMMENT '原本文件名',
    `file_ext_name`     varchar(32)  NOT NULL DEFAULT '' COMMENT '文件扩展名',
    `mime_type`         varchar(128) NOT NULL DEFAULT '' COMMENT '文件类型',
    `filepath`          varchar(512) NOT NULL DEFAULT '' COMMENT '存储路径',
    `video_thumb_path`  varchar(512) NOT NULL DEFAULT '' COMMENT '视频缩略图',
    `file_hash`         varchar(128) NOT NULL DEFAULT '' COMMENT '文件哈希值',
    `file_size`         bigint       NOT NULL DEFAULT 0 COMMENT '文件大小',
    `created_at`        datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`        datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`chat_id`, `message_id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='tg文档信息';

-- TG群组标签关联表
CREATE TABLE `tg_group_tag`
(
    `id`         int      NOT NULL AUTO_INCREMENT,
    `group_id`   int      NOT NULL DEFAULT 0 COMMENT 'tg_group.id',
    `tag_id`     int      NOT NULL DEFAULT 0 COMMENT '标签id',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_parse_tag` (`group_id`, `tag_id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='tg群组-标签关系表';

-- TG用户标签关联表
CREATE TABLE `tg_user_tag`
(
    `id`         int      NOT NULL AUTO_INCREMENT,
    `tg_user_id` int      NOT NULL DEFAULT 0 COMMENT 'tg_group_user.id',
    `tag_id`     int      NOT NULL DEFAULT 0 COMMENT '标签id',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_parse_tag` (`tg_user_id`, `tag_id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='tg群组用户-标签关系表';

-- ================================================
-- 化工平台管理系统
-- ================================================

-- 化工平台表
CREATE TABLE `chemical_platform`
(
    `id`         int          NOT NULL AUTO_INCREMENT,
    `name`       varchar(126) NOT NULL DEFAULT '' COMMENT '名称',
    `url`        varchar(255) NOT NULL DEFAULT '' COMMENT '网址',
    `status`     int          NOT NULL DEFAULT 0 COMMENT '状态 0-待处理 1-处理中 2-已处理',
    `created_at` datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='化工平台';

-- 化工平台产品信息表
CREATE TABLE `chemical_platform_product_info`
(
    `id`             int          NOT NULL AUTO_INCREMENT,
    `platform_id`    int          NOT NULL DEFAULT 0 COMMENT 'chemical_platform.id',
    `product_name`   varchar(128) NOT NULL DEFAULT '' COMMENT '产品名称',
    `seller_name`    varchar(256) NOT NULL DEFAULT '' COMMENT '商家名称',
    `compound_name`  varchar(256) NOT NULL DEFAULT '' COMMENT '化合物名称',
    `contact_number` varchar(128) NOT NULL DEFAULT '' COMMENT '联系方式',
    `status`         int          NOT NULL DEFAULT 0,
    `created_at`     datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`     datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='化工平台产品信息';

-- ================================================
-- 任务队列系统
-- ================================================

-- 任务队列日志表
CREATE TABLE `job_queue_log`
(
    `id`           int          NOT NULL AUTO_INCREMENT,
    `name`         varchar(126) NOT NULL DEFAULT '' COMMENT 'job name',
    `description`  varchar(255)          DEFAULT '' COMMENT 'job description',
    `resource_id`  varchar(100)          DEFAULT '' COMMENT '资源ID，根据任务类型可以是chat_id、account_id、file_id等',
    `session_name` varchar(100)          DEFAULT '' COMMENT '使用的连接名称',
    `status`       int          NOT NULL DEFAULT 0 COMMENT '状态 0-待处理 1-处理中 2-已处理',
    `priority`     int          NOT NULL DEFAULT 0 COMMENT '任务优先级 0-10',
    `timeout_at`   datetime              DEFAULT NULL COMMENT '任务超时时间',
    `extra_params` text                  DEFAULT NULL COMMENT '扩展参数JSON',
    `result`       text                  DEFAULT NULL COMMENT '任务执行结果',
    `created_at`   datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`   datetime     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='job队列';

-- ================================================
-- 创建索引和约束
-- ================================================

-- TG相关索引
CREATE INDEX `idx_chat_id` ON `tg_group_chat_history` (`chat_id`);
CREATE INDEX `idx_message_id` ON `tg_group_chat_history` (`message_id`);
CREATE INDEX `idx_user_id` ON `tg_group_chat_history` (`user_id`);
CREATE INDEX `idx_postal_time` ON `tg_group_chat_history` (`postal_time`);

-- 黑词相关索引  
CREATE INDEX `idx_keyword_status` ON `black_keyword` (`keyword`, `status`);
CREATE INDEX `idx_search_batch` ON `keyword_search` (`search_type`, `batch_id`);

-- 任务队列索引
CREATE INDEX `idx_job_status` ON `job_queue_log` (`status`);
CREATE INDEX `idx_job_priority` ON `job_queue_log` (`priority`, `status`);
CREATE INDEX `idx_job_timeout` ON `job_queue_log` (`timeout_at`);

-- 用户权限索引
CREATE INDEX `idx_secure_user_status` ON `secure_user` (`status`, `permission_level`);

-- ================================================
-- 数据库建表语句完成
-- 版本: v2.0
-- 最后更新: 2025-09-08
-- ================================================