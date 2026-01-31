"""
Gmail API 服务器版本
部署在外网服务器上，通过HTTP API提供验证码获取服务
"""
from flask import Flask, request, jsonify
import os
import sys
from gmail_api_fetcher import GmailAPIFetcher
import logging

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局Gmail API获取器
gmail_fetcher = None

def init_gmail_api():
    """初始化Gmail API"""
    global gmail_fetcher
    try:
        gmail_fetcher = GmailAPIFetcher()
        if gmail_fetcher.authenticate():
            logger.info("Gmail API初始化成功")
            return True
        else:
            logger.error("Gmail API认证失败")
            return False
    except Exception as e:
        logger.error(f"Gmail API初始化异常: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'service': 'Gmail API Server',
        'gmail_api_ready': gmail_fetcher is not None
    })

@app.route('/fetch-code', methods=['POST'])
def fetch_verification_code():
    """获取验证码API"""
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        target_email = data.get('target_email')
        hours_back = data.get('hours_back', 1)
        
        if not target_email:
            return jsonify({
                'success': False,
                'error': '缺少target_email参数'
            }), 400
        
        logger.info(f"收到验证码获取请求: {target_email}")
        
        # 检查Gmail API是否可用
        if not gmail_fetcher:
            return jsonify({
                'success': False,
                'error': 'Gmail API未初始化'
            }), 500
        
        # 获取验证码
        code = gmail_fetcher.fetch_verification_code(
            target_email=target_email,
            hours_back=hours_back
        )
        
        if code:
            logger.info(f"成功获取验证码: {code} (目标邮箱: {target_email})")
            return jsonify({
                'success': True,
                'code': code,
                'target_email': target_email
            })
        else:
            logger.warning(f"未找到验证码 (目标邮箱: {target_email})")
            return jsonify({
                'success': False,
                'error': '未找到验证码'
            })
    
    except Exception as e:
        logger.error(f"获取验证码异常: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/search-emails', methods=['POST'])
def search_emails():
    """搜索邮件API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        query = data.get('query', 'from:openai.com newer_than:1h')
        max_results = data.get('max_results', 10)
        
        logger.info(f"收到邮件搜索请求: {query}")
        
        if not gmail_fetcher:
            return jsonify({
                'success': False,
                'error': 'Gmail API未初始化'
            }), 500
        
        # 搜索邮件
        message_ids = gmail_fetcher.search_messages(query, max_results)
        
        # 获取邮件详情
        emails = []
        for msg_id in message_ids[:5]:  # 最多返回5封邮件详情
            email_data = gmail_fetcher.get_message(msg_id)
            if email_data:
                emails.append({
                    'id': email_data['id'],
                    'from': email_data['from'],
                    'to': email_data['to'],
                    'subject': email_data['subject'],
                    'date': email_data['date'],
                    'body_preview': email_data['body'][:200] + '...' if len(email_data['body']) > 200 else email_data['body']
                })
        
        logger.info(f"搜索到 {len(message_ids)} 封邮件，返回 {len(emails)} 封详情")
        
        return jsonify({
            'success': True,
            'total_found': len(message_ids),
            'emails': emails
        })
    
    except Exception as e:
        logger.error(f"搜索邮件异常: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test-connection', methods=['GET'])
def test_connection():
    """测试Gmail API连接"""
    try:
        if not gmail_fetcher:
            return jsonify({
                'success': False,
                'error': 'Gmail API未初始化'
            })
        
        # 尝试获取用户信息
        if gmail_fetcher.service:
            profile = gmail_fetcher.service.users().getProfile(userId='me').execute()
            return jsonify({
                'success': True,
                'email': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal'),
                'threads_total': profile.get('threadsTotal')
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Gmail服务未创建'
            })
    
    except Exception as e:
        logger.error(f"测试连接异常: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    # 检查必要文件
    if not os.path.exists('credentials.json'):
        print("❌ 缺少 credentials.json 文件")
        print("请将OAuth2凭据文件上传到服务器")
        sys.exit(1)
    
    if not os.path.exists('token.json'):
        print("❌ 缺少 token.json 文件")
        print("请先在本地完成OAuth认证，然后上传token.json到服务器")
        sys.exit(1)
    
    # 初始化Gmail API
    if not init_gmail_api():
        print("❌ Gmail API初始化失败")
        sys.exit(1)
    
    # 启动服务器
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 Gmail API服务器启动")
    print(f"   地址: http://{host}:{port}")
    print(f"   健康检查: http://{host}:{port}/health")
    print(f"   获取验证码: POST http://{host}:{port}/fetch-code")
    
    app.run(host=host, port=port, debug=False)