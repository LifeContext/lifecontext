/**
 * 数据刷新管理器 - 根据事件类型自动刷新对应数据
 */

import { todoService } from '../api/todoService';
import { reportService } from '../api/reportService';
import { tipService } from '../api/tipService';
import { timelineService } from '../api/timelineService';
import type { EventData } from '../api/eventService';
import type { TodoItem, DailyReport, Tip } from '../../types';

export interface DataRefreshCallbacks {
  onTodosUpdate: (todos: TodoItem[]) => void;
  onReportsUpdate: (reports: DailyReport[]) => void;
  onTipsUpdate: (tips: Tip[]) => void;
  onTimelineUpdate: (activities: any[]) => void;
  onError: (error: string, dataType: string) => void;
}

export class DataRefreshManager {
  private callbacks: DataRefreshCallbacks | null = null;

  /**
   * 设置回调函数
   */
  setCallbacks(callbacks: DataRefreshCallbacks): void {
    this.callbacks = callbacks;
  }

  /**
   * 处理事件并刷新对应数据
   */
  async handleEvent(event: EventData): Promise<void> {
    console.log(`数据刷新管理器处理事件: ${event.type}`);

    switch (event.type) {
      case 'todo':
        await this.refreshTodos(event);
        break;
      case 'report':
        await this.refreshReports(event);
        break;
      case 'tip':
        await this.refreshTips(event);
        break;
      case 'activity':
        await this.refreshTimeline(event);
        break;
      default:
        console.warn(`未知的事件类型: ${event.type}`);
    }
  }

  /**
   * 刷新待办事项数据
   */
  private async refreshTodos(event: EventData): Promise<void> {
    try {
      console.log('刷新待办事项数据...');
      const response = await todoService.getTodos();
      const todos = (response as any)?.data?.todos ?? (response as any)?.todos ?? [];
      
      if (this.callbacks?.onTodosUpdate) {
        this.callbacks.onTodosUpdate(todos);
      }
      
      console.log(`待办事项数据已更新，共 ${todos.length} 项`);
    } catch (error) {
      console.error('刷新待办事项数据失败:', error);
      this.callbacks?.onError?.('刷新待办事项失败', 'todos');
    }
  }

  /**
   * 刷新报告数据
   */
  private async refreshReports(event: EventData): Promise<void> {
    try {
      console.log('刷新报告数据...');
      const response = await reportService.getReports();
      const reports = (response as any)?.data?.reports ?? (response as any)?.reports ?? [];
      
      if (this.callbacks?.onReportsUpdate) {
        this.callbacks.onReportsUpdate(reports);
      }
      
      console.log(`报告数据已更新，共 ${reports.length} 项`);
    } catch (error) {
      console.error('刷新报告数据失败:', error);
      this.callbacks?.onError?.('刷新报告失败', 'reports');
    }
  }

  /**
   * 刷新提示数据
   */
  private async refreshTips(event: EventData): Promise<void> {
    try {
      console.log('刷新提示数据...');
      const response = await tipService.getTips();
      const tips = (response as any)?.data?.tips ?? (response as any)?.tips ?? [];
      
      if (this.callbacks?.onTipsUpdate) {
        this.callbacks.onTipsUpdate(tips);
      }
      
      console.log(`提示数据已更新，共 ${tips.length} 项`);
    } catch (error) {
      console.error('刷新提示数据失败:', error);
      this.callbacks?.onError?.('刷新提示失败', 'tips');
    }
  }

  /**
   * 刷新时间线数据
   */
  private async refreshTimeline(event: EventData): Promise<void> {
    try {
      console.log('刷新时间线数据...');
      
      // 实际获取时间线数据
      const response = await timelineService.getTimelineSegments();
      const segs = (response as any)?.data?.activities ?? (response as any);
      const activities = Array.isArray(segs) ? segs : [];
      
      // 通过自定义事件通知 Timeline 组件刷新
      // Timeline 组件会监听这个事件
      window.dispatchEvent(new CustomEvent('timeline-data-updated', {
        detail: { activities }
      }));
      
      // 调用回调
      if (this.callbacks?.onTimelineUpdate) {
        this.callbacks.onTimelineUpdate(activities);
      }
      
      console.log(`时间线数据已更新，共 ${activities.length} 个活动`);
    } catch (error) {
      console.error('刷新时间线数据失败:', error);
      this.callbacks?.onError?.('刷新时间线失败', 'timeline');
    }
  }

  /**
   * 手动刷新所有数据
   */
  async refreshAllData(): Promise<void> {
    console.log('手动刷新所有数据...');
    
    const refreshPromises = [
      this.refreshTodos({ type: 'todo', data: {}, id: '', timestamp: 0, datetime: '' }),
      this.refreshReports({ type: 'report', data: {}, id: '', timestamp: 0, datetime: '' }),
      this.refreshTips({ type: 'tip', data: {}, id: '', timestamp: 0, datetime: '' }),
      this.refreshTimeline({ type: 'activity', data: {}, id: '', timestamp: 0, datetime: '' })
    ];

    try {
      await Promise.allSettled(refreshPromises);
      console.log('所有数据刷新完成');
    } catch (error) {
      console.error('刷新所有数据时出错:', error);
    }
  }
}

// 导出单例实例
export const dataRefreshManager = new DataRefreshManager();
