# JD_WEB 2.0

## 项目概述

一个基于Flask的Web应用程序，主要功能为Telegram监控。该系统利用通过Celery的分布式任务处理，2.0版本已经从传统的Jinja2模板积极迁移到现代Vue.js SPA前端。

**核心功能：**
- 实时Telegram群组监控和聊天历史分析
- 基于角色的访问控制（RBAC）和用户管理
- 分布式任务调度和处理

## 快速开始命令

### 🚀 一键安装脚本（推荐）
```bash
# 完整系统安装和启动（适合首次部署）
bash setup_project.sh

# 查看安装选项和帮助
bash setup_project.sh --help

# 仅安装环境依赖
bash setup_project.sh -e

# 仅安装数据库（MariaDB + Redis）
bash setup_project.sh -m -r

# 自定义端口安装
bash setup_project.sh --mysql-port 3307 --backend-port 8932 --frontend-port 3000
```

**一键安装脚本功能特性：**
- ✅ **智能环境检测**：自动检测系统环境和Linux发行版（Ubuntu/Debian/CentOS/Amazon Linux）
- ✅ **Conda环境管理**：自动配置Python环境和依赖安装
- ✅ **数据库自动化**：MariaDB/Redis自动安装、配置和初始化
- ✅ **用户数据预置**：自动创建默认管理员和测试用户账户
- ✅ **前端环境配置**：Node.js依赖安装和构建配置
- ✅ **服务自动启动**：后端API、前端UI、Celery队列全部自动启动
- ✅ **配置文件生成**：自动生成完整的配置文件模板
- ✅ **端口自定义**：支持自定义所有服务端口避免冲突
- ✅ **模块化安装**：支持选择性安装单个组件
- ✅ **安装验证**：自动验证安装结果和服务状态

**脚本参数说明：**
```bash
# 查看完整帮助信息
bash setup_project.sh --help

# 常用安装模式
bash setup_project.sh -a              # 完整安装（推荐）
bash setup_project.sh -e              # 仅Python环境
bash setup_project.sh -m -r           # 仅数据库组件
bash setup_project.sh -d              # 仅数据库初始化
bash setup_project.sh -f              # 仅前端环境
bash setup_project.sh -s              # 仅启动服务

# 端口自定义（避免冲突）
bash setup_project.sh --mysql-port 3307     # 自定义MySQL端口
bash setup_project.sh --redis-port 6380     # 自定义Redis端口
bash setup_project.sh --backend-port 8932   # 自定义后端端口
bash setup_project.sh --frontend-port 3000  # 自定义前端端口

# 静默安装
bash setup_project.sh --skip-confirm        # 跳过确认提示
bash setup_project.sh --force              # 强制重新安装
```

**安装完成后默认信息：**
- 🔐 **超级管理员**：admin / admin123
- 👤 **普通用户**：user1 / 111111、user2 / 111111  
- 📱 **后端服务**：http://localhost:8931
- 🎨 **前端服务**：http://localhost:8930
- 🗄️ **数据库**：MariaDB端口3306，数据库jd2，用户jd_user
- 🔧 **Redis**：localhost:6379

**重要提示：**
⚠️ 首次运行需要初始化Telegram：`python -m scripts.job init_tg`  
🔑 请更新 config.py 中的敏感信息（密码、API密钥等）  
📚 详细配置说明请查看自动生成的 config_template.py

### 开发环境设置
```bash
# 完整系统启动（推荐用于开发）
bash start.sh -a

# 干净地停止所有服务
bash stop.sh

# 前端开发服务器
cd frontend && npm install && npm run dev

# 初始化Telegram集成（首次设置时必需）
python -m scripts.job init_tg

# 手动数据库初始化
bash scripts/init_database.sh

# 手动创建conda环境
bash scripts/setup_conda_env.sh
```

### 服务管理
```bash
# 选择性服务启动
bash start.sh -w    # 仅Web服务器（Flask应用，端口8981）
bash start.sh -c    # 仅Celery工作进程

# 前端开发
cd frontend && npm run dev                                 # Vue.js开发服务器（端口8930）
```

### 常见开发任务
```bash
# 数据库操作
python -m utils.insert_dml_data      # 插入测试数据
python -m utils.delete_chat_history  # 清理聊天历史

# 任务执行
python -m jd.jobs.init_roles_users   # 初始化用户角色
```

## 系统架构

