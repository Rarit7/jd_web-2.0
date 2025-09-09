#!/bin/bash

# SDJD_TG管理系统 - Conda环境配置脚本
# 用于创建和配置项目所需的conda虚拟环境

set -e  # 遇到错误立即退出

# 配置变量
CONDA_ENV_NAME="sdweb2"
PYTHON_VERSION="3.9"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查conda是否已安装
check_conda() {
    print_status "检查 Conda 是否已安装..."
    if ! command -v conda &> /dev/null; then
        print_error "Conda 未找到！请先安装 Anaconda 或 Miniconda"
        print_status "下载地址: https://docs.conda.io/en/latest/miniconda.html"
        exit 1
    fi
    print_success "Conda 已安装: $(conda --version)"
}

# 初始化conda
init_conda() {
    print_status "初始化 Conda 环境..."
    
    # 检查是否已经初始化
    if [[ ! -f ~/.bashrc ]] || ! grep -q "conda initialize" ~/.bashrc; then
        print_status "初始化 Conda shell 集成..."
        conda init bash
        print_warning "请重新启动终端或运行 'source ~/.bashrc' 后重新执行此脚本"
        exit 0
    fi
    
    # 加载conda初始化脚本
    eval "$(conda shell.bash hook)"
    print_success "Conda 环境已初始化"
}

# 创建或更新conda环境
setup_conda_env() {
    print_status "设置 Conda 虚拟环境: $CONDA_ENV_NAME"
    
    # 检查环境是否已存在
    if conda env list | grep -q "^$CONDA_ENV_NAME "; then
        print_warning "环境 '$CONDA_ENV_NAME' 已存在"
        read -p "是否要重新创建环境? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "删除现有环境..."
            conda env remove -n $CONDA_ENV_NAME -y
        else
            print_status "使用现有环境"
            return 0
        fi
    fi
    
    # 创建新环境
    print_status "创建 Python $PYTHON_VERSION 环境..."
    conda create -n $CONDA_ENV_NAME python=$PYTHON_VERSION -y
    print_success "环境 '$CONDA_ENV_NAME' 创建成功"
}

# 激活环境并安装Python依赖
install_python_deps() {
    print_status "激活环境并安装 Python 依赖..."
    
    # 激活环境
    conda activate $CONDA_ENV_NAME
    
    # 升级pip
    print_status "升级 pip..."
    pip install --upgrade pip
    
    # 安装项目依赖
    print_status "安装项目依赖..."
    cd "$PROJECT_DIR"
    
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
        print_success "Python 依赖安装完成"
    else
        print_error "未找到 requirements.txt 文件"
        exit 1
    fi
}

# 验证安装
verify_installation() {
    print_status "验证安装..."
    
    # 激活环境
    conda activate $CONDA_ENV_NAME
    
    # 检查关键包
    local key_packages=("flask" "celery" "telethon" "sqlalchemy" "redis")
    local missing_packages=()
    
    for package in "${key_packages[@]}"; do
        if ! python -c "import $package" &> /dev/null; then
            missing_packages+=("$package")
        fi
    done
    
    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        print_error "以下关键包未正确安装: ${missing_packages[*]}"
        exit 1
    fi
    
    print_success "所有关键包验证通过"
}

# 创建环境激活脚本
create_activation_script() {
    print_status "创建环境激活脚本..."
    
    local activate_script="$PROJECT_DIR/activate_env.sh"
    cat > "$activate_script" << 'EOF'
#!/bin/bash
# 项目环境激活脚本

# 加载conda初始化
eval "$(conda shell.bash hook)"

# 激活项目环境
conda activate sdweb

echo "项目环境已激活: sdweb"
echo "Python版本: $(python --version)"
echo "工作目录: $(pwd)"
echo ""
echo "可用命令:"
echo "  bash start.sh -a    # 启动所有服务"
echo "  bash start.sh -w    # 启动web服务"
echo "  bash start.sh -c    # 启动celery服务" 
echo "  bash start.sh -f    # 启动前端服务"
EOF

    chmod +x "$activate_script"
    print_success "环境激活脚本已创建: $activate_script"
}

# 显示环境信息
show_env_info() {
    print_success "=== 环境配置完成 ==="
    echo ""
    print_status "环境信息:"
    echo "  环境名称: $CONDA_ENV_NAME"
    echo "  Python版本: $PYTHON_VERSION"
    echo "  项目目录: $PROJECT_DIR"
    echo ""
    print_status "激活环境:"
    echo "  conda activate $CONDA_ENV_NAME"
    echo "  # 或者运行:"
    echo "  source $PROJECT_DIR/activate_env.sh"
    echo ""
    print_status "下一步:"
    echo "  1. 配置数据库连接 (编辑 config.py)"
    echo "  2. 初始化数据库: bash scripts/init_database.sh"
    echo "  3. 启动服务: bash start.sh -a"
}

# 主函数
main() {
    echo "========================================"
    echo "  SDJD_TG管理系统 - 环境配置脚本"
    echo "========================================"
    echo ""
    
    check_conda
    init_conda
    setup_conda_env
    install_python_deps
    verify_installation
    create_activation_script
    show_env_info
}

# 执行主函数
main "$@"