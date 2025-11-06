"""
智能对话接口路由
"""

import uuid
import json
from datetime import datetime
from flask import Blueprint, request, Response, stream_with_context
import config
from utils.helpers import convert_resp, auth_required, get_logger
from utils.llm import get_openai_client

logger = get_logger(__name__)

agent_bp = Blueprint('agent', __name__, url_prefix='/api/agent')

# 工作流状态存储（简化实现，实际应该使用数据库或 Redis）
workflows = {}


def call_llm(query: str, temperature: float = 0.7) -> str:
    """调用大模型生成响应"""
    try:
        client = get_openai_client()
        if not client:
            return "抱歉，LLM 服务暂时不可用，请检查 API Key 配置。"
        
        # 直接调用大模型
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": "你是一个智能助手，能够帮助用户解答问题、分析信息和提供建议。请用简洁、清晰的方式回答。"},
                {"role": "user", "content": query}
            ],
            temperature=temperature,
            max_tokens=config.LLM_MAX_TOKENS
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.exception(f"Error calling LLM: {e}")
        return f"抱歉，处理您的请求时出现错误：{str(e)}"


@agent_bp.route('/chat', methods=['POST'])
@auth_required
def chat():
    """智能对话接口（非流式）- 直接调用大模型"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return convert_resp(code=400, status=400, message="缺少 query 参数")
        
        query = data['query']
        session_id = data.get('session_id') or str(uuid.uuid4())
        workflow_id = str(uuid.uuid4())
        temperature = data.get('temperature', 0.7)
        
        logger.info(f"Processing chat query: {query}, session: {session_id}")
        
        # 调用大模型
        llm_response = call_llm(query, temperature)
        
        # 构建响应
        response = {
            "success": True,
            "workflow_id": workflow_id,
            "session_id": session_id,
            "query": query,
            "response": llm_response,
            "timestamp": datetime.now().isoformat(),
            "model": config.LLM_MODEL
        }
        
        # 保存工作流状态
        workflows[workflow_id] = {
            "query": query,
            "session_id": session_id,
            "status": "completed",
            "result": response,
            "created_at": datetime.now().isoformat()
        }
        
        return convert_resp(data=response)
        
    except Exception as e:
        logger.exception(f"Error in chat: {e}")
        return convert_resp(code=500, status=500, message=f"对话失败: {str(e)}")


@agent_bp.route('/chat/stream', methods=['POST'])
@auth_required
def chat_stream():
    """智能对话接口（流式）- 直接调用大模型流式API"""
    
    def generate():
        try:
            data = request.get_json()
            
            if not data or 'query' not in data:
                yield f"data: {json.dumps({'type': 'error', 'content': '缺少 query 参数'}, ensure_ascii=False)}\n\n"
                return
            
            query = data['query']
            session_id = data.get('session_id') or str(uuid.uuid4())
            workflow_id = str(uuid.uuid4())
            temperature = data.get('temperature', 0.7)
            
            logger.info(f"Processing stream chat query: {query}, session: {session_id}")
            
            # 发送会话开始事件
            yield f"data: {json.dumps({'type': 'start', 'session_id': session_id, 'workflow_id': workflow_id, 'model': config.LLM_MODEL}, ensure_ascii=False)}\n\n"
            
            # 调用大模型流式API
            client = get_openai_client()
            if not client:
                yield f"data: {json.dumps({'type': 'error', 'content': 'LLM 服务不可用'}, ensure_ascii=False)}\n\n"
                return
            
            # 流式调用
            stream = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个智能助手，能够帮助用户解答问题、分析信息和提供建议。请用简洁、清晰的方式回答。"},
                    {"role": "user", "content": query}
                ],
                temperature=temperature,
                max_tokens=config.LLM_MAX_TOKENS,
                stream=True
            )
            
            # 流式输出每个 token
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    
                    event = {
                        "type": "content",
                        "content": content,
                        "workflow_id": workflow_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            
            # 发送完成事件
            yield f"data: {json.dumps({'type': 'done', 'workflow_id': workflow_id, 'full_response': full_response}, ensure_ascii=False)}\n\n"
            
            # 保存工作流状态
            workflows[workflow_id] = {
                "query": query,
                "session_id": session_id,
                "status": "completed",
                "response": full_response,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.exception(f"Error in stream chat: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


@agent_bp.route('/resume/<workflow_id>', methods=['POST'])
@auth_required
def resume_workflow(workflow_id):
    """恢复工作流"""
    try:
        data = request.get_json() or {}
        user_input = data.get('user_input')
        
        # 检查工作流是否存在
        if workflow_id not in workflows:
            return convert_resp(code=404, status=404, message="工作流不存在")
        
        workflow = workflows[workflow_id]
        
        logger.info(f"Resuming workflow: {workflow_id}, input: {user_input}")
        
        # 更新工作流状态
        workflow['status'] = 'resumed'
        workflow['resumed_at'] = datetime.now().isoformat()
        workflow['user_input'] = user_input
        
        # 生成新的响应
        query = workflow.get('query', '')
        session_id = workflow.get('session_id', '')
        response = generate_mock_response(f"{query} (resumed with: {user_input})", session_id)
        
        workflow['result'] = response
        workflow['status'] = 'completed'
        
        return convert_resp(data=response)
        
    except Exception as e:
        logger.exception(f"Error resuming workflow: {e}")
        return convert_resp(code=500, status=500, message=f"恢复工作流失败: {str(e)}")


@agent_bp.route('/state/<workflow_id>', methods=['GET'])
@auth_required
def get_workflow_state(workflow_id):
    """获取工作流状态"""
    try:
        if workflow_id not in workflows:
            return convert_resp(
                code=404,
                status=404,
                message="工作流不存在",
                data={"success": False}
            )
        
        workflow = workflows[workflow_id]
        
        return convert_resp(
            data={
                "success": True,
                "state": workflow
            }
        )
        
    except Exception as e:
        logger.exception(f"Error getting workflow state: {e}")
        return convert_resp(code=500, status=500, message=f"获取工作流状态失败: {str(e)}")


@agent_bp.route('/cancel/<workflow_id>', methods=['DELETE'])
@auth_required
def cancel_workflow(workflow_id):
    """取消工作流"""
    try:
        if workflow_id not in workflows:
            return convert_resp(
                code=404,
                status=404,
                message="工作流不存在",
                data={"success": False}
            )
        
        # 更新工作流状态
        workflows[workflow_id]['status'] = 'cancelled'
        workflows[workflow_id]['cancelled_at'] = datetime.now().isoformat()
        
        logger.info(f"Cancelled workflow: {workflow_id}")
        
        return convert_resp(
            data={
                "success": True,
                "message": f"工作流 {workflow_id} 已取消"
            }
        )
        
    except Exception as e:
        logger.exception(f"Error cancelling workflow: {e}")
        return convert_resp(code=500, status=500, message=f"取消工作流失败: {str(e)}")


@agent_bp.route('/test', methods=['GET'])
@auth_required
def test_agent():
    """测试智能代理"""
    try:
        # 执行简单的测试查询
        test_query = "Hello, test the system"
        session_id = str(uuid.uuid4())
        
        response = generate_mock_response(test_query, session_id)
        
        logger.info("Agent test successful")
        
        return convert_resp(
            data={
                "success": True,
                "message": "智能代理运行正常",
                "test_response": response
            }
        )
        
    except Exception as e:
        logger.exception(f"Error testing agent: {e}")
        return convert_resp(
            code=500,
            status=500,
            message=f"测试失败: {str(e)}",
            data={"success": False}
        )
