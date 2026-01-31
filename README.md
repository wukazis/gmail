# Gmail API 外网服务器

在外网服务器上部署Gmail API服务，绕过中国防火墙限制，提供稳定的验证码获取服务。

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

## ⚠️ 安全提醒

1. **不要提交敏感文件**: `credentials.json` 和 `token.json` 包含敏感信息，不应提交到公开仓库
2. **设置文件权限**: 上传后设置适当的文件权限
3. **使用HTTPS**: 生产环境建议配置SSL证书
4. **API密钥**: 考虑添加API密钥认证

## 💰 成本估算

- VPS服务器: $5-10/月 (1GB RAM)
- 流量费用: 几乎可忽略
- 总成本: 约 $5-10/月

## 🏗️ 架构

```
中国本地客户端 → 外网服务器 → Gmail API → 返回验证码
     ↓              ↓
  混合获取器    Gmail API服务器
     ↓              ↓
  IMAP备用      OAuth认证
```

## 📖 详细文档

查看 [server_deployment_guide.md](server_deployment_guide.md) 获取完整的部署指南。

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License