<template>
  <div class="bg-slate-100 dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-600 p-4 flex flex-col transition-all duration-300 ease-in-out h-full max-h-screen overflow-hidden">
    <!-- 头部区域 - 只在展开状态下显示 -->
    <div v-if="!isCollapsed" class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Daily</h2>
      <button 
        @click="onToggle"
        class="p-2 rounded-lg transition-all duration-200 hover:scale-105 flex-shrink-0 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
      >
        <Icon path="M8.293 17.293a1 1 0 010-1.414L13.586 10 8.293 4.707a1 1 0 011.414-1.414l5.707 5.707a2 2 0 010 2.828l-5.707 5.707a1 1 0 01-1.414 0z" class="h-4 w-4 transition-transform duration-200" />
      </button>
    </div>
    
    <!-- 折叠状态下的简洁显示 -->
    <div v-if="isCollapsed" class="flex justify-center mb-2">
      <button 
        @click="onToggle"
        class="px-2 py-1 bg-slate-100 hover:bg-slate-100 dark:bg-slate-900 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 rounded text-xs font-medium transition-all duration-200 flex items-center gap-1 hover:scale-105"
      >
        <Icon path="M15.707 17.293a1 1 0 01-1.414 0L8.586 11.586a2 2 0 010-2.828l5.707-5.707a1 1 0 011.414 1.414L10.414 10l5.293 5.293a1 1 0 010 1.414z" class="h-4 w-4 transition-transform duration-200" />
      </button>
    </div>
    
    <!-- 内容区域 -->
    <div class="relative flex-1 overflow-y-auto min-h-0">
      <!-- 加载状态 -->
      <div v-if="isLoading" class="py-8 flex items-center justify-center">
        <div class="text-center">
          <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto mb-2"></div>
          <p class="text-sm text-slate-500 dark:text-slate-400">加载报告中...</p>
        </div>
      </div>
      
      <!-- 错误状态 -->
      <div v-else-if="error" class="py-8 px-4">
        <div class="text-center">
          <div class="text-red-500 dark:text-red-400 mb-2">
            <Icon path="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 16.5c-.77.833.192 2.5 1.732 2.5z" class="h-6 w-6 mx-auto" />
          </div>
          <p class="text-sm text-red-600 dark:text-red-400 mb-3">{{ error }}</p>
          <button 
            v-if="onRefresh"
            @click="onRefresh"
            class="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white text-xs rounded transition-colors duration-200"
          >
            重试
          </button>
        </div>
      </div>
      
      <!-- 折叠状态下无数据 -->
      <div v-else-if="isCollapsed && reports.length === 0" class="py-8 flex items-center justify-center">
        <div class="text-center">
          <div class="text-slate-300 dark:text-slate-600 mb-2">
            <Icon path="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zM9 14H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2zm-8 4H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2z" class="h-6 w-6 mx-auto" />
          </div>
          <p class="text-xs text-slate-400 dark:text-slate-500">暂无报告</p>
        </div>
      </div>
      
      <!-- 折叠状态下的日历样式显示 -->
      <div 
        v-else-if="isCollapsed" 
        class="py-4 transition-all duration-300 ease-in-out"
      >
        <div class="space-y-4">
          <div 
            v-for="report in reports.slice(0, 13)" 
            :key="report.id"
            @click="() => onSelectReport(report)"
            class="flex items-center gap-3 rounded-lg cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors duration-200"
            :class="selectedReport?.id === report.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''"
          >
            <!-- 日历图标 -->
            <div class="flex-shrink-0 w-9 h-9 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg flex flex-col items-center justify-center shadow-sm hover:shadow-md transition-shadow duration-200">
              <!-- 日历顶部条 -->
              <div class="w-full h-1 bg-blue-500 rounded-t-lg"></div>
              <!-- 日期数字 -->
              <div class="text-sm font-bold text-slate-700 dark:text-slate-200 leading-none">
                {{ new Date(report.create_time).getDate() }}
              </div>
              <!-- 月份缩写 -->
              <div class="text-[9px] text-slate-500 dark:text-slate-400 uppercase font-medium leading-none">
                {{ new Date(report.create_time).toLocaleDateString('en', { month: 'short' }) }}
              </div>
            </div>
          </div>
          
          <!-- 显示更多报告的提示 -->
          <div v-if="reports.length > 10" class="text-center pt-2">
            <span class="text-xs text-slate-400 dark:text-slate-500">
              +{{ reports.length - 13 }} 更多报告
            </span>
          </div>
        </div>
      </div>
      
      <!-- 展开状态下无数据 -->
      <div v-else-if="!isCollapsed && reports.length === 0" class="py-8 flex items-center justify-center">
        <div class="text-center">
          <div class="text-slate-300 dark:text-slate-600 mb-2">
            <Icon path="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zM9 14H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2zm-8 4H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2z" class="h-6 w-6 mx-auto" />
          </div>
          <p class="text-sm text-slate-400 dark:text-slate-500">暂无日报数据</p>
          <p class="text-xs text-slate-300 dark:text-slate-500 mt-1">生成你的第一份日报记录吧</p>
        </div>
      </div>
      
      <!-- 展开状态下的完整内容 -->
      <div 
        v-else-if="!isCollapsed"
        class="space-y-2 transition-all duration-300 ease-in-out pr-2 pb-2"
      >
        <div 
          v-for="report in reports" 
          :key="report.id"
          @click="() => onSelectReport(report)"
          :class="`p-3 rounded-lg cursor-pointer transition-all duration-200 ${selectedReport?.id === report.id ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-300/50 dark:hover:bg-slate-700/50'}`"
        >
          <h3 class="font-medium text-sm">{{ report.title }}</h3>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">{{ formatDateTime(report.create_time) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Icon from './Icon.vue';