### 高级架构
```
┌─────────────────────────────────────────────────────────────────┐
│                    客户端层（浏览器）                            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│            前端（Vue.js 3 + TypeScript）                      │
│              Element Plus UI + Vite（端口8930）               │
└─────────────────────────────┬───────────────────────────────────┘
                              │ REST APIs
┌─────────────────────────────┴───────────────────────────────────┐
│               后端（Flask + SQLAlchemy）                      │
│                    API服务器（端口8981）                       │
└─────────────┬─────────────────────────────┬───────────────────┘
              │                             │
┌─────────────┴──────────────┐   ┌──────────┴──────────────────┐
│     Celery工作进程         │   │      数据库层               │
│  - jd.celery.first (6)     │   │    MySQL + Redis缓存        │
│  - jd.celery.telegram (1)  │   │                             │
└────────────────────────────┘   └─────────────────────────────┘
```

### 目录结构
```
jd_web/
├── web.py                      # Flask应用程序入口点
├── config.py                   # 应用程序配置
├── start.sh / stop.sh          # 服务管理脚本
├── requirements.txt            # Python依赖
├── package.json               # Node.js依赖
│
├── jd/                        # 主要后端应用程序
│   ├── __init__.py            # Flask应用工厂，自动蓝图加载
│   ├── models/                # SQLAlchemy ORM模型
│   │   ├── tg_group.py        # Telegram群组管理
│   │   ├── tg_account.py      # Telegram账户管理
│   │   ├── secure_user.py     # 用户认证
│   │   └── ...                # 其他域模型
│   ├── services/              # 业务逻辑层（不允许数据库提交）
│   │   └── spider/            # 网络爬虫服务
│   ├── views/api/             # RESTful API端点
│   │   ├── tg/                # Telegram相关API
│   │   ├── user/              # 用户管理API
│   │   └── ...                # 其他API模块
│   ├── jobs/                  # 独立任务脚本
│   │   ├── tg_*.py            # Telegram操作脚本
│   │   └── init_*.py          # 初始化脚本
│   └── tasks/                 # Celery任务定义
│       ├── telegram/          # Telegram处理任务
│       └── first/             # 数据处理任务
│
├── frontend/                  # Vue.js SPA应用程序
│   ├── src/
│   │   ├── views/             # 页面级组件
│   │   ├── components/        # 可重用UI组件
│   │   ├── api/               # HTTP客户端服务
│   │   ├── store/             # Pinia状态管理
│   │   └── router/            # Vue Router配置
│   ├── package.json           # 前端依赖
│   └── vite.config.ts         # Vite构建配置
│
├── scripts/                   # 实用脚本和任务运行器
├── tests/                     # 测试套件
├── utils/                     # 实用脚本
└── dbrt/                      # 数据库模式（DDL/DML）
```

## 核心功能与组件

### 数据处理管道

- **Telegram集成**：
  - 实时群组监控和用户活动跟踪
  - 聊天历史收集和分析
  - 文件下载和处理
  - 用户信息提取和管理

- **任务队列系统**：
  - `jd.celery.first`：重度数据处理（6个并发工作进程）
  - `jd.celery.telegram`：Telegram操作（1个工作进程用于速率限制）
  - Celery Beat：自动化任务调度

### 前端架构（Vue.js 3）
- **现代技术栈**：组合API与TypeScript保证类型安全
- **UI框架**：Element Plus提供一致的专业界面
- **构建系统**：Vite提供快速开发和优化构建
- **路由**：Vue Router支持懒加载组件
- **状态管理**：Pinia用于全局应用程序状态
- **HTTP客户端**：Axios集中化API配置

### 认证与安全
- **多层认证**：基于会话的认证，可选JWT支持
- **RBAC系统**：基于角色的访问控制，具有细粒度权限
- **API保护**：自定义`ApiBlueprint`自动认证
- **安全配置**：加密数据库连接和安全默认设置

## 开发指南

### API标准与约定
```json
// 标准API响应格式
{
  "err_code": 0,           // 0 = 成功，>0 = 应用程序错误
  "err_msg": "",           // 人类可读的错误消息
  "payload": {             // 响应数据
    "data": [],            // 主要数据数组/对象
    "total": 100,          // 分页总数
    "page": 1,             // 当前页面
    "page_size": 20        // 每页项目数
  }
}

// HTTP状态码使用：
// 200: 成功（始终检查err_code应用程序错误）
// 400: 错误请求/验证错误
// 401: 需要认证
// 403: 权限被拒绝
// 404: 资源未找到
// 500: 内部服务器错误
```

### 代码组织与架构规则

#### 层级职责
- **模型**（`jd/models/`）：数据库实体、关系和基本序列化
- **服务**（`jd/services/`）：纯业务逻辑，无状态操作（**不允许数据库提交**）
- **视图**（`jd/views/api/`）：API端点、请求/响应处理、认证
- **任务**（`jd/tasks/`）：Celery后台处理，支持数据库提交
- **任务脚本**（`jd/jobs/`）：手动/计划执行的独立脚本

