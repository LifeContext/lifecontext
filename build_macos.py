"""
LifeContext macOS 构建脚本
构建 LifeContext.app 并打包为 DMG
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import time

class MacOSBuilder:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.build_dir = self.base_dir / "build_macos"
        self.dist_dir = self.base_dir / "dist_macos"
        self.output_dir = self.base_dir / "LifeContext_Output"
        self.app_name = "LifeContext.app"
        self.dmg_name = "LifeContext.dmg"
        
    def log(self, message, level="INFO"):
        """输出日志"""
        symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
        print(f"{symbols.get(level, 'ℹ️')} {message}")
    
    def run_command(self, command, cwd=None, shell=False):
        """运行命令并处理错误"""
        try:
            subprocess.run(
                command,
                cwd=str(cwd) if cwd else str(self.base_dir),
                check=True,
                shell=shell,
                capture_output=False
            )
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"命令执行失败: {e}", "ERROR")
            return False
    
    def clean(self):
        """清理旧的构建文件"""
        self.log("清理旧的构建文件...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir, self.output_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                self.log(f"已删除: {dir_path}")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return True
    
    def build_backend(self):
        """构建 Backend 可执行文件"""
        self.log("开始构建 Backend...")
        
        backend_dir = self.base_dir / "backend"
        spec_file = backend_dir / "build.spec"
        
        if not spec_file.exists():
            self.log("找不到 build.spec 文件", "ERROR")
            return False
        
        # 使用 PyInstaller 构建
        cmd = [
            sys.executable, "-m", "PyInstaller",
            str(spec_file),
            "--distpath", str(self.dist_dir / "backend_dist"),
            "--workpath", str(self.build_dir / "backend_build")
        ]
        
        if self.run_command(cmd, cwd=backend_dir):
            self.log("Backend 构建完成", "SUCCESS")
            return True
        return False
    
    def build_frontend(self):
        """构建 Frontend"""
        self.log("开始构建 Frontend...")
        
        frontend_dir = self.base_dir / "frontend"
        
        # 检查 node_modules
        if not (frontend_dir / "node_modules").exists():
            self.log("安装 Frontend 依赖...")
            if not self.run_command(["npm", "install"], cwd=frontend_dir, shell=True):
                return False
        
        # 构建前端
        self.log("正在构建前端...")
        if self.run_command(["npm", "run", "build"], cwd=frontend_dir, shell=True):
            self.log("Frontend 构建完成", "SUCCESS")
            return True
        return False
    
    def build_launcher_app(self):
        """构建启动器 .app"""
        self.log("构建启动器应用...")
        
        # 创建临时的 spec 文件用于构建 .app
        # 注意：这里我们使用 --windowed 模式
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "launcher.py",
            "--name", "LifeContext",
            "--windowed",  # 生成 .app
            "--clean",
            "--noconfirm",
            "--distpath", str(self.dist_dir),
            "--workpath", str(self.build_dir / "launcher_build"),
            # 排除不必要的模块以减小体积（如果需要）
        ]
        
        if self.run_command(cmd):
            self.log("启动器 .app 构建完成", "SUCCESS")
            return True
        return False
    
    def assemble_app(self):
        """组装最终的 .app 包"""
        self.log("组装应用包...")
        
        app_path = self.dist_dir / self.app_name
        if not app_path.exists():
            self.log("未找到生成的 .app 包", "ERROR")
            return False
        
        # macOS .app 的可执行文件目录
        contents_macos = app_path / "Contents" / "MacOS"
        
        # 1. 复制 Backend
        self.log("复制 Backend...")
        # 注意：build.spec 生成的是一个文件夹 (onedir 模式)
        backend_src = self.dist_dir / "backend_dist" / "LifeContextBackend"
        backend_dst = contents_macos / "backend"
        if backend_src.exists():
            if backend_dst.exists():
                shutil.rmtree(backend_dst)
            shutil.copytree(backend_src, backend_dst)
        else:
            self.log("未找到 Backend 构建产物", "ERROR")
            return False
            
        # 2. 复制 Frontend Dist
        self.log("复制 Frontend...")
        frontend_dist_src = self.base_dir / "frontend" / "dist"
        frontend_dst = contents_macos / "frontend" / "dist"
        frontend_dst.parent.mkdir(parents=True, exist_ok=True)
        if frontend_dist_src.exists():
            if frontend_dst.exists():
                shutil.rmtree(frontend_dst)
            shutil.copytree(frontend_dist_src, frontend_dst)
        else:
            self.log("未找到 Frontend 构建产物", "ERROR")
            return False
            
        # 3. 复制 Extension
        self.log("复制 Extension...")
        extension_src = self.base_dir / "Extension"
        extension_dst = contents_macos / "Extension"
        if extension_src.exists():
            if extension_dst.exists():
                shutil.rmtree(extension_dst)
            shutil.copytree(extension_src, extension_dst)
        
        # 4. 创建必要的空目录
        (contents_macos / "logs").mkdir(exist_ok=True)
        
        self.log("应用组装完成", "SUCCESS")
        return True
    
    def create_dmg(self):
        """创建 DMG 镜像"""
        self.log("正在创建 DMG...")
        
        app_path = self.dist_dir / self.app_name
        dmg_output = self.output_dir / self.dmg_name
        
        if dmg_output.exists():
            dmg_output.unlink()
            
        # 使用 create-dmg (需要先安装: brew install create-dmg)
        # 或者使用 hdiutil (macOS 自带)
        
        # 这里使用 hdiutil，因为它不需要额外安装
        cmd = [
            "hdiutil", "create",
            "-volname", "LifeContext",
            "-srcfolder", str(app_path),
            "-ov",
            "-format", "UDZO",
            str(dmg_output)
        ]
        
        if self.run_command(cmd):
            self.log(f"DMG 创建成功: {dmg_output}", "SUCCESS")
            return True
        else:
            self.log("DMG 创建失败，尝试使用简单的复制方式", "WARNING")
            # 如果 hdiutil 失败，至少把 .app 复制出来
            final_app_path = self.output_dir / self.app_name
            if final_app_path.exists():
                shutil.rmtree(final_app_path)
            shutil.copytree(app_path, final_app_path)
            self.log(f"已将 .app 复制到输出目录: {final_app_path}", "SUCCESS")
            return True

    def run(self):
        """执行构建流程"""
        start_time = time.time()
        self.log("=== 开始 LifeContext macOS 构建流程 ===")
        
        if not self.clean(): return
        if not self.build_backend(): return
        if not self.build_frontend(): return
        if not self.build_launcher_app(): return
        if not self.assemble_app(): return
        if not self.create_dmg(): return
        
        duration = time.time() - start_time
        self.log(f"=== 构建流程结束，耗时 {duration:.2f} 秒 ===", "SUCCESS")
        self.log(f"输出目录: {self.output_dir}", "SUCCESS")

if __name__ == "__main__":
    # 检查是否在 macOS 上运行
    if sys.platform != "darwin":
        print("❌ 错误: 此脚本必须在 macOS 系统上运行")
        print("Windows 用户请将项目复制到 Mac 电脑后运行此脚本")
        sys.exit(1)
        
    builder = MacOSBuilder()
    builder.run()
