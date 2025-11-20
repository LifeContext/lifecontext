import type { DailyReport } from '../../types';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Daily Report API服务类
export class ReportService {
  // 获取所有Daily Reports
  async getReports(date?: string): Promise<DailyReport[]> {
    try {
      const targetDate = date ?? new Date().toISOString().split('T')[0];
      const response = await fetch(`/api/generation/daily-feed?date=${targetDate}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch reports: ${response.statusText}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching reports:', error);
      throw error;
    }
  }
}

// 导出服务实例
export const reportService = new ReportService();
