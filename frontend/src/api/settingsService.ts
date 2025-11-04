export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export interface Settings {
  tips_interval_minutes: number;
  daily_report_hour: number;
  daily_report_minute: number;
}

// Settings API服务类
export class SettingsService {
  // 获取设置
  async getSettings(): Promise<Settings> {
    try {
      const response = await fetch(`/api/settings`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch settings: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching settings:', error);
      throw error;
    }
  }

  // 更新设置
  async updateSettings(settings: Partial<Settings>): Promise<Settings> {
    try {
      const response = await fetch(`/api/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: response.statusText }));
        throw new Error(errorData.error || `Failed to update settings: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error updating settings:', error);
      throw error;
    }
  }
}

// 导出服务实例
export const settingsService = new SettingsService();

