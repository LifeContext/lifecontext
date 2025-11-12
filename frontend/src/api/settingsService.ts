export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export interface Settings {
  tips_interval_minutes: number;
  todo_interval_minutes: number;
  daily_report_hour: number;
  daily_report_minute: number;
  excluded_domains?: string[];
}

interface UrlBlacklistItem {
  id: number;
  url: string;
  create_time?: string;
}

// Settings API服务类
export class SettingsService {
  // 获取设置
  async getSettings(): Promise<Settings> {
    try {
      const response = await fetch('/api/settings', {
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
      const response = await fetch('/api/settings', {
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

  async getExcludedDomains(): Promise<string[]> {
    try {
      const response = await fetch('/api/url-blacklist', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch excluded domains: ${response.statusText}`);
      }

      const data: unknown = await response.json();

      if (Array.isArray(data)) {
        return data
      }

      return [];
    } catch (error) {
      console.error('Error fetching excluded domains:', error);
      throw error;
    }
  }

  async createExcludedDomain(url: string): Promise<UrlBlacklistItem> {
    try {
      const response = await fetch('/api/url-blacklist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Failed to create excluded domain: ${response.statusText}`);
      }

      const data: unknown = await response.json();
      if (data && typeof data === 'object') {
        const item = data as Partial<UrlBlacklistItem>;
        if (typeof item.url === 'string') {
          return {
            id: typeof item.id === 'number' ? item.id : Date.now(),
            url: item.url,
            create_time: item.create_time
          };
        }
      }

      if (typeof data === 'string') {
        return {
          id: Date.now(),
          url: data
        };
      }

      throw new Error('Invalid response when creating excluded domain');
    } catch (error) {
      console.error('Error creating excluded domain:', error);
      throw error;
    }
  }

  async deleteExcludedDomain(id: number): Promise<void> {
    try {
      const response = await fetch(`/api/url-blacklist/${id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Failed to delete excluded domain: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error deleting excluded domain:', error);
      throw error;
    }
  }
}

// 导出服务实例
export const settingsService = new SettingsService();
