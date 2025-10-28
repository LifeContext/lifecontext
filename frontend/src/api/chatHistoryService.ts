import type { ChatSession, ChatMessage } from '../../types';

// 聊天历史API服务类
export class ChatHistoryService {
  private readonly STORAGE_KEY = 'chat_sessions';

  // 保存聊天会话到本地存储
  saveChatSession(messages: ChatMessage[]): void {
    if (messages.length === 0) return;

    try {
      // 获取现有的聊天会话
      const existingSessions = this.getChatSessions();
      
      // 创建新的会话
      const newSession: ChatSession = {
        id: Date.now(), // 使用时间戳作为ID
        title: this.generateSessionTitle(messages),
        createdAt: new Date().toISOString(),
        messages: [...messages] // 复制消息数组
      };

      // 将会话添加到列表的开头
      existingSessions.unshift(newSession);

      // 限制保存的会话数量（最多保存50个会话）
      const maxSessions = 50;
      if (existingSessions.length > maxSessions) {
        existingSessions.splice(maxSessions);
      }

      // 保存到本地存储
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(existingSessions));
      
      console.log('聊天会话已保存:', newSession.title);
    } catch (error) {
      console.error('保存聊天会话失败:', error);
    }
  }

  // 获取所有聊天会话
  getChatSessions(): ChatSession[] {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.error('获取聊天会话失败:', error);
      return [];
    }
  }

  // 根据ID获取特定会话
  getChatSessionById(id: number): ChatSession | null {
    const sessions = this.getChatSessions();
    return sessions.find(session => session.id === id) || null;
  }

  // 删除聊天会话
  deleteChatSession(id: number): void {
    try {
      const sessions = this.getChatSessions();
      const filteredSessions = sessions.filter(session => session.id !== id);
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(filteredSessions));
      console.log('聊天会话已删除:', id);
    } catch (error) {
      console.error('删除聊天会话失败:', error);
    }
  }

  // 清空所有聊天会话
  clearAllSessions(): void {
    try {
      localStorage.removeItem(this.STORAGE_KEY);
      console.log('所有聊天会话已清空');
    } catch (error) {
      console.error('清空聊天会话失败:', error);
    }
  }

  // 生成会话标题（基于前几条消息）
  private generateSessionTitle(messages: ChatMessage[]): string {
    if (messages.length === 0) return '新对话';

    // 获取用户的第一条消息作为标题
    const firstUserMessage = messages.find(msg => msg.sender === 'user');
    if (firstUserMessage) {
      const content = firstUserMessage.content;
      // 限制标题长度
      return content.length > 30 ? content.substring(0, 30) + '...' : content;
    }

    // 如果没有用户消息，使用时间戳
    return `对话 ${new Date().toLocaleString('zh-CN')}`;
  }

  // 导出聊天会话数据
  exportChatSessions(): string {
    const sessions = this.getChatSessions();
    return JSON.stringify(sessions, null, 2);
  }

  // 导入聊天会话数据
  importChatSessions(data: string): boolean {
    try {
      const sessions = JSON.parse(data);
      if (Array.isArray(sessions)) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(sessions));
        console.log('聊天会话已导入');
        return true;
      }
      return false;
    } catch (error) {
      console.error('导入聊天会话失败:', error);
      return false;
    }
  }
}

// 导出服务实例
export const chatHistoryService = new ChatHistoryService();
