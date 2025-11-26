<template>
  <div class="bg-slate-100 dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-600 p-4 flex flex-col transition-all duration-300 ease-in-out h-full max-h-screen overflow-hidden">
    <!-- 头部区域 - 只在展开状态下显示 -->
    <div v-if="!isCollapsed" class="mb-4">
      <div class="flex items-center justify-between gap-3">
        <h2 class="text-xl font-bold text-slate-900 dark:text-slate-100 flex-shrink-0">{{ t('dashboard.sectionTitle') }}</h2>
        
        <!-- 日期选择器 -->
        <div class="relative date-picker-container flex-1">
          <button
            @click.stop="toggleDatePicker"
            class="w-full flex items-center justify-center gap-2.5 px-2 py-2.5 bg-slate-300 dark:bg-slate-600 rounded-lg hover:bg-slate-400 dark:hover:bg-slate-500 transition-colors duration-200"
          >
            <Icon 
              path="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zM9 14H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2zm-8 4H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2z"
              class="h-4 w-4 text-white"
            />
            <span class="text-sm font-medium text-white">{{ formatSelectedDate(selectedDate) }}</span>
          </button>
          
        <!-- 日期选择下拉菜单 -->
        <div 
          v-if="isDatePickerOpen"
          class="absolute top-full left-1/3 -translate-x-1/2 w-[280px] z-50"
        >
          <div class="bg-slate-100 dark:bg-slate-900 p-4 w-full">
            <div class="bg-slate-100 dark:bg-slate-900 rounded-full px-4 py-3 border border-slate-300 dark:border-slate-600 shadow-inner">
              <div class="flex items-center justify-between gap-4">
                <button
                  @click.stop="navigateDate(-1)"
                  class="w-10 h-10 rounded-full bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 flex items-center justify-center transition-colors duration-200 hover:bg-slate-100 dark:hover:bg-slate-600 disabled:opacity-30 disabled:hover:bg-white dark:disabled:hover:bg-slate-700"
                  :disabled="!canNavigatePrev"
                >
                  <Icon 
                    path="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"
                    class="h-4 w-4 text-slate-700 dark:text-white"
                  />
                </button>
                
                <div class="flex-1 text-center">
                  <div class="text-base font-semibold whitespace-nowrap tracking-wide text-slate-900 dark:text-white">{{ formatSelectedDateFull(selectedDate) }}</div>
                  <div class="text-[11px] uppercase tracking-[0.35em] text-slate-500 dark:text-slate-400 mt-1">{{ locale === 'zh-CN' ? '近 7 天' : 'Last 7 Days' }}</div>
                </div>
                
                <button
                  @click.stop="navigateDate(1)"
                  class="w-10 h-10 rounded-full bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 flex items-center justify-center transition-colors duration-200 hover:bg-slate-100 dark:hover:bg-slate-600 disabled:opacity-30 disabled:hover:bg-white dark:disabled:hover:bg-slate-700"
                  :disabled="!canNavigateNext"
                >
                  <Icon 
                    path="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"
                    class="h-4 w-4 text-slate-700 dark:text-white"
                  />
                </button>
              </div>
            </div>
          </div>
        </div>
        </div>
        
        <button 
          @click="onToggle"
          class="p-2 rounded-lg transition-all duration-200 hover:scale-105 flex-shrink-0 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
        >
          <Icon path="M8.293 17.293a1 1 0 010-1.414L13.586 10 8.293 4.707a1 1 0 011.414-1.414l5.707 5.707a2 2 0 010 2.828l-5.707 5.707a1 1 0 01-1.414 0z" class="h-4 w-4 transition-transform duration-200" />
        </button>
      </div>
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
          <p class="text-sm text-slate-500 dark:text-slate-400">{{ t('dashboard.loading') }}</p>
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
            {{ t('common.retry') }}
          </button>
        </div>
      </div>
      
      <!-- 折叠状态下的日历样式显示 -->
      <div 
        v-else-if="isCollapsed" 
        class="py-2 transition-all duration-300 ease-in-out"
      >
        <div class="flex flex-col gap-1.5">
          <div 
            v-for="dayInfo in last7Days" 
            :key="dayInfo.dateStr"
            @click="() => handleDayClick(dayInfo)"
            class="cursor-pointer group"
          >
            <!-- 日历卡片 -->
            <div 
              class="w-full rounded-lg flex items-center justify-center py-2.5 shadow-md transition-all duration-200 relative"
              :class="{
                'bg-blue-500 dark:bg-blue-500 ring-blue-400 dark:ring-blue-400 ring-offset-1 ring-offset-slate-100 dark:ring-offset-slate-900': isSelectedDay(dayInfo),
                'bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700': !isSelectedDay(dayInfo)
              }"
            >
              <!-- 日期数字 -->
              <span 
                class="text-base font-bold transition-all duration-200"
                :class="{
                  'text-white': isSelectedDay(dayInfo),
                  'text-slate-700 dark:text-slate-200': !isSelectedDay(dayInfo)
                }"
              >
                {{ dayInfo.day }}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 展开状态下无数据 -->
      <div v-else-if="!isCollapsed && reports.length === 0" class="py-8 flex items-center justify-center">
        <div class="text-center">
          <div class="text-slate-300 dark:text-slate-600 mb-2">
            <Icon path="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zM9 14H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2zm-8 4H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2z" class="h-6 w-6 mx-auto" />
          </div>
          <p class="text-sm text-slate-400 dark:text-slate-500">{{ t('dashboard.emptyTitle') }}</p>
          <p class="text-xs text-slate-300 dark:text-slate-500 mt-1">{{ t('dashboard.waiting') }}</p>
        </div>
      </div>
      
      <!-- 展开状态下的完整内容 -->
      <div 
        v-else-if="!isCollapsed"
        class="space-y-4 transition-all duration-300 ease-in-out pr-2 pb-2"
      >
        <div 
          v-for="(report, index) in filteredReports" 
          :key="report.id"
          @click="() => onSelectReport(report)"
          class="report-card relative rounded-xl overflow-hidden cursor-pointer transition-all duration-200 hover:shadow-xl shadow-md"
          :class="selectedReport?.id === report.id ? 'ring-2 ring-blue-500' : ''"
        >
          <!-- 封面图片背景 -->
          <img 
            v-if="report.cover"
            :src="report.cover"
            :alt="report.title"
            class="absolute inset-0 w-full h-full object-cover report-cover-image"
            @error="handleImageError"
            @load="handleImageLoad"
          />
          
          <!-- 背景渐变 - 当没有封面图片或图片加载失败时显示 -->
          <div 
            class="absolute inset-0 report-gradient-background"
            :class="getCardGradient(index)"
            :style="report.cover ? 'display: none;' : ''"
          ></div>
          
          <!-- 整体渐变遮罩层 -->
          <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/60 to-transparent z-10 report-gradient-overlay"></div>
          
          <!-- 底部半透明面板 -->
          <div class="absolute bottom-0 left-0 right-0 z-20">
            <div class="report-overlay-panel bg-black/800 backdrop-blur-md rounded-b-xl px-4 pt-2 pb-2">
              <div class="flex items-center gap-2 mb-2">
                <Icon 
                  :path="getReportTypeIcon(report.type)" 
                  class="h-4 w-4 text-orange-400 flex-shrink-0" 
                />
                <span class="text-[10px] font-bold text-white uppercase tracking-wider">{{ report.type || 'Daily Report' }}</span>
              </div>
              <h3 class="font-bold text-white text-xs leading-tight line-clamp-2">{{ report.title }}</h3>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import Icon from './Icon.vue';
