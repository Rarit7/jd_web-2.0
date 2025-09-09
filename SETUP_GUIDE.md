# SDJD_TG管理系统 - 项目安装指南

## 快速开始

### 一键安装（推荐）

```bash
# 完整安装（环境配置+数据库+前端+启动服务）
bash setup_project.sh

# 或者使用简化命令
bash setup_project.sh -a
```

### 分步安装

如果需要分步执行，可以使用以下命令：

```bash
# 1. 仅配置conda环境
bash setup_project.sh -e

# 2. 仅初始化数据库
bash setup_project.sh -d

# 3. 仅配置前端环境
bash setup_project.sh -f

# 4. 仅启动服务
bash setup_project.sh -s
```

## 安装前准备

### 系统要求

- **操作系统**: Linux/macOS/Windows(WSL)
- **Python**: 3.9+ (通过conda安装)
- **Node.js**: 18+ (用于前端开发)
- **MySQL**: 5.7+ 或 MySQL 8.0+
- **Redis**: 6.0+ (用于Celery任务队列)

### 必要组件检查

```bash
# 检查conda
conda --version

# 检查MySQL
mysql --version

# 检查Redis
redis-cli --version

# 检查Node.js (可选，仅开发前端需要)
node --version
npm --version
```

## 详细安装步骤

### 1. 环境配置

```bash
# 运行环境配置脚本
bash scripts/setup_conda_env.sh

# 手动激活环境
conda activate sdweb
```

环境配置脚本会：
- 检查conda是否已安装
- 创建名为`sdweb`的虚拟环境
- 安装requirements.txt中的所有依赖
- 创建环境激活快捷脚本

### 2. 数据库初始化

```bash
# 完整数据库初始化
bash scripts/init_database.sh -a

# 或分步执行
bash scripts/init_database.sh -c    # 创建数据库
bash scripts/init_database.sh -t    # 创建表
bash scripts/init_database.sh -d    # 插入数据
```

数据库脚本会：
- 检查MySQL连接
- 创建项目数据库
- 执行DDL脚本创建表结构
- 执行DML脚本插入初始数据（如果存在）

### 3. 配置文件设置

编辑`config.py`文件，确保数据库连接信息正确：

```python
# mysql相关配置
SQLALCHEMY_DATABASE_URI = 'mysql+mysqldb://用户名:密码@主机:端口/数据库名?charset=utf8mb4'
```

### 4. 前端环境配置（可选）

如果需要前端开发：

```bash
cd frontend
npm install
npm run dev
```

### 5. 启动服务

```bash
# 启动所有服务
bash start.sh -a

# 或分别启动
bash start.sh -w    # Web服务 (端口8931)
bash start.sh -c    # Celery服务
bash start.sh -f    # 前端服务 (端口8930)
```

### 6. Telegram初始化（首次运行）

```bash
conda activate sdweb
python -m scripts.job init_tg
```

按提示输入：
- Telegram账号手机号
- 验证码
- 两步验证密码（如果启用）

## 服务管理

### 启动服务

```bash
bash start.sh -a    # 启动所有服务
bash start.sh -w    # 仅启动Web服务
bash start.sh -c    # 仅启动Celery服务
bash start.sh -f    # 仅启动前端服务
```

### 停止服务

```bash
bash stop.sh
```

### 服务状态检查

```bash
# 检查端口占用
lsof -i :8931    # Web服务
lsof -i :8930    # 前端服务

# 检查进程
ps aux | grep celery
ps aux | grep python
ps aux | grep node
```

## 访问系统

- **后端API**: http://localhost:8931
- **前端界面**: http://localhost:8930
- **API文档**: http://localhost:8931/api

## 故障排查

### 常见问题

1. **conda命令未找到**
   ```bash
   # 添加conda到PATH
   export PATH="/path/to/anaconda3/bin:$PATH"
   # 或重新安装anaconda/miniconda
   ```

2. **MySQL连接失败**
   ```bash
   # 检查MySQL服务状态
   sudo systemctl status mysql
   # 检查端口
   netstat -an | grep 3306
   # 测试连接
   mysql -h 127.0.0.1 -u root -p
   ```

3. **端口已占用**
   ```bash
   # 查看占用端口的进程
   lsof -i :8931
   # 杀死进程
   kill -9 PID
   ```

4. **前端依赖安装失败**
   ```bash
   # 清理缓存
   npm cache clean --force
   # 删除node_modules重新安装
   rm -rf node_modules package-lock.json
   npm install
   ```

### 日志文件

检查以下日志文件来诊断问题：

- `log/flask_out.txt` - Flask Web服务日志
- `log/celery_out.txt` - Celery Worker日志
- `log/celery_telegram_out.txt` - Telegram任务日志
- `log/celery_beat.txt` - Celery定时任务日志
- `log/frontend_out.txt` - 前端开发服务器日志

### 重新安装

如果安装过程中出现问题，可以清理后重新安装：

```bash
# 删除conda环境
conda env remove -n sdweb

# 清理前端依赖
rm -rf frontend/node_modules

# 重新执行安装
bash setup_project.sh -a
```

## 开发环境

### 开发模式启动

```bash
# 激活环境
conda activate sdweb

# 启动后端（开发模式）
python web.py

# 启动前端（开发模式）
cd frontend && npm run dev

# 启动Celery（开发模式）
celery -A scripts.worker:celery worker --loglevel=debug
```

### 代码热重载

- **后端**: Flask会自动检测代码变化并重载
- **前端**: Vite开发服务器支持热重载
- **Celery**: 需要手动重启worker进程

## 生产部署

生产环境部署建议：

1. 使用Gunicorn作为WSGI服务器
2. 配置Nginx反向代理
3. 使用Supervisor管理进程
4. 配置数据库连接池
5. 设置日志轮转
6. 配置SSL证书

详细的生产部署配置请参考项目文档。

## 技术支持

如果遇到问题：

1. 检查错误日志文件
2. 查看CLAUDE.md项目文档
3. 确认系统依赖是否完整安装
4. 验证配置文件是否正确

---

**提示**: 首次安装建议使用`bash setup_project.sh`一键安装脚本，该脚本会自动处理大部分配置工作。