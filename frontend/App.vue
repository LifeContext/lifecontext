<template>
  <div class="h-screen w-screen bg-slate-100 dark:bg-slate-900 text-slate-800 dark:text-slate-200 flex flex-row overflow-hidden">
    <Header
      :on-settings-click="() => isSettingsModalOpen = true"
      :active-view="getHeaderActiveView()"
      :on-navigate="handleNavigation"
    />
    <div class="flex-1 min-h-0 relative flex flex-col">
      <main :class="`absolute inset-0 p-2 transition-opacity duration-200 ${activeView === 'dashboard' ? 'opacity-100' : 'opacity-0 pointer-events-none'}`">
        <div class="h-full grid grid-rows-[auto_1fr] gap-4">
          <!-- Header Row -->
          <div class="h-14 flex items-end justify-between">
            <div>
              <h1 class="text-3xl font-bold bg-gradient-to-r from-blue-500 to-teal-400 bg-clip-text text-transparent tracking-tight">
                {{ t('app.title') }}
              </h1>
              <p class="text-base font-light text-slate-500 dark:text-slate-400 tracking-wide">
                {{ t('app.subtitle') }}
              </p>
            </div>
            <div class="flex flex-col items-end pb-0.5 gap-2 pr-4 translate-y-2">
              <div 
                class="relative"
                @mouseleave="scheduleLinkPopoverHide"
              >
                <div 
                  ref="linkButtonRef"
                  class="flex items-center overflow-hidden rounded-full shadow border border-slate-200 dark:border-slate-700 h-8"
                >
                  <div class="px-4 h-full flex items-center bg-blue-700 text-white text-sm font-semibold tracking-wide">
                    LifeContext.Link
                  </div>
                  <button
                    class="w-8 h-8 flex items-center justify-center bg-blue-100 hover:bg-blue-200 dark:bg-blue-800 dark:hover:bg-blue-700 transition-colors"
                    @mouseenter="showLinkPopoverPanel"
                    @focus="showLinkPopoverPanel"
                    @click="handleLinkButtonClick"
                  >
                    <img src="/link_logo.png" alt="link" class="h-4 w-4 object-contain" />
                  </button>
                </div>
                <Teleport to="body">
                  <transition name="fade">
                    <div
                      v-if="showLinkPopover"
                      :style="linkPopoverStyle"
                      class="fixed w-72 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-lg p-4 space-y-2 text-sm text-slate-600 dark:text-slate-300 z-[9999]"
                    >
                      <p>
                        你的 Life 已压缩进这枚 Link，复制即可与 LLM 或朋友分享你的数字故事。
                      </p>
                      <div class="text-xs text-blue-600 dark:text-blue-300 break-all font-medium">
                        {{ lifeContextLink }}
                      </div>
                      <button
                        class="px-3 py-1.5 text-xs rounded-lg bg-blue-600 text-white hover:bg-blue-500 transition-colors"
                        @click="handleLinkButtonClick"
                      >
                        {{ copyButtonText }}
                      </button>
                      <p class="text-xs text-green-600 dark:text-green-300 flex items-center gap-2 flex-nowrap whitespace-nowrap" v-if="copyState === 'copied'">
                        <span>链接已复制，可直接粘贴使用。</span>
                        <span class="text-slate-500 dark:text-slate-400">Coming soon！</span>
                      </p>
                    </div>
                  </transition>
                </Teleport>
              </div>
              <span class="text-sm font-medium text-slate-500 dark:text-slate-400 whitespace-nowrap">
                {{ today }}
              </span>
            </div>
          </div>
          <!-- Content Row -->
          <div 
            class="grid gap-4 transition-all duration-500 ease-in-out min-h-0" 
            :style="{ gridTemplateColumns: isDailyPanelCollapsed ? '1fr 72px' : '1fr 288px' }"
          >
            <!-- 在App.vue的模板中 -->
            <CenterPanel 
              :todos="todos" 
              :set-todos="setTodos" 
              :on-select-tip="handleViewTip"
              :is-loading="isLoadingTodos"
              :error="errorLoadingTodos"
              :refresh-todos="loadTodos"
              :tips="tips"
              :is-loading-tips="isLoadingTips"
              :error-loading-tips="errorLoadingTips"
              :refresh-tips="loadTips"
              @addTodo="addTodo"
              @toggleTodo="toggleTodoStatus"
              @updateTodo="updateTodoItem"
              @deleteTodo="deleteTodoItem"
            />
            <LeftPanel
              :is-collapsed="isDailyPanelCollapsed"
              :on-toggle="handleToggleDailyPanel"
              :reports="reports"
              :selected-report="selectedDashboardReport"
              :on-select-report="handleViewReport"
              :is-loading="isLoadingReports"
              :error="errorLoadingReports"
              :on-refresh="() => loadReports()"
              :on-date-change="handleReportDateChange"
            />
          </div>
        </div>
      </main>
      
      <div :class="`absolute inset-0 flex flex-row transition-opacity duration-200 ${activeView === 'chat' ? 'animate-view-in' : 'opacity-0 pointer-events-none'}`">
        <ChatHistoryPanel 
          v-if="isChatHistoryOpen"
          :sessions="chatSessions" 
          :active-session-id="activeChatSessionId"
          :on-select-session="handleSelectChatSession"
          :on-close="handleToggleChatHistory" 
        />
        <div class="flex-1 relative bg-slate-900">
          <!-- <button 
            v-if="!isChatHistoryOpen && activeView === 'chat'"
            @click="handleToggleChatHistory"
            class="chat-history-toggle-btn absolute top-4 left-4 z-10 p-2 rounded-md transition-colors"
            aria-label="Expand chat history"
          >
            <Icon path="M8.293 17.293a1 1 0 010-1.414L13.586 10 8.293 4.707a1 1 0 011.414-1.414l5.707 5.707a2 2 0 010 2.828l-5.707 5.707a1 1 0 01-1.414 0z" class="h-4 w-4 transition-transform duration-200" />
          </button> -->
          <ChatView />
        </div>
      </div>

      <div :class="`absolute inset-0 py-4 pr-4 pl-0 transition-transform duration-200 ${exitingView === 'timeline' ? 'animate-view-out' : ''} ${activeView === 'timeline' ? 'animate-view-in' : 'opacity-0 pointer-events-none'}`">
        <Timeline />
      </div>

      <div :class="`absolute inset-0 transition-opacity duration-200 ${viewingTip || viewingReport ? 'opacity-100' : 'opacity-0 pointer-events-none'}`">
        <div v-if="viewingTip" :class="exitingView === 'tipDetail' ? 'animate-view-out' : 'animate-view-in'">
          <TipDetailView
            :tips="tips"
            :selected-tip="viewingTip"
            :on-select-tip="setViewingTip"
            :on-close="() => handleCloseDetailView()"
          />
        </div>
        <div v-if="viewingReport" :class="exitingView === 'reportDetail' ? 'animate-view-out' : 'animate-view-in'" class="h-full max-h-full">
          <ReportDetailView 
            :reports="reports"
            :selected-report="viewingReport" 
            :on-close="() => handleCloseDetailView()" 
            :on-navigate="handleNavigateReport"
            :on-select-report="handleViewReport"
          />
        </div>
      </div>
    </div>
    
    <SettingsModal 
      v-if="isSettingsModalOpen"
      :on-close="() => isSettingsModalOpen = false" 
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import Header from './src/components/Header.vue';
import LeftPanel from './src/components/LeftPanel.vue';
import CenterPanel from './src/components/CenterPanel.vue';
import SettingsModal from './src/components/SettingsModal.vue';
import Timeline from './src/components/Timeline.vue';
import ChatView from './src/components/ChatView.vue';
import ChatHistoryPanel from './src/components/ChatHistoryPanel.vue';
import TipDetailView from './src/components/TipDetailView.vue';
import ReportDetailView from './src/components/ReportDetailView.vue';
import { chatSessions } from './constants';
import type { DailyReport, TodoItem, ChatMessage, ChatSession, Tip, TipCategory } from './types';
import { todoService } from './src/api/todoService'; // 导入API服务
import { reportService } from './src/api/reportService'; // 导入Report API服务
import { tipService } from './src/api/tipService'; // 导入Tip API服务
import { eventService } from './src/api/eventService'; // 导入事件服务
import { dataRefreshManager } from './src/utils/dataRefreshManager'; // 导入数据刷新管理器
import { useI18n } from './src/i18n';

