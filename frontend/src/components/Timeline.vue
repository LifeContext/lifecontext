<template>
  <div class="bg-slate-50 dark:bg-slate-900 h-full flex flex-col">
    <!-- Header with date selector and clear history -->
    <div class="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-800 max-w-[900px] mx-auto w-full">
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
    <div class="flex-1 p-6 overflow-y-auto max-w-[900px] mx-auto w-full">
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
      <div v-else class="space-y-10">
        <div 
          v-for="(segment, index) in timelineSegments" 
          :key="segment.id"
          class="relative"
        >
          <!-- Timeline Line -->
          <div 
            v-if="index < timelineSegments.length - 1"
            class="absolute left-6 top-12 w-0.5 h-full bg-slate-200 dark:bg-slate-700"
          ></div>
          
          <!-- Timeline Dot -->
          <div class="absolute left-5 top-6 w-3 h-3 bg-blue-500 rounded-full shadow"></div>
          
          <!-- Content -->
          <div class="ml-12">
            <!-- Section Header -->
            <div class="flex items-center space-x-3 mb-3">
              <!-- Segment Select Checkbox -->
              <input 
                type="checkbox" 
                :checked="isSegmentChecked(segment)" 
                @change="toggleSegment(segment)"
                class="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-blue-600 focus:ring-blue-500"
              />
              <h3 class="text-base font-semibold text-slate-800 dark:text-slate-200">{{ segment.title }}</h3>
            </div>
            
            <!-- Activity List -->
            <ul class="divide-y divide-slate-200 dark:divide-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
              <li 
                v-for="(url, i) in getUrls(segment)" 
                :key="i"
                class="flex items-center gap-3 px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition"
              >
                <!-- Item Select Checkbox -->
                <input 
                  type="checkbox" 
                  :checked="isItemChecked(segment.id, url)" 
                  @change="toggleItem(segment.id, url)"
                  class="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-blue-600 focus:ring-blue-500"
                />
                <span class="w-4 h-4 shrink-0 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center">
                  <svg class="w-3 h-3 text-slate-500 dark:text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M2 12h20M12 2a15.3 15.3 0 010 20a15.3 15.3 0 010-20z"></path></svg>
                </span>
                <div class="min-w-0">
                  <a :href="url" target="_blank" rel="noopener" class="block text-sm font-medium text-slate-800 dark:text-slate-200 truncate hover:underline">{{ formatTitle(url) }}</a>
                  <p class="text-[11px] text-slate-500 dark:text-slate-400 truncate">{{ extractHostname(url) }}</p>
                </div>
              </li>
            </ul>
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
const allSegments = ref<TimelineSegment[]>([]);
const dateOptions = ref<{ label: string; value: string }[]>([]);

// Computed
const selectedDateText = computed(() => {
  const option = dateOptions.value.find(opt => opt.value === selectedDate.value);
  return option ? option.label : '';
});

// Helpers for URL display
const extractHostname = (url: string): string => {
  try {
    const u = new URL(url);
    return u.hostname.replace(/^www\./, '');
  } catch {
    return url;
  }
};

const formatTitle = (url: string): string => {
  try {
    const u = new URL(url);
    const path = decodeURIComponent(u.pathname).replace(/\/+$/, '');
    const clean = `${u.hostname.replace(/^www\./, '')}${path ? ' - ' + path.split('/').filter(Boolean).slice(-1)[0] : ''}`;
    return clean || url;
  } catch {
    return url;
  }
};

// 从 segment 取得 url 列表
const getUrls = (segment: any): string[] => {
  return segment.urls as string[];
};

const selectedItemKeys = ref<Set<string>>(new Set());
const makeKey = (segmentId: number, url: string) => `${segmentId}::${url}`;

const isItemChecked = (segmentId: number, url: string): boolean => {
  return selectedItemKeys.value.has(makeKey(segmentId, url));
};

const toggleItem = (segmentId: number, url: string) => {
  const key = makeKey(segmentId, url);
  const next = new Set(selectedItemKeys.value);
  if (next.has(key)) next.delete(key); else next.add(key);
  selectedItemKeys.value = next;
};

