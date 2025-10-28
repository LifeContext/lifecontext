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
                LifeContext
              </h1>
              <p class="text-base font-light text-slate-500 dark:text-slate-400 tracking-wide">
                Your Proactive Life Search Engine
              </p>
            </div>
            <div class="flex items-end gap-2 pb-0.5">
              <Icon :path="CALENDAR_ICON" class="h-5 w-5 text-slate-400" />
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
              :on-refresh="loadReports"
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
          <button 
            v-if="!isChatHistoryOpen && activeView === 'chat'"
            @click="handleToggleChatHistory"
            class="chat-history-toggle-btn absolute top-4 left-4 z-10 p-2 rounded-md transition-colors"
            aria-label="Expand chat history"
          >
            <Icon :path="chevronDoubleRight" class="w-5 h-5"/>
          </button>
          <ChatView />
        </div>
      </div>

      <div :class="`absolute inset-0 py-4 pr-4 pl-0 transition-transform duration-200 ${exitingView === 'timeline' ? 'animate-view-out' : ''} ${activeView === 'timeline' ? 'animate-view-in' : 'opacity-0 pointer-events-none'}`">
        <Timeline />
      </div>

      <div :class="`absolute inset-0 py-4 pr-4 pl-0 transition-opacity duration-200 ${viewingTip || viewingReport ? 'opacity-100' : 'opacity-0 pointer-events-none'}`">
        <div v-if="viewingTip" :class="exitingView === 'tipDetail' ? 'animate-view-out' : 'animate-view-in'">
          <TipDetailView
            :tips="tips"
            :selected-tip="viewingTip"
            :on-select-tip="setViewingTip"
            :on-close="() => handleCloseDetailView()"
          />
        </div>
        <div v-if="viewingReport" :class="exitingView === 'reportDetail' ? 'animate-view-out' : 'animate-view-in'">
          <ReportDetailView 
            :reports="reports"
            :selected-report="viewingReport" 
            :on-close="() => handleCloseDetailView()" 
            :on-navigate="handleNavigateReport"
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
import { ref, computed, onMounted, onUnmounted } from 'vue';
import Header from './src/components/Header.vue';
import LeftPanel from './src/components/LeftPanel.vue';
import CenterPanel from './src/components/CenterPanel.vue';
import Icon from './src/components/Icon.vue';
import SettingsModal from './src/components/SettingsModal.vue';
import Timeline from './src/components/Timeline.vue';
import ChatView from './src/components/ChatView.vue';
import ChatHistoryPanel from './src/components/ChatHistoryPanel.vue';
import TipDetailView from './src/components/TipDetailView.vue';
import ReportDetailView from './src/components/ReportDetailView.vue';
import { dailyReports, chatSessions, tips as tipsFromConstants } from './constants';
import type { DailyReport, TodoItem, ChatMessage, ChatSession, Tip, TipCategory } from './types';
import { todoService } from './src/api/todoService'; // 导入API服务
import { reportService } from './src/api/reportService'; // 导入Report API服务
import { tipService } from './src/api/tipService'; // 导入Tip API服务

const REPORT_DETAIL_ICONS = {
  chevronLeft: 'M15.707 17.293a1 1 0 01-1.414 0L8.586 11.586a2 2 0 010-2.828l5.707-5.707a1 1 0 011.414 1.414L10.414 10l5.293 5.293a1 1 0 010 1.414z',
  chevronRight: 'M8.293 17.293a1 1 0 010-1.414L13.586 10 8.293 4.707a1 1 0 011.414-1.414l5.707 5.707a2 2 0 010 2.828l-5.707 5.707a1 1 0 01-1.414 0z',
  barChart: 'M5 9.2h3V19H5zM10.6 5h2.8v14h-2.8zm5.6 8H19v6h-2.8z',
  fileText: 'M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z',
  listCheck: 'M14 10H2v2h12v-2zm0-4H2v2h12V6zM2 16h8v-2H2v2zm19.5-4.5L23 13l-6.99 7-4.51-4.5L13 14l3.01 3L21.5 11.5z',
  shieldAlert: 'M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-1 14h2v2h-2v-2zm0-8h2v6h-2V7z',
  close: 'M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z',
};