const router = useRouter();
const route = useRoute();

const { t, locale } = useI18n();

type ActiveView = 'dashboard' | 'timeline' | 'chat' | 'tipDetail' | 'reportDetail';

// Reactive state
const isSettingsModalOpen = ref(false);
const activeView = ref<ActiveView>('dashboard');
const exitingView = ref<ActiveView | null>(null);
const viewToCloseRef = ref<ActiveView | null>(null);

const isDailyPanelCollapsed = ref(false);
const reports = ref<DailyReport[]>([]); // 初始化为空数组，从API加载
const selectedDashboardReport = ref<DailyReport | null>(null);
const isLoadingReports = ref(true); // 添加加载状态
const errorLoadingReports = ref<string | null>(null); // 错误状态
const selectedReportDate = ref<string>(new Date().toISOString().split('T')[0]);
const todos = ref<TodoItem[]>([]); // 初始化为空数组，从API加载
const isLoadingTodos = ref(true); // 添加加载状态
const errorLoadingTodos = ref<string | null>(null); // 错误状态

const tips = ref<Tip[]>([]); // 初始化为空数组，从API加载
const isLoadingTips = ref(true); // 添加加载状态
const errorLoadingTips = ref<string | null>(null); // 错误状态

const viewingTip = ref<Tip | null>(null);
const viewingReport = ref<DailyReport | null>(null);

