"""
清空向量数据库的工具脚本
"""

import sys
from pathlib import Path

# 添加项目路径
_backend_dir = Path(__file__).parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from utils.vectorstore import get_collection, clear_vectorstore, reset_vectorstore
from utils.helpers import get_logger
import config

logger = get_logger(__name__)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="清空向量数据库")
    parser.add_argument(
        "--method",
        type=str,
        choices=["clear", "reset"],
        default="clear",
        help="清空方法：clear（删除所有文档）或 reset（删除集合并重建）"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="跳过确认提示"
    )
    
    args = parser.parse_args()
    
    # 显示当前状态
    try:
        collection = get_collection()
        count = collection.count()
        print(f"\n{'='*60}")
        print(f"向量数据库当前状态")
        print(f"{'='*60}")
        print(f"集合名称: {config.CHROMA_COLLECTION_NAME}")
        print(f"存储路径: {config.CHROMA_PERSIST_DIR}")
        print(f"当前文档数: {count}")
        print(f"{'='*60}\n")
        
        if count == 0:
            print("向量数据库已经是空的，无需清空。")
            return
        
        # 确认操作
        if not args.confirm:
            confirm = input(f"确定要清空 {count} 个文档吗？(yes/no): ")
            if confirm.lower() not in ['yes', 'y']:
                print("操作已取消。")
                return
        
        # 执行清空
        print(f"\n开始清空向量数据库（方法: {args.method}）...")
        
        if args.method == "clear":
            success = clear_vectorstore()
        else:
            success = reset_vectorstore()
        
        if success:
            print("✅ 向量数据库清空成功！")
            
            # 验证结果
            try:
                collection = get_collection()
                new_count = collection.count()
                print(f"当前文档数: {new_count}")
            except:
                pass
        else:
            print("❌ 向量数据库清空失败，请查看日志获取详细信息。")
    
    except Exception as e:
        logger.exception(f"清空向量数据库时出错: {e}")
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    main()
