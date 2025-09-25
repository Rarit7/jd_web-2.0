# CLAUDE.md

这是一个基于 Flask + Vue.js 的化工行业数据聚合与 Telegram 监控系统的完整开发指南。

## 项目概述

**JD Web** 是一个专业的化工行业情报收集与 Telegram 群组监控平台，集成了多平台数据爬取、实时消息监控、竞争分析等功能。系统采用现代化的前后端分离架构，利用分布式任务队列处理复杂的数据采集和分析任务。

**核心能力：**
- 多平台化工数据爬取（百度、Google、ChemicalBook、Molbase、1688等）
- 实时 Telegram 群组监控和聊天历史分析
- 自动化竞争情报收集
- 基于角色的访问控制（RBAC）
- 分布式任务调度与处理

## 快速启动命令

### 环境管理
```bash
# 激活 conda 环境（项目使用 sdweb2）
conda activate sdweb2

# 完整系统启动（推荐用于开发）
bash start.sh -a

# 清理环境并启动所有服务
bash start.sh -a -q

# 优雅关闭所有服务
bash stop.sh
```

### 分模块启动
```bash
# 仅启动 Web 服务器
bash start.sh -w                # Flask API 服务器 (端口 8931)

# 仅启动 Celery 任务队列
bash start.sh -c               # 后台任务处理

# 仅启动前端开发服务器
bash start.sh -f               # Vue.js 开发服务器 (端口 8930)
```

### 手动服务控制
```bash
# Flask 应用
python -m web                  # 启动 Web API 服务器

# Celery 工作队列
celery -A scripts.worker:celery worker -Q jd.celery.first -c 6        # 数据处理队列
celery -A scripts.worker:celery worker -Q jd.celery.telegram -c 1     # Telegram 操作队列
celery -A scripts.worker:celery beat                                   # 任务调度器

# 前端开发
cd frontend && npm install && npm run dev                              # Vue.js 开发服务器
```

### 常用开发任务
```bash
# 初始化与配置
python -m scripts.job init_tg                    # 初始化 Telegram 集成
python -m jd.jobs.init_roles_users              # 初始化用户角色
bash scripts/init_database.sh                   # 数据库初始化

# 数据操作
python -m utils.insert_dml_data                 # 插入测试数据
python -m utils.delete_chat_history             # 清理聊天历史

# 任务管理
python -m jd.jobs.job_queue_manager             # 队列管理
python -m jd.jobs.auto_tagging                  # 自动标签任务

# 测试与检查
pytest                                          # 运行测试套件
python jd/tasks/test_base_task.py              # 测试基础任务功能
```

## 系统架构

### 技术栈概览
```
┌─────────────────────────────────────────────────────────┐
│                   浏览器客户端                           │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP/WebSocket
┌─────────────────────┴───────────────────────────────────┐
│          前端 (Vue.js 3 + TypeScript)                  │
│     Element Plus UI + Vite (开发端口 8930)             │
└─────────────────────┬───────────────────────────────────┘
                      │ RESTful API
┌─────────────────────┴───────────────────────────────────┐
│              后端 (Flask + SQLAlchemy)                 │
│                API 服务器 (端口 8931)                   │
└─────────┬───────────────────────────────┬───────────────┘
          │                               │
┌─────────┴────────────┐       ┌──────────┴─────────────────┐
│   Celery 任务队列     │       │        数据层              │
│ • first队列 (6工作者) │       │   MySQL + Redis 缓存       │
│ • telegram队列 (1工作者)│      │                           │
└──────────────────────┘       └────────────────────────────┘
```

### 目录结构
```
jd_web/
├── web.py                     # Flask 应用入口点
├── config.py                  # 应用配置文件
├── start.sh / stop.sh         # 服务管理脚本
├── requirements.txt           # Python 依赖
│
├── jd/                       # 主后端应用
│   ├── __init__.py           # Flask 应用工厂
│   ├── models/               # SQLAlchemy ORM 模型
│   ├── services/             # 业务逻辑层（无数据库提交）
│   ├── views/api/            # RESTful API 端点
│   ├── jobs/                 # 独立任务脚本
│   ├── tasks/                # Celery 任务定义
│   ├── helpers/              # 辅助工具函数
│   └── utils/                # 通用工具模块
│
├── frontend/                 # Vue.js SPA 应用
│   ├── src/
│   │   ├── views/            # 页面级组件
│   │   ├── components/       # 可复用 UI 组件
│   │   ├── api/              # HTTP 客户端服务
│   │   ├── store/            # Pinia 状态管理
│   │   ├── router/           # Vue Router 配置
│   │   ├── utils/            # 前端工具函数
│   │   └── types/            # TypeScript 类型定义
│   ├── package.json          # 前端依赖管理
│   └── vite.config.ts        # Vite 构建配置
│
├── scripts/                  # 实用脚本和任务运行器
├── tests/                    # 测试套件
├── static/                   # 静态文件服务
├── logs/                     # 应用日志文件
├── dbrt/                     # 数据库架构 (DDL/DML)
└── utils/                    # 系统级实用脚本
```

