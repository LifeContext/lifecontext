<template>
  <div class="flex h-full w-full gap-4 p-4">
    <aside class="w-72 flex-shrink-0 bg-slate-200 dark:bg-slate-800 rounded-2xl p-4 flex flex-col shadow-lg">
      <h1 class="text-lg font-bold text-slate-900 dark:text-slate-100 px-2 my-2">All Tips</h1>
      <nav class="flex-1 overflow-y-auto pr-1">
        <ul>
          <li v-for="tip in props.tips" :key="tip.id">
            <button 
              @click="() => props.onSelectTip(tip)"
              :class="`w-full text-left flex items-center gap-3 p-3 rounded-lg font-medium text-sm transition-colors ${
                props.selectedTip.id === tip.id 
                  ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300' 
                  : 'text-slate-600 dark:text-slate-300 hover:bg-slate-300/50 dark:hover:bg-slate-700/50'
              }`"
            >
              <Icon :path="getCategoryIcon(tip.tip_type)" :class="`h-4 w-4 flex-shrink-0 ${getCategoryColor(tip.tip_type)}`" />
              <span class="truncate">{{ tip.title }}</span>
            </button>
          </li>
        </ul>
      </nav>
    </aside>

    <main class="relative flex-1 bg-slate-200 dark:bg-slate-800 rounded-2xl p-8 overflow-y-auto shadow-lg flex flex-col">
      <button 
        @click="props.onClose" 
        class="absolute top-6 right-6 p-2 rounded-full text-slate-500 dark:text-slate-400 hover:bg-slate-300 dark:hover:bg-slate-700 z-10"
        aria-label="Close tips view"
      >
        <Icon path="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" class="h-6 w-6" />
      </button>
      
      <div class="flex-1 flex flex-col">
        <header class="mb-8">
          <h1 class="text-4xl font-bold text-slate-900 dark:text-slate-100 mb-2">{{ selectedTip.title }}</h1>
          <p class="text-lg text-slate-500 dark:text-slate-400">{{ formatDateTime(selectedTip.create_time) }}</p>
        </header>
        
        <div class="flex-1 bg-white dark:bg-slate-700 rounded-2xl p-8 shadow-inner">
          <section class="h-full">
            <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6 flex items-center gap-3">
              <Icon path="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7z" class="h-6 w-6 text-yellow-400" />
              <span>Tip Content</span>
            </h2>
            <div class="prose prose-lg max-w-none dark:prose-invert text-slate-700 dark:text-slate-300 markdown-content h-full">
              <div v-html="renderedContent"></div>
            </div>
          </section>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { marked } from 'marked';
import Icon from './Icon.vue';
import type { Tip, TipCategory } from '../../types';

interface Props {
  tips: Tip[];
  selectedTip: Tip;
  onSelectTip: (tip: Tip) => void;
  onClose: () => void;
}

const props = defineProps<Props>();

const formatDateTime = (dateTime: string): string => {
  if (!dateTime) return '';
  if (dateTime.includes('.')) {
    return dateTime.split('.')[0];
  }
  return dateTime;
};

// Markdown 渲染
const renderedContent = computed(() => {
  if (!props.selectedTip?.content) return '';
  return marked(props.selectedTip.content);
});

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
</script>

<style scoped>
.tip-detail {
  min-height: calc(100vh - 2rem);
}

/* 侧边栏滚动条样式 */
aside nav::-webkit-scrollbar {
  width: 6px;
}

aside nav::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

aside nav::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

aside nav::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

.dark aside nav::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.dark aside nav::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
}

.dark aside nav::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* 主内容区域滚动条样式 */
main::-webkit-scrollbar {
  width: 8px;
}

main::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

main::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

main::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

.dark main::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.dark main::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
}

.dark main::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* 确保内容区域有足够的高度 */
main {
  height: calc(100vh - 2rem);
  max-height: calc(100vh - 2rem);
  overflow-y: auto;
  min-height: calc(100vh - 2rem);
}

/* 侧边栏高度限制 */
aside {
  height: calc(100vh - 2rem);
  max-height: calc(100vh - 2rem);
  min-height: calc(100vh - 2rem);
}

aside nav {
  height: calc(100vh - 8rem); /* 减去标题和padding的高度 */
  max-height: calc(100vh - 8rem);
}

/* 内容卡片样式 */
.bg-white.dark\\:bg-slate-700 {
  min-height: calc(100vh - 12rem);
  display: flex;
  flex-direction: column;
}

.bg-white.dark\\:bg-slate-700 section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.bg-white.dark\\:bg-slate-700 .markdown-content {
  flex: 1;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .flex {
    flex-direction: column;
  }
  
  aside {
    width: 100%;
    max-height: 40vh;
    min-height: 40vh;
  }
  
  main {
    max-height: 60vh;
    min-height: 60vh;
  }
}

/* 滚动条在Firefox中的样式 */
aside nav {
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) rgba(0, 0, 0, 0.05);
}

main {
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) rgba(0, 0, 0, 0.05);
}

.dark aside nav {
  scrollbar-color: rgba(255, 255, 255, 0.2) rgba(255, 255, 255, 0.05);
}

.dark main {
  scrollbar-color: rgba(255, 255, 255, 0.2) rgba(255, 255, 255, 0.05);
}

/* Markdown内容样式（与日报详情保持一致的小一号排版） */
.prose h1, .prose h2, .prose h3, .prose h4, .prose h5, .prose h6 {
  color: rgb(15 23 42);
  font-weight: 600;
  line-height: 1.25;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

.dark .prose h1, .dark .prose h2, .dark .prose h3, .dark .prose h4, .dark .prose h5, .dark .prose h6 {
  color: rgb(241 245 249);
}

.prose p {
  margin-top: 1em;
  margin-bottom: 1em;
  line-height: 1.7;
}

.prose ul, .prose ol {
  margin-top: 1em;
  margin-bottom: 1em;
  padding-left: 1.5em;
}

.prose li {
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

.prose blockquote {
  border-left: 4px solid rgb(59 130 246);
  padding-left: 1em;
  margin: 1.5em 0;
  font-style: italic;
  color: rgb(71 85 105);
}

.dark .prose blockquote {
  color: rgb(148 163 184);
  border-left-color: rgb(96 165 250);
}

.prose code {
  background-color: rgb(241 245 249);
  padding: 0.125em 0.25em;
  border-radius: 0.25em;
  font-size: 0.875em;
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace;
}

.dark .prose code {
  background-color: rgb(30 41 59);
  color: rgb(241 245 249);
}

.prose pre {
  background-color: rgb(241 245 249);
  border-radius: 0.5em;
  padding: 1em;
  overflow-x: auto;
  margin: 1.5em 0;
}

.dark .prose pre {
  background-color: rgb(30 41 59);
}

.prose pre code {
  background-color: transparent;
  padding: 0;
  font-size: 0.875em;
}

.prose a {
  color: rgb(59 130 246);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.prose a:hover {
  color: rgb(37 99 235);
}

.dark .prose a {
  color: rgb(96 165 250);
}

.dark .prose a:hover {
  color: rgb(147 197 253);
}

.markdown-content {
  line-height: 1.7;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  font-weight: 600;
}

.markdown-content p {
  margin-bottom: 1em;
}

.markdown-content ul,
.markdown-content ol {
  margin-bottom: 1em;
  padding-left: 1.5em;
}

.markdown-content li {
  margin-bottom: 0.25em;
}

.markdown-content code {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 0.125em 0.25em;
  border-radius: 0.25em;
  font-size: 0.875em;
}

.dark .markdown-content code {
  background-color: rgba(255, 255, 255, 0.1);
}

.markdown-content pre {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 1em;
  border-radius: 0.5em;
  overflow-x: auto;
  margin: 1em 0;
}

.dark .markdown-content pre {
  background-color: rgba(255, 255, 255, 0.05);
}

.markdown-content blockquote {
  border-left: 4px solid #3b82f6;
  padding-left: 1em;
  margin: 1em 0;
  font-style: italic;
}

.markdown-content strong {
  font-weight: 600;
}

.markdown-content em {
  font-style: italic;
}
</style>