const isSegmentChecked = (segment: any): boolean => {
  const urls = getUrls(segment) || [];
  if (urls.length === 0) return false;
  return urls.every(u => selectedItemKeys.value.has(makeKey(segment.id, u)));
};

const toggleSegment = (segment: any) => {
  const urls = getUrls(segment) || [];
  const allSelected = urls.length > 0 && urls.every(u => selectedItemKeys.value.has(makeKey(segment.id, u)));
  const next = new Set(selectedItemKeys.value);
  if (allSelected) {
    for (const u of urls) next.delete(makeKey(segment.id, u));
  } else {
    for (const u of urls) next.add(makeKey(segment.id, u));
  }
  selectedItemKeys.value = next;
};

// Build date options from all segments
const buildDateOptions = (segments: TimelineSegment[]) => {
  const set = new Set<string>();
  const now = new Date();
  const opts: { label: string; value: string }[] = [];
  for (const s of segments) {
    const d = new Date(s.start_time);
    const key = d.toISOString().slice(0, 10);
    if (!set.has(key)) {
      set.add(key);
      const isToday = d.toDateString() === now.toDateString();
      const y = new Date(now.getTime() - 24*60*60*1000);
      const isYesterday = d.toDateString() === y.toDateString();
      let label = d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
      let value = key;
      if (isToday) { label = 'Today'; value = 'today'; }
      else if (isYesterday) { label = 'Yesterday'; value = 'yesterday'; }
      opts.push({ label, value });
    }
  }
  // 可按时间倒序
  dateOptions.value = opts.sort((a,b)=> a.label==='Today'? -1 : a.label==='Yesterday' && b.label!=='Today' ? -1 : a.value < b.value ? 1 : -1);
};

// Filter segments by selected date
const applyDateFilter = (value: string) => {
  let targetStart: Date;
  let targetEnd: Date;
  const now = new Date();
  if (value === 'today') {
    targetStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  } else if (value === 'yesterday') {
    targetStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()-1);
  } else {
    const [y,m,d] = value.split('-').map(Number);
    targetStart = new Date(y, m-1, d);
  }
  targetEnd = new Date(targetStart);
  targetEnd.setDate(targetStart.getDate()+1);
  const filtered = allSegments.value.filter(s => {
    const t = new Date(s.start_time);
    return t >= targetStart && t < targetEnd;
  });
  timelineSegments.value = filtered;
  hasActivity.value = filtered.length > 0;
};

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
  isAnalyzing.value = true;
  try {
    applyDateFilter(date.value);
  } finally {
    isAnalyzing.value = false;
  }
};

const clearHistory = async (type: '24h' | 'all') => {
  isClearDropdownOpen.value = false;
  
  try {
    applyDateFilter(selectedDate.value);
  } catch (error) {
    console.error('Error clearing history:', error);
  }
};

const refreshTimelineData = async () => {
  console.log('刷新时间线数据...');
  try {
    const resp = await timelineService.getTimelineSegments();
    const segs = (resp as any)?.data?.activities ?? (resp as any);
    allSegments.value = Array.isArray(segs) ? segs : [];
    buildDateOptions(allSegments.value);
    applyDateFilter(selectedDate.value);
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
    const resp = await timelineService.getTimelineSegments();
    const segs = (resp as any)?.data?.activities ?? (resp as any);
    allSegments.value = Array.isArray(segs) ? segs : [];
    buildDateOptions(allSegments.value);
    // 默认选择 Today（若不存在则选择第一项）
    const defaultOpt = dateOptions.value.find(o=>o.value==='today') || dateOptions.value[0];
    if (defaultOpt) {
      selectedDate.value = defaultOpt.value;
      applyDateFilter(defaultOpt.value);
    } else {
      timelineSegments.value = [];
      hasActivity.value = false;
    }
  } catch (error) {
    console.error('Error loading timeline data:', error);
    timelineSegments.value = [];
    hasActivity.value = false;
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
