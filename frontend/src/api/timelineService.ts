import type { TimelineItem, TimelineSegment } from '../../types';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Timeline API服务类
export class TimelineService {
  // 获取指定日期的Timeline数据
  async getTimelineByDate(date: string): Promise<TimelineSegment[]> {
    try {
      const response = await fetch(`/api/generation/activities`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch timeline data: ${response.statusText}`);
      }
      
      const data = await response.json();
      const activities: TimelineItem[] = data.data.activities || [];
      
      // 根据日期过滤活动
      const filteredActivities = this.filterActivitiesByDate(activities, date);
      
      // 每个activity作为独立的segment
      return this.createIndividualSegments(filteredActivities);
    } catch (error) {
      console.error('Error fetching timeline data:', error);
      return [];
    }
  }

  // 获取所有可用的日期选项
  async getAvailableDates(): Promise<{ label: string; value: string }[]> {
    try {
      const response = await fetch(`/api/debug/activities`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch available dates: ${response.statusText}`);
      }
      
      const data = await response.json();
      const activities: TimelineItem[] = data.data.activities || [];
      
      // 从活动中提取唯一日期
      return this.extractAvailableDates(activities);
    } catch (error) {
      console.error('Error fetching available dates:', error);
      return [
        { label: 'Today', value: 'today' },
        { label: 'Yesterday', value: 'yesterday' }
      ];
    }
  }

  // 清除指定时间范围的历史记录
  async clearHistory(type: '24h' | 'all'): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/timeline/clear`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ type })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to clear history: ${response.statusText}`);
      }
      
      return true;
    } catch (error) {
      console.error('Error clearing history:', error);
      return false;
    }
  }

  // 获取Timeline活动详情
  async getTimelineItemDetails(itemId: number): Promise<TimelineItem | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/timeline/item/${itemId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch timeline item: ${response.statusText}`);
      }
      
      const data = await response.json();
      return data.item || null;
    } catch (error) {
      console.error('Error fetching timeline item:', error);
      return null;
    }
  }

  // 根据日期过滤活动
  private filterActivitiesByDate(activities: TimelineItem[], date: string): TimelineItem[] {
    const now = new Date();
    let targetDate: Date;

    switch (date) {
      case 'today':
        targetDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        break;
      case 'yesterday':
        targetDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
        break;
      default:
        // 处理其他日期格式
        targetDate = new Date(date);
        break;
    }

    const nextDay = new Date(targetDate);
    nextDay.setDate(targetDate.getDate() + 1);

    return activities.filter(activity => {
      const activityDate = new Date(activity.timestamp);
      return activityDate >= targetDate && activityDate < nextDay;
    });
  }

  // 创建独立的segments，每个activity作为一个segment
  private createIndividualSegments(activities: TimelineItem[]): TimelineSegment[] {
    if (activities.length === 0) return [];

    // 按时间排序
    const sortedActivities = activities.sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    const segments: TimelineSegment[] = [];
    let segmentId = 1;

    for (const activity of sortedActivities) {
      const activityTime = new Date(activity.timestamp);
      const timeString = activityTime.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      });

      // TimelineSegment 对应一个 activity（来自后端）
      // TimelineItem 对应 activity 中的小活动（模拟数据）
      const segment: TimelineSegment = {
        id: segmentId++,
        title: activity.title, // TimelineSegment的标题来自activity
        start_time: timeString, // TimelineSegment的时间来自activity
        activities: this.generateSubActivitiesForSegment(activity) // 生成模拟的TimelineItem小活动
      };

      segments.push(segment);
    }

    return segments;
  }



  // 为TimelineSegment生成模拟的TimelineItem小活动数据
  private generateSubActivitiesForSegment(activity: TimelineItem): TimelineItem[] {
    const domain = activity.domain.toLowerCase();
    const subActivities: TimelineItem[] = [];
    
    // 根据主activity的域名类型，生成相关的TimelineItem小活动
    if (domain.includes('github') || domain.includes('gitlab')) {
      // 代码开发相关的TimelineItem小活动
      subActivities.push(
        {
          id: Math.random() * 1000,
          timestamp: activity.timestamp,
          url: 'https://github.com/features/copilot',
          domain: 'github.com',
          title: 'GitHub Copilot · Your AI pair programmer',
          thumbnailUrl: ''
        },
        {
          id: Math.random() * 1000,
          timestamp: new Date(new Date(activity.timestamp).getTime() + 2 * 60 * 1000).toISOString(),
          url: 'https://stackoverflow.com/questions/5623838/rgb-to-hex-and-hex-to-rgb',
          domain: 'stackoverflow.com',
          title: 'Convert RGB to Hex and vice-versa',
          thumbnailUrl: ''
        },
        {
          id: Math.random() * 1000,
          timestamp: new Date(new Date(activity.timestamp).getTime() + 5 * 60 * 1000).toISOString(),
          url: 'https://developer.mozilla.org/en-US/docs/Web/API/Node/contains',
          domain: 'developer.mozilla.org',
          title: 'Node.contains() - Web APIs | MDN',
          thumbnailUrl: ''
        }
      );
    } else if (domain.includes('figma') || domain.includes('dribbble') || domain.includes('behance')) {
      // 设计工作相关的TimelineItem小活动
      subActivities.push(
        {
          id: Math.random() * 1000,
          timestamp: activity.timestamp,
          url: 'https://www.figma.com/community',
          domain: 'figma.com',
          title: 'Figma Community - Home',
          thumbnailUrl: ''
        },
        {
          id: Math.random() * 1000,
          timestamp: new Date(new Date(activity.timestamp).getTime() + 3 * 60 * 1000).toISOString(),
          url: 'https://m3.material.io/',
          domain: 'm3.material.io',
          title: 'Material Design',
          thumbnailUrl: ''
        },
        {
          id: Math.random() * 1000,
          timestamp: new Date(new Date(activity.timestamp).getTime() + 8 * 60 * 1000).toISOString(),
          url: 'https://dribbble.com/',
          domain: 'dribbble.com',
          title: 'Dribbble - Discover the World\'s Top Designers',
          thumbnailUrl: ''
        },
        {
          id: Math.random() * 1000,
          timestamp: new Date(new Date(activity.timestamp).getTime() + 12 * 60 * 1000).toISOString(),
          url: 'https://coolors.co/',
          domain: 'coolors.co',
          title: 'Coolors - The super fast color schemes generator',
          thumbnailUrl: ''
        }
      );
    } else if (domain.includes('stackoverflow') || domain.includes('developer.mozilla')) {
      // 技术学习相关的TimelineItem小活动
      subActivities.push(
        {
          id: Math.random() * 1000,
          timestamp: activity.timestamp,
          url: 'https://react.dev/learn',
          domain: 'react.dev',
          title: 'Learn React - Quick Start',
          thumbnailUrl: ''
        },
        {
          id: Math.random() * 1000,
          timestamp: new Date(new Date(activity.timestamp).getTime() + 2 * 60 * 1000).toISOString(),
          url: 'https://tailwindcss.com/docs/installation',
          domain: 'tailwindcss.com',
          title: 'Installation: Tailwind CSS',
          thumbnailUrl: ''
        },
        {
          id: Math.random() * 1000,
          timestamp: new Date(new Date(activity.timestamp).getTime() + 5 * 60 * 1000).toISOString(),
          url: 'https://vitejs.dev/',
          domain: 'vitejs.dev',
          title: 'Vite | Next Generation Frontend Tooling',
          thumbnailUrl: ''
        }
      );
    } else if (domain.includes('trello') || domain.includes('asana') || domain.includes('notion')) {
      // 项目管理相关的TimelineItem小活动
      subActivities.push(
        {
          id: Math.random() * 1000,
          timestamp: activity.timestamp,
          url: 'https://trello.com/',
          domain: 'trello.com',
          title: 'Trello | Bring everyone together and move projects forward.',
          thumbnailUrl: ''
        },
        {
          id: Math.random() * 1000,
          timestamp: new Date(new Date(activity.timestamp).getTime() + 3 * 60 * 1000).toISOString(),
          url: 'https://asana.com/',
          domain: 'asana.com',
          title: 'Asana - Organize team work',
          thumbnailUrl: ''
        }
      );
    } else if (domain.includes('youtube') || domain.includes('vimeo')) {
      // 视频学习相关的TimelineItem小活动
      subActivities.push(
        {
          id: Math.random() * 1000,
          timestamp: activity.timestamp,
          url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
          domain: 'youtube.com',
          title: 'Learn Programming - Complete Course',
          thumbnailUrl: ''
        },
        {
          id: Math.random() * 1000,
          timestamp: new Date(new Date(activity.timestamp).getTime() + 5 * 60 * 1000).toISOString(),
          url: 'https://www.youtube.com/watch?v=example',
          domain: 'youtube.com',
          title: 'Advanced React Patterns',
          thumbnailUrl: ''
        }
      );
    } else {
      // 其他网络浏览相关的TimelineItem小活动
      subActivities.push(
        {
          id: Math.random() * 1000,
          timestamp: activity.timestamp,
          url: activity.url,
          domain: activity.domain,
          title: activity.title,
          thumbnailUrl: ''
        },
        {
          id: Math.random() * 1000,
          timestamp: new Date(new Date(activity.timestamp).getTime() + 2 * 60 * 1000).toISOString(),
          url: 'https://www.google.com/search?q=related+topics',
          domain: 'google.com',
          title: 'Related topics search',
          thumbnailUrl: ''
        },
        {
          id: Math.random() * 1000,
          timestamp: new Date(new Date(activity.timestamp).getTime() + 5 * 60 * 1000).toISOString(),
          url: 'https://en.wikipedia.org/wiki/example',
          domain: 'wikipedia.org',
          title: 'Wikipedia - Example Article',
          thumbnailUrl: ''
        }
      );
    }

    return subActivities;
  }

  // 从活动中提取可用日期
  private extractAvailableDates(activities: TimelineItem[]): { label: string; value: string }[] {
    const dateMap = new Map<string, string>();
    const now = new Date();
    
    for (const activity of activities) {
      const activityDate = new Date(activity.timestamp);
      const dateKey = activityDate.toDateString();
      
      if (!dateMap.has(dateKey)) {
        const isToday = activityDate.toDateString() === now.toDateString();
        const isYesterday = activityDate.toDateString() === new Date(now.getTime() - 24 * 60 * 60 * 1000).toDateString();
        
        let label: string;
        let value: string;
        
        if (isToday) {
          label = 'Today';
          value = 'today';
        } else if (isYesterday) {
          label = 'Yesterday';
          value = 'yesterday';
        } else {
          label = activityDate.toLocaleDateString('zh-CN', { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric' 
          });
          value = activityDate.toISOString().split('T')[0];
        }
        
        dateMap.set(dateKey, JSON.stringify({ label, value }));
      }
    }
    
    return Array.from(dateMap.values()).map(item => JSON.parse(item));
  }
}

// 导出服务实例
export const timelineService = new TimelineService();
