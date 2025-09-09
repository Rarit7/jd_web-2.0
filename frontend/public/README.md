# 项目文档

该文件为 Claude Code 提供了处理化工行业数据聚合和 Telegram 监控系统时的指导。

## 项目概述

基于 Flask 的 Web 应用程序，结合了化工行业情报、Telegram 监控和竞争分析。系统采用 Celery 分布式任务处理，正在从传统的 Jinja2 模板过渡到现代的 Vue.js 前端架构。

**核心功能：**
- 多平台化工数据爬取（7+ 个专业爬虫）
- Telegram 群组监控和聊天记录分析
- 实时竞争情报收集
- 基于角色的访问控制 (RBAC)
- 自动任务调度和处理

## 快速启动命令

### 基本开发命令
```bash
# 启动所有服务（推荐）
bash start.sh -a

# 停止所有服务
bash stop.sh

# 前端开发
cd frontend && npm install && npm run dev

# 初始化 Telegram（首次使用必需）
python -m scripts.job init_tg
```

### 服务管理
```bash
# 单独组件
bash start.sh -w    # 仅 Web 服务器
bash start.sh -c    # 仅 Celery 工作进程

# 手动服务控制
python web.py       # Flask 应用（端口 8931）
celery -A scripts.worker:celery worker -Q jd.celery.first -c 6
celery -A scripts.worker:celery worker -Q jd.celery.telegram -c 1
celery -A scripts.worker:celery beat
```

## 系统架构

### 应用程序栈
```
前端 (Vue.js 3 + TypeScript) ←→ 后端 APIs (Flask + SQLAlchemy)
         ↓                              ↓
    Element Plus UI                 Celery 工作进程
         ↓                              ↓
    Vite 开发服务器              MySQL + Redis
    (端口 8930)                  (端口 8931)
```

### 目录结构
```
jd_web/
├── web.py                 # Flask 应用程序入口点
├── jd/                    # 后端应用程序
│   ├── __init__.py       # Flask 工厂，自动蓝图加载
│   ├── models/           # SQLAlchemy 模型 (User, TgGroup 等)
│   ├── services/         # 业务逻辑（不进行数据库提交）
│   ├── views/api/        # RESTful API 端点
│   ├── jobs/             # 独立作业脚本（TG 操作，数据初始化）
│   └── tasks/            # Celery 任务定义
├── frontend/             # Vue.js 应用程序
│   ├── src/views/        # 页面组件
│   ├── src/components/   # 可重用 UI 组件
│   ├── src/api/          # API 服务模块
│   └── src/store/        # Pinia 状态管理
└── scripts/              # 作业运行器和工具
```

## 主要功能和组件

### 数据处理流水线
- **爬虫服务**：化工平台自动爬取（百度、ChemicalBook、Molbase 等）
- **Telegram 集成**：群组监控、聊天记录收集、用户分析
- **任务队列**：
  - `jd.celery.first`：数据处理（6 个工作进程）
  - `jd.celery.telegram`：Telegram 操作（1 个工作进程）

### 前端架构
- **Vue.js 3**：带 TypeScript 的组合式 API
- **Element Plus**：一致的 UI 组件
- **Vite**：快速开发和构建工具
- **客户端路由**：Vue Router 用于 SPA 导航
- **状态管理**：Pinia 用于全局应用状态

### 身份验证和授权
- 带 JWT 支持的基于会话的身份验证
- 基于角色的访问控制 (RBAC) 系统
- 带自定义 `ApiBlueprint` 的 API 端点保护

## 开发指南

### API 标准
```json
// 标准响应格式
{
  "err_code": 0,        // 0 = 成功，>0 = 业务错误
  "err_msg": "",        // 用户友好的错误消息
  "payload": {}         // 响应数据
}

// HTTP 状态码
// 200: 成功（检查 err_code）
// 400: 错误请求/验证
// 401: 需要身份验证
// 500: 服务器错误
```

### 数据库规则
- **事务控制**：只有任务、作业和视图可以提交到数据库
- **服务层**：services/ 中不允许数据库提交
- **模型序列化**：使用内置 `to_dict()` 方法进行 JSON 响应

### 代码组织
- **模型**：数据库实体和关系
- **服务**：纯业务逻辑（无状态）
- **视图**：带身份验证的 API 端点
- **任务**：后台作业处理
- **作业**：计划和手动脚本执行

## 环境配置

### 运行要求
- **后端**：Python 3.7+，Conda 环境 `sdweb`
- **前端**：Node.js，Vue.js 3 + TypeScript
- **数据库**：带加密连接的 MySQL
- **缓存/队列**：Redis 用于 Celery 和会话存储

### 外部集成
- **Telegram API**：需要来自 my.telegram.org 的 api_id/api_hash
- **化工平台**：多个 API 集成
- **代理服务**：OxyLabs 用于网络爬取
- **调度**：Celery Beat 用于自动任务

### 开发流程
1. **遗留迁移**：模板正在被 Vue.js 组件取代
2. **API 一致性**：后端 API 支持旧版和现代前端
3. **双重开发**：同时运行前端（8930）和后端（8931）服务器
4. **任务处理**：后台作业处理繁重操作

## 技术栈

### 后端依赖
- Flask 2.2.5 + SQLAlchemy 2.0.31
- Celery 5.2.7 + Redis 4.5.1
- Telethon 1.36.0 (Telegram 客户端)
- Selenium 4.11.2 (网络自动化)

### 前端依赖
- Vue.js 3 (组合式 API)
- Element Plus UI 库
- TypeScript 类型安全
- Vite 构建工具
- Vue Router + Pinia
- Axios HTTP 客户端

### 计划操作
- **每日**：化工平台数据收集
- **10 分钟**：Telegram 聊天记录更新
- **每小时**：文件处理和清理
- **按需**：通过脚本手动执行作业

## 重要注意事项

- 数据库提交仅限于任务/作业/视图层
- Celery 包可能需要单独安装以解决依赖关系
- 首次使用前需要 Telegram 会话初始化
- 开发期间前端和后端在不同端口运行
- 项目正在从服务端模板逐步迁移到 SPA 架构
