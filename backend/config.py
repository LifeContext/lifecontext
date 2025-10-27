"""
配置文件 - 直接在此文件中配置 API Key
"""

from pathlib import Path

# ============================================================================
# 🔑 API Key 配置（必填项）
# ============================================================================
# 在这里直接配置你的 API Key，不需要使用环境变量

# LLM API 配置（用于内容分析和智能对话）
LLM_API_KEY = "your_key"
LLM_BASE_URL = "your_url"
LLM_MODEL = "your_model"

# 向量化 Embedding API 配置（用于向量数据库）
EMBEDDING_API_KEY = "your_key"
EMBEDDING_BASE_URL = "your_url"
EMBEDDING_MODEL = "your_model"

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
LLM_MAX_TOKENS = 2000

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
    print("   请在 config.py 中配置 LLM_API_KEY")

if ENABLE_VECTOR_STORAGE:
    print("✅ 向量数据库功能：已启用")
    print(f"   模型：{EMBEDDING_MODEL}")
else:
    print("❌ 向量数据库功能：未启用")
    print("   请在 config.py 中配置 EMBEDDING_API_KEY")

print("="*60 + "\n")
