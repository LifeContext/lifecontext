"""
OAuth 授权路由 - 处理 Google/Microsoft OAuth 流程
"""

from flask import Blueprint, request, redirect, jsonify, session
from utils.helpers import get_logger
import os
import json

logger = get_logger(__name__)

oauth_bp = Blueprint('oauth', __name__, url_prefix='/api/oauth')

# Google OAuth 相关导入
try:
    from google_auth_oauthlib.flow import Flow
    from google.oauth2.credentials import Credentials
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False
    logger.warning("Google auth libraries not installed")


@oauth_bp.route('/google/authorize', methods=['GET'])
def google_authorize():
    """
    启动 Google OAuth 授权流程
    """
    if not GOOGLE_AUTH_AVAILABLE:
        return jsonify({
            "error": "Google 认证库未安装",
            "message": "请安装: pip install google-auth-oauthlib"
        }), 500
    
    try:
        # Gmail API 作用域
        SCOPES = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/calendar.readonly',
            'https://www.googleapis.com/auth/documents.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        # 创建 OAuth 流程
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/oauth/google/callback")
        
        if not client_id or not client_secret:
            return jsonify({
                "error": "Google OAuth 未配置",
                "message": "请在 .env 文件中配置 GOOGLE_CLIENT_ID 和 GOOGLE_CLIENT_SECRET"
            }), 500
        
        # 构建客户端配置
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
        # 生成授权 URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # 保存 state 到 session
        session['oauth_state'] = state
        
        # 重定向到 Google 授权页面
        return redirect(authorization_url)
        
    except Exception as e:
        logger.exception(f"Google 授权失败: {e}")
        return jsonify({
            "error": "授权失败",
            "message": str(e)
        }), 500


@oauth_bp.route('/google/callback', methods=['GET'])
def google_callback():
    """
    处理 Google OAuth 回调
    """
    if not GOOGLE_AUTH_AVAILABLE:
        return "Google 认证库未安装", 500
    
    try:
        # 获取授权码
        code = request.args.get('code')
        state = request.args.get('state')
        
        if not code:
            error = request.args.get('error')
            return f"授权失败: {error}", 400
        
        # 验证 state
        if state != session.get('oauth_state'):
            return "State 验证失败", 400
        
        # 创建 OAuth 流程
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/oauth/google/callback")
        
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        }
        
        SCOPES = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/calendar.readonly',
            'https://www.googleapis.com/auth/documents.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri,
            state=state
        )
        
        # 使用授权码获取令牌
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # 保存凭据到文件
        token_path = "./data/gmail_token.json"
        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        
        creds_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        with open(token_path, 'w') as token_file:
            json.dump(creds_data, token_file)
        
        logger.info(f"Google OAuth 授权成功，token 已保存到 {token_path}")
        
        # 返回成功页面
        return """
        <html>
            <head>
                <title>授权成功</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }
                    .container {
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                        text-align: center;
                    }
                    h1 { color: #4CAF50; margin-bottom: 20px; }
                    p { color: #666; line-height: 1.6; }
                    .success-icon {
                        font-size: 64px;
                        margin-bottom: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success-icon">✅</div>
                    <h1>授权成功！</h1>
                    <p>Google 账号已成功授权</p>
                    <p>现在可以关闭此页面，返回应用使用邮件/日历/文档功能了</p>
                </div>
            </body>
        </html>
        """
        
    except Exception as e:
        logger.exception(f"Google OAuth 回调处理失败: {e}")
        return f"授权回调处理失败: {str(e)}", 500


@oauth_bp.route('/google/status', methods=['GET'])
def google_status():
    """
    检查 Google OAuth 授权状态
    """
    token_path = "./data/gmail_token.json"
    
    if os.path.exists(token_path):
        try:
            with open(token_path, 'r') as f:
                creds_data = json.load(f)
            
            return jsonify({
                "authorized": True,
                "scopes": creds_data.get('scopes', []),
                "message": "已授权"
            })
        except Exception as e:
            return jsonify({
                "authorized": False,
                "message": f"Token 文件损坏: {str(e)}"
            })
    else:
        return jsonify({
            "authorized": False,
            "message": "未授权，请先访问 /api/oauth/google/authorize 进行授权"
        })


@oauth_bp.route('/google/revoke', methods=['POST'])
def google_revoke():
    """
    撤销 Google OAuth 授权
    """
    token_path = "./data/gmail_token.json"
    
    if os.path.exists(token_path):
        try:
            os.remove(token_path)
            logger.info("Google OAuth token 已删除")
            return jsonify({
                "success": True,
                "message": "授权已撤销"
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"删除 token 失败: {str(e)}"
            }), 500
    else:
        return jsonify({
            "success": False,
            "message": "未找到授权信息"
        }), 404
