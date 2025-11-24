# LifeContext 便携包构建指南

本文档介绍如何构建 LifeContext 的便携 ZIP 包。

## 📋 前置要求

### 1. Python 环境
- Python 3.8 或更高版本
- 已安装 PyInstaller：`pip install pyinstaller`

### 2. Node.js 环境
- Node.js 18 或更高版本
- npm 或 yarn

### 3. 项目依赖
确保已安装所有项目依赖：

```bash
# Backend 依赖
cd backend
pip install -r requirements.txt

# Frontend 依赖
cd ../frontend
npm install

# Extension 依赖
cd ../Extension
npm install
```

## 🚀 快速构建

### 方式一：使用自动构建脚本（推荐）

```bash
python build_portable.py
```

该脚本会自动完成以下步骤：
1. 清理旧的构建文件
2. 构建前端静态文件
3. 构建前端服务器可执行文件
4. 准备浏览器插件文件
5. 构建后端可执行文件
6. 构建启动器可执行文件
7. 复制必要的配置文件
8. 打包成 ZIP 文件

构建完成后，会在项目根目录生成：
- `LifeContext-Portable/` - 便携包文件夹
- `LifeContext-Portable-{platform}.zip` - 压缩包

### 方式二：手动构建

如果自动构建脚本遇到问题，可以按以下步骤手动构建：

#### 1. 构建前端

```bash
cd frontend
npm run build
```

#### 2. 构建后端

```bash
cd backend
python -m PyInstaller build.spec
```

#### 3. 构建前端服务器

```bash
cd ..
python -m PyInstaller frontend_server.spec
```

#### 4. 构建启动器

```bash
python -m PyInstaller launcher.spec
```

#### 5. 组织文件结构

创建以下目录结构：

```
LifeContext-Portable/
├── LifeContext.exe              # 启动器
├── frontend_server.exe          # 前端服务器
├── README.txt                   # 使用说明
├── backend/
│   ├── LifeContextBackend.exe   # 后端服务
│   ├── data/                    # 数据目录（空）
│   └── .env.example             # 配置模板
├── frontend/
│   └── dist/                    # 前端静态文件
└── Extension/
    ├── extension/               # 浏览器插件
    ├── server.js                # Extension 服务器
    ├── package.json
    └── node_modules/            # Node.js 依赖
```

#### 6. 创建 ZIP 包

将 `LifeContext-Portable/` 文件夹压缩成 ZIP 文件。

## 🔍 构建问题排查

### PyInstaller 找不到模块

**问题**: 打包后运行提示缺少某个模块

**解决方案**:
1. 在 `build.spec` 的 `hiddenimports` 中添加缺少的模块
2. 重新运行 PyInstaller

### 前端构建失败

**问题**: `npm run build` 报错

**解决方案**:
1. 删除 `node_modules` 和 `package-lock.json`
2. 重新运行 `npm install`
3. 再次尝试构建

### 打包后体积过大

**问题**: 生成的可执行文件体积超过 500MB

**解决方案**:
1. 在 `build.spec` 中添加更多排除项到 `excludes` 列表
2. 使用 UPX 压缩（已在 spec 中启用）
3. 考虑不打包某些大型依赖，改为运行时安装

### Extension Server 无法启动

**问题**: Extension 服务启动失败

**解决方案**:
1. 确保 `Extension/node_modules` 存在
2. 检查 `server.js` 中的依赖是否正确
3. 可以选择不打包 Extension Server，保持使用 `node server.js` 运行

## 📦 减小打包体积的技巧

### 1. 排除不必要的依赖

编辑 `backend/build.spec`，在 `excludes` 中添加：

```python
excludes=[
    'matplotlib',
    'scipy',
    'pandas',
    'notebook',
    'jupyter',
    'IPython',
    'pytest',
    'sphinx',
],
```

### 2. 使用 One-Directory 模式

如果不需要单文件 EXE，可以改用 One-Directory 模式，这样构建更快，体积可能更小：

在 `build.spec` 中修改：

```python
exe = EXE(
    pyz,
    a.scripts,
    # 注释掉以下三行以使用 One-Directory 模式
    # a.binaries,
    # a.zipfiles,
    # a.datas,
    ...
)

# 添加 COLLECT
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LifeContextBackend'
)
```

### 3. 使用外部依赖

对于特别大的依赖（如 PyTorch、Transformers），可以考虑：
- 不打包到 EXE 中
- 在首次运行时下载安装
- 使用更轻量的替代方案

## 🌍 跨平台构建

### Windows

在 Windows 上运行构建脚本会生成 `.exe` 文件。

### macOS

在 macOS 上运行构建脚本会生成 Unix 可执行文件：

```bash
python build_portable.py
```

需要修改的地方：
- 文件扩展名从 `.exe` 改为无扩展名或 `.app`
- 启动脚本改为 `.sh` 而不是 `.bat`

### Linux

与 macOS 类似，生成 Unix 可执行文件。

## 📝 发布检查清单

构建完成后，发布前请检查：

- [ ] 启动器能正常打开并显示配置界面
- [ ] 配置保存功能正常
- [ ] 所有服务能正常启动
- [ ] 浏览器能访问 http://localhost:3000
- [ ] 浏览器插件能正常加载
- [ ] 插件功能正常（聊天、记录等）
- [ ] 日志显示正常
- [ ] 停止服务功能正常
- [ ] README 文档完整
- [ ] ZIP 包能正常解压

## 🔐 签名与验证

### Windows 代码签名

为了避免 Windows Defender 警告，建议对可执行文件进行代码签名：

```bash
# 使用 signtool 签名
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com LifeContext.exe
```

### 生成校验和

为发布的 ZIP 包生成校验和：

```bash
# SHA256
certutil -hashfile LifeContext-Portable-win32.zip SHA256 > checksums.txt

# 或使用 PowerShell
Get-FileHash LifeContext-Portable-win32.zip -Algorithm SHA256 >> checksums.txt
```

## 📞 获取帮助

如果在构建过程中遇到问题：

1. 查看构建日志中的错误信息
2. 检查是否满足所有前置要求
3. 在 GitHub 上提交 Issue
4. 加入 Discord 社区寻求帮助

## 📄 相关文档

- [PyInstaller 文档](https://pyinstaller.org/)
- [Vite 构建指南](https://vitejs.dev/guide/build.html)
- [项目部署指南](deploy_guide_zh.md)