const isChatHistoryOpen = ref(false);
const activeChatSessionId = ref<number | null>(5);

const isChatWindowOpen = ref(false);
const currentDate = ref(new Date());
const lifeContextLink = ref('https://lifecontext.link/demo');
const copyState = ref<'idle' | 'copied'>('idle');
const showLinkPopover = ref(false);
const copyButtonText = computed(() => (copyState.value === 'copied' ? '已复制' : '复制链接'));
const linkButtonRef = ref<HTMLElement | null>(null);

// Computed
const linkPopoverStyle = computed(() => {
  if (!linkButtonRef.value || !showLinkPopover.value) {
    return {};
  }
  const rect = linkButtonRef.value.getBoundingClientRect();
  return {
    right: `${window.innerWidth - rect.right}px`,
    top: `${rect.bottom + 12}px`,
  };
});

const today = computed(() => {
  const activeLocale = locale.value === 'zh-CN' ? 'zh-CN' : 'en-US';
  return currentDate.value.toLocaleString(activeLocale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
});

const resolveReportDate = (dateValue?: string) => {
  if (dateValue) return dateValue;
  if (selectedReportDate.value) return selectedReportDate.value;
  return new Date().toISOString().split('T')[0];
};

// 加载Reports数据的方法
const loadReports = async (dateValue?: string) => {
  try {
    isLoadingReports.value = true;
    errorLoadingReports.value = null;
    const targetDate = resolveReportDate(dateValue);
    const reportsData = await reportService.getReports(targetDate);
    selectedReportDate.value = targetDate;
    const cards = reportsData?.data?.cards ?? reportsData ?? [];
    reports.value = cards;
  } catch (error) {
    console.error('Failed to load reports:', error);
    errorLoadingReports.value = t('errors.loadReports');
    // 使用备用数据
    reports.value = dailyReports;
  } finally {
    isLoadingReports.value = false;
  }
};

// 加载Todo数据的方法
const loadTodos = async () => {
  try {
    isLoadingTodos.value = true;
    errorLoadingTodos.value = null;
    const todosData = await todoService.getTodos();    
    todos.value = todosData.data.todos;
  } catch (error) {
    console.error('Failed to load todos:', error);
    errorLoadingTodos.value = t('errors.loadTodos');
  } finally {
    isLoadingTodos.value = false;
  }
};

// 加载Tips数据的方法
const loadTips = async () => {
  try {
    isLoadingTips.value = true;
    errorLoadingTips.value = null;
    const tipsData = await tipService.getTips();
    tips.value = tipsData.data.tips;
  } catch (error) {
    console.error('Failed to load tips:', error);
    errorLoadingTips.value = t('errors.loadTips');
  } finally {
    isLoadingTips.value = false;
  }
};

// Methods
const handleToggleDailyPanel = () => {
  isDailyPanelCollapsed.value = !isDailyPanelCollapsed.value;
};

const handleReportDateChange = (dateValue: string) => {
  loadReports(dateValue);
};

let copyFeedbackTimer: number | undefined;
let linkPopoverHideTimer: number | undefined;

const showLinkPopoverPanel = () => {
  if (linkPopoverHideTimer) {
    clearTimeout(linkPopoverHideTimer);
  }
  showLinkPopover.value = true;
};

const scheduleLinkPopoverHide = () => {
  if (linkPopoverHideTimer) {
    clearTimeout(linkPopoverHideTimer);
  }
  linkPopoverHideTimer = window.setTimeout(() => {
    showLinkPopover.value = false;
  }, 200);
};

const copyLifeContextLink = async () => {
  try {
    await navigator.clipboard.writeText(lifeContextLink.value);
    copyState.value = 'copied';
    if (copyFeedbackTimer) {
      clearTimeout(copyFeedbackTimer);
    }
    copyFeedbackTimer = window.setTimeout(() => {
      copyState.value = 'idle';
    }, 2000);
  } catch (error) {
    console.error('Failed to copy LifeContext link:', error);
  }
};

const handleLinkButtonClick = async () => {
  await copyLifeContextLink();
  showLinkPopover.value = true;
};

// 添加直接操作Todo的API方法
const addTodo = async (text: string, priority: 'low' | 'medium' | 'high') => {
  try {
    const newTodo = await todoService.addTodo(text, priority);
    todos.value = [...todos.value, newTodo];
  } catch (error) {
    console.error('Failed to add todo:', error);
    throw error;
  }
};

const toggleTodoStatus = async (id: number) => {
  try {
    const todo = todos.value.find(item => item.id === id);
    if (!todo) {
      console.warn('Todo not found with id:', id);
      return;
    }
    const newStatus = !todo.status;
    await todoService.toggleTodo(id, newStatus);
    
    // 使用本地数据更新，只更新 status 字段
    todos.value = todos.value.map(item => 
      item.id === id ? { ...item, status: newStatus } : item
    );
  } catch (error) {
    console.error('Failed to toggle todo:', error);
    console.error('Error details:', error.message);
  }
};

const updateTodoItem = async (id: number, text: string, priority: 'low' | 'medium' | 'high') => {
  try {
    const updated = await todoService.updateTodo(id, text, priority);
    // 合并更新：仅替换被编辑字段，保留 status 等其他字段
    todos.value = todos.value.map(item => 
      item.id === id ? { ...item, description: updated.description, priority: updated.priority } : item
    );
  } catch (error) {
    console.error('Failed to update todo:', error);
  }
};

const deleteTodoItem = async (id: number) => {
  try {
    await todoService.deleteTodo(id);
    todos.value = todos.value.filter(item => item.id !== id);
  } catch (error) {
    console.error('Failed to delete todo:', error);
  }
};

const handleViewReport = (report: DailyReport) => {
  selectedDashboardReport.value = report;
  viewingReport.value = report;
  router.push({ name: 'reportDetail', params: { id: report.id.toString() } });
};

const handleViewTip = (tip: Tip) => {
  viewingTip.value = tip;
  router.push({ name: 'tipDetail', params: { id: tip.id.toString() } });
};

const handleToggleChatHistory = () => {
  isChatHistoryOpen.value = !isChatHistoryOpen.value;
};

const handleSelectChatSession = (id: number) => {
  activeChatSessionId.value = id;
};

const handleCloseDetailView = (targetView: 'dashboard' | 'timeline' | 'chat' = 'dashboard') => {
  if (activeView.value === 'tipDetail' || activeView.value === 'reportDetail') {
    viewToCloseRef.value = activeView.value;
    exitingView.value = activeView.value;
    
    // 使用路由导航
    router.push({ name: targetView });

    setTimeout(() => {
      if (viewToCloseRef.value === 'tipDetail') {
        viewingTip.value = null;
      }
      if (viewToCloseRef.value === 'reportDetail') {
        viewingReport.value = null;
        selectedDashboardReport.value = null;
      }
      exitingView.value = null;
      viewToCloseRef.value = null;
    }, 200);
  }
};

const handleNavigation = (targetView: 'dashboard' | 'timeline' | 'chat') => {
  if (activeView.value === targetView) return;
  
  // Close chat window if navigating
  isChatWindowOpen.value = false;

  if (activeView.value === 'tipDetail' || activeView.value === 'reportDetail') {
    handleCloseDetailView(targetView);
  } else {
    exitingView.value = activeView.value as ActiveView;
    router.push({ name: targetView });
    setTimeout(() => exitingView.value = null, 200);
  }
};

const handleNavigateReport = (direction: 'prev' | 'next') => {
  if (!viewingReport.value) return;
  
  const currentIndex = reports.value.findIndex(r => r.id === viewingReport.value!.id);
  if (currentIndex === -1) return;

  const newIndex = direction === 'prev' ? currentIndex - 1 : currentIndex + 1;

  if (newIndex >= 0 && newIndex < reports.value.length) {
    const newReport = reports.value[newIndex];
    viewingReport.value = newReport;
    selectedDashboardReport.value = newReport;
  }
};

const getHeaderActiveView = (): 'dashboard' | 'timeline' | 'chat' => {
  if (activeView.value === 'timeline') return 'timeline';
  if (activeView.value === 'chat') return 'chat';
  return 'dashboard';
};

const setTodos = (newTodos: TodoItem[]) => {
  todos.value = newTodos;
};

const setViewingTip = (tip: Tip) => {
  viewingTip.value = tip;
};

// 初始化事件轮询和数据刷新
const initializeEventPolling = () => {
  // 设置数据刷新回调
  dataRefreshManager.setCallbacks({
    onTodosUpdate: (newTodos: TodoItem[]) => {
      todos.value = newTodos;
      console.log('待办事项数据已自动更新');
    },
    onReportsUpdate: (newReports: DailyReport[]) => {
      reports.value = newReports;
      // 如果当前选中的报告被删除，选择第一个报告
      if (selectedDashboardReport.value && !newReports.find(r => r.id === selectedDashboardReport.value!.id)) {
        selectedDashboardReport.value = newReports.length > 0 ? newReports[0] : null;
      }
      console.log('报告数据已自动更新');
    },
    onTipsUpdate: (newTips: Tip[]) => {
      tips.value = newTips;
      console.log('提示数据已自动更新');
    },
    onTimelineUpdate: (activities: any[]) => {
      // 时间线组件会自动处理数据刷新
      console.log('时间线数据已自动更新');
    },
    onError: (error: string, dataType: string) => {
      console.error(`数据刷新错误 (${dataType}):`, error);
    }
  });

  // 注册事件处理器
  eventService.onEvent('todo', (event) => {
    dataRefreshManager.handleEvent(event);
  });
  
  eventService.onEvent('report', (event) => {
    dataRefreshManager.handleEvent(event);
  });
  
  eventService.onEvent('tip', (event) => {
    dataRefreshManager.handleEvent(event);
  });
  
  eventService.onEvent('activity', (event) => {
    dataRefreshManager.handleEvent(event);
  });

  // 开始轮询事件
  eventService.startPolling();
  console.log('事件轮询已启动');
};

// Lifecycle
let timer: number;

// 监听路由变化
watch(() => [route.name, route.params.id], async ([routeName, tipId]) => {
  if (routeName === 'tipDetail') {
    const id = parseInt(tipId as string);
    if (id) {
      // 如果 tips 数据已加载，直接查找
      if (tips.value.length > 0) {
        const tip = tips.value.find(t => t.id === id);
        if (tip) {
          viewingTip.value = tip;
          activeView.value = 'tipDetail';
        }
      } else {
        // 如果数据未加载，等待数据加载完成后再查找
        await loadTips();
        const tip = tips.value.find(t => t.id === id);
        if (tip) {
          viewingTip.value = tip;
          activeView.value = 'tipDetail';
        }
      }
    }
  } else if (routeName === 'reportDetail') {
    const id = parseInt(tipId as string);
    if (id) {
      if (reports.value.length > 0) {
        const report = reports.value.find(r => r.id === id);
        if (report) {
          viewingReport.value = report;
          selectedDashboardReport.value = report;
          activeView.value = 'reportDetail';
        }
      } else {
        await loadReports();
        const report = reports.value.find(r => r.id === id);
        if (report) {
          viewingReport.value = report;
          selectedDashboardReport.value = report;
          activeView.value = 'reportDetail';
        }
      }
    }
  } else {
    // 当路由不是 reportDetail 时，清除报告相关的选中状态
    if (routeName === 'dashboard' || routeName === 'chat' || routeName === 'timeline') {
      activeView.value = routeName as ActiveView;
    }
    viewingTip.value = null;
    viewingReport.value = null;
    selectedDashboardReport.value = null;
  }
}, { immediate: true });

onMounted(() => {
  loadReports(); // 组件挂载时加载Reports数据
  loadTodos(); // 组件挂载时加载Todo数据
  loadTips(); // 组件挂载时加载Tips数据
  
  // 初始化事件轮询
  initializeEventPolling();
  
  timer = setInterval(() => {
    currentDate.value = new Date();
  }, 60000); // Update every minute
});

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
  }
  if (copyFeedbackTimer) {
    clearTimeout(copyFeedbackTimer);
  }
  if (linkPopoverHideTimer) {
    clearTimeout(linkPopoverHideTimer);
  }
  
  // 停止事件轮询
  eventService.stopPolling();
  console.log('事件轮询已停止');
});
</script>

<style scoped>
.chat-history-toggle-btn {
  background-color: #1e293b;
  color: #94a3b8;
}

.chat-history-toggle-btn:hover {
  background-color: #334155;
  color: #f1f5f9;
}

/* 亮色模式样式 */
@media (prefers-color-scheme: light) {
  .chat-history-toggle-btn {
    background-color: white;
    color: #6b7280;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  }

  .chat-history-toggle-btn:hover {
    background-color: #f9fafb;
    color: #111827;
    border-color: #d1d5db;
  }
}
</style>