import type { DailyReport } from '../../types';
import { useI18n } from '../i18n';

const { t, locale } = useI18n();

interface Props {
  isCollapsed: boolean;
  onToggle: () => void;
  reports: DailyReport[];
  selectedReport: DailyReport | null;
  onSelectReport: (report: DailyReport) => void;
  isLoading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  onDateChange?: (date: string) => void;
}

const props = defineProps<Props>();

// 日期选择器状态
const isDatePickerOpen = ref(false);
const selectedDate = ref<string>('today');

// 格式化日期值为 YYYY-MM-DD
const formatDateValue = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

// 格式化选中的日期显示
const formatSelectedDate = (value: string): string => {
  const lang = locale.value === 'zh-CN' ? 'zh-CN' : 'en-US';
  
  if (value === 'today') {
    const today = new Date();
    if (lang === 'zh-CN') {
      return `${today.getMonth() + 1}月${today.getDate()}日`;
    } else {
      return today.toLocaleDateString(lang, { month: 'long', day: 'numeric' });
    }
  } else if (value === 'yesterday') {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    if (lang === 'zh-CN') {
      return `${yesterday.getMonth() + 1}月${yesterday.getDate()}日`;
    } else {
      return yesterday.toLocaleDateString(lang, { month: 'long', day: 'numeric' });
    }
  } else {
    const date = parseDateValue(value);
    if (lang === 'zh-CN') {
      return `${date.getMonth() + 1}月${date.getDate()}日`;
    } else {
      return date.toLocaleDateString(lang, { month: 'long', day: 'numeric' });
    }
  }
};