const chevronDoubleRight = 'M5.59 7.41L10.18 12l-4.59 4.59L7 18l6-6-6-6zM12.59 7.41L17.18 12l-4.59 4.59L14 18l6-6-6-6z';
const CALENDAR_ICON = 'M17 12h-5v5h5v-5zM16 1v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2h-1V1h-2zm3 18H5V8h14v11z';

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

// Computed
const today = computed(() => {
  return currentDate.value.toLocaleString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
});

// 加载Reports数据的方法
const loadReports = async () => {
  try {
    isLoadingReports.value = true;
    errorLoadingReports.value = null;
    const reportsData = await reportService.getReports();
    reports.value = reportsData.data.reports;
    // 设置默认选中的报告
    if (reportsData.length > 0 && !selectedDashboardReport.value) {
      selectedDashboardReport.value = reportsData[0];
    }
  } catch (error) {
    console.error('Failed to load reports:', error);
    errorLoadingReports.value = 'Failed to load reports. Please try again later.';
    // 使用备用数据
    reports.value = dailyReports;
    selectedDashboardReport.value = dailyReports[0];
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
    errorLoadingTodos.value = 'Failed to load tasks. Please try again later.';
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
    errorLoadingTips.value = 'Failed to load tips. Please try again later.';
  } finally {
    isLoadingTips.value = false;
  }
};

// Methods
const handleToggleDailyPanel = () => {
  isDailyPanelCollapsed.value = !isDailyPanelCollapsed.value;
};

// // 更新setTodos方法，使其使用API服务
// const setTodos = async (newTodos: TodoItem[]) => {
//   todos.value = newTodos;
// };

// 添加直接操作Todo的API方法
const addTodo = async (text: string, priority: 'low' | 'medium' | 'high') => {
  try {
    const newTodo = await todoService.addTodo(text, priority);
    todos.value = [...todos.value, newTodo];
  } catch (error) {
    console.error('Failed to add todo:', error);
    // 可以在这里添加用户通知
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
    const updatedTodo = await todoService.updateTodo(id, text, priority);
    todos.value = todos.value.map(item => 
      item.id === id ? updatedTodo : item
    );
  } catch (error) {
    console.error('Failed to update todo:', error);
    // 可以在这里添加用户通知
  }
};

const deleteTodoItem = async (id: number) => {
  try {
    await todoService.deleteTodo(id);
    todos.value = todos.value.filter(item => item.id !== id);
  } catch (error) {
    console.error('Failed to delete todo:', error);
    // 可以在这里添加用户通知
  }
};

const handleViewReport = (report: DailyReport) => {
  selectedDashboardReport.value = report;
  viewingReport.value = report;
  activeView.value = 'reportDetail';
};

const handleViewTip = (tip: Tip) => {
  viewingTip.value = tip;
  activeView.value = 'tipDetail';
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
    activeView.value = targetView;

    setTimeout(() => {
      if (viewToCloseRef.value === 'tipDetail') {
        viewingTip.value = null;
      }
      if (viewToCloseRef.value === 'reportDetail') {
        viewingReport.value = null;
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
    activeView.value = targetView;
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

// Lifecycle
let timer: NodeJS.Timeout;

onMounted(() => {
  loadReports(); // 组件挂载时加载Reports数据
  loadTodos(); // 组件挂载时加载Todo数据
  loadTips(); // 组件挂载时加载Tips数据
  
  timer = setInterval(() => {
    currentDate.value = new Date();
  }, 60000); // Update every minute
});

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
  }
});
</script>

<style scoped>
/* 暗色模式样式（默认） */
.chat-history-toggle-btn {
  background-color: #1e293b; /* bg-slate-800 */
  color: #94a3b8; /* text-slate-400 */
}

.chat-history-toggle-btn:hover {
  background-color: #334155; /* hover:bg-slate-700 */
  color: #f1f5f9; /* hover:text-slate-100 */
}

/* 亮色模式样式 */
@media (prefers-color-scheme: light) {
  .chat-history-toggle-btn {
    background-color: white;
    color: #6b7280; /* text-gray-500 */
    border: 1px solid #e5e7eb; /* border-gray-200 */
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  }

  .chat-history-toggle-btn:hover {
    background-color: #f9fafb; /* hover:bg-gray-50 */
    color: #111827; /* hover:text-gray-900 */
    border-color: #d1d5db; /* hover:border-gray-300 */
  }
}
</style>
