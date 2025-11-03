# 🚀 LifeContext 一键部署指南

本文档介绍如何使用一键部署脚本快速启动 LifeContext 的所有服务。

## 📋 前置准备

### 必需环境

1. **Python 环境**
   - 安装 [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 或 [Anaconda](https://www.anaconda.com/)
   - 确保 `conda` 命令可用

2. **Node.js 环境**
   - 安装 [Node.js](https://nodejs.org/) (推荐 v18 或更高版本)
   - 确保 `node` 和 `npm` 命令可用

3. **配置 API Key**
   - 编辑 `backend/config.py` 文件
   - 配置你的 LLM API Key 和 Embedding API Key

### 首次运行准备

**仅首次运行时需要**创建 conda 环境：

```bash
cd backend
conda env create -f environment.yml
cd ..
```

## 🎯 快速启动

### Windows 系统

#### 启动所有服务

双击运行 `deploy.bat` 或在命令行中执行：

```cmd
deploy.bat
```

#### 停止所有服务

双击运行 `stop.bat` 或在命令行中执行：

```cmd
stop.bat
```

### Linux / macOS 系统

#### 首次使用：添加执行权限

```bash
chmod +x deploy.sh stop.sh
```

#### 启动所有服务

```bash
./deploy.sh
```

#### 停止所有服务

```bash
./stop.sh
```

## 📊 服务说明

脚本会自动启动以下三个服务：

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端服务 | 8000 | Flask API 服务 |
| 前端界面 | 3000 | Vue.js 前端界面 |
| 插件服务 | - | 浏览器插件后端支持 |

## 🔍 服务验证

### 检查服务是否启动成功

访问以下地址验证：

- **后端 API**: http://localhost:8000
- **前端界面**: http://localhost:3000

### 查看日志（Linux/macOS）

```bash
# 查看后端日志
tail -f logs/backend.log

# 查看插件日志
tail -f logs/extension.log

# 查看前端日志
tail -f logs/frontend.log
```

## 🧩 浏览器插件安装

服务启动后，还需要手动安装浏览器插件：

1. 打开浏览器（推荐 Chrome 或 Edge）
2. 进入扩展管理页面
   - Chrome: `chrome://extensions/`
   - Edge: `edge://extensions/`
3. 开启右上角的**开发者模式**
4. 点击**加载已解压的扩展程序**
5. 选择项目目录下的 `Extension/extension` 文件夹
6. 插件加载完成后即可使用

## ⚙️ 配置说明

### 后端配置

编辑 `backend/config.py` 文件：

```python
# LLM API 配置
LLM_API_KEY = "your-api-key-here"
LLM_BASE_URL = "https://api.openai.com/v1"
LLM_MODEL = "gpt-4o-mini"

# Embedding API 配置
EMBEDDING_API_KEY = "your-embedding-key-here"
EMBEDDING_BASE_URL = "https://api.openai.com/v1"
EMBEDDING_MODEL = "text-embedding-3-small"

# 定时任务配置
ENABLE_SCHEDULER_ACTIVITY = True   # 每15分钟生成活动记录
ENABLE_SCHEDULER_TODO = False      # 每30分钟生成待办任务
ENABLE_SCHEDULER_TIP = True        # 每小时整生成智能提示
ENABLE_SCHEDULER_REPORT = True     # 每天早上8点生成日报
```

### 事件推送配置

在 `backend/config.py` 中控制各类事件推送：

```python
ENABLE_EVENT_TIP = True           # Tips 生成事件推送
ENABLE_EVENT_TODO = False         # Todo 生成事件推送
ENABLE_EVENT_ACTIVITY = False     # Activity 生成事件推送
ENABLE_EVENT_REPORT = True        # Report 生成事件推送
```

## 🐛 常见问题

### 1. conda 环境未找到

**错误**: `环境 'lifecontext' 不存在`

**解决**: 手动创建环境

```bash
cd backend
conda env create -f environment.yml
conda activate lifecontext
```

### 2. 端口已被占用

**错误**: `Address already in use`

**解决**: 
- 运行停止脚本关闭之前的服务
- 或手动终止占用端口的进程

```bash
# Linux/macOS
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### 3. npm 依赖安装失败

**解决**: 清理缓存后重新安装

```bash
cd frontend  # 或 Extension
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### 4. Python 包安装失败

**解决**: 使用 pip 手动安装

```bash
conda activate lifecontext
cd backend
pip install -r requirements.txt
```

### 5. macOS Vite 权限问题

**错误**: `Permission denied: vite`

**解决**: 添加执行权限

```bash
cd frontend
chmod +x node_modules/.bin/vite
```

## 📝 手动启动方式

如果一键部署脚本遇到问题，可以手动启动各个服务：

### 启动后端

```bash
cd backend
conda activate lifecontext
python app.py
```

### 启动插件服务

```bash
cd Extension
npm install  # 首次运行
node server.js
```

### 启动前端

```bash
cd frontend
npm install  # 首次运行
npm run dev
```

## 🔄 更新代码后重启

当代码更新后，使用以下步骤重启服务：

```bash
# 1. 停止所有服务
./stop.sh        # Linux/macOS
stop.bat         # Windows

# 2. 更新代码
git pull

# 3. 重新启动
./deploy.sh      # Linux/macOS
deploy.bat       # Windows
```

## 💡 开发提示

- **修改后端代码**: 后端使用 Flask，修改代码后会自动重载（如果启用了 DEBUG 模式）
- **修改前端代码**: 前端使用 Vite，修改代码后会自动热更新
- **修改插件代码**: 插件需要重新加载扩展才能看到更新

## 📚 更多信息

详细使用说明请参考：
- [中文文档](readme_zh.md)
- [English Documentation](readme.md)

