# 🧠 人生上下文

![img](src/logo.jpg)
[![GitHub stars](https://img.shields.io/github/stars/LifeContext/lifecontext?style=flat-square&color=F8C63D)](https://github.com/LifeContext/lifecontext/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/LifeContext/lifecontext?style=flat-square&color=F00F80)](https://github.com/LifeContext/lifecontext/issues)
[![GitHub contributors](https://img.shields.io/github/contributors/LifeContext/lifecontext?style=flat-square&color=A4DD00)](https://github.com/LifeContext/lifecontext/graphs/contributors)
[![GitHub license](https://img.shields.io/github/license/LifeContext/lifecontext?style=flat-square&color=lightgrey)](https://github.com/LifeContext/lifecontext/blob/main/LICENSE)
[![GitHub last commit](https://img.shields.io/github/last-commit/LifeContext/lifecontext?style=flat-square&color=BFD500)](https://github.com/LifeContext/lifecontext/commits/main)
[![微信群](https://img.shields.io/badge/WeChat-Join_Us-brightgreen?logo=wechat&style=flat-square)](https://github.com/LifeContext/lifecontext/blob/main/src/wechat.jpg?raw=true)
[![飞书群](https://img.shields.io/badge/Feishu-Join_Us-blue?logo=lark&style=flat-square)](https://github.com/LifeContext/lifecontext/blob/main/src/feishu.jpg?raw=true)
[![Discord](https://img.shields.io/badge/Discord-Join_Us-7289DA?logo=discord&style=flat-square)](https://discord.gg/sb8Xg8xR)
[![Follow on X](https://img.shields.io/badge/Follow_%40LifeContext2025-000000?logo=x&style=flat-square)](https://x.com/LifeContext)



## 🌍 LifeContext

Shaped by your life. Empower yourself. Interact with the world.
- 源于您独一无二的人生上下文，为您塑造一个真正'懂你'的数字分身。
- 提供人生级别的长周期检索，低成本的多模态数据存储，精确的上下文对齐，高效的实时上下文压缩技术等等Context Memory底层能力。
- 重塑您的连接方式，与这个世界展开无限可能的交互、连接与创造。

## 🎯 核心功能

- **个人上下文库**：智能构建你的人生上下文，覆盖网页、应用与智能设备等多数据源，通过持续交互不断学习与进化，沉淀知识与体验。
- **标准化上下文接口**：为开发者提供统一接口，用于存储、读取与管理上下文数据，让跨平台集成与扩展更加简单高效。
- **伴随式洞察**：主动洞察你的人生上下文，在恰当的时刻呈现对你真正重要的时刻、想法与优先事项，让信息不再被动等待。
- **上下文对话**：理解你的人生上下文，随时回答提问、回忆片段或重组灵感，成为您记忆与思维的延伸。
- **场景自适应**：基于你的指令，在特定垂直场景中提供更精准、更具执行力的响应，实现真正的“上下文驱动智能”。
- **驱动任务**：让 AI 从思考者进化为行动者，根据你的语境主动触发、持续执行多种条件任务，让智能真正融入你的人生。
- **内容生成**：根据需求生成文档、图片、音频、视频与笔记，高效整理与表达你的想法，让创造回归自然流畅。
- **数字分身**：作为您的专属数字分身，与这个世界展开无限可能的交互。

![img](src/mindmap_zh.png)

## 🧩 当前版本

- 聚焦您的核心工作空间——**网页浏览器**，建立强大且主动的个性化智能助手。
- 全自动地对您浏览的网页进行分析，生成您的数字人生上下文。
- 不打扰您的心流状态，主动提供及时、可行动的洞察与建议。


## 🚀 快速开始
### 📋 前置准备

#### 1️⃣ **Python 环境**
   - 安装 [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 或 [Anaconda](https://www.anaconda.com/)
   - 确保 `conda` 命令可用

#### 2️⃣ **Node.js 环境**
   - 安装 [Node.js](https://nodejs.org/) (推荐 v18 或更高版本)
   - 确保 `node` 和 `npm` 命令可用
### 🛠️ 前后端配置与启动

#### 1️⃣ 配置大模型与向量服务
📦 进入 backend 目录，复制 `.env.example`文件并命名为`.env`：
```bash
cd backend
cp .env.example .env
```

✅ 将你的模型和向量数据库接口信息填入刚刚生成的`.env`中，示例如下：
```python
# LLM API 
LLM_API_KEY = "sk-1234abcd5678efgh9012ijkl"
LLM_BASE_URL = "https://api.openai.com/v1"
LLM_MODEL = "gpt-4o-mini"

# Embedding API 
EMBEDDING_API_KEY = "sk-embed-9876mnop4321qrst"
EMBEDDING_BASE_URL = "https://api.openai.com/v1"
EMBEDDING_MODEL = "text-embedding-3-small"

```

#### 2️⃣ 创建conda环境（仅首次运行需要）
📦 在 conda 环境 backend 目录下，根据 `environment.yml` 创建环境：
```bash
cd backend
conda env create -f environment.yml
```

#### 3️⃣ 启动服务
#### Windows 系统

启动所有服务

在conda环境中执行：

```cmd
deploy.bat
```

停止所有服务

在conda环境中执行：

```cmd
stop.bat
```

#### Linux / macOS 系统

首次使用：添加执行权限

```bash
chmod +x deploy.sh stop.sh
```

启动所有服务

```bash
./deploy.sh
```

停止所有服务

```bash
./stop.sh
```


### 🧩 浏览器插件（Extension）配置

#### 1️⃣ 导入浏览器插件
📦 步骤如下：

1. 打开浏览器（推荐使用 Chrome 或 Edge）。
2. 进入 [管理扩展程序] 页面，打开右上角的 [开发者模式] 。
3. 点击 [加载已解压的扩展程序] ，选择项目目录下的 `./Extension/extension` 文件夹。
4. 加载完成后，即可在浏览器工具栏中看到插件图标。
5. 插件功能启用后，可关闭开发者模式以提升安全性。

🎉打开浏览器访问 http://localhost:3000/ 

如果部署还有问题，请参考 deploy_guide_zh.md

## 🌄 场景介绍

1. LifeContext会自动无感地记录您在网页上浏览的信息。
2. 在任意网页上，点击悬浮球即可打开 Chatbox，与 AI 自然对话。它能理解您正在浏览的内容，结合人生上下文提供即时回答、总结或建议。

![img](src/product01.png)

![img](src/product02.png)

3. LifeContext将无感记录您的一切浏览体验并据此生成智能提示、待办和日报，并以即时通知的形式浮现在您的浏览的网页右侧，您也可以在主页上查看所有信息

![img](src/product03.png)

- 提示信息是根据您的浏览的信息进行的内容推送，您可点击卡片查看详细的提示信息。

![img](src/product04.png)

- TodoList是参考您的活动自动生成，您可以手动编辑、删除或添加。

![img](src/product05.png)

- 点击主页页面左侧边栏中的日期可查看该日日报详情。
默认生成时间为次日8:30，您可通过设置进行修改。

![img](src/product06.png)

4. 隐私问题

- 如您不想将特定网站记录在您的人生上下文中，可以在设置中屏蔽对应url。
如您不想记录任何浏览器行为可以关闭插件。

![img](src/product07.png)

- 您也可在主页左上角选择TimeLine页面进行存储管理，删除您不想留存在LifeContext的页面

![img](src/product08.png)

## 🤖 开发计划

LifeContext 的进化蓝图将围绕三个维度展开：

1. **上下文的「广度」**：我们始于浏览器，将逐步融合您的PC、移动设备、应用数据，直至智能硬件，构筑一个无缝的、全方位的人生上下文。
2. **AI能力的「深度」**：功能上，我们提供人生级别的长周期检索，低成本的多模态上下文存储，精确的上下文对齐，高效的实时上下文压缩技术等 Context Memory 底层能力。
3. **连接的「高度」**：最终，我们将实现数字分身作为你的专属代理，在授权下，与这个世界展开无限可能的交互、连接与创造。

![上下文来源扩展路线图](src/roadmap_zh.png)

### 🧰 上下文来源扩展路线图

为了让 AI 更懂用户，我们将分阶段、按优先级接入以下上下文来源。

- P0: 浏览器网页数据
- P1: 文档
- P2: 常见应用 MCP 和 PC 屏幕截图
- P3: 音视频文件和智能硬件
- P4: DeepResearch 和 RSS
- P5: 手机屏幕截图
- P6: 社区知识库

| 优先级 | 接入方式         | 内容                | 进度 |
| :----- | :--------------- | :------------------ | :--- |
| P0     | 浏览器插件       | AI 对话             |   ✅   |
| P0     | 浏览器插件       | 常规网页            |   ✅   |
| P0     | 浏览器插件       | 视频网页            |      |
| P1     | 文件上传         | 非结构化文档        |      |
| P1     | 文件上传         | 结构化文档          |      |
| P1     | 文件上传         | 图片                |      |
| P1     | 用户输入         | 笔记                |      |
| P2     | 应用 MCP/API     | 应用信息            |      |
| P2     | PC屏幕共享       | 用户 PC 信息        |      |
| P3     | 文件上传         | 视频/音频           |      |
| P3     | 浏览器插件       | 会议记录            |      |
| P3     | 智能硬件（手表） | 健康数据            |      |
| P3     | 智能硬件（音频） | 音频                |      |
| P3     | 智能硬件（视频） | 视频                |      |
| P4     | RSS              | 订阅网页更新信息    |      |
| P4     | Deep Research    | 高质量研究分析      |      |
| P4     | 文件上传         | 代码                |      |
| P5     | 手机屏幕截图         | 用户移动端信息      |      |
| P6     | 社区/导入知识库       | 官方/用户精选知识库      |      |
| P6     | 脑机接口      | 神经编码 |      |

### 🧰 Agent 能力扩展路线图

基于不断丰富的上下文，我们将逐步解锁 Agent 的核心能力。

- P0: 主动信息推送
- P1: 文档生成
- P2: 常见应用操作和任务生成
- P3: 多模态生成与编辑
- P4: 细分场景能力

| 优先级 | 功能                             | 进度 |
| :----- | :------------------------------- | :--- |
| P0     | 主动推送日报                     |   ✅   |
| P0     | 主动推送提示                     |   ✅   |
| P0     | 主动推送待办事项                 |   ✅   |
| P0     | 数字分身交互               |     |
| P1     | 知识库                           |      |
| P1     | 联网搜索                         |      |
| P1     | 多模态主动推送                   |      |
| P1     | 文档生成 (PDF, EXCEL, PPT, WORD) |      |
| P1     | 思维导图                         |      |
| P1     | 笔记                             |      |
| P2     | 应用操作 (MCP)                   |      |
| P2     | 定时/条件触发任务                |      |
| P2     | 网页生成 (html)                  |      |
| P3     | 图片生成、编辑                   |      |
| P3     | 音频生成、编辑                   |      |
| P3     | 视频生成、编辑                   |      |
| P4     | 细分场景能力                     |      |

## Community

<div style="display: flex; gap: 10px; align-items: flex-start;">
  <img src="src/feishu.jpg" alt="Feishu Community" style="height: 400px; width: auto; flex: 1; object-fit: cover;">
  <img src="src/wechat.jpg" alt="WeChat Community" style="height: 400px; width: auto; flex: 1; object-fit: cover;">
</div>

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=LifeContext/lifecontext&type=date&legend=top-left)](https://www.star-history.com/#LifeContext/lifecontext&type=date&legend=top-left)
