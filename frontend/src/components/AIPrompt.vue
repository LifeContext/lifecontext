<template>
  <div class="bg-slate-100 dark:bg-slate-900 rounded-2xl shadow-lg p-4 h-full border border-slate-200 dark:border-slate-600">
    <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100 mb-4">Tips</h2>
    
    <!-- 加载状态 -->
    <div v-if="isLoading" class="flex items-center justify-center h-full min-h-[200px]">
      <div class="text-slate-500 dark:text-slate-400">加载中...</div>
    </div>
    
    <!-- 错误状态 -->
    <div v-else-if="error" class="flex items-center justify-center h-full min-h-[200px]">
      <div class="text-red-500 dark:text-red-400 text-center">
        <p>{{ error }}</p>
        <button 
          @click="loadTips" 
          class="mt-2 px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
        >
          重试
        </button>
      </div>
    </div>

    <!-- 无数据状态 -->
    <div v-else-if="tips.length === 0" class="flex flex-col items-center justify-center h-full min-h-[200px]">
      <svg class="w-12 h-12 text-slate-400 dark:text-slate-500 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
      </svg>
      <h3 class="text-lg font-medium text-slate-600 dark:text-slate-300 mb-2">No tips yet</h3>
      <p class="text-sm text-slate-500 dark:text-slate-400">Wait for generation</p>
    </div>
    
    <!-- Tips列表 -->
    <div v-else ref="tipsScroll" :class="['grid tips-grid gap-4 pb-2 max-h-[calc(100%-2.5rem)] overflow-y-auto', { scrolling: isScrollingTips }]">
      <div 
        v-for="tip in tips" 
        :key="tip.id"
        @click="() => props.onSelectTip(tip)"
        class="tip-card bg-white dark:bg-slate-700 rounded-lg p-3 cursor-pointer transition-all duration-300 shadow-sm hover:shadow-md relative"
      >
        <!-- 右上角图标 -->
        <div class="absolute top-3 right-3">
          <svg class="w-4 h-4" :class="getCategoryColor(tip.tip_type)" fill="currentColor" viewBox="0 0 24 24">
            <path :d="getCategoryIcon(tip.tip_type)"></path>
          </svg>
        </div>
        
        <!-- 标题 -->
        <h3 class="text-lg font-bold text-slate-900 dark:text-slate-100 mb-1 pr-6">{{ tip.title }}</h3>
        
        <!-- 描述（Markdown 渲染，限制高度作为预览） -->
        <div 
          class="text-sm text-slate-600 dark:text-slate-300 mb-1 markdown-content markdown-preview"
          v-html="renderMarkdown(tip.content)"
        ></div>
        
        <!-- 时间戳 -->
        <p class="text-xs text-slate-500 dark:text-slate-400">{{ formatTimeAgo(tip.create_time) }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, defineProps } from 'vue';
import { marked } from 'marked';
import { tipService } from '../api/tipService';
import type { Tip, TipCategory } from '../../types';

interface Props {
  onSelectTip: (tip: Tip) => void;
}

const props = defineProps<Props>();

// 响应式数据
const tips = ref<Tip[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);

// 分类图标配置
const TIP_CATEGORY_ICONS = {
  blocker: 'M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z',
  task: 'M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z',
  collaboration: 'M16.5 13c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM9 13c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm4.5 9.5c-2.5 0-4.5-2-4.5-4.5H5c0 3.9 3.1 7 7 7s7-3.1 7-7h-4.5c0 2.5-2 4.5-4.5 4.5zM12 1c-3.9 0-7 3.1-7 7h4.5c0-2.5 2-4.5 4.5-4.5s4.5 2 4.5 4.5H19c0-3.9-3.1-7-7-7z',
  planning: 'M17 12h-5v5h5v-5zM16 1v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2h-1V1h-2zm3 18H5V8h14v11z',
  research: 'M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z'
};

const tipCategoryConfig: { [key in TipCategory]: { icon: string; color: string; } } = {
  DEEP_DIVE: { icon: TIP_CATEGORY_ICONS.blocker, color: 'text-red-500 dark:text-red-400' },
  RESOURCE_RECOMMENDATION: { icon: TIP_CATEGORY_ICONS.task, color: 'text-blue-500 dark:text-blue-400' },
  RISK_ANALYSIS: { icon: TIP_CATEGORY_ICONS.collaboration, color: 'text-green-500 dark:text-green-400' },
  KNOWLEDGE_EXPANSION: { icon: TIP_CATEGORY_ICONS.planning, color: 'text-yellow-500 dark:text-yellow-400' },
  ALTERNATIVE_PERSPECTIVE: { icon: TIP_CATEGORY_ICONS.research, color: 'text-purple-500 dark:text-purple-400' }
};

const getCategoryIcon = (category: string) => {
  const defaultCategory = 'suggestion'; // 默认分类
  const validCategory = category && tipCategoryConfig[category as TipCategory] ? category as TipCategory : defaultCategory;
  return tipCategoryConfig[validCategory].icon;
};

const getCategoryColor = (category: string) => {
  const defaultCategory = 'suggestion'; // 默认分类
  const validCategory = category && tipCategoryConfig[category as TipCategory] ? category as TipCategory : defaultCategory;
  return tipCategoryConfig[validCategory].color;
};

