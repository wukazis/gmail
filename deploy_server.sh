#!/bin/bash
# Gmail API服务器部署脚本

echo "🚀 Gmail API服务器部署脚本"
echo "================================"

# 检查Python版本
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python3未安装"
    exit 1
fi

# 创建虚拟环境
echo "📦 创建虚拟环境..."
python3 -m venv gmail_api_env
source gmail_api_env/bin/activate

# 安装依赖
echo "📥 安装依赖..."
pip install -r requirements_server.txt

# 检查必要文件
echo "🔍 检查必要文件..."
if [ ! -f "credentials.json" ]; then
    echo "❌ 缺少 credentials.json 文件"
    echo "请上传OAuth2凭据文件"
    exit 1
fi

if [ ! -f "token.json" ]; then
    echo "❌ 缺少 token.json 文件"
    echo "请先在本地完成OAuth认证，然后上传token.json"
    exit 1
fi

# 复制必要的Python文件
echo "📋 复制必要文件..."
# 确保gmail_api_fetcher.py存在
if [ ! -f "gmail_api_fetcher.py" ]; then
    echo "❌ 缺少 gmail_api_fetcher.py 文件"
    exit 1
fi

# 设置环境变量
export PORT=5000
export HOST=0.0.0.0

echo "✅ 部署准备完成"
echo ""
echo "🚀 启动服务器:"
echo "   开发模式: python gmail_api_server.py"
echo "   生产模式: gunicorn -w 4 -b 0.0.0.0:5000 gmail_api_server:app"
echo ""
echo "🔗 API端点:"
echo "   健康检查: GET  /health"
echo "   获取验证码: POST /fetch-code"
echo "   搜索邮件: POST /search-emails"
echo "   测试连接: GET  /test-connection"