#### 数据库事务规则
```python
# ✅ 允许 - 视图、任务、任务脚本可以提交
@api_bp.route('/api/users', methods=['POST'])
def create_user():
    user = User(**data)
    db.session.add(user)
    db.session.commit()  # 在视图中允许

# ❌ 禁止 - 服务不能提交
class UserService:
    def create_user(self, data):
        user = User(**data)
        db.session.add(user)
        # db.session.commit()  # 在服务中不允许
        return user
```

#### 模型约定
```python
# 使用内置to_dict()进行JSON序列化
class TgGroup(db.Model):
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# API使用
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

# 检查代码质量（如果配置）
flake8 jd/
pylint jd/
```

## 环境配置

### 运行时要求
- **Python**：3.7+ 配合Conda环境`sdweb`
- **Node.js**：最新LTS版本用于前端开发
- **数据库**：MySQL 8.0+ 支持加密连接
- **缓存/消息代理**：Redis 6.0+ 用于Celery和会话
- **系统**：推荐Linux/macOS进行开发

### 外部服务依赖
- **Telegram API**：
  - 需要从 https://my.telegram.org 获取`api_id`和`api_hash`
  - 本地存储会话文件以保持持久连接
- **任务调度**：Celery Beat用于自动化操作

### 配置管理
```python
# config.py结构
class Config:
    # 数据库
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://...'
    
    # Redis
    REDIS_URL = 'redis://localhost:6379/0'
    
    # Telegram
    TG_API_ID = 'your_api_id'
    TG_API_HASH = 'your_api_hash'
    
    # Celery
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
```

### 开发工作流程
1. **环境设置**：使用提供的设置脚本确保一致的开发环境
2. **双服务器开发**：同时运行前端（8930）和后端（8981）
3. **数据库迁移**：在`dbrt/`目录中使用手动SQL脚本
4. **任务处理**：重度操作由后台Celery工作进程处理
5. **遗留系统迁移**：逐步用Vue.js组件替换Jinja2模板

## 技术栈

### 后端技术
- **Web框架**：Flask 2.2.5配合SQLAlchemy 2.0.31 ORM
- **任务队列**：Celery 5.2.7配合Redis 4.5.1代理
- **Telegram客户端**：Telethon 1.36.0用于API交互
- **Web自动化**：Selenium 4.11.2用于动态内容爬取
- **数据库**：MySQL配合PyMySQL连接器
- **认证**：Flask-Session配合Redis后端

### 前端技术
- **框架**：Vue.js 3配合组合API
- **语言**：TypeScript增强开发者体验
- **UI库**：Element Plus提供一致的组件设计
- **构建工具**：Vite提供快速开发和优化构建
- **路由**：Vue Router用于SPA导航
- **状态管理**：Pinia作为现代Vuex替代品
- **HTTP客户端**：Axios配合请求/响应拦截器

### 运维与监控
- **任务调度**：Celery Beat配合crontab风格调度
- **日志记录**：Python日志配合可配置级别
- **进程管理**：自定义shell脚本管理服务生命周期
- **开发工具**：热重载、源映射、TypeScript检查

### 计划操作
- **每日（00:00）**：数据收集和分析
- **每10分钟**：Telegram聊天历史更新和用户跟踪
- **每小时**：文件处理、清理和系统维护
- **按需**：通过CLI脚本手动执行任务

## 关键运维注意事项

### 数据库与事务管理
- **严格层次分离**：只有视图、任务和任务脚本可以提交数据库事务
- **服务层隔离**：服务提供纯业务逻辑，无副作用
- **模型序列化**：使用内置`to_dict()`方法保证一致的JSON输出

### Celery与后台处理
- **队列隔离**：不同操作类型使用单独队列防止阻塞
- **工作进程配置**：根据操作特性配置不同并发级别
- **依赖解析**：某些Celery包可能需要单独安装步骤

### Telegram集成
- **会话管理**：首次使用前必须初始化Telegram会话
- **速率限制**：Telegram操作使用单个工作进程以遵守API限制
- **文件处理**：自动下载和处理媒体文件

### 开发环境
- **端口管理**：前端（8930）和后端（8981）运行在不同端口
- **热重载**：两个服务器都支持代码更改时自动重启
- **架构迁移**：系统逐渐从SSR过渡到SPA模型

### 安全考虑
- **API认证**：所有端点通过自定义蓝图认证保护
- **数据库安全**：加密连接和参数化查询
- **会话管理**：配合Redis后端的安全会话处理
- **配置**：敏感值存储在环境特定配置文件中