// 解析日期值
const parseDateValue = (value: string): Date => {
  const [year, month, day] = value.split('-').map(Number);
  return new Date(year, month - 1, day);
};

const getSelectedDateInstance = (value: string): Date => {
  const normalize = (date: Date) => {
    const normalized = new Date(date);
    normalized.setHours(0, 0, 0, 0);
    return normalized;
  };
  
  if (value === 'today') {
    return normalize(new Date());
  }
  
  if (value === 'yesterday') {
    const date = new Date();
    date.setDate(date.getDate() - 1);
    return normalize(date);
  }
  
  return normalize(parseDateValue(value));
};

// 格式化选中的日期显示（包含年份）
const formatSelectedDateFull = (value: string): string => {
  const lang = locale.value === 'zh-CN' ? 'zh-CN' : 'en-US';
  const date = getSelectedDateInstance(value);
  
  if (lang === 'zh-CN') {
    return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
  }
  
  return date.toLocaleDateString(lang, { month: 'long', day: 'numeric', year: 'numeric' });
};

const emitDateChange = () => {
  if (!props.onDateChange) return;
  const apiDate = formatDateValue(getSelectedDateInstance(selectedDate.value));
  props.onDateChange(apiDate);
};

const isSameDay = (a: Date, b: Date) => {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
};

const canNavigatePrev = computed(() => {
  const today = getSelectedDateInstance('today');
  const earliest = new Date(today);
  earliest.setDate(today.getDate() - 6);
  const current = getSelectedDateInstance(selectedDate.value);
  return current > earliest;
});

const canNavigateNext = computed(() => {
  const today = getSelectedDateInstance('today');
  const current = getSelectedDateInstance(selectedDate.value);
  return current < today;
});

const navigateDate = (direction: number) => {
  const today = getSelectedDateInstance('today');
  const earliest = new Date(today);
  earliest.setDate(today.getDate() - 6);
  
  const current = getSelectedDateInstance(selectedDate.value);
  const newDate = new Date(current);
  newDate.setDate(current.getDate() + direction);
  
  if (newDate > today || newDate < earliest) {
    return;
  }
  
  const yesterday = getSelectedDateInstance('yesterday');
  
  if (isSameDay(newDate, today)) {
    selectedDate.value = 'today';
  } else if (isSameDay(newDate, yesterday)) {
    selectedDate.value = 'yesterday';
  } else {
    selectedDate.value = formatDateValue(newDate);
  }
  emitDateChange();
};

// 切换日期选择器
const toggleDatePicker = () => {
  isDatePickerOpen.value = !isDatePickerOpen.value;
};

// 点击外部关闭日期选择器
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement;
  if (!target.closest('.date-picker-container')) {
    isDatePickerOpen.value = false;
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});

// 根据选择的日期过滤报告
const filteredReports = computed(() => {
  if (!props.reports || props.reports.length === 0) return [];
  
  // 获取目标日期
  let targetDate: Date;
  if (selectedDate.value === 'today') {
    targetDate = new Date();
  } else if (selectedDate.value === 'yesterday') {
    targetDate = new Date();
    targetDate.setDate(targetDate.getDate() - 1);
  } else {
    targetDate = parseDateValue(selectedDate.value);
  }
  
  return props.reports;
});

const last7Days = computed(() => {
  const days: Array<{
    date: Date;
    dateStr: string;
    day: number;
    weekday: string;
    isToday: boolean;
    report: DailyReport | null;
  }> = [];
  
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const lang = locale.value === 'zh-CN' ? 'zh-CN' : 'en-US';

  for (let i = 0; i < 7; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() - i);
    
    const dateStr = formatDateValue(date);
    const day = date.getDate();
    
    // 获取星期缩写
    const weekdayOptions: Intl.DateTimeFormatOptions = { weekday: 'short' };
    let weekday = date.toLocaleDateString(lang, weekdayOptions);
    if (lang === 'zh-CN') {
      // 中文星期转换为更短的格式
      const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
      weekday = weekdays[date.getDay()];
    } else {
      // 英文取前3个字母
      weekday = weekday.substring(0, 3).toUpperCase();
    }
    
    const isToday = i === 0;

    let report: DailyReport | null = null;
    if (props.reports && props.reports.length > 0) {

      if (i < props.reports.length) {
        report = props.reports[i];
      }
    }
    
    days.push({
      date,
      dateStr,
      day,
      weekday,
      isToday,
      report
    });
  }
  
  return days;
});