// 加载tips数据
const loadTips = async () => {
  try {
    isLoading.value = true;
    error.value = null;
    const tipsData = await tipService.getTips();
    tips.value = tipsData.data.tips;
  } catch (err) {
    console.error('Failed to load tips:', err);
    error.value = 'Failed to load tips. Please try again later.';
  } finally {
    isLoading.value = false;
  }
};

// 截断内容函数
// 保留：如需在渲染前做裁剪可复用
const truncateContent = (content: string): string => {
  if (!content) return '';
  return content.length > 100 
    ? content.substring(0, 100) + '...'
    : content;
};

// Markdown 渲染
const renderMarkdown = (content: string): string => {
  if (!content) return '';
  return marked.parse(content);
};

// 格式化时间函数
const formatTimeAgo = (dateString: string): string => {
  if (!dateString) return '';
  
  const now = new Date();
  const date = new Date(dateString);
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (diffInSeconds < 60) {
    return '刚刚';
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes} 分钟前`;
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours} 小时前`;
  } else if (diffInSeconds < 2592000) {
    const days = Math.floor(diffInSeconds / 86400);
    return `${days} 天前`;
  } else {
    return date.toLocaleDateString();
  }
};

// 组件挂载时加载数据
onMounted(() => {
  loadTips();
  if (tipsScroll.value) tipsScroll.value.addEventListener('scroll', handleTipsScroll);
});

onUnmounted(() => {
  if (tipsScroll.value) tipsScroll.value.removeEventListener('scroll', handleTipsScroll);
  if (tipsScrollTimer) window.clearTimeout(tipsScrollTimer);
});

const tipsScroll = ref<HTMLElement | null>(null);
const isScrollingTips = ref(false);
let tipsScrollTimer: number | undefined;
const handleTipsScroll = () => {
  isScrollingTips.value = true;
  if (tipsScrollTimer) window.clearTimeout(tipsScrollTimer);
  tipsScrollTimer = window.setTimeout(() => (isScrollingTips.value = false), 600);
};
</script>

<style scoped>
/* 垂直滚动条样式 */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

/* 悬停或滚动时显示滚动条 */
.overflow-y-auto:hover::-webkit-scrollbar-thumb,
.overflow-y-auto.scrolling::-webkit-scrollbar-thumb {
  opacity: 1;
}

.dark .overflow-y-auto::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.dark .overflow-y-auto::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
}

.dark .overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.overflow-y-auto { scrollbar-width: none; }
.overflow-y-auto:hover,
.overflow-y-auto.scrolling { scrollbar-width: thin; }

/* 卡片样式 */
.tip-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  aspect-ratio: 1/1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  min-height: 100px;
  max-height: 200px;
}

.tip-card h3 {
  font-size: 1rem;
  line-height: 1.2;
  min-height: 2rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.tip-card p {
  font-size: 0.8rem;
}

.tip-card:hover {
  transform: translateY(-3px);
  box-shadow: 
    0 10px 30px rgba(0, 0, 0, 0.08),
    0 4px 12px rgba(0, 0, 0, 0.04);
  border-color: rgba(59, 130, 246, 0.2);
}

.tip-card:hover h3 {
  color: #1e40af;
  font-weight: 700;
}

.tip-card:hover p {
  color: #1f2937;
}

.tip-card:hover .text-xs {
  color: #6b7280;
}

.dark .tip-card:hover {
  box-shadow: 
    0 10px 30px rgba(0, 0, 0, 0.4),
    0 4px 12px rgba(0, 0, 0, 0.2);
  border-color: rgba(96, 165, 250, 0.3);
}

.dark .tip-card:hover h3 {
  color: #93c5fd;
  font-weight: 700;
}

.dark .tip-card:hover p {
  color: #1f2937;
}

.dark .tip-card:hover .text-xs {
  color: #94a3b8;
}

/* 文本截断样式 */
.line-clamp-4 {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 悬浮时的文字增强 */
.tip-card:hover h3 {
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.dark .tip-card:hover h3 {
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* 悬浮时的图标增强 */
.tip-card:hover svg {
  transform: scale(1.1);
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

.dark .tip-card:hover svg {
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

/* 悬浮时的过渡效果 */
.tip-card h3,
.tip-card p,
.tip-card svg {
  transition: all 0.2s ease;
}

/* 自适应列：默认宽度下约为 5 列，容器更宽（daily 折叠）时能扩到 6 列 */
.tips-grid {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}


/* 移动端降列 */
@media (max-width: 768px) {
  .tips-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .tips-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

/* Markdown 预览样式与高度裁剪 */
.markdown-content {
  line-height: 1.6;
}

.markdown-content p,
.markdown-content ul,
.markdown-content ol,
.markdown-content pre,
.markdown-content blockquote {
  margin: 0.25rem 0;
}

.markdown-content code {
  background-color: rgba(0, 0, 0, 0.06);
  padding: 0.1em 0.3em;
  border-radius: 0.25em;
}

.dark .markdown-content code {
  background-color: rgba(255, 255, 255, 0.12);
}

.markdown-preview {
  max-height: 5.5rem; /* 约 3-4 行高度 */
  overflow: hidden;
}
</style>