## 核心功能模块

### 数据处理管道
- **化工情报系统**：
  - 多平台爬虫引擎（百度、Google、ChemicalBook、Molbase、1688等）
  - 自动化产品数据采集与分析
  - 竞争定价情报收集
  - 市场趋势分析与报告

- **Telegram 集成**：
  - 实时群组监控与用户活动跟踪
  - 聊天历史收集与分析
  - 文件下载与自动处理
  - 用户信息提取与管理

- **任务队列系统**：
  - `jd.celery.first`: 重型数据处理（6个并发工作者）
  - `jd.celery.telegram`: Telegram 操作（1个工作者，支持速率限制）
  - Celery Beat: 自动化任务调度

### 前端架构（Vue.js 3）
- **现代化技术栈**: Composition API + TypeScript，提供类型安全
- **UI 框架**: Element Plus，确保一致的专业界面
- **构建系统**: Vite，快速开发与优化构建
- **路由管理**: Vue Router，支持懒加载组件
- **状态管理**: Pinia，全局应用状态管理
- **HTTP 客户端**: Axios，集中化 API 配置
- **样式方案**: UnoCSS + TailwindCSS + SCSS

### 认证与安全
- **多层认证**: 基于 Session 的认证，支持可选 JWT
- **RBAC 系统**: 基于角色的访问控制，细粒度权限管理
- **API 保护**: 自定义 `ApiBlueprint`，自动认证检查
- **安全配置**: 加密数据库连接，安全默认设置

## 开发指南

### API 标准与约定
```json
// 标准 API 响应格式
{
  "err_code": 0,           // 0 = 成功, >0 = 应用错误
  "err_msg": "",           // 人类可读的错误消息
  "payload": {             // 响应数据
    "data": [],            // 主数据数组/对象
    "total": 100,          // 分页总数
    "page": 1,             // 当前页码
    "page_size": 20        // 每页项目数
  }
}

// HTTP 状态码使用规范:
// 200: 成功 (总是检查 err_code 获取应用错误)
// 400: 错误请求 / 验证错误
// 401: 需要认证
// 403: 权限拒绝
// 404: 资源未找到
// 500: 内部服务器错误
```

### 代码组织架构规则

#### 分层职责
- **模型层** (`jd/models/`): 数据库实体、关系定义、基本序列化
- **服务层** (`jd/services/`): 纯业务逻辑，无状态操作 (**不允许数据库提交**)
- **视图层** (`jd/views/api/`): API 端点、请求/响应处理、认证检查
- **任务层** (`jd/tasks/`): Celery 后台处理，包含数据库提交
- **作业层** (`jd/jobs/`): 独立脚本，用于手动/定时执行

#### 数据库事务规则
```python
# ✅ 允许 - 视图、任务、作业可以提交
@api_bp.route('/api/users', methods=['POST'])
def create_user():
    user = User(**data)
    db.session.add(user)
    db.session.commit()  # 在视图中允许

# ❌ 禁止 - 服务层不能提交
class UserService:
    def create_user(self, data):
        user = User(**data)
        db.session.add(user)
        # db.session.commit()  # 服务层中不允许
        return user
```

#### 模型约定
```python
# 使用内置 to_dict() 进行 JSON 序列化
class TgGroup(db.Model):
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# API 使用方式
return jsonify({
    'err_code': 0,
    'payload': {'data': [group.to_dict() for group in groups]}
})
```

### 测试与质量保证
```bash
# 运行测试套件
pytest tests/

# 测试特定模块
python jd/tasks/test_base_task.py

# 代码质量检查（如果配置）
flake8 jd/
pylint jd/

# 前端类型检查
cd frontend && npm run type-check
```

## 环境配置

### 运行时需求
- **Python**: 3.9+ 与 Conda 环境 `sdweb2`
- **Node.js**: 最新 LTS 版本（前端开发）
- **数据库**: MySQL 8.0+，支持加密连接
- **缓存/消息代理**: Redis 6.0+（Celery 和会话存储）
- **系统**: Linux/macOS（推荐用于开发）

