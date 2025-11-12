"""
邮箱工具 - 支持从 Gmail/Outlook 获取邮件信息
"""

from typing import Dict, Any, List, Optional
from tools.base import BaseTool
from utils.helpers import get_logger
import os
from datetime import datetime, timedelta
import base64
import json

logger = get_logger(__name__)

# Gmail API 相关导入
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import httplib2
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    logger.warning("Google API libraries not installed. Gmail integration unavailable.")


class EmailTool(BaseTool):
    """邮箱工具 - 获取邮件信息"""
    
    # Gmail API 作用域
    GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self):
        super().__init__(
            name="email_reader",
            description="从用户的邮箱(Gmail/Outlook)中读取和搜索邮件。当用户询问邮件、邮箱、收件箱、email相关问题时使用此工具。可以获取最新邮件、搜索特定邮件、查看未读邮件等。",
            is_async=False
        )
        # 配置项
        self.email_provider = os.getenv("EMAIL_PROVIDER", "gmail")
        self.max_results = 10
        # Token 文件路径（OAuth 授权后自动生成）
        self.token_path = "./data/gmail_token.json"
        self._gmail_service = None
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "操作类型",
                    "enum": ["search", "get_latest", "get_by_date", "get_unread"],
                    "default": "get_latest"
                },
                "query": {
                    "type": "string",
                    "description": "搜索关键词(用于 search 操作)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大返回邮件数量",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50
                },
                "start_date": {
                    "type": "string",
                    "description": "起始日期(格式: YYYY-MM-DD,用于 get_by_date)"
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期(格式: YYYY-MM-DD,用于 get_by_date)"
                }
            },
            "required": ["action"]
        }
    
    def execute(
        self, 
        action: str = "get_latest",
        query: Optional[str] = None,
        max_results: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        执行邮箱操作
        
        Args:
            action: 操作类型
            query: 搜索关键词
            max_results: 最大结果数
            start_date: 起始日期
            end_date: 结束日期
        
        Returns:
            邮件信息列表
        """
        try:
            if self.email_provider == "gmail":
                return self._get_gmail_data(action, query, max_results, start_date, end_date)
            elif self.email_provider == "outlook":
                return self._get_outlook_data(action, query, max_results, start_date, end_date)
            else:
                return {
                    "error": f"Unsupported email provider: {self.email_provider}",
                    "message": "请在环境变量中设置 EMAIL_PROVIDER 为 gmail 或 outlook"
                }
                
        except Exception as e:
            logger.exception(f"Error in EmailTool.execute: {e}")
            return {
                "error": str(e),
                "message": "获取邮件信息失败"
            }
    
    def _get_gmail_data(
        self, 
        action: str, 
        query: Optional[str],
        max_results: int,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> Dict[str, Any]:
        """
        从 Gmail 获取数据
        使用 Google Gmail API
        """
        if not GMAIL_AVAILABLE:
            return {
                "provider": "gmail",
                "status": "error",
                "message": "Gmail API 库未安装。请运行: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            }
        
        try:
            # 获取 Gmail 服务
            service = self._get_gmail_service()
            if not service:
                # 检查是否有 token 文件
                if not os.path.exists(self.token_path):
                    return {
                        "provider": "gmail",
                        "status": "not_authorized",
                        "message": "Gmail 尚未授权。请先完成 Google 账号授权。",
                        "authorization_url": "http://localhost:8000/api/oauth/google/authorize",
                        "instructions": "请在浏览器中打开上述链接，登录 Google 账号并授权访问 Gmail。授权完成后，即可查询邮件。"
                    }
                else:
                    return {
                        "provider": "gmail",
                        "status": "authorization_failed",
                        "message": "Gmail 授权已过期或无效。",
                        "authorization_url": "http://localhost:8000/api/oauth/google/authorize",
                        "instructions": "请重新授权：在浏览器中打开上述链接。"
                    }
            
            # 构建查询条件
            gmail_query = self._build_gmail_query(action, query, start_date, end_date)
            
            # 获取邮件列表
            results = service.users().messages().list(
                userId='me',
                q=gmail_query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return {
                    "provider": "gmail",
                    "action": action,
                    "status": "success",
                    "count": 0,
                    "emails": [],
                    "message": "未找到符合条件的邮件"
                }
            
            # 获取邮件详情
            emails = []
            for msg in messages[:max_results]:
                try:
                    email_data = self._get_email_details(service, msg['id'])
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.error(f"获取邮件详情失败 (ID: {msg['id']}): {e}")
                    continue
            
            return {
                "provider": "gmail",
                "action": action,
                "status": "success",
                "count": len(emails),
                "emails": emails,
                "query": gmail_query
            }
            
        except Exception as e:
            logger.exception(f"Gmail API 调用失败: {e}")
            return {
                "provider": "gmail",
                "status": "error",
                "message": f"获取邮件失败: {str(e)}"
            }
    
    def _get_gmail_service(self):
        """获取 Gmail API 服务实例"""
        if self._gmail_service:
            return self._gmail_service
        
        if not GMAIL_AVAILABLE:
            return None
        
        creds = None
        
        # 尝试从 token 文件加载凭据
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'r') as token:
                    creds_data = json.load(token)
                    creds = Credentials.from_authorized_user_info(creds_data, self.GMAIL_SCOPES)
            except Exception as e:
                logger.error(f"加载 token 失败: {e}")
        
        # 如果没有有效凭据，需要进行授权
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # 保存刷新后的凭据
                    with open(self.token_path, 'w') as token:
                        token.write(creds.to_json())
                except Exception as e:
                    logger.error(f"刷新 token 失败: {e}")
                    return None
            else:
                # 需要新的授权流程
                logger.warning("需要 OAuth 授权。请使用 Gmail 授权端点。")
                return None
        
        try:
            # 配置代理
            http_proxy = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
            if http_proxy:
                logger.info(f"使用代理: {http_proxy}")
                # 创建带代理的授权 http 对象
                import httplib2
                import socks
                from google_auth_httplib2 import AuthorizedHttp
                
                # 解析代理 URL
                if http_proxy.startswith('http://') or http_proxy.startswith('https://'):
                    proxy_url = http_proxy.replace('http://', '').replace('https://', '')
                    if ':' in proxy_url:
                        proxy_host, proxy_port = proxy_url.split(':')
                        http = httplib2.Http(
                            proxy_info=httplib2.ProxyInfo(
                                socks.PROXY_TYPE_HTTP,
                                proxy_host,
                                int(proxy_port)
                            ),
                            timeout=30
                        )
                    else:
                        http = httplib2.Http(timeout=30)
                else:
                    http = httplib2.Http(timeout=30)
                
                # 使用 AuthorizedHttp 包装，而不是同时传递 http 和 credentials
                authorized_http = AuthorizedHttp(creds, http=http)
                self._gmail_service = build('gmail', 'v1', http=authorized_http)
            else:
                self._gmail_service = build('gmail', 'v1', credentials=creds)
            
            return self._gmail_service
        except Exception as e:
            logger.exception(f"创建 Gmail 服务失败: {e}")
            return None
    
    def _build_gmail_query(
        self,
        action: str,
        query: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> str:
        """构建 Gmail API 查询字符串"""
        query_parts = []
        
        # 根据 action 类型添加条件
        if action == "get_unread":
            query_parts.append("is:unread")
        
        # 添加日期范围
        if start_date:
            query_parts.append(f"after:{start_date}")
        if end_date:
            query_parts.append(f"before:{end_date}")
        
        # 添加搜索关键词
        if query:
            query_parts.append(query)
        
        return " ".join(query_parts) if query_parts else ""
    
    def _get_email_details(self, service, msg_id: str) -> Optional[Dict[str, Any]]:
        """获取单封邮件的详细信息"""
        try:
            msg = service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            headers = msg['payload'].get('headers', [])
            
            # 提取邮件头信息
            subject = ""
            sender = ""
            date = ""
            to = ""
            
            for header in headers:
                name = header['name'].lower()
                if name == 'subject':
                    subject = header['value']
                elif name == 'from':
                    sender = header['value']
                elif name == 'date':
                    date = header['value']
                elif name == 'to':
                    to = header['value']
            
            # 提取邮件正文
            snippet = msg.get('snippet', '')
            
            # 判断是否未读
            labels = msg.get('labelIds', [])
            is_unread = 'UNREAD' in labels
            
            return {
                "id": msg_id,
                "subject": subject,
                "from": sender,
                "to": to,
                "date": date,
                "snippet": snippet,
                "is_unread": is_unread,
                "labels": labels
            }
            
        except Exception as e:
            logger.error(f"获取邮件详情失败 (ID: {msg_id}): {e}")
            return None
    
    def _get_outlook_data(
        self, 
        action: str, 
        query: Optional[str],
        max_results: int,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> Dict[str, Any]:
        """
        从 Outlook 获取数据
        需要配置 Microsoft Graph API 凭据和 MCP 服务器
        """
        # TODO: 实现 Microsoft Graph API 调用或通过 MCP 服务器
        logger.info(f"Outlook action: {action}, query: {query}")
        
        return {
            "provider": "outlook",
            "action": action,
            "status": "not_implemented",
            "message": "Outlook 集成待实现。需要配置 Microsoft Graph API 凭据。",
            "hint": "请参考 https://learn.microsoft.com/en-us/graph/api/user-list-messages"
        }


def get_email_tools() -> list:
    """获取所有邮箱工具实例"""
    return [EmailTool()]
