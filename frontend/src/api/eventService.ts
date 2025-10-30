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
      // 轮询各资源的变化并派发合成事件
      await this.pollAllResources();

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

  // 资源轮询实现（合成事件）
  private lastSignatures: Record<string, string> = {};

  private async pollAllResources(): Promise<void> {
    await Promise.allSettled([
      this.checkAndEmit('todo', this.fetchTodosSignature),
      this.checkAndEmit('report', this.fetchReportsSignature),
      this.checkAndEmit('tip', this.fetchTipsSignature),
      this.checkAndEmit('activity', this.fetchActivitiesSignature)
    ]);
  }

  private async checkAndEmit(
    type: 'todo' | 'report' | 'tip' | 'activity',
    fetchSignature: () => Promise<string>
  ): Promise<void> {
    try {
      const signature = await fetchSignature();
      if (this.lastSignatures[type] !== undefined && this.lastSignatures[type] !== signature) {
        // 合成一个简化事件
        const event: EventData = {
          id: `${type}-${Date.now()}`,
          type,
          data: { changed: true },
          timestamp: Date.now(),
          datetime: new Date().toISOString()
        };
        this.handleEvent(event);
      }
      this.lastSignatures[type] = signature;
    } catch (e) {
      // 忽略单个资源失败，整体轮询继续
      console.warn(`检查资源 ${type} 失败:`, e);
    }
  }

  private async fetchTodosSignature(): Promise<string> {
    const res = await fetch(`/api/generation/todos?limit=1&offset=0`);
    if (!res.ok) throw new Error(`todos fetch failed: ${res.status}`);
    const json = await res.json();
    const total = json?.data?.total ?? (json?.data?.todos?.length ?? 0);
    const firstId = json?.data?.todos?.[0]?.id ?? null;
    return JSON.stringify({ total, firstId });
  }

  private async fetchReportsSignature(): Promise<string> {
    const res = await fetch(`/api/generation/reports?limit=1&offset=0`);
    if (!res.ok) throw new Error(`reports fetch failed: ${res.status}`);
    const json = await res.json();
    const total = json?.data?.total ?? (json?.data?.reports?.length ?? 0);
    const firstId = json?.data?.reports?.[0]?.id ?? null;
    return JSON.stringify({ total, firstId });
  }

  private async fetchTipsSignature(): Promise<string> {
    const res = await fetch(`/api/generation/tips?limit=1&offset=0`);
    if (!res.ok) throw new Error(`tips fetch failed: ${res.status}`);
    const json = await res.json();
    const total = json?.data?.total ?? (json?.data?.tips?.length ?? 0);
    const firstId = json?.data?.tips?.[0]?.id ?? null;
    return JSON.stringify({ total, firstId });
  }

  private async fetchActivitiesSignature(): Promise<string> {
    const res = await fetch(`/api/generation/activities`);
    if (!res.ok) throw new Error(`activities fetch failed: ${res.status}`);
    const json = await res.json();
    const list = json?.data?.activities ?? [];
    const total = Array.isArray(list) ? list.length : 0;
    const firstId = Array.isArray(list) && list.length > 0 ? (list[0]?.id ?? null) : null;
    return JSON.stringify({ total, firstId });
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
