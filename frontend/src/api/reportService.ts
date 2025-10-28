import type { DailyReport } from '../../types';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Daily Report API服务类
export class ReportService {
  // 获取所有Daily Reports
  async getReports(): Promise<DailyReport[]> {
    try {
      const response = await fetch(`/api/generation/reports?limit=100`);
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

  // 根据ID获取单个报告
  async getReportById(id: number): Promise<DailyReport> {
    try {
      const response = await fetch(`/api/debug/reports/${id}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch report: ${response.statusText}`);
      }
      const data = await response.json();
      return data.data.report || data.report || data;
    } catch (error) {
      console.error('Error fetching report:', error);
      throw error;
    }
  }

  // 创建新的报告
  async createReport(report: Omit<DailyReport, 'id'>): Promise<DailyReport> {
    try {
      const response = await fetch(`${API_BASE_URL}/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(report)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create report: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating report:', error);
      throw error;
    }
  }

  // 更新报告
  async updateReport(id: number, report: Partial<DailyReport>): Promise<DailyReport> {
    try {
      const response = await fetch(`${API_BASE_URL}/reports/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(report)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to update report: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error updating report:', error);
      throw error;
    }
  }

  // 删除报告
  async deleteReport(id: number): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/reports/${id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete report: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error deleting report:', error);
      throw error;
    }
  }
}

// 导出服务实例
export const reportService = new ReportService();
