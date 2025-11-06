"""
网络搜索工具（异步示例）
"""

import aiohttp
from typing import Dict, Any, List, Optional
from tools.base import BaseTool
from utils.helpers import get_logger

logger = get_logger(__name__)


class WebSearchTool(BaseTool):
    """网络搜索工具"""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="在互联网上搜索相关信息。当需要获取最新的、不在本地数据库中的信息时使用此工具。",
            is_async=True
        )
        # 初始化缺失的属性
        self.proxy = None  # 代理设置（可选）
        self.timeout = 10  # 超时时间（秒）
        self.max_results = 5  # 默认最大结果数
        self.default_engine = "DuckDuckGo"  # 默认搜索引擎
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询文本"
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大结果数量",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                },
                "lang": {
                    "type": "string",
                    "description": "搜索语言（可选），默认 zh-cn",
                    "default": "zh-cn"
                }
            },
            "required": ["query"]
        }
    
    def execute(self, query: str, max_results: int = 5, **kwargs) -> Any:
        """
        同步执行方法（异步工具通常不需要实现）
        """
        raise NotImplementedError("This tool is async only. Use execute_async() instead.")
    
    async def execute_async(self, query: str, lang: str = "zh-cn", max_results: int = None, **kwargs) -> Any:
        """
        异步执行网络搜索
        
        Args:
            query: 搜索查询
            lang: 搜索语言（可选）
            max_results: 最大结果数量
            
        Returns:
            搜索结果列表，每个结果包含 title, url, snippet
        """
        try:
            if max_results is None:
                max_results = self.max_results
            max_results = min(max_results, 20)  # 限制最大结果数
            
            logger.info(f"Using primary search engine: DuckDuckGo")
            results = await self._search_duckduckgo_async(query, max_results, lang)

            if results:
                logger.info(f"Successfully retrieved {len(results)} results from {self.default_engine}")
                return {
                    "success": True,
                    "query": query,
                    "results_count": len(results),
                    "results": results,
                    "engine": self.default_engine,
                }

            # 所有搜索引擎都失败
            return {
                "success": False,
                "query": query,
                "error": "All search engines failed",
                "results": [],
            }
        except Exception as e:
            logger.exception(f"Error in web search: {e}")
            return []
    
    async def _search_duckduckgo_async(self, query: str, max_results: int, lang: str) -> List[Dict[str, Any]]:
        """使用 ddgs 库进行异步搜索"""
        try:
            from ddgs import DDGS
            import asyncio

            # 获取区域设置
            region = self._get_region(lang)
            results = []

            # 在线程池中执行同步的 DDGS 调用（因为 ddgs 是同步库）
            loop = asyncio.get_event_loop()
            
            def _sync_search():
                """同步搜索函数"""
                with DDGS(proxy=self.proxy, timeout=self.timeout, verify=True) as ddgs:
                    # 新 API: text(query, ...) 作为第一个位置参数
                    search_results = list(
                        ddgs.text(
                            query,  # 第一个位置参数
                            region=region,
                            safesearch="moderate",
                            max_results=max_results,
                        )
                    )
                    return search_results
            
            # 在线程池中执行同步搜索
            search_results = await loop.run_in_executor(None, _sync_search)

            # 格式化结果
            for r in search_results:
                results.append(
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("href", ""),
                        "source": "DuckDuckGo",
                    }
                )
            return results
            
        except ImportError:
            logger.error("ddgs library not installed")
            logger.error("Please install with: pip install duckduckgo-search")
            return []
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []

    def _get_region(self, lang: str) -> str:
        """根据语言获取区域代码（用于 DuckDuckGo）"""
        region_map = {
            "zh-cn": "cn-zh",
            "zh": "cn-zh",
            "en": "us-en",
            "en-us": "us-en",
            "en-gb": "gb-en",
            "ja": "jp-ja",
            "ko": "kr-ko",
            "fr": "fr-fr",
            "de": "de-de",
            "es": "es-es",
            "ru": "ru-ru",
        }

        return region_map.get(lang.lower(), "wt-wt")  # wt-wt 表示无特定区域


def get_operation_tools() -> list:
    """获取所有操作工具实例"""
    return [
        WebSearchTool(),
        # 可以添加更多操作工具
    ]