import type { DailyReport } from '../../types';

const formatDateTime = (dateTime: string): string => {
  if (!dateTime) return '';
  
  // 如果包含微秒部分，则截取到秒
  if (dateTime.includes('.')) {
    return dateTime.split('.')[0];
  }
  
  return dateTime;
};

interface Props {
  isCollapsed: boolean;
  onToggle: () => void;
  reports: DailyReport[];
  selectedReport: DailyReport | null;
  onSelectReport: (report: DailyReport) => void;
  isLoading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
}

defineProps<Props>();
</script>

<style scoped>
.relative::-webkit-scrollbar {
  width: 6px;
}

.relative::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 3px;
}

.relative::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.4) 0%, rgba(148, 163, 184, 0.2) 100%);
  border-radius: 3px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.2s ease;
}

.relative::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.6) 0%, rgba(148, 163, 184, 0.4) 100%);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transform: scaleX(1.2);
}

.relative::-webkit-scrollbar-thumb:active {
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.8) 0%, rgba(148, 163, 184, 0.6) 100%);
}

/* 暗色模式滚动条 */
.dark .relative::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(71, 85, 105, 0.4) 0%, rgba(71, 85, 105, 0.2) 100%);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.dark .relative::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, rgba(71, 85, 105, 0.6) 0%, rgba(71, 85, 105, 0.4) 100%);
  border: 1px solid rgba(0, 0, 0, 0.2);
}

.dark .relative::-webkit-scrollbar-thumb:active {
  background: linear-gradient(180deg, rgba(71, 85, 105, 0.8) 0%, rgba(71, 85, 105, 0.6) 100%);
}

/* Firefox 滚动条样式 */
.relative {
  scrollbar-width: thin;
  scrollbar-color: rgba(148, 163, 184, 0.3) transparent;
}

.dark .relative {
  scrollbar-color: rgba(71, 85, 105, 0.3) transparent;
}

/* 滚动条淡入淡出效果 */
.relative {
  transition: scrollbar-color 0.3s ease;
}

/* 当内容不需要滚动时隐藏滚动条 */
.relative:not(:hover)::-webkit-scrollbar-thumb {
  opacity: 0;
  transition: opacity 0.3s ease;
}

.relative:hover::-webkit-scrollbar-thumb {
  opacity: 1;
  transition: opacity 0.3s ease;
}
</style>