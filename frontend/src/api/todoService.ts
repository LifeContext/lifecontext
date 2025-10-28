import type { TodoItem } from '../../types';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Todo API服务类
export class TodoService {
  // 获取所有Todo项
  async getTodos(): Promise<TodoItem[]> {
    try {
      const response = await fetch(`/api/generation/todos?limit=100`);
      if (!response.ok) {
        throw new Error(`Failed to fetch todos: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching todos:', error);
      throw error;
    }
  }

  // 添加新的Todo项
  async addTodo(text: string, priority: 'low' | 'medium' | 'high'): Promise<TodoItem> {
    try {
      const response = await fetch(`${API_BASE_URL}/todos`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: text, urgency: priority, status: false })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to add todo: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error adding todo:', error);
      throw error;
    }
  }

  // 更新Todo项的完成状态
  async toggleTodo(id: number, status: boolean): Promise<TodoItem> {
    try {
      const statusInt = status ? 1 : 0;
      const requestBody = {
        status: statusInt
      };
      const url = `/api/generation/todos/${id}`;
      const response = await fetch(url, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error Response:', errorText);
        throw new Error(`Failed to toggle todo: ${response.statusText} - ${errorText}`);
      }
      
      // API 只返回成功消息，不返回更新后的数据
      const responseData = await response.json();
      return {
        id: id,
        status: status
      };
    } catch (error) {
      console.error('Error toggling todo:', error);
      throw error;
    }
  }

  // 更新Todo项的内容
  async updateTodo(id: number, text: string, priority: 'low' | 'medium' | 'high'): Promise<TodoItem> {
    try {
      const response = await fetch(`${API_BASE_URL}/todos/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: text, urgency: priority })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to update todo: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error updating todo:', error);
      throw error;
    }
  }

  // 删除Todo项
  async deleteTodo(id: number): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/todos/${id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete todo: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error deleting todo:', error);
      throw error;
    }
  }
}

// 导出服务实例
export const todoService = new TodoService();