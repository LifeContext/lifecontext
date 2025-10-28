import type { ChatMessage } from '../../types';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// 聊天API服务类
export class ChatService {
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

  // 获取聊天历史（如果需要的话）
  async getChatHistory(): Promise<ChatMessage[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/history`);
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
