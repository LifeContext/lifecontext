<template>
  <div class="bg-slate-50 dark:bg-slate-900 h-full flex flex-col">
    <!-- Header with date selector and clear history -->
    <div class="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-800">
      <!-- Date Selector -->
      <div class="relative">
        <button 
          @click="toggleDateDropdown"
          class="flex items-center space-x-2 text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors"
        >
          <span class="text-lg font-semibold">{{ selectedDateText }}</span>
          <Icon path="M19 9l-7 7-7-7" class="w-4 h-4" />
        </button>
        
        <!-- Date Dropdown -->
        <div 
          v-if="isDateDropdownOpen"
          class="absolute top-full left-0 mt-2 w-48 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 z-10"
        >
          <div 
            v-for="date in dateOptions" 
            :key="date.value"
            @click="selectDate(date)"
            :class="`px-4 py-3 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors ${
              selectedDate === date.value ? 'bg-blue-50 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400' : 'text-slate-700 dark:text-slate-300'
            }`"
          >
            {{ date.label }}
          </div>
        </div>
      </div>
      
      <!-- Clear History Button -->
      <div class="relative">
        <button 
          @click="toggleClearDropdown"
          class="flex items-center space-x-2 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
        >
          <Icon path="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" class="w-4 h-4" />
          <span class="text-sm font-medium">Clear History</span>
        </button>
        
        <!-- Clear History Dropdown -->
        <div 
          v-if="isClearDropdownOpen"
          class="absolute top-full right-0 mt-2 w-48 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 z-10"
        >
          <div 
            @click="clearHistory('24h')"
            class="px-4 py-3 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-slate-700 dark:text-slate-300"
          >
            Clear last 24 hours
          </div>
          <div 
            @click="clearHistory('all')"
            class="px-4 py-3 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-red-600 dark:text-red-400"
          >
            Clear all history
          </div>
        </div>
      </div>
    </div>
    
    <!-- Main Content Area -->
    <div class="flex-1 p-6 overflow-y-auto">
      <!-- Loading State -->
      <div v-if="isAnalyzing" class="flex flex-col items-center justify-center h-full">
        <div class="relative">
          <div class="w-12 h-12 border-4 border-blue-200 border-t-blue-600 dark:border-blue-800 dark:border-t-blue-500 rounded-full animate-spin"></div>
        </div>
        <p class="mt-4 text-slate-600 dark:text-slate-400 text-lg">Analyzing activity...</p>
      </div>
      
      <!-- No Activity State -->
      <div v-else-if="!hasActivity" class="flex flex-col items-center justify-center h-full">
        <div class="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
          <Icon path="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" class="w-8 h-8 text-slate-400 dark:text-slate-500" />
        </div>
        <p class="text-slate-500 dark:text-slate-400 text-lg">No activity recorded for this day.</p>
      </div>
      
      <!-- Timeline Content -->
      <div v-else class="space-y-8">
        <div 
          v-for="(segment, index) in timelineSegments" 
          :key="segment.id"
          class="relative"
        >
          <!-- Timeline Line -->
          <div 
            v-if="index < timelineSegments.length - 1"
            class="absolute left-6 top-12 w-0.5 h-16 bg-blue-200 dark:bg-blue-900"
          ></div>
          
          <!-- Timeline Dot -->
          <div class="absolute left-5 top-6 w-3 h-3 bg-blue-500 rounded-full"></div>
          
          <!-- Content -->
          <div class="ml-12">
            <div class="flex items-center space-x-4 mb-4">
              <h3 class="text-lg font-semibold text-slate-800 dark:text-slate-200">{{ segment.title }}</h3>
              <span class="text-sm text-slate-500 dark:text-slate-400">{{ segment.start_time }}</span>
            </div>
            
            <!-- Activity Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              <div 
                v-for="activity in segment.activities" 
                :key="activity.id"
                class="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4 hover:shadow-md transition-shadow cursor-pointer"
              >
                <div class="aspect-video bg-slate-100 dark:bg-slate-700 rounded-lg mb-3 overflow-hidden">
                  <img 
                    v-if="activity.thumbnailUrl" 
                    :src="activity.thumbnailUrl" 
                    :alt="activity.title"
                    class="w-full h-full object-cover"
                  />
                  <div v-else class="w-full h-full flex items-center justify-center">
                    <Icon path="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" class="w-8 h-8 text-slate-400 dark:text-slate-500" />
                  </div>
                </div>
                <h4 class="font-medium text-slate-800 dark:text-slate-200 text-sm mb-1 line-clamp-2">{{ activity.title }}</h4>
                <p class="text-xs text-slate-500 dark:text-slate-400">{{ activity.domain }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import Icon from './Icon.vue';
import { timelineService } from '../api/timelineService';
import { eventService } from '../api/eventService';
import type { TimelineItem, TimelineSegment } from '../../types';

// State
const selectedDate = ref('today');
const isDateDropdownOpen = ref(false);
const isClearDropdownOpen = ref(false);
const isAnalyzing = ref(false);
const hasActivity = ref(true);
const timelineSegments = ref<TimelineSegment[]>([]);
const dateOptions = ref<{ label: string; value: string }[]>([]);

// Computed
const selectedDateText = computed(() => {
  const option = dateOptions.value.find(opt => opt.value === selectedDate.value);
  return option ? option.label : 'Monday, October 20, 2025';
});

// Methods
const toggleDateDropdown = () => {
  isDateDropdownOpen.value = !isDateDropdownOpen.value;
  isClearDropdownOpen.value = false;
};

const toggleClearDropdown = () => {
  isClearDropdownOpen.value = !isClearDropdownOpen.value;
  isDateDropdownOpen.value = false;
};

const selectDate = async (date: { label: string; value: string }) => {
  selectedDate.value = date.value;
  isDateDropdownOpen.value = false;
  
  // 开始加载状态
  isAnalyzing.value = true;
  
  try {
    // 从后端获取Timeline数据
    const segments = await timelineService.getTimelineByDate(date.value);
    timelineSegments.value = segments;
    hasActivity.value = segments.length > 0;
  } catch (error) {
    console.error('Error loading timeline data:', error);
    timelineSegments.value = [];
    hasActivity.value = false;
  } finally {
    isAnalyzing.value = false;
  }
};

const clearHistory = async (type: '24h' | 'all') => {
  isClearDropdownOpen.value = false;
  
  try {
    const success = await timelineService.clearHistory(type);
    if (success) {
      // 重新加载当前日期的数据
      await selectDate({ label: selectedDateText.value, value: selectedDate.value });
    }
  } catch (error) {
    console.error('Error clearing history:', error);
  }
};

const refreshTimelineData = async () => {
  console.log('刷新时间线数据...');
  try {
    const segments = await timelineService.getTimelineByDate(selectedDate.value);
    timelineSegments.value = segments;
    hasActivity.value = segments.length > 0;
    console.log('时间线数据已刷新');
  } catch (error) {
    console.error('刷新时间线数据失败:', error);
  }
};

// Close dropdowns when clicking outside
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement;
  if (!target.closest('.relative')) {
    isDateDropdownOpen.value = false;
    isClearDropdownOpen.value = false;
  }
};

// 加载可用日期和初始数据
const loadInitialData = async () => {
  try {
    // 获取可用日期
    const dates = await timelineService.getAvailableDates();
    dateOptions.value = dates;
    
    // 加载当前选中日期的数据
    await selectDate({ label: 'Today', value: 'today' });
  } catch (error) {
    console.error('Error loading initial data:', error);
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
  loadInitialData();
  
  // 注册活动事件监听器
  eventService.onEvent('activity', () => {
    refreshTimelineData();
  });
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
  
  // 移除事件监听器
  eventService.offEvent('activity');
});
</script>

<style scoped>
/* 滚动条样式 */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.4) 0%, rgba(148, 163, 184, 0.2) 100%);
  border-radius: 3px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.2s ease;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.6) 0%, rgba(148, 163, 184, 0.4) 100%);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.overflow-y-auto::-webkit-scrollbar-thumb:active {
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.8) 0%, rgba(148, 163, 184, 0.6) 100%);
}

/* 暗色模式滚动条 */
.dark .overflow-y-auto::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(71, 85, 105, 0.4) 0%, rgba(71, 85, 105, 0.2) 100%);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.dark .overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, rgba(71, 85, 105, 0.6) 0%, rgba(71, 85, 105, 0.4) 100%);
  border: 1px solid rgba(0, 0, 0, 0.2);
}

.dark .overflow-y-auto::-webkit-scrollbar-thumb:active {
  background: linear-gradient(180deg, rgba(71, 85, 105, 0.8) 0%, rgba(71, 85, 105, 0.6) 100%);
}

/* Firefox 滚动条样式 */
.overflow-y-auto {
  scrollbar-width: thin;
  scrollbar-color: rgba(148, 163, 184, 0.3) transparent;
}

.dark .overflow-y-auto {
  scrollbar-color: rgba(71, 85, 105, 0.3) transparent;
}

/* 滚动条淡入淡出效果 */
.overflow-y-auto {
  transition: scrollbar-color 0.3s ease;
}
</style>
