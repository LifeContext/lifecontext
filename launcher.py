"""
LifeContext 启动器
- 检查配置
- 启动所有服务
- 提供配置界面
"""

import os
import sys
import subprocess
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
import webbrowser
from threading import Thread
import signal

class LifeContextLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LifeContext 启动器")
        self.root.geometry("800x750")
        self.root.minsize(700, 600)  # 最小尺寸
        self.root.resizable(True, True)  # 允许调整大小
        
        # 进程管理
        self.processes = []
        self.backend_process = None
        self.frontend_process = None
        
        # 路径配置
        # 处理 PyInstaller 打包后的路径问题
        if getattr(sys, 'frozen', False):
            # 打包后：可执行文件所在目录
            self.base_dir = Path(sys.executable).parent
        else:
            # 开发模式：脚本所在目录
            self.base_dir = Path(__file__).parent
        
        self.backend_dir = self.base_dir / "backend"
        self.frontend_dir = self.base_dir / "frontend"
        self.extension_dir = self.base_dir / "Extension"
        self.env_file = self.backend_dir / ".env"
        
        # 确保必要的目录存在
        self.backend_dir.mkdir(parents=True, exist_ok=True)
        (self.backend_dir / "data").mkdir(parents=True, exist_ok=True)
        
        # 配置
        self.config = self.load_config()
        
        # 设置窗口关闭处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 创建界面
        self.create_ui()
        
        # 启动检查
        self.root.after(500, self.check_and_start)
    
    def load_config(self):
        """从.env文件加载配置"""
        config = {
            'LLM_API_KEY': '',
            'LLM_BASE_URL': 'https://api.openai.com/v1',
            'LLM_MODEL': 'gpt-4o-mini',
            'EMBEDDING_API_KEY': '',
            'EMBEDDING_BASE_URL': 'https://api.openai.com/v1',
            'EMBEDDING_MODEL': 'text-embedding-3-small',
            'PROMPT_LANGUAGE': 'zh'
        }
        
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key in config:
                            config[key] = value
        
        return config
    
    def save_config(self):
        """保存配置到.env文件"""
        try:
            self.backend_dir.mkdir(exist_ok=True)
            
            self.log(f"保存配置到: {self.env_file}")
            
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write("# LifeContext 配置文件\n\n")
                f.write("# LLM API 配置（用于内容分析和智能对话）\n")
                f.write(f'LLM_API_KEY = "{self.config["LLM_API_KEY"]}"\n')
                f.write(f'LLM_BASE_URL = "{self.config["LLM_BASE_URL"]}"\n')
                f.write(f'LLM_MODEL = "{self.config["LLM_MODEL"]}"\n\n')
                
                f.write("# 向量化 Embedding API 配置（用于向量数据库）\n")
                f.write(f'EMBEDDING_API_KEY = "{self.config["EMBEDDING_API_KEY"]}"\n')
                f.write(f'EMBEDDING_BASE_URL = "{self.config["EMBEDDING_BASE_URL"]}"\n')
                f.write(f'EMBEDDING_MODEL = "{self.config["EMBEDDING_MODEL"]}"\n\n')
                
                f.write("# 提示词语言\n")
                f.write(f'PROMPT_LANGUAGE = "{self.config["PROMPT_LANGUAGE"]}"\n')
            
            self.log(f"配置文件已写入，文件大小: {self.env_file.stat().st_size} 字节")
            return True
        except Exception as e:
            self.log(f"保存配置失败: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return False
    
    def create_ui(self):
        """创建用户界面"""
        # 标题
        title_frame = tk.Frame(self.root, bg="#4A90E2", height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🧠 LifeContext",
            font=("Arial", 24, "bold"),
            bg="#4A90E2",
            fg="white"
        )
        title_label.pack(pady=20)
        
        # 底部按钮（先创建，确保在底部）
        button_frame = tk.Frame(self.root, padx=20, pady=10, bg="#F5F5F5")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 主内容区域
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook（标签页）
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 配置标签页
        self.config_frame = self.create_config_tab()
        self.notebook.add(self.config_frame, text="⚙️ 配置")
        
        # 日志标签页
        self.log_frame = self.create_log_tab()
        self.notebook.add(self.log_frame, text="📋 日志")
        
        self.start_button = tk.Button(
            button_frame,
            text="▶️ 启动服务",
            command=self.start_services,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            width=15
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(
            button_frame,
            text="⏹️ 停止服务",
            command=self.stop_services,
            bg="#F44336",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            width=15,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.open_browser_button = tk.Button(
            button_frame,
            text="🌐 打开主页",
            command=lambda: webbrowser.open("http://localhost:8000"),
            bg="#2196F3",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            width=15,
            state=tk.DISABLED
        )
        self.open_browser_button.pack(side=tk.LEFT, padx=5)
        
        # 状态标签
        self.status_label = tk.Label(
            button_frame,
            text="● 未启动",
            font=("Arial", 10),
            fg="gray"
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)
    
    def create_config_tab(self):
        """创建配置标签页"""
        # 创建主框架和滚动条
        main_frame = tk.Frame(self.notebook)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建 Canvas 和滚动条
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 配置标签页内容
        frame = scrollable_frame
        frame.configure(padx=20, pady=20)
        
        # LLM 配置
        llm_label = tk.Label(frame, text="LLM 配置", font=("Arial", 14, "bold"))
        llm_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        tk.Label(frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.llm_key_entry = tk.Entry(frame, width=50, show="*")
        self.llm_key_entry.insert(0, self.config['LLM_API_KEY'])
        self.llm_key_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        tk.Label(frame, text="Base URL:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.llm_url_entry = tk.Entry(frame, width=50)
        self.llm_url_entry.insert(0, self.config['LLM_BASE_URL'])
        self.llm_url_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        tk.Label(frame, text="Model:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.llm_model_entry = tk.Entry(frame, width=50)
        self.llm_model_entry.insert(0, self.config['LLM_MODEL'])
        self.llm_model_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # 分隔线
        ttk.Separator(frame, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=20)
        
        # Embedding 配置
        emb_label = tk.Label(frame, text="Embedding 配置", font=("Arial", 14, "bold"))
        emb_label.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        tk.Label(frame, text="API Key:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.emb_key_entry = tk.Entry(frame, width=50, show="*")
        self.emb_key_entry.insert(0, self.config['EMBEDDING_API_KEY'])
        self.emb_key_entry.grid(row=6, column=1, sticky=tk.W, pady=5)
        
        tk.Label(frame, text="Base URL:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.emb_url_entry = tk.Entry(frame, width=50)
        self.emb_url_entry.insert(0, self.config['EMBEDDING_BASE_URL'])
        self.emb_url_entry.grid(row=7, column=1, sticky=tk.W, pady=5)
        
        tk.Label(frame, text="Model:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.emb_model_entry = tk.Entry(frame, width=50)
        self.emb_model_entry.insert(0, self.config['EMBEDDING_MODEL'])
        self.emb_model_entry.grid(row=8, column=1, sticky=tk.W, pady=5)
        
        # 分隔线
        ttk.Separator(frame, orient='horizontal').grid(row=9, column=0, columnspan=2, sticky=tk.EW, pady=20)
        
        # 语言配置
        lang_label = tk.Label(frame, text="提示词语言", font=("Arial", 14, "bold"))
        lang_label.grid(row=10, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        tk.Label(frame, text="语言:").grid(row=11, column=0, sticky=tk.W, pady=5)
        self.lang_var = tk.StringVar(value=self.config['PROMPT_LANGUAGE'])
        lang_frame = tk.Frame(frame)
        lang_frame.grid(row=11, column=1, sticky=tk.W, pady=5)
        tk.Radiobutton(lang_frame, text="中文", variable=self.lang_var, value="zh").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(lang_frame, text="English", variable=self.lang_var, value="en").pack(side=tk.LEFT, padx=5)
        
        # 保存按钮
        save_button = tk.Button(
            frame,
            text="💾 保存配置",
            command=self.save_config_from_ui,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11, "bold")
        )
        save_button.grid(row=12, column=0, columnspan=2, pady=20)
        
        # 绑定鼠标滚轮事件
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 更新滚动区域
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        return main_frame
    
    def create_log_tab(self):
        """创建日志标签页"""
        frame = tk.Frame(self.notebook, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            frame,
            width=80,
            height=25,
            font=("Consolas", 9),
            bg="#1E1E1E",
            fg="#D4D4D4"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        return frame
    
    def log(self, message, level="INFO"):
        """添加日志"""
        if level == "ERROR":
            prefix = "❌"
        elif level == "WARNING":
            prefix = "⚠️"
        elif level == "SUCCESS":
            prefix = "✅"
        else:
            prefix = "ℹ️"
        
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {prefix} {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def save_config_from_ui(self):
        """从UI保存配置"""
        self.log("开始保存配置...")
        
        # 更新配置
        self.config['LLM_API_KEY'] = self.llm_key_entry.get().strip()
        self.config['LLM_BASE_URL'] = self.llm_url_entry.get().strip()
        self.config['LLM_MODEL'] = self.llm_model_entry.get().strip()
        self.config['EMBEDDING_API_KEY'] = self.emb_key_entry.get().strip()
        self.config['EMBEDDING_BASE_URL'] = self.emb_url_entry.get().strip()
        self.config['EMBEDDING_MODEL'] = self.emb_model_entry.get().strip()
        self.config['PROMPT_LANGUAGE'] = self.lang_var.get()
        
        self.log(f"工作目录: {self.base_dir}")
        self.log(f"Backend 目录: {self.backend_dir}")
        self.log(f"配置文件路径: {self.env_file}")
        
        # 保存配置
        if self.save_config():
            messagebox.showinfo("成功", f"配置已保存到:\n{self.env_file}")
            self.log("✅ 配置已保存")
        else:
            messagebox.showerror("错误", "配置保存失败！\n请查看日志获取详细信息。")
            self.log("❌ 配置保存失败")
    
    def check_and_start(self):
        """检查配置并启动"""
        # 显示路径信息
        self.log("=" * 60)
        self.log("LifeContext 启动器")
        self.log("=" * 60)
        self.log(f"工作目录: {self.base_dir}")
        self.log(f"Backend 目录: {self.backend_dir}")
        self.log(f"Frontend 目录: {self.frontend_dir}")
        self.log(f"Extension 目录: {self.extension_dir}")
        self.log(f"配置文件: {self.env_file}")
        self.log(f"配置文件存在: {self.env_file.exists()}")
        self.log("=" * 60)
        
        # 检查配置
        if not self.config['LLM_API_KEY'] or not self.config['EMBEDDING_API_KEY']:
            self.log("⚠️ 检测到配置未完成，请先配置 API Key")
            self.notebook.select(0)  # 切换到配置标签页
            messagebox.showwarning(
                "配置提醒",
                "首次使用需要配置 LLM 和 Embedding API Key。\n\n"
                "请在「配置」标签页中填写相关信息。"
            )
        else:
            self.log("✅ 配置检查通过")
            # 询问是否立即启动
            if messagebox.askyesno("启动确认", "配置已就绪，是否立即启动服务？"):
                self.start_services()
    
    def start_services(self):
        """启动所有服务"""
        self.log("🚀 开始启动服务...")
        self.start_button.config(state=tk.DISABLED)
        self.status_label.config(text="● 启动中...", fg="orange")
        
        # 在新线程中启动服务，避免阻塞UI
        Thread(target=self._start_services_thread, daemon=True).start()
    
    def _start_services_thread(self):
        """启动服务线程"""
        try:
            # 1. 启动 Backend
            self.log("📦 启动 Backend 服务...")
            backend_exe = self.backend_dir / "LifeContextBackend.exe"
            if backend_exe.exists():
                creationflags = 0
                preexec_fn = None
                if sys.platform == 'win32':
                    creationflags = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
                else:
                    preexec_fn = os.setsid
                self.backend_process = subprocess.Popen(
                    [str(backend_exe)],
                    cwd=str(self.backend_dir),
                    creationflags=creationflags,
                    preexec_fn=preexec_fn
                )
                self.processes.append(self.backend_process)
                self.log("✅ Backend 服务已启动 (端口 8000)")
                time.sleep(3)
            else:
                self.log(f"❌ 找不到 Backend 可执行文件: {backend_exe}")
                self.log("   使用开发模式启动...")
                # 开发模式：直接运行 Python
                creationflags = 0
                preexec_fn = None
                if sys.platform == 'win32':
                    creationflags = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
                else:
                    preexec_fn = os.setsid
                self.backend_process = subprocess.Popen(
                    [sys.executable, "app.py"],
                    cwd=str(self.backend_dir),
                    creationflags=creationflags,
                    preexec_fn=preexec_fn
                )
                self.processes.append(self.backend_process)
                self.log("✅ Backend 服务已启动（开发模式）")
                time.sleep(3)
            
            # 2. Extension 插件依赖浏览器直连，跳过独立服务
            self.log("ℹ️ 插件采用直连模式，无需单独的 Extension Server")
            
            # 3. Frontend 静态文件由 Backend 代理提供，无需单独启动
            self.log("ℹ️ Frontend 静态文件由 Backend 代理提供（端口 8000）")
            
            time.sleep(2)
            
            # 更新UI状态
            self.root.after(0, self._update_ui_started)
            
            self.log("=" * 60)
            self.log("🎉 所有服务启动完成！")
            self.log("")
            self.log("📝 服务地址:")
            self.log("   • Backend:   http://localhost:8000")
            self.log("   • Frontend:  http://localhost:8000 (代理)")
            self.log("")
            self.log("💡 提示:")
            self.log("   1. 点击「打开主页」访问 LifeContext")
            self.log("   2. 在浏览器中安装插件: Extension/extension")
            self.log("=" * 60)
            
            # 自动打开浏览器
            time.sleep(2)
            webbrowser.open("http://localhost:8000")
            
        except Exception as e:
            self.log(f"❌ 启动服务时出错: {e}")
            self.root.after(0, self._update_ui_error)
    
    def _update_ui_started(self):
        """更新UI为已启动状态"""
        self.stop_button.config(state=tk.NORMAL)
        self.open_browser_button.config(state=tk.NORMAL)
        self.status_label.config(text="● 运行中", fg="green")
    
    def _update_ui_error(self):
        """更新UI为错误状态"""
        self.start_button.config(state=tk.NORMAL)
        self.status_label.config(text="● 启动失败", fg="red")
    
    def stop_services(self):
        """停止所有服务"""
        self.log("🛑 正在停止服务...")
        
        for process in self.processes:
            self._terminate_process(process)
        
        self.processes.clear()
        self.backend_process = None
        self.frontend_process = None
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.open_browser_button.config(state=tk.DISABLED)
        self.status_label.config(text="● 已停止", fg="gray")
        self.log("✅ 所有服务已停止")

    def _terminate_process(self, process):
        """终止子进程（包含其子进程）"""
        if process is None:
            return
        try:
            if sys.platform == 'win32':
                # 使用 taskkill 终止整个进程树
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
            self.log(f"   • 已终止进程 PID={process.pid}")
        except Exception as e:
            self.log(f"   • 终止进程 PID={process.pid} 失败: {e}", "WARNING")
    
    def on_closing(self):
        """窗口关闭处理"""
        if self.processes:
            if messagebox.askokcancel("退出确认", "服务正在运行，确定要退出吗？\n\n退出后所有服务将被停止。"):
                self.stop_services()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """运行启动器"""
        self.root.mainloop()


if __name__ == "__main__":
    launcher = LifeContextLauncher()
    launcher.run()