### 外部服务依赖
- **Telegram API**:
  - 需要从 https://my.telegram.org 获取 `api_id` 和 `api_hash`
  - 本地存储会话文件以保持持久连接
- **化工平台 APIs**: 各种供应商集成
- **代理服务**: OxyLabs 网络爬取（可选）
- **任务调度**: Celery Beat 自动化操作

### 配置管理
```python
# config.py 结构示例
class Config:
    # 数据库
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqldb://user:pass@host:port/db'

    # Redis
    REDIS_URL = 'redis://localhost:6379/0'

    # Telegram
    TG_CONFIG = {
        "api_id": "your_api_id",
        "api_hash": "your_api_hash",
        "sqlite_db_name": "jd_tg.db"
    }

    # Celery
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
```

### 开发工作流程
1. **环境设置**: 使用提供的设置脚本确保一致的开发环境
2. **双服务器开发**: 同时运行前端 (8930) 和后端 (8931) 服务器
3. **数据库迁移**: 使用 `dbrt/` 目录中的手动 SQL 脚本
4. **任务处理**: 重型操作由后台 Celery 工作者处理
5. **现代化迁移**: 逐步将 Jinja2 模板替换为 Vue.js 组件

## 技术栈详情

### 后端技术
- **Web 框架**: Flask 2.2.5 + SQLAlchemy 2.0.42 ORM
- **任务队列**: Celery 5.5.3 + Redis 4.5.1 代理
- **Telegram 客户端**: Telethon 1.40.0，用于 API 交互
- **Web 自动化**: Selenium 4.34.2，动态内容爬取
- **数据库**: MySQL + PyMySQL/mysqlclient 连接器
- **认证**: Flask-JWT-Extended + Flask-Session，Redis 后端

### 前端技术
- **框架**: Vue.js 3.5.21 + Composition API
- **语言**: TypeScript 5.7.2，增强开发体验
- **UI 库**: Element Plus 2.11.2，一致的组件设计
- **构建工具**: Vite 6.0.7，快速开发和优化构建
- **路由**: Vue Router 4.5.1，SPA 导航
- **状态管理**: Pinia 2.3.0，现代化 Vuex 替代方案
- **HTTP 客户端**: Axios 1.7.9，请求/响应拦截器
- **样式**: UnoCSS 0.65.1 + TailwindCSS 3.4.16 + SCSS

### 操作与监控
- **任务调度**: Celery Beat，crontab 风格调度
- **日志记录**: Python logging，可配置级别
- **进程管理**: 自定义 shell 脚本管理服务生命周期
- **开发工具**: 热重载、源映射、TypeScript 检查

### 定时操作
- **每日 (00:00)**: 化工平台数据收集与分析
- **每 10 分钟**: Telegram 聊天历史更新和用户跟踪
- **每小时**: 文件处理、清理和系统维护
- **按需**: 通过 CLI 脚本手动执行任务

## 关键操作注意事项

### 数据库与事务管理
- **严格分层分离**: 只有视图、任务和作业可以提交数据库事务
- **服务层隔离**: 服务提供纯业务逻辑，无副作用
- **模型序列化**: 使用内置 `to_dict()` 方法确保一致的 JSON 输出

### Celery 与后台处理
- **队列隔离**: 不同操作类型使用独立队列防止阻塞
- **工作者配置**: 根据操作特性设置不同并发级别
- **依赖解析**: 某些 Celery 包可能需要单独安装步骤

### Telegram 集成
- **会话管理**: 首次使用前必须初始化 Telegram 会话
- **速率限制**: 单一工作者处理 Telegram 操作以遵守 API 限制
- **文件处理**: 自动下载和处理媒体文件

### 开发环境
- **端口管理**: 前端 (8930) 和后端 (8931) 运行在不同端口
- **热重载**: 两个服务器都支持代码更改时自动重启
- **架构迁移**: 系统正在从 SSR 逐步过渡到 SPA 模型

### 安全考虑
- **API 认证**: 通过自定义蓝图认证保护所有端点
- **数据库安全**: 加密连接和参数化查询
- **会话管理**: 使用 Redis 后端的安全会话处理
- **配置**: 敏感值存储在环境特定配置文件中

---

## 重要提醒

- **环境**: 项目使用 `sdweb2` conda 环境，不是 `sdweb`
- **端口**: Flask 服务运行在 8931，前端开发服务器运行在 8930
- **数据库**: 事务管理严格按分层架构执行
- **任务队列**: 重型操作和 Telegram 操作使用不同队列
- **前端构建**: 生产构建输出到 `../static/dist` 目录

遵循本指南确保高效开发和系统稳定性。如有疑问，请参考相关源代码或联系项目维护者。