"""
配置文件 - 从本地环境变量读取 API Key 与模型配置
优先使用环境变量，未设置时采用安全的空值或合理默认值
"""

from pathlib import Path
import os

# 尝试加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有安装 python-dotenv，忽略
    pass

# ============================================================================
# 🔑 API Key / 模型配置（从环境变量读取）
# ============================================================================

# LLM API 配置（用于内容分析和智能对话）
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL")

# 向量化 Embedding API 配置（用于向量数据库）
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

# ============================================================================
# 📁 基础路径配置
# ============================================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SCREENSHOT_DIR = DATA_DIR / "screenshots"
DATABASE_PATH = DATA_DIR / "database.db"
CHROMA_PERSIST_DIR = DATA_DIR / "chromadb"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
SCREENSHOT_DIR.mkdir(exist_ok=True)
CHROMA_PERSIST_DIR.mkdir(exist_ok=True)

# ============================================================================
# 🌐 Flask 服务配置
# ============================================================================
SECRET_KEY = "dev-secret-key-change-in-production"
DEBUG = True
HOST = "0.0.0.0"
PORT = 8000

# ============================================================================
# 🔐 认证配置
# ============================================================================
AUTH_TOKEN = ""  # 留空表示不启用认证，填写 token 则启用

# ============================================================================
# 📤 文件上传配置
# ============================================================================
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# ============================================================================
# 🤖 LLM 处理配置
# ============================================================================
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 4096  # LLM 输出的最大 token 数
LLM_MAX_INPUT_TOKENS = 8192  # LLM 输入的最大 token 数（包括 system prompt + user prompt）

# 各类提示词的预估 token 数（用于动态计算）
# 这些数值是根据实际 prompt 长度估算的
SYSTEM_PROMPT_TOKENS = {
    'tip': 2500,      # tip_gen_new.py 的 system prompt 约 2500 tokens
    'todo': 2000,     # todo_gen_new.py 的 system prompt 约 2000 tokens
    'activity': 2000, # activity_gen_new.py 的 system prompt 约 2000 tokens
    'report': 3000,   # report_gen_new.py 的 system prompt 约 3000 tokens
}

# 为用户消息保留的 token 空间（用于问题描述等）
USER_MESSAGE_RESERVE_TOKENS = 500

# ============================================================================
# 🔍 向量数据库配置
# ============================================================================
CHROMA_COLLECTION_NAME = "web_data"
CHUNK_SIZE = 1000  # 文本分块大小
CHUNK_OVERLAP = 200  # 分块重叠大小

# ============================================================================
# ⚙️ 功能开关（根据 API Key 自动判断）
# ============================================================================
# LLM 内容分析：需要配置 LLM_API_KEY
ENABLE_LLM_PROCESSING = bool(LLM_API_KEY)

# 向量数据库存储：需要配置 EMBEDDING_API_KEY
ENABLE_VECTOR_STORAGE = bool(EMBEDDING_API_KEY)

# 定时任务调度器：自动生成报告、待办等
ENABLE_SCHEDULER = True  # 设置为 False 可关闭定时任务

# ============================================================================
# 📡 事件推送配置
# ============================================================================
# 控制各类事件是否推送到客户端（前端/Extension）

# Tips 生成事件推送
ENABLE_EVENT_TIP = True

# Todo 生成事件推送
ENABLE_EVENT_TODO = False

# Activity 生成事件推送
ENABLE_EVENT_ACTIVITY = False

# Report 生成事件推送
ENABLE_EVENT_REPORT = True

# 系统状态事件推送
ENABLE_EVENT_SYSTEM_STATUS = False

# ============================================================================
# 📊 启动提示
# ============================================================================
print("\n" + "="*60)
print("LifeContext API 配置状态")
print("="*60)

if ENABLE_LLM_PROCESSING:
    print("✅ LLM 内容分析功能：已启用")
    print(f"   模型：{LLM_MODEL}")
else:
    print("❌ LLM 内容分析功能：未启用")
    print("   请在本地环境变量中配置 LLM_API_KEY")

if ENABLE_VECTOR_STORAGE:
    print("✅ 向量数据库功能：已启用")
    print(f"   模型：{EMBEDDING_MODEL}")
else:
    print("❌ 向量数据库功能：未启用")
    print("   请在本地环境变量中配置 EMBEDDING_API_KEY")

print("="*60 + "\n")
