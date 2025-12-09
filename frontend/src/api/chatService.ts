import type { ChatMessage } from '../../types';

// 聊天API服务类
export class ChatService {
  async sendMessageStream(
    message: string,
    workflowId?: string,
    handlers: {
      onToken?: (token: string) => void;
      onWorkflowId?: (workflowId: string) => void;
      onPromptOptimized?: (payload: Record<string, unknown>) => void;
    } = {},
    extraPayload: Record<string, unknown> = {}
  ): Promise<ChatMessage> {
    try {
      const requestBody = {
        query: message,
        workflow_id: workflowId || null,
        ...extraPayload
      };
      const response = await fetch(`/api/agent/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream'
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Failed to send message: ${response.statusText} - ${errorData}`);
      }

      if (!response.body) {
        const data = await response.json();
        const content = data?.data?.response || '抱歉，我无法理解您的问题。';
        const finalMessage: ChatMessage = {
          workflow_id: data?.data?.workflow_id || '',
          content,
          sender: 'ai',
          timestamp: new Date().toISOString()
        };
        if (finalMessage.workflow_id) {
          handlers.onWorkflowId?.(finalMessage.workflow_id);
        }
        handlers.onToken?.(content);
        return finalMessage;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let accumulatedContent = '';
      let workflowIdFromStream = workflowId || '';
      let isDone = false;

      while (!isDone) {
        const { value, done } = await reader.read();
        if (done) {
          isDone = true;
          break;
        }
        if (!value) continue;

        buffer += decoder.decode(value, { stream: true });
        const segments = buffer.split('\n\n');
        buffer = segments.pop() ?? '';

        for (const segment of segments) {
          const line = segment.trim();
          if (!line) continue;

          if (line === '[DONE]') {
            isDone = true;
            break;
          }

          let dataString = line;
          if (dataString.startsWith('data:')) {
            dataString = dataString.replace(/^data:\s*/, '');
          }

          if (!dataString) continue;

          let token = '';
          try {
            const payload = JSON.parse(dataString);
            if (payload?.error) {
              throw new Error(payload.error);
            }
            if (payload?.workflow_id) {
              workflowIdFromStream = payload.workflow_id;
              handlers.onWorkflowId?.(workflowIdFromStream);
            }

            const payloadType = payload?.type;
            if (payloadType === 'prompt_optimized') {
              handlers.onPromptOptimized?.(payload);
              continue;
            }
            if (payloadType === 'start') {
              if (payload?.workflow_id) {
                workflowIdFromStream = payload.workflow_id;
                handlers.onWorkflowId?.(workflowIdFromStream);
              }
            } else if (payloadType === 'content') {
              token = payload?.content ?? '';
            } else if (payloadType === 'done') {
              const fullResponse = payload?.full_response;
              if (typeof fullResponse === 'string' && fullResponse.length > 0) {
                accumulatedContent = fullResponse;
              }
              isDone = true;
            } else if (payloadType === 'tool_complete') {
              // ignore, used for bookkeeping
            } else {
              if (payload?.delta !== undefined) {
                token = payload.delta;
              } else if (payload?.content !== undefined) {
                token = payload.content;
              } else if (payload?.token !== undefined) {
                token = payload.token;
              }
              if (payload?.done === true || payload?.event === 'end' || payloadType === 'end') {
                isDone = true;
              }
            }
          } catch (err) {
            token = dataString;
          }

          if (token) {
            accumulatedContent += token;
            handlers.onToken?.(token);
          }
        }
      }

      if (buffer.trim()) {
        const remaining = buffer.trim();
        if (remaining !== '[DONE]') {
          try {
            const payload = JSON.parse(remaining);
            if (payload?.workflow_id && !workflowIdFromStream) {
              workflowIdFromStream = payload.workflow_id;
              handlers.onWorkflowId?.(workflowIdFromStream);
            }
            if (payload?.type === 'done') {
              const fullResponse = payload?.full_response;
              if (typeof fullResponse === 'string' && fullResponse.length > 0) {
                accumulatedContent = fullResponse;
              }
            } else {
              const token =
                payload?.delta ?? payload?.content ?? payload?.token ?? '';
              if (token) {
                accumulatedContent += token;
                handlers.onToken?.(token);
              }
            }
          } catch {
            accumulatedContent += remaining;
            handlers.onToken?.(remaining);
          }
        }
      }

      const finalMessage: ChatMessage = {
        workflow_id: workflowIdFromStream,
        content: accumulatedContent || '抱歉，我无法理解您的问题。',
        sender: 'ai',
        timestamp: new Date().toISOString()
      };

      if (!finalMessage.workflow_id) {
        handlers.onWorkflowId?.('');
      }

      return finalMessage;
    } catch (error) {
      console.error('Error sending message:', error);
      return {
        workflow_id: '',
        content: '抱歉，连接服务器时出现错误。请稍后再试。',
        sender: 'ai',
        timestamp: new Date().toISOString()
      };
    }
  }

  // 发送消息到后端并获取AI回复
  async sendMessage(message: string, workflowId?: string): Promise<ChatMessage> {
    try {
      const requestBody = {
        query: message,
        workflow_id: workflowId || null
      };
      const response = await fetch(`/api/agent/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });
      if (!response.ok) {
        // 获取更详细的错误信息
        const errorData = await response.text();
        throw new Error(`Failed to send message: ${response.statusText} - ${errorData}`);
      }
      const data = await response.json();

      // 处理API响应格式
      let content = '抱歉，我无法理解您的问题。';
      const contentOutput = data.data.response;
      if (contentOutput) {
        content = contentOutput;
      }
      return {
        workflow_id: data.data.workflow_id || '',
        content: content,
        sender: 'ai',
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('Error sending message:', error);
      // 返回错误消息
      return {
        workflow_id: '',
        content: '抱歉，连接服务器时出现错误。请稍后再试。',
        sender: 'ai',
        timestamp: new Date().toISOString()
      };
    }
  }

  // 获取聊天历史（注意：后端暂未实现此接口，聊天历史保存在本地 localStorage）
  async getChatHistory(): Promise<ChatMessage[]> {
    try {
      const response = await fetch(`/api/agent/chat/history`);
      if (!response.ok) {
        throw new Error(`Failed to fetch chat history: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching chat history:', error);
      return [];
    }
  }
}

// 导出服务实例
export const chatService = new ChatService();
