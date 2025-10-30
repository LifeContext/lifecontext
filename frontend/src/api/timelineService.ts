import type { TimelineItem, TimelineSegment } from '../../types';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export class TimelineService {
  async getTimelineSegments(): Promise<TimelineSegment[]> {
    try {
      const response = await fetch(`/api/generation/activities?limit=100`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch timeline data: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching timeline data:', error);
      return [];
    }
  }
}
// 导出服务实例
export const timelineService = new TimelineService();
