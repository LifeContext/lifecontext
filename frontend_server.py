"""
LifeContext Frontend 静态文件服务器
提供前端静态文件服务，并代理 API 请求到后端
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path
import urllib.request
import urllib.error
from io import BytesIO

PORT = 3000
BACKEND_URL = "http://localhost:8000"

# 处理 PyInstaller 打包后的路径问题
if getattr(sys, 'frozen', False):
    # 打包后：可执行文件所在目录
    BASE_DIR = Path(sys.executable).parent
else:
    # 开发模式：脚本所在目录
    BASE_DIR = Path(__file__).parent

FRONTEND_DIR = BASE_DIR / "frontend" / "dist"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)
    
    def do_GET(self):
        # 如果是 API 请求，代理到后端
        if self.path.startswith('/api/'):
            self.proxy_request('GET')
        else:
            # 静态文件请求
            super().do_GET()
    
    def do_POST(self):
        # API 请求代理到后端
        if self.path.startswith('/api/'):
            self.proxy_request('POST')
        else:
            self.send_error(405, "Method Not Allowed")
    
    def do_PATCH(self):
        # API 请求代理到后端
        if self.path.startswith('/api/'):
            self.proxy_request('PATCH')
        else:
            self.send_error(405, "Method Not Allowed")
    
    def do_DELETE(self):
        # API 请求代理到后端
        if self.path.startswith('/api/'):
            self.proxy_request('DELETE')
        else:
            self.send_error(405, "Method Not Allowed")
    
    def do_OPTIONS(self):
        # 处理 CORS 预检请求
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def proxy_request(self, method):
        """代理请求到后端服务器"""
        try:
            # 构建完整的后端 URL
            backend_url = f"{BACKEND_URL}{self.path}"
            
            # 读取请求体（如果有）
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # 创建请求
            headers = {}
            if self.headers.get('Content-Type'):
                headers['Content-Type'] = self.headers.get('Content-Type')
            
            req = urllib.request.Request(
                backend_url,
                data=body,
                headers=headers,
                method=method
            )
            
            # 发送请求到后端
            with urllib.request.urlopen(req, timeout=30) as response:
                # 发送响应状态码
                self.send_response(response.status)
                
                # 转发响应头
                for header, value in response.headers.items():
                    if header.lower() not in ['server', 'date']:
                        self.send_header(header, value)
                
                # 添加 CORS 头
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                # 转发响应体
                self.wfile.write(response.read())
                
                print(f"[Proxy] {method} {self.path} -> {response.status}")
                
        except urllib.error.HTTPError as e:
            # HTTP 错误（4xx, 5xx）
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_body = e.read()
            self.wfile.write(error_body)
            print(f"[Proxy Error] {method} {self.path} -> {e.code}")
            
        except urllib.error.URLError as e:
            # 连接错误
            self.send_error(502, f"Bad Gateway: Cannot connect to backend - {e.reason}")
            print(f"[Proxy Error] {method} {self.path} -> Connection failed: {e.reason}")
            
        except Exception as e:
            # 其他错误
            self.send_error(500, f"Internal Server Error: {str(e)}")
            print(f"[Proxy Error] {method} {self.path} -> {str(e)}")
    
    def end_headers(self):
        # 为静态文件添加CORS头
        if not self.path.startswith('/api/'):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def log_message(self, format, *args):
        # 自定义日志格式
        if not self.path.startswith('/api/'):
            print(f"[Frontend] {self.address_string()} - {format % args}")

def main():
    print("=" * 60)
    print("LifeContext Frontend Server")
    print("=" * 60)
    print(f"🔍 工作目录: {BASE_DIR}")
    print(f"📁 前端目录: {FRONTEND_DIR}")
    print(f"📁 目录存在: {FRONTEND_DIR.exists()}")
    
    # 检查前端目录是否存在
    if not FRONTEND_DIR.exists():
        print(f"\n❌ 错误: 找不到前端构建目录")
        print(f"   期望路径: {FRONTEND_DIR}")
        print(f"\n请确保目录结构正确:")
        print(f"   {BASE_DIR}/")
        print(f"   ├── frontend_server.exe")
        print(f"   └── frontend/")
        print(f"       └── dist/  ← 前端构建文件应在此处")
        
        # 列出实际存在的目录
        print(f"\n当前目录内容:")
        try:
            for item in BASE_DIR.iterdir():
                if item.is_dir():
                    print(f"   [目录] {item.name}")
                else:
                    print(f"   [文件] {item.name}")
        except Exception as e:
            print(f"   无法列出目录: {e}")
        
        input("\n按回车键退出...")
        return
    
    print(f"🌐 服务地址: http://localhost:{PORT}")
    print(f"🚀 服务器启动中...")
    print("=" * 60)
    
    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            print(f"✅ Frontend 服务器已启动在端口 {PORT}")
            print("按 Ctrl+C 停止服务器")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except OSError as e:
        if e.errno == 10048:  # Address already in use
            print(f"❌ 端口 {PORT} 已被占用，请检查是否有其他服务在运行")
        else:
            print(f"❌ 错误: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()

