"""
工具基类模块
定义所有工具的统一接口和基础功能
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Union
from utils.helpers import get_logger

logger = get_logger(__name__)


class BaseTool(ABC):
    """工具基类 - 所有工具都应继承此类"""
    
    def __init__(self, name: str, description: str, is_async: bool = False):
        """
        初始化工具
        
        Args:
            name: 工具名称（唯一标识符）
            description: 工具描述
            is_async: 是否为异步工具
        """
        self.name = name
        self.description = description
        self.is_async = is_async
        self._validate()
    
    def _validate(self):
        """验证工具配置"""
        if not self.name:
            raise ValueError("Tool name cannot be empty")
        if not self.description:
            raise ValueError("Tool description cannot be empty")
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """
        获取工具的 OpenAI Function Calling 参数模式
        
        Returns:
            符合 OpenAI Function Calling 规范的参数模式字典
            格式: {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        执行工具（同步方法）
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        pass
    
    async def execute_async(self, **kwargs) -> Any:
        """
        执行工具（异步方法）
        如果工具是异步的，应该重写此方法
        否则默认在线程池中执行同步方法
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        if self.is_async:
            return await self.execute(**kwargs)
        else:
            # 同步工具在线程池中执行
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self.execute(**kwargs))
    
    def get_function_definition(self) -> Dict[str, Any]:
        """
        获取工具的 OpenAI Function Calling 定义
        
        Returns:
            符合 OpenAI Function Calling 规范的函数定义
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema()
            }
        }
    
    def validate_parameters(self, **kwargs) -> bool:
        """
        验证参数是否有效（可选实现）
        
        Args:
            **kwargs: 待验证的参数
            
        Returns:
            参数是否有效
        """
        schema = self.get_parameters_schema()
        required = schema.get("required", [])
        
        # 检查必需参数
        for param in required:
            if param not in kwargs:
                logger.warning(f"Missing required parameter: {param}")
                return False
        
        # 检查参数类型（可选，可以扩展）
        properties = schema.get("properties", {})
        for param_name, param_value in kwargs.items():
            if param_name in properties:
                param_type = properties[param_name].get("type")
                if param_type == "integer" and not isinstance(param_value, int):
                    logger.warning(f"Parameter {param_name} should be integer")
                    return False
                elif param_type == "string" and not isinstance(param_value, str):
                    logger.warning(f"Parameter {param_name} should be string")
                    return False
        
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取工具元数据
        
        Returns:
            工具元数据字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "is_async": self.is_async,
            "category": self.__class__.__module__.split('.')[-2] if '.' in self.__class__.__module__ else "unknown"
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', async={self.is_async})>"


class ToolsExecutor:
    """工具执行器 - 管理所有工具实例"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._register_tools()
    
    def _register_tools(self):
        """
        注册所有可用工具
        自动发现并注册继承自 BaseTool 的工具类
        """
        # 延迟导入，避免循环依赖
        # 删除 retrieval_tools 注册部分
        # try:
        #     # 检索工具
        #     from tools.retrieval_tools import get_retrieval_tools
        #     for tool in get_retrieval_tools():
        #         self.register_tool(tool)
        # except ImportError:
        #     logger.debug("Retrieval tools not found, skipping")
        
        try:
            # 配置工具
            from tools.profile_tools import get_profile_tools
            tools = get_profile_tools()
            logger.info(f"Found {len(tools)} profile tools")
            for tool in tools:
                self.register_tool(tool)
        except ImportError as e:
            logger.error(f"Failed to import profile tools: {e}")
        except Exception as e:
            logger.exception(f"Error loading profile tools: {e}")
        
        try:
            # 操作工具
            from tools.operation_tools import (
                get_operation_tools, 
                get_email_tools
            )
            
            # 注册会话记忆工具
            tools = get_operation_tools()
            logger.info(f"Found {len(tools)} operation tools")
            for tool in tools:
                self.register_tool(tool)
            
            # 注册邮箱工具
            email_tools = get_email_tools()
            logger.info(f"Found {len(email_tools)} email tools")
            for tool in email_tools:
                self.register_tool(tool)
                
        except ImportError as e:
            logger.error(f"Failed to import operation tools: {e}")
        except Exception as e:
            logger.exception(f"Error loading operation tools: {e}")
        
        # 记录最终注册的工具数量
        logger.info(f"Total tools registered: {len(self.tools)}")
        if self.tools:
            logger.info(f"Registered tool names: {list(self.tools.keys())}")
    
    def register_tool(self, tool: BaseTool):
        """
        注册工具
        
        Args:
            tool: 工具实例
        """
        if not isinstance(tool, BaseTool):
            raise TypeError(f"Tool must be an instance of BaseTool, got {type(tool)}")
        
        if tool.name in self.tools:
            logger.warning(f"Tool '{tool.name}' already registered, overwriting")
        
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        获取工具实例
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例，如果不存在则返回 None
        """
        return self.tools.get(name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """
        获取所有工具实例
        
        Returns:
            工具实例列表
        """
        return list(self.tools.values())
    
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的 OpenAI Function Calling 定义
        
        Returns:
            工具定义列表
        """
        return [tool.get_function_definition() for tool in self.tools.values()]
    
    async def run_async(self, function_name: str, **kwargs) -> Any:
        """
        异步执行工具
        
        Args:
            function_name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        if function_name not in self.tools:
            raise ValueError(f"Unknown tool: {function_name}. Available tools: {list(self.tools.keys())}")
        
        tool = self.tools[function_name]
        
        # 验证参数
        if not tool.validate_parameters(**kwargs):
            logger.warning(f"Parameter validation failed for tool '{function_name}', proceeding anyway")
        
        try:
            # 执行工具
            result = await tool.execute_async(**kwargs)
            logger.info(f"Tool '{function_name}' executed successfully")
            return result
        except Exception as e:
            logger.exception(f"Error executing tool '{function_name}': {e}")
            raise
