"""
Gmail API 验证码获取模块
更稳定、更快速的验证码获取方案
"""
import base64
import json
import re
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

# Gmail API 权限范围
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailAPIFetcher:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        """
        初始化Gmail API客户端
        
        Args:
            credentials_file: OAuth2凭据文件路径
            token_file: 访问令牌文件路径
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        
    def authenticate(self):
        """认证并获取Gmail API服务"""
        creds = None
        
        # 检查是否已有有效的token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # 如果没有有效凭据，进行OAuth流程
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    print('✅ 刷新访问令牌成功')
                except Exception as e:
                    print(f'⚠️ 刷新令牌失败: {e}')
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    print(f'❌ 未找到凭据文件: {self.credentials_file}')
                    print('💡 请从Google Cloud Console下载OAuth2凭据文件')
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
                print('✅ OAuth2认证成功')
            
            # 保存凭据
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        return True
    
    def search_messages(self, query, max_results=10):
        """
        搜索邮件
        
        Args:
            query: 搜索查询字符串
            max_results: 最大结果数
            
        Returns:
            邮件ID列表
        """
        try:
            result = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = result.get('messages', [])
            return [msg['id'] for msg in messages]
        except Exception as e:
            print(f'❌ 搜索邮件失败: {e}')
            return []
    
    def get_message(self, message_id):
        """
        获取邮件详情
        
        Args:
            message_id: 邮件ID
            
        Returns:
            邮件详情字典
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return self.parse_message(message)
        except Exception as e:
            print(f'❌ 获取邮件失败: {e}')
            return None
    
    def parse_message(self, message):
        """解析邮件内容"""
        headers = message['payload'].get('headers', [])
        
        # 提取邮件头信息
        email_data = {
            'id': message['id'],
            'thread_id': message['threadId'],
            'from': '',
            'to': '',
            'subject': '',
            'date': '',
            'body': ''
        }
        
        for header in headers:
            name = header['name'].lower()
            value = header['value']
            
            if name == 'from':
                email_data['from'] = value
            elif name == 'to':
                email_data['to'] = value
            elif name == 'subject':
                email_data['subject'] = value
            elif name == 'date':
                email_data['date'] = value
        
        # 提取邮件正文
        email_data['body'] = self.extract_body(message['payload'])
        
        return email_data
    
    def extract_body(self, payload):
        """提取邮件正文"""
        body = ''
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'text/html':
                    data = part['body']['data']
                    html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    # 简单的HTML标签清理
                    import re
                    clean_body = re.sub(r'<[^>]+>', '', html_body)
                    body += clean_body
        else:
            if payload['mimeType'] in ['text/plain', 'text/html']:
                if 'data' in payload['body']:
                    data = payload['body']['data']
                    decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    if payload['mimeType'] == 'text/html':
                        # 清理HTML标签
                        import re
                        decoded = re.sub(r'<[^>]+>', '', decoded)
                    body += decoded
        
        return body
    
    def extract_verification_code(self, text, target_email=None):
        """从文本中提取验证码"""
        # 如果指定了目标邮箱，检查邮件内容是否包含该邮箱或用户名部分
        if target_email:
            username = target_email.split('@')[0]
            if target_email not in text and username not in text:
                return None
        
        # 验证码模式
        patterns = [
            r'Your ChatGPT code is (\d{6})',  # ChatGPT 特定格式
            r'验证码[：:]\s*(\d{6})',
            r'verification code[：:]\s*(\d{6})',
            r'code[：:]\s*(\d{6})',
            r'(\d{6})\s*is your',
            r'your code is\s*(\d{6})',
            r'代码为\s*(\d{6})',
            r'\b(\d{6})\b',  # 6位数字
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def fetch_verification_code(self, target_email=None, hours_back=1):
        """
        获取验证码
        
        Args:
            target_email: 目标邮箱地址
            hours_back: 搜索多少小时内的邮件
            
        Returns:
            验证码字符串或None
        """
        if not self.service:
            print('❌ Gmail API服务未初始化')
            return None
        
        # 构建搜索查询
        # 搜索来自OpenAI的邮件
        query_parts = [
            'from:openai.com',
            f'newer_than:{hours_back}h'
        ]
        
        if target_email:
            # 添加目标邮箱的用户名部分到搜索
            username = target_email.split('@')[0]
            query_parts.append(f'({target_email} OR {username})')
        
        query = ' '.join(query_parts)
        print(f'🔍 搜索查询: {query}')
        
        # 搜索邮件
        message_ids = self.search_messages(query, max_results=10)
        
        if not message_ids:
            print('⚠️ 未找到来自OpenAI的邮件')
            return None
        
        print(f'📬 找到 {len(message_ids)} 封邮件，开始检查...')
        
        # 检查每封邮件
        for message_id in message_ids:
            email_data = self.get_message(message_id)
            
            if not email_data:
                continue
            
            print(f'📧 检查邮件:')
            print(f'   发件人: {email_data["from"]}')
            print(f'   收件人: {email_data["to"]}')
            print(f'   主题: {email_data["subject"][:60]}...')
            print(f'   时间: {email_data["date"]}')
            
            # 检查是否来自OpenAI
            if 'openai.com' not in email_data['from'].lower():
                print('   ⚠️ 跳过非OpenAI邮件')
                continue
            
            # 完整文本
            full_text = f"{email_data['subject']} {email_data['body']} {email_data['to']}"
            
            # 提取验证码
            code = self.extract_verification_code(full_text, target_email)
            
            if code:
                print(f'✅ 找到验证码: {code}')
                print(f'   邮件主题: {email_data["subject"]}')
                return code
            else:
                print('   ❌ 此邮件中未找到匹配的验证码')
        
        print('❌ 未在邮件中找到验证码')
        return None


def setup_gmail_api():
    """设置Gmail API的说明"""
    print('📋 Gmail API 设置说明:')
    print('=' * 50)
    print('1. 访问 Google Cloud Console: https://console.cloud.google.com/')
    print('2. 创建新项目或选择现有项目')
    print('3. 启用 Gmail API')
    print('4. 创建 OAuth 2.0 凭据 (桌面应用程序)')
    print('5. 下载凭据文件并重命名为 credentials.json')
    print('6. 将 credentials.json 放在当前目录')
    print('7. 运行脚本进行首次认证')
    print('=' * 50)


def test_gmail_api():
    """测试Gmail API"""
    fetcher = GmailAPIFetcher()
    
    if not fetcher.authenticate():
        setup_gmail_api()
        return
    
    # 测试获取验证码
    target_email = 'bnttrr1@frust.de5.net'
    code = fetcher.fetch_verification_code(target_email=target_email)
    
    if code:
        print(f'\n✅ 成功获取验证码: {code}')
    else:
        print('\n❌ 未能获取验证码')


if __name__ == '__main__':
    test_gmail_api()