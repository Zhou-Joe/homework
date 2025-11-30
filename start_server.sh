#!/bin/bash

# 学生学习平台启动脚本

echo "=========================================="
echo "    学生学习平台启动脚本"
echo "=========================================="

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "检查并安装依赖..."
pip install -r requirements.txt

# 数据库迁移
echo "执行数据库迁移..."
python manage.py makemigrations
python manage.py migrate

# 初始化管理员用户
echo "初始化管理员用户..."
python manage.py init_admin

# 启动服务器
echo "启动Django服务器..."
echo "服务地址: http://localhost:8000"
echo "管理后台: http://localhost:8000/admin"
echo "API文档: 请查看 API_DOCUMENTATION.md"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "=========================================="

python manage.py runserver 0.0.0.0:8000