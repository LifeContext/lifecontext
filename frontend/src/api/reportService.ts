import type { DailyReport } from '../../types';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Daily Report API服务类
export class ReportService {
  // 获取所有Daily Reports
  async getReports(): Promise<DailyReport[]> {
    try {
      const response = await fetch(`/api/generation/daily-feed`);
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