// 处理日期点击
const handleDayClick = async (dayInfo: { date: Date; dateStr: string; report: DailyReport | null }) => {
  // 如果面板是折叠的，先展开
  if (props.isCollapsed) {
    props.onToggle();
    // 等待展开动画完成
    await nextTick();
    
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  // 设置选中的日期
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  
  if (isSameDay(dayInfo.date, today)) {
    selectedDate.value = 'today';
  } else if (isSameDay(dayInfo.date, yesterday)) {
    selectedDate.value = 'yesterday';
  } else {
    selectedDate.value = dayInfo.dateStr;
  }
  
  // 触发日期变化，加载对应日期的数据
  emitDateChange();
};

// 判断是否是选中的日期
const isSelectedDay = (dayInfo: { date: Date; dateStr: string }): boolean => {
  const selectedDateInstance = getSelectedDateInstance(selectedDate.value);
  return isSameDay(dayInfo.date, selectedDateInstance);
};

const getCardGradient = (index: number): string => {
  const gradients = [
    'bg-gradient-to-br from-slate-600 via-slate-700 to-slate-800 dark:from-slate-800 dark:via-slate-900 dark:to-slate-950',
    'bg-gradient-to-br from-slate-700 via-slate-800 to-slate-900 dark:from-slate-900 dark:via-slate-950 dark:to-black',
    'bg-gradient-to-br from-blue-900/80 via-slate-800 to-slate-900 dark:from-blue-950/60 dark:via-slate-900 dark:to-black',
    'bg-gradient-to-br from-purple-900/70 via-slate-800 to-slate-900 dark:from-purple-950/50 dark:via-slate-900 dark:to-black',
    'bg-gradient-to-br from-teal-900/70 via-slate-800 to-slate-900 dark:from-teal-950/50 dark:via-slate-900 dark:to-black',
  ];
  return gradients[index % gradients.length];
};

// 根据报告类型返回对应的图标路径
const getReportTypeIcon = (type: string | undefined): string => {
  if (!type) {
    // 默认日历图标
    return 'M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zM9 14H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2zm-8 4H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2z';
  }
  
  const normalizedType = type.toUpperCase();
  
  // 总结/摘要图标 - 文档/文件图标
  if (normalizedType.includes('SUMMARY') || normalizedType.includes('总结')) {
    return 'M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z';
  }
  
  // 待办事项图标 - 清单/复选框图标
  if (normalizedType.includes('TODO') || normalizedType.includes('待办') || normalizedType.includes('TASK')) {
    return 'M14 10H2v2h12v-2zm0-4H2v2h12V6zM2 16h8v-2H2v2zm19.5-4.5L23 13l-6.99 7-4.51-4.5L13 14l3.01 3L21.5 11.5z';
  }
  
  // 新闻图标 - 报纸/新闻图标
  if (normalizedType.includes('NEWS') || normalizedType.includes('新闻')) {
    return 'M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z';
  }
  
  // 日历图标 - 默认
  return 'M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zM9 14H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2zm-8 4H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2z';
};

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement;
  if (img) {
    img.style.display = 'none';
    // 显示渐变背景
    const card = img.closest('.report-card');
    if (card) {
      const gradientDiv = card.querySelector('.report-gradient-background') as HTMLElement;
      if (gradientDiv) {
        gradientDiv.style.display = 'block';
      }
    }
  }
};

const handleImageLoad = (event: Event) => {
  const img = event.target as HTMLImageElement;
  if (img) {
    const card = img.closest('.report-card');
    if (card) {
      const gradientDiv = card.querySelector('.report-gradient-background') as HTMLElement;
      if (gradientDiv) {
        gradientDiv.style.display = 'none';
      }
      // 确保图片可见
      img.style.display = 'block';
    }
  }
};
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

/* 报告卡片样式 */
.report-card {
  min-height: 200px;
  height: 200px;
}

.report-card .line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.report-card .line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.report-cover-image {
  transition: transform 0.3s ease, filter 0.3s ease;
  z-index: 1;
  pointer-events: none;
  filter: saturate(0.85) brightness(0.95);
}

.report-card:hover .report-cover-image {
  transform: scale(1.01);
  filter: saturate(0.9) brightness(0.97);
}

.report-overlay-panel {
  min-height: 55px;
  height: 28%;
  max-height: 78px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.report-gradient-background {
  z-index: 1;
  pointer-events: none;
}

.report-gradient-overlay {
  height: 31%;
  pointer-events: none;
}
</style>
