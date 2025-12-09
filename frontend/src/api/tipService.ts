import type { Tip } from '../../types';

// Tip API服务类
export class TipService {
  // 获取所有Tips
  async getTips(): Promise<Tip[]> {
    try {
      const response = await fetch(`/api/generation/tips?limit=100`);
      if (!response.ok) {
        throw new Error(`Failed to fetch tips: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching tips:', error);
      throw error;
    }
  }

  // 根据ID获取单个Tip（注意：后端暂未实现此接口）
  async getTipById(id: number): Promise<Tip> {
    try {
      const response = await fetch(`/api/generation/tips/${id}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch tip: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching tip:', error);
      throw error;
    }
  }

  // 创建新的Tip（注意：后端暂未实现此接口，请使用 /api/generation/generate/tips）
  async createTip(tip: Omit<Tip, 'id' | 'created_at'>): Promise<Tip> {
    try {
      const response = await fetch(`/api/generation/tips`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(tip)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create tip: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating tip:', error);
      throw error;
    }
  }

  // 更新Tip（注意：后端暂未实现此接口）
  async updateTip(id: number, tip: Partial<Tip>): Promise<Tip> {
    try {
      const response = await fetch(`/api/generation/tips/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(tip)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to update tip: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error updating tip:', error);
      throw error;
    }
  }

  // 删除Tip（注意：后端暂未实现此接口）
  async deleteTip(id: number): Promise<void> {
    try {
      const response = await fetch(`/api/generation/tips/${id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete tip: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error deleting tip:', error);
      throw error;
    }
  }
}

// 导出服务实例
export const tipService = new TipService();
