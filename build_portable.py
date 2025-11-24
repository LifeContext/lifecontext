"""
LifeContext 便携包构建脚本
自动化构建便携ZIP包
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import zipfile

class PortableBuilder:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.build_dir = self.base_dir / "build_portable"
        self.dist_dir = self.base_dir / "dist_portable"
        self.output_dir = self.base_dir / "LifeContext-Portable"
        
    def log(self, message, level="INFO"):
        """输出日志"""
        symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
        print(f"{symbols.get(level, 'ℹ️')} {message}")
    
    def get_npm_command(self):
        """获取正确的 npm 命令（Windows 使用 npm.cmd）"""
        if sys.platform == 'win32':
            return 'npm.cmd'
        return 'npm'
    
    def get_node_command(self):
        """获取正确的 node 命令"""
        if sys.platform == 'win32':
            return 'node.exe'
        return 'node'
    
    def clean(self):
        """清理旧的构建文件"""
        self.log("清理旧的构建文件...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir, self.output_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                self.log(f"已删除: {dir_path}")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log("清理完成", "SUCCESS")
        return True
    
    def build_backend(self):
        """构建 Backend 可执行文件"""
        self.log("开始构建 Backend...")
        
        backend_dir = self.base_dir / "backend"
        spec_file = backend_dir / "build.spec"
        
        if not spec_file.exists():
            self.log("找不到 build.spec 文件", "ERROR")
            return False
        
        try:
            # 运行 PyInstaller
            result = subprocess.run(
                [sys.executable, "-m", "PyInstaller", str(spec_file)],
                cwd=str(backend_dir),
                check=True,
                capture_output=True,
                text=True
            )
            
            self.log("Backend 构建完成", "SUCCESS")
            
            # 复制生成的文件
            backend_exe = backend_dir / "dist" / "LifeContextBackend.exe"
            if backend_exe.exists():
                target_dir = self.output_dir / "backend"
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backend_exe, target_dir / "LifeContextBackend.exe")
                self.log(f"已复制 Backend 到: {target_dir}")
            else:
                self.log("找不到生成的 Backend 可执行文件", "ERROR")
                return False
            
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Backend 构建失败: {e}", "ERROR")
            self.log(f"输出: {e.stdout}", "ERROR")
            self.log(f"错误: {e.stderr}", "ERROR")
            return False
        except Exception as e:
            self.log(f"Backend 构建出错: {e}", "ERROR")
            return False
    
    def build_frontend(self):
        """构建 Frontend"""
        self.log("开始构建 Frontend...")
        
        frontend_dir = self.base_dir / "frontend"
        
        try:
            npm_cmd = self.get_npm_command()
            
            # 检查 node_modules
            if not (frontend_dir / "node_modules").exists():
                self.log("安装 Frontend 依赖...")
                subprocess.run(
                    [npm_cmd, "install"],
                    cwd=str(frontend_dir),
                    check=True,
                    shell=True
                )
            
            # 构建前端
            self.log("正在构建前端（这可能需要几分钟）...")
            subprocess.run(
                [npm_cmd, "run", "build"],
                cwd=str(frontend_dir),
                check=True,
                shell=True
            )
            
            self.log("Frontend 构建完成", "SUCCESS")
            
            # 复制构建文件
            dist_dir = frontend_dir / "dist"
            if dist_dir.exists():
                target_dir = self.output_dir / "frontend" / "dist"
                shutil.copytree(dist_dir, target_dir)
                self.log(f"已复制 Frontend 到: {target_dir}")
            else:
                self.log("找不到 Frontend 构建输出", "ERROR")
                return False
            
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Frontend 构建失败: {e}", "ERROR")
            return False
        except Exception as e:
            self.log(f"Frontend 构建出错: {e}", "ERROR")
            return False
    
    def build_extension_server(self):
        """构建 Extension Server"""
        self.log("准备 Extension Server...")
        
        extension_dir = self.base_dir / "Extension"
        
        try:
            # 复制 Extension 文件
            target_dir = self.output_dir / "Extension"
            
            # 复制 extension 文件夹（浏览器插件）
            if (extension_dir / "extension").exists():
                shutil.copytree(
                    extension_dir / "extension",
                    target_dir / "extension"
                )
                self.log("已复制 Extension 插件文件")
            
            # 复制 server.js 和相关文件
            files_to_copy = ["server.js", "package.json"]
            for file_name in files_to_copy:
                src_file = extension_dir / file_name
                if src_file.exists():
                    shutil.copy2(src_file, target_dir / file_name)
            
            # 检查是否需要安装依赖
            if (extension_dir / "node_modules").exists():
                shutil.copytree(
                    extension_dir / "node_modules",
                    target_dir / "node_modules"
                )
                self.log("已复制 Extension 依赖")
            else:
                self.log("Extension node_modules 不存在，需要手动安装", "WARNING")
            
            self.log("Extension Server 准备完成", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Extension Server 准备出错: {e}", "ERROR")
            return False
    
    def build_launcher(self):
        """构建启动器"""
        self.log("构建启动器...")
        
        try:
            # 创建临时 spec 文件
            spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LifeContext',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
"""
            
            spec_file = self.base_dir / "launcher.spec"
            with open(spec_file, 'w', encoding='utf-8') as f:
                f.write(spec_content)
            
            # 运行 PyInstaller
            subprocess.run(
                [sys.executable, "-m", "PyInstaller", "launcher.spec", "--clean"],
                cwd=str(self.base_dir),
                check=True
            )
            
            # 复制生成的启动器
            launcher_exe = self.base_dir / "dist" / "LifeContext.exe"
            if launcher_exe.exists():
                shutil.copy2(launcher_exe, self.output_dir / "LifeContext.exe")
                self.log("启动器构建完成", "SUCCESS")
                return True
            else:
                self.log("找不到生成的启动器", "ERROR")
                return False
        except Exception as e:
            self.log(f"启动器构建出错: {e}", "ERROR")
            return False
    
    def build_frontend_server(self):
        """构建前端服务器"""
        self.log("构建前端服务器...")
        
        try:
            spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['frontend_server.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='frontend_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
            
            spec_file = self.base_dir / "frontend_server.spec"
            with open(spec_file, 'w', encoding='utf-8') as f:
                f.write(spec_content)
            
            subprocess.run(
                [sys.executable, "-m", "PyInstaller", "frontend_server.spec", "--clean"],
                cwd=str(self.base_dir),
                check=True
            )
            
            frontend_server_exe = self.base_dir / "dist" / "frontend_server.exe"
            if frontend_server_exe.exists():
                shutil.copy2(frontend_server_exe, self.output_dir / "frontend_server.exe")
                self.log("前端服务器构建完成", "SUCCESS")
                return True
            else:
                self.log("找不到生成的前端服务器", "ERROR")
                return False
        except Exception as e:
            self.log(f"前端服务器构建出错: {e}", "ERROR")
            return False
    
    def copy_additional_files(self):
        """复制额外文件"""
        self.log("复制额外文件...")
        
        # 创建 backend/data 目录
        (self.output_dir / "backend" / "data").mkdir(parents=True, exist_ok=True)
        
        # 复制 .env.example
        env_example = self.base_dir / "backend" / ".env.example"
        if env_example.exists():
            shutil.copy2(env_example, self.output_dir / "backend" / ".env.example")
        
        # 创建 README
        readme_content = """
# LifeContext 便携版

## 🚀 快速开始

1. 双击运行 `LifeContext.exe`
2. 首次运行会提示配置 API Key，请按照提示填写
3. 点击「启动服务」按钮
4. 浏览器会自动打开 http://localhost:3000

## 📝 浏览器插件安装

1. 打开浏览器（推荐 Chrome 或 Edge）
2. 访问扩展管理页面
3. 开启「开发者模式」
4. 点击「加载已解压的扩展程序」
5. 选择 `Extension/extension` 文件夹

## ⚙️ 配置说明

### API Key 配置
- **LLM API**: 用于内容分析和智能对话
- **Embedding API**: 用于向量数据库存储

推荐使用 OpenAI API，也可以使用兼容的第三方服务。

### 配置文件位置
`backend/.env`

### 修改配置
可以通过启动器界面修改，或直接编辑 `.env` 文件。

## 📊 服务端口

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Extension Server: http://localhost:3001

## ❓ 常见问题

### 端口被占用
如果提示端口被占用，请检查是否有其他服务在运行，或修改配置文件中的端口号。

### 无法启动服务
1. 检查是否正确配置了 API Key
2. 检查防火墙是否拦截
3. 查看日志标签页的错误信息

## 📞 获取帮助

- GitHub: https://github.com/LifeContext/lifecontext
- Discord: https://discord.gg/sb8Xg8xR

## 📄 许可证

开源项目，详见 LICENSE 文件。
"""
        
        with open(self.output_dir / "README.txt", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # 如果存在更详细的 PORTABLE_README.txt，也复制进去
        portable_readme = self.base_dir / "PORTABLE_README.txt"
        if portable_readme.exists():
            shutil.copy2(portable_readme, self.output_dir / "使用说明.txt")
            self.log("已复制详细使用说明")
        
        self.log("额外文件复制完成", "SUCCESS")
        return True
    
    def create_zip(self):
        """创建ZIP压缩包"""
        self.log("创建ZIP压缩包...")
        
        zip_name = f"LifeContext-Portable-{sys.platform}.zip"
        zip_path = self.base_dir / zip_name
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.output_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(self.output_dir.parent)
                        zipf.write(file_path, arcname)
            
            # 显示文件大小
            size_mb = zip_path.stat().st_size / (1024 * 1024)
            self.log(f"ZIP包创建完成: {zip_name} ({size_mb:.2f} MB)", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"创建ZIP包出错: {e}", "ERROR")
            return False
    
    def build(self):
        """执行完整构建流程"""
        self.log("=" * 60)
        self.log("LifeContext 便携包构建工具")
        self.log("=" * 60)
        self.log("")
        
        steps = [
            ("清理旧文件", self.clean),
            ("构建前端", self.build_frontend),
            ("构建前端服务器", self.build_frontend_server),
            ("准备Extension", self.build_extension_server),
            ("构建Backend", self.build_backend),
            ("构建启动器", self.build_launcher),
            ("复制额外文件", self.copy_additional_files),
            ("创建ZIP包", self.create_zip),
        ]
        
        for i, (step_name, step_func) in enumerate(steps, 1):
            self.log("=" * 60)
            self.log(f"步骤 [{i}/{len(steps)}]: {step_name}")
            self.log("=" * 60)
            
            try:
                result = step_func()
                if result is False:
                    self.log(f"构建失败: {step_name}", "ERROR")
                    return False
                elif result is None:
                    self.log(f"警告: {step_name} 未返回状态", "WARNING")
            except Exception as e:
                self.log(f"构建出错: {step_name}", "ERROR")
                self.log(f"错误信息: {e}", "ERROR")
                import traceback
                self.log(traceback.format_exc(), "ERROR")
                return False
            
            self.log("")
        
        self.log("=" * 60)
        self.log("🎉 构建完成！", "SUCCESS")
        self.log("=" * 60)
        self.log(f"输出目录: {self.output_dir}")
        self.log(f"ZIP包位置: {self.base_dir / f'LifeContext-Portable-{sys.platform}.zip'}")
        self.log("")
        
        # 验证关键文件
        self.log("验证构建结果...")
        checks = [
            ("启动器", self.output_dir / "LifeContext.exe"),
            ("前端服务器", self.output_dir / "frontend_server.exe"),
            ("前端静态文件", self.output_dir / "frontend" / "dist" / "index.html"),
            ("Backend 服务", self.output_dir / "backend" / "LifeContextBackend.exe"),
            ("Extension 插件", self.output_dir / "Extension" / "extension" / "manifest.json"),
            ("使用说明", self.output_dir / "README.txt"),
        ]
        
        all_ok = True
        for name, path in checks:
            if path.exists():
                self.log(f"✅ {name}: {path.name}")
            else:
                self.log(f"❌ {name}: 未找到", "WARNING")
                all_ok = False
        
        if all_ok:
            self.log("\n✅ 所有关键文件验证通过！", "SUCCESS")
        else:
            self.log("\n⚠️ 部分文件未找到，但构建已完成", "WARNING")
        
        self.log("")
        return True


if __name__ == "__main__":
    builder = PortableBuilder()
    success = builder.build()
    
    if not success:
        print("\n构建失败！")
        sys.exit(1)
    
    print("\n按回车键退出...")
    input()

