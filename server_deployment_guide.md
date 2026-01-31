# Gmail API 外网服务器部署指南

## 概述
在外网服务器上部署Gmail API服务，绕过中国防火墙限制，提供稳定的验证码获取服务。

## 架构图
```
中国本地客户端 → 外网服务器 → Gmail API → 返回验证码
     ↓              ↓
  混合获取器    Gmail API服务器
     ↓              ↓
  IMAP备用      OAuth认证
```

## 部署步骤

### 1. 准备外网服务器
- **推荐**: AWS EC2, Google Cloud, DigitalOcean, Vultr
- **配置**: 1GB RAM, 1 CPU核心即可
- **系统**: Ubuntu 20.04+ 或 CentOS 8+
- **网络**: 确保可以访问 `googleapis.com`

### 2. 上传文件到服务器
```bash
# 需要上传的文件
scp credentials.json user@your-server:/path/to/app/
scp token.json user@your-server:/path/to/app/
scp gmail_api_server.py user@your-server:/path/to/app/
scp gmail_api_fetcher.py user@your-server:/path/to/app/
scp requirements_server.txt user@your-server:/path/to/app/
scp deploy_server.sh user@your-server:/path/to/app/
```

### 3. 服务器端部署
```bash
# SSH登录服务器
ssh user@your-server

# 进入应用目录
cd /path/to/app/

# 给部署脚本执行权限
chmod +x deploy_server.sh

# 运行部署脚本
./deploy_server.sh

# 启动服务器 (开发模式)
python gmail_api_server.py

# 或启动生产模式
gunicorn -w 4 -b 0.0.0.0:5000 gmail_api_server:app
```

### 4. 配置防火墙
```bash
# Ubuntu/Debian
sudo ufw allow 5000

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

### 5. 设置系统服务 (可选)
创建 `/etc/systemd/system/gmail-api.service`:
```ini
[Unit]
Description=Gmail API Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/app
Environment=PATH=/path/to/app/gmail_api_env/bin
ExecStart=/path/to/app/gmail_api_env/bin/gunicorn -w 4 -b 0.0.0.0:5000 gmail_api_server:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gmail-api
sudo systemctl start gmail-api
sudo systemctl status gmail-api
```

## API接口文档

### 1. 健康检查
```http
GET /health
```
响应:
```json
{
  "status": "ok",
  "service": "Gmail API Server",
  "gmail_api_ready": true
}
```

### 2. 获取验证码
```http
POST /fetch-code
Content-Type: application/json

{
  "target_email": "user@example.com",
  "hours_back": 1
}
```
响应:
```json
{
  "success": true,
  "code": "123456",
  "target_email": "user@example.com"
}
```

### 3. 搜索邮件
```http
POST /search-emails
Content-Type: application/json

{
  "query": "from:openai.com newer_than:1h",
  "max_results": 10
}
```

### 4. 测试连接
```http
GET /test-connection
```

## 本地客户端配置

### 1. 更新混合获取器
```python
# 在 updated_hybrid_fetcher.py 中设置服务器地址
API_SERVER_URL = 'http://your-server-ip:5000'
```

### 2. 使用更新版获取器
```python
from updated_hybrid_fetcher import get_verification_code_with_server

# 获取验证码
code = await get_verification_code_with_server(
    gmail_email='your-gmail@gmail.com',
    gmail_password='your-app-password',
    target_email='target@example.com'
)
```

## 安全建议

### 1. 使用HTTPS
```bash
# 安装Nginx和SSL证书
sudo apt install nginx certbot python3-certbot-nginx

# 配置SSL
sudo certbot --nginx -d your-domain.com
```

### 2. API密钥认证
在服务器代码中添加API密钥验证:
```python
@app.before_request
def check_api_key():
    if request.endpoint != 'health_check':
        api_key = request.headers.get('X-API-Key')
        if api_key != 'your-secret-api-key':
            return jsonify({'error': 'Unauthorized'}), 401
```

### 3. 限制访问IP
```python
from flask import request

ALLOWED_IPS = ['your-local-ip', 'another-allowed-ip']

@app.before_request
def limit_remote_addr():
    if request.remote_addr not in ALLOWED_IPS:
        return jsonify({'error': 'Forbidden'}), 403
```

## 监控和日志

### 1. 日志配置
```python
import logging
from logging.handlers import RotatingFileHandler

# 配置日志轮转
handler = RotatingFileHandler('gmail_api.log', maxBytes=10000000, backupCount=5)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
```

### 2. 监控脚本
```bash
#!/bin/bash
# monitor.sh - 监控服务状态
while true; do
    if ! curl -f http://localhost:5000/health > /dev/null 2>&1; then
        echo "$(date): Service down, restarting..."
        sudo systemctl restart gmail-api
    fi
    sleep 60
done
```

## 成本估算
- **VPS服务器**: $5-10/月 (1GB RAM)
- **流量费用**: 几乎可忽略 (API调用很少)
- **总成本**: 约 $5-10/月

## 优势
1. **绕过防火墙**: 外网服务器可正常访问Gmail API
2. **高可用性**: 24/7运行，不受本地网络影响
3. **快速响应**: 外网服务器到Gmail API延迟更低
4. **集中管理**: 多个本地客户端可共享一个API服务器
5. **备用策略**: 服务器不可用时自动回退到IMAP

## 故障排除

### 1. 服务器无法访问Gmail API
```bash
# 测试网络连接
curl -I https://gmail.googleapis.com
nslookup gmail.googleapis.com
```

### 2. OAuth认证问题
```bash
# 检查token.json文件权限和内容
ls -la token.json
cat token.json | python -m json.tool
```

### 3. 端口访问问题
```bash
# 检查端口是否开放
netstat -tlnp | grep 5000
sudo ufw status
```

这个方案可以完美解决Gmail API在中国无法使用的问题！