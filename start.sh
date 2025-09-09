#!/bin/bash

# 帮助信息
usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -w              启动web"
  echo "  -c                启动Celery 服务"
  echo "  -f              启动前端开发服务器"
  echo "  -a              执行所有启动（包括前端）"
  echo "  -h             显示帮助信息"
  exit 1
}

# 处理命令行参数
while [[ $# -gt 0 ]]; do
  case $1 in
    -w)
      web=true
      shift
      ;;
    -c)
      celery_flag=true
      shift
      ;;
    -f)
      frontend=true
      shift
      ;;
    -a)
      web=true
      celery_flag=true
      frontend=true
      shift
      ;;
    -h)
      usage
      ;;
    *)
      echo "Unknown option: $1"
      usage
      ;;
  esac
done
# 加载 conda 初始化脚本
echo "加载 conda 初始化脚本"
# export PATH="/home/ubuntu/miniconda3"
eval "$(conda shell.bash hook)"

# 激活 conda 环境
echo "激活环境: sdweb2"
conda activate sdweb2

# celery
if [ "${celery_flag}" = "true" ]; then
  pid=$(ps aux | grep celery | grep -v grep | awk '{print $2}')
  if [ -z "$pid" ]; then
    echo "Celery 未运行"
  else
    kill -9 $pid
    echo "已关闭 Celery 进程: $pid"
  fi
  echo "启动 Celery Worker"
  nohup celery -A scripts.worker:celery worker -Q jd.celery.first -c 6 --loglevel=info > log/celery_out.txt 2>&1 &
  echo "启动 Celery Telegram Worker"
  nohup celery -A scripts.worker:celery worker -Q jd.celery.telegram -c 1 --loglevel=info > log/celery_telegram_out.txt 2>&1 &
  echo "启动 Celery Beat"
  nohup celery -A scripts.worker:celery beat --loglevel=info > log/celery_beat.txt 2>&1 &
  #  echo "启动 Flower"
#  nohup celery -A scripts.worker:celery flower --loglevel=info --persistent=True --db="flower_db" > log/celery_flower.txt 2>&1 &
fi


# web
if [ "${web}" = "true" ]; then
  pid=$(lsof -i :8931 -t)
  if [ -z "$pid" ]; then
    echo "Flask 未运行"
  else
    kill -9 $pid
    echo "已关闭 Flask 进程: $pid"
  fi
  echo "启动 Flask"
  nohup python -m web > log/flask_out.txt 2>&1 &
  echo "Web: http://127.0.0.1:8931"
fi

# frontend
if [ "${frontend}" = "true" ]; then
  pid=$(lsof -i :8930 -t)
  if [ -z "$pid" ]; then
    echo "前端开发服务器未运行"
    echo "启动前端开发服务器"
    # 检查frontend目录是否存在
    if [ -d "frontend" ]; then
      cd frontend
      # 检查node_modules是否存在，如果不存在则安装依赖
      if [ ! -d "node_modules" ]; then
        echo "安装前端依赖"
        npm install
      fi
      # 启动前端开发服务器
      nohup npm run dev > ../log/frontend_out.txt 2>&1 &
      cd ..
      echo "前端开发服务器: http://127.0.0.1:8930"
    else
      echo "前端目录不存在，跳过前端启动"
    fi
  else
    echo "前端开发服务器已在运行，进程ID: $pid"
  fi
fi


echo 'End'
