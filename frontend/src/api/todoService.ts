import type { TodoItem } from '../../types';

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
  async addTodo(
    text: string,
    priority: 'low' | 'medium' | 'high',
    options?: { description?: string; startTime?: string; endTime?: string }
  ): Promise<TodoItem> {
    try {
      // 前端优先级与后端优先级(数值)映射
      const priorityMap = { low: 1, medium: 2, high: 3 } as const;

      const payload: Record<string, unknown> = {
        title: text,
        description: options?.description ?? text,
        priority: priorityMap[priority]
      };

      if (options?.startTime) payload.start_time = options.startTime;
      if (options?.endTime) payload.end_time = options.endTime;
      const response = await fetch(`/api/generation/todos`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error Response:', errorText);
        throw new Error(`Failed to add todo: ${response.statusText} - ${errorText}`);
      }

      const json = await response.json();
      // 兼容不同返回结构，尽量规范化为 TodoItem
      const created: any = (json && (json.data?.todo ?? json.data ?? json)) ?? {};

      const normalized: TodoItem = {
        id: created.id ?? created.todo_id ?? 0,
        description: created.description ?? created.title ?? text,
        status: Boolean(
          created.status === true ||
          created.status === 1 ||
          created.completed === true
        ),
        priority: (created.priority as number) ?? priorityMap[priority]
      };

      return normalized;
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
  async updateTodo(id: number, text: string, priority: 'low' | 'medium' | 'high'): Promise<{ id: number; description: string; priority: number; }> {
    try {
      // 将前端优先级 low/medium/high 映射为后端数值 1/2/3
      const priorityMap = { low: 1, medium: 2, high: 3 } as const;
      const payload: Record<string, unknown> = {
        description: text,
        priority: priorityMap[priority]
      };

      const response = await fetch(`/api/generation/todos/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to update todo: ${response.statusText} - ${errorText}`);
      }

      return {
        id,
        description: text,
        priority: priorityMap[priority]
      };
    } catch (error) {
      console.error('Error updating todo:', error);
      throw error;
    }
  }

  // 删除Todo项
  async deleteTodo(id: number): Promise<void> {
    try {
      const response = await fetch(`/api/generation/todos/${id}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to delete todo: ${response.statusText} - ${errorText}`);
      }
    } catch (error) {
      console.error('Error deleting todo:', error);
      throw error;
    }
  }
}

// 导出服务实例
export const todoService = new TodoService();