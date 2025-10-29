/**
 * 事件服务 - 用于轮询后端事件并处理数据更新
 */

export interface EventData {
  id: string;
  type: string;
  data: Record<string, any>;
  timestamp: number;
  datetime: string;
}

export interface EventResponse {
  code: number;
  message: string;
  data: {
    events: EventData[];
    count: number;
  };
}

export class EventService {
  private pollingInterval: number | null = null;
  private isPolling = false;
  private pollInterval = 3000; // 3秒轮询一次
  private maxRetries = 3;
  private retryCount = 0;

  // 事件回调函数类型
  private eventHandlers: Map<string, (event: EventData) => void> = new Map();

  /**
   * 开始轮询事件
   */
  startPolling(): void {
    if (this.isPolling) {
      console.warn('Event polling is already running');
      return;
    }

    this.isPolling = true;
    this.retryCount = 0;
    console.log('开始轮询后端事件...');
    
    this.pollEvents();
  }

  /**
   * 停止轮询事件
   */
  stopPolling(): void {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
    this.isPolling = false;
    console.log('停止轮询后端事件');
  }

  /**
   * 轮询事件
   */
  private async pollEvents(): Promise<void> {
    if (!this.isPolling) return;

    try {
      const response = await fetch('/api/events/fetch');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: EventResponse = await response.json();
      
      if (result.code === 200 && result.data.events.length > 0) {
        console.log(`收到 ${result.data.count} 个事件`);
        
        // 处理每个事件
        result.data.events.forEach(event => {
          this.handleEvent(event);
        });
      }

      // 重置重试计数
      this.retryCount = 0;
      
    } catch (error) {
      console.error('轮询事件失败:', error);
      this.handlePollingError();
    }

    // 继续轮询
    if (this.isPolling) {
      this.pollingInterval = window.setTimeout(() => {
        this.pollEvents();
      }, this.pollInterval);
    }
  }

  /**
   * 处理轮询错误
   */
  private handlePollingError(): void {
    this.retryCount++;
    
    if (this.retryCount >= this.maxRetries) {
      console.error(`轮询失败 ${this.maxRetries} 次，停止轮询`);
      this.stopPolling();
      return;
    }

    // 指数退避重试
    const retryDelay = Math.min(1000 * Math.pow(2, this.retryCount), 10000);
    console.log(`${retryDelay}ms 后重试轮询...`);
    
    setTimeout(() => {
      if (this.isPolling) {
        this.pollEvents();
      }
    }, retryDelay);
  }

  /**
   * 处理单个事件
   */
  private handleEvent(event: EventData): void {
    console.log(`处理事件: ${event.type}`, event.data);
    
    // 调用对应的事件处理器
    const handler = this.eventHandlers.get(event.type);
    if (handler) {
      try {
        handler(event);
      } catch (error) {
        console.error(`处理事件 ${event.type} 时出错:`, error);
      }
    } else {
      console.warn(`未找到事件类型 ${event.type} 的处理器`);
    }
  }

  /**
   * 注册事件处理器
   */
  onEvent(eventType: string, handler: (event: EventData) => void): void {
    this.eventHandlers.set(eventType, handler);
    console.log(`注册事件处理器: ${eventType}`);
  }

  /**
   * 移除事件处理器
   */
  offEvent(eventType: string): void {
    this.eventHandlers.delete(eventType);
    console.log(`移除事件处理器: ${eventType}`);
  }

  /**
   * 获取轮询状态
   */
  getPollingStatus(): { isPolling: boolean; retryCount: number } {
    return {
      isPolling: this.isPolling,
      retryCount: this.retryCount
    };
  }

  /**
   * 设置轮询间隔
   */
  setPollInterval(interval: number): void {
    this.pollInterval = Math.max(1000, interval); // 最小1秒
    console.log(`设置轮询间隔为 ${this.pollInterval}ms`);
  }
}

// 导出单例实例
export const eventService = new EventService();
