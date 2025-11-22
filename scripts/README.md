# LifeContext 脚本管理

本目录包含项目的所有部署和管理脚本。

## 📁 脚本文件说明

### 部署脚本

#### Linux/macOS
```bash
./scripts/deploy.sh
```
- 一键启动所有服务（后端、前端、浏览器扩展）
- 自动检查依赖项（conda、Node.js、npm）
- 自动创建 conda 环境（如果不存在）
- 启动前清理旧进程
- 将服务 PID 保存到 `logs/` 目录

#### Windows
```bash
scripts\deploy.bat
```
- Windows 一键启动脚本
- 在新窗口中启动各个服务
- 支持自动依赖项安装

### 停止脚本

#### Linux/macOS
```bash
./scripts/stop.sh
```
- 停止所有运行中的服务
- 优先使用保存的 PID 文件停止进程
- 如果 PID 文件不存在，通过进程名称查找并停止

#### Windows
```bash
scripts\stop.bat
```
- 停止所有 LifeContext 服务窗口

## 🚀 使用方法

### Linux/macOS 用户

**启动所有服务：**
```bash
cd /path/to/lifetcontext
./scripts/deploy.sh
```

**停止所有服务：**
```bash
cd /path/to/lifetcontext
./scripts/stop.sh
```

### Windows 用户

**启动所有服务：**
```cmd
cd C:\path\to\lifetcontext
scripts\deploy.bat
```

**停止所有服务：**
关闭对应的服务窗口或运行：
```cmd
scripts\stop.bat
```

## 📝 服务信息

启动后可访问以下地址：

- **后端 API**: http://localhost:8000
- **前端界面**: http://localhost:3000
- **扩展服务**: http://localhost:3001

## 📊 日志文件

所有日志文件保存在项目根目录的 `logs/` 文件夹中：

- `logs/backend.log` - 后端服务日志
- `logs/extension.log` - 浏览器扩展日志
- `logs/frontend.log` - 前端服务日志
- `logs/backend.pid` - 后端进程 ID
- `logs/extension.pid` - 扩展进程 ID
- `logs/frontend.pid` - 前端进程 ID

## 💡 常见问题

### 脚本权限错误
如果在 Linux/macOS 上遇到权限错误，运行：
```bash
chmod +x ./scripts/*.sh
```

### 相对路径问题
脚本会自动检测脚本位置并计算正确的项目根目录，无需担心执行路径问题。

### 查看实时日志
```bash
# 后端日志
tail -f logs/backend.log

# 扩展日志
tail -f logs/extension.log

# 前端日志
tail -f logs/frontend.log
```

## 🔧 脚本修改指南

### 路径变量
脚本使用以下变量来管理路径：
- **Linux/macOS**: `$PROJECT_ROOT` 自动计算为脚本目录的上一级
- **Windows**: `%PROJECT_ROOT%` 自动计算为脚本所在目录的上一级

所有路径都使用绝对路径引用，确保无论从哪个目录执行脚本都能正常工作。

