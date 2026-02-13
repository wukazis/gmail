# Gmail API 外网服务器

在服务器上部署Gmail API服务，提供稳定的验证码获取服务。

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/wukazis/gmail.git
cd gmail
```

### 2. 准备OAuth文件
- 从Google Cloud Console下载 `credentials.json`
- 在本地完成OAuth认证生成 `token.json`
- 将这两个文件上传到服务器

### 3. 部署服务器
```bash
chmod +x deploy_server.sh
./deploy_server.sh
```

### 4. 启动服务
```bash
# 开发模式
python gmail_api_server.py

# 生产模式
gunicorn -w 4 -b 0.0.0.0:5000 gmail_api_server:app
```

## 📁 文件说明

- `gmail_api_server.py` - Flask API服务器主程序
- `gmail_api_fetcher.py` - Gmail API获取器核心模块
- `requirements_server.txt` - Python依赖包列表
- `deploy_server.sh` - 自动部署脚本
- `server_deployment_guide.md` - 详细部署指南

## 🔗 API接口

### 健康检查
```http
GET /health
```

### 获取验证码
```http
POST /fetch-code
Content-Type: application/json

{
  "target_email": "user@example.com",
  "hours_back": 1
}
```

### 搜索邮件
```http
POST /search-emails
Content-Type: application/json

{
  "query": "from:openai.com newer_than:1h",
  "max_results": 10
}
```

### 测试连接
```http
GET /test-connection
```


下面是各参数的含义（用在 /fetch-code 和 /search-emails）：


✅ /fetch-code

{
  "target_email": "user@example.com",
  "hours_back": 1
}

• target_email
要查验证码的目标收件人邮箱（邮件发送到谁）
• hours_back
回查的时间范围（单位：小时）
例如 1 = 只查最近 1 小时的邮件
如果没找到验证码，可以改成 6、12

✅ /search-emails

{
  "query": "from:openai.com newer_than:1h",
  "max_results": 10
}

• query
Gmail 搜索语法（和 Gmail 网页搜索一样）
常用示例：  • from:openai.com newer_than:1h → 最近 1 小时来自 openai.com (http://openai.com/)
  • to:user@example.com newer_than:12h → 最近 12 小时发给 user@example.com
  • subject:验证码 newer_than:6h → 主题含“验证码”

• max_results
最多返回多少封邮件 ID（默认 10）

## 🏗️ 架构

```
   本地客户端 → 外网服务器 → Gmail API → 返回验证码
     ↓              ↓
  混合获取器    Gmail API服务器
     ↓              ↓
  IMAP备用      OAuth认证
```

## 📖 详细文档

查看 [server_deployment_guide.md](server_deployment_guide.md) 获取完整的部署指南。



## 📄 许可证

MIT License
