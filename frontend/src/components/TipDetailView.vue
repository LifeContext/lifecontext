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
      
      <div class="flex-1 flex flex-col overflow-hidden">
        <header class="sticky-header flex-shrink-0">

          <h1 class="text-4xl font-bold text-slate-900 dark:text-slate-100 mb-2">{{ selectedTip.title }}</h1>
          <p class="text-lg text-slate-500 dark:text-slate-400">{{ formatTimeAgo(selectedTip.create_time) }}</p>

        </header>
        
        <div class="flex-1 bg-white dark:bg-slate-700 rounded-2xl p-8 shadow-inner overflow-y-auto">
          <section class="h-full">
            <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6 flex items-center gap-3">
              <Icon path="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7z" class="h-6 w-6 text-yellow-400" />
              <span>Tip Content</span>
            </h2>
            <div class="markdown-content max-w-7xl mx-auto text-slate-700 dark:text-slate-300 h-full">
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

// 规范化后端返回的 Markdown 文本中的换行/回车
const normalizeMarkdown = (raw: string): string => {
  if (!raw) return '';
  let text = raw.replace(/\\r\\n/g, '\n').replace(/\\n/g, '\n');
  text = text.replace(/\r/g, '');
  return text;
};

// Markdown 渲染
const renderedContent = computed(() => {
  if (!props.selectedTip?.content) return '';
  marked.setOptions({
    gfm: true,
    breaks: true
  });
  const normalized = normalizeMarkdown(props.selectedTip.content);
  return marked(normalized);
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

main {
  height: calc(100vh - 2rem);
  max-height: calc(100vh - 2rem);
  overflow: hidden;
  min-height: calc(100vh - 2rem);
}

/* 侧边栏高度限制 */
aside {
  height: calc(100vh - 2rem);
  max-height: calc(100vh - 2rem);
  min-height: calc(100vh - 2rem);
}

aside nav {
  height: calc(100vh - 8rem);
  max-height: calc(100vh - 8rem);
}

/* 固定标题栏样式 */
.sticky-header {
  padding-top: 0;
  padding-bottom: 1.5rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  padding-left: 0;
  padding-right: 0;
}

.dark .sticky-header {
  border-bottom-color: rgba(148, 163, 184, 0.2);
}

/* 内容区域滚动条样式 */
.bg-white.dark\\:bg-slate-700::-webkit-scrollbar {
  width: 8px;
}

.bg-white.dark\\:bg-slate-700::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

.bg-white.dark\\:bg-slate-700::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.bg-white.dark\\:bg-slate-700::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

.dark .bg-white.dark\\:bg-slate-700::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.dark .bg-white.dark\\:bg-slate-700::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
}

.dark .bg-white.dark\\:bg-slate-700::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.bg-white.dark\\:bg-slate-700 {
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) rgba(0, 0, 0, 0.05);
}

.dark .bg-white.dark\\:bg-slate-700 {
  scrollbar-color: rgba(255, 255, 255, 0.2) rgba(255, 255, 255, 0.05);
}

/* 内容卡片样式 */
.bg-white.dark\\:bg-slate-700 {
  min-height: calc(100vh - 12rem);
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
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

/* Markdown内容样式 */
:deep(.prose h1), :deep(.prose h2), :deep(.prose h3), :deep(.prose h4), :deep(.prose h5), :deep(.prose h6) {
  color: rgb(15 23 42);
  font-weight: 600;
  line-height: 1.25;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

:global(.dark) :deep(.prose h1), :global(.dark) :deep(.prose h2), :global(.dark) :deep(.prose h3), :global(.dark) :deep(.prose h4), :global(.dark) :deep(.prose h5), :global(.dark) :deep(.prose h6) {
  color: #ffffff !important;
}

:deep(.prose p) {
  margin-top: 1em;
  margin-bottom: 1em;
  line-height: 1.7;
}

:deep(.prose ul), :deep(.prose ol) {
  margin-top: 1em;
  margin-bottom: 1em;
  padding-left: 1.5em;
}

:deep(.prose li) {
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

:deep(.prose blockquote) {
  border-left: 4px solid rgb(59 130 246);
  padding-left: 1em;
  margin: 1.5em 0;
  font-style: italic;
  color: rgb(71 85 105);
}

:global(.dark) :deep(.prose blockquote) {
  color: rgb(148 163 184);
  border-left-color: rgb(96 165 250);
}

:deep(.prose code) {
  background-color: rgb(241 245 249);
  padding: 0.125em 0.25em;
  border-radius: 0.25em;
  font-size: 0.875em;
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace;
}

:global(.dark) :deep(.prose code) {
  background-color: rgb(30 41 59);
  color: rgb(241 245 249);
}

:deep(.prose pre) {
  background-color: rgb(241 245 249);
  border-radius: 0.5em;
  padding: 1em;
  overflow-x: auto;
  margin: 1.5em 0;
}

:global(.dark) :deep(.prose pre) {
  background-color: rgb(30 41 59);
}

:deep(.prose pre code) {
  background-color: transparent;
  padding: 0;
  font-size: 0.875em;
}

:deep(.prose a) {
  color: rgb(59 130 246);
  text-decoration: underline;
  text-underline-offset: 2px;
}

:deep(.prose a:hover) {
  color: rgb(37 99 235);
}

:global(.dark) :deep(.prose a) {
  color: rgb(96 165 250);
}

:global(.dark) :deep(.prose a:hover) {
  color: rgb(147 197 253);
}

:deep(.prose table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5em 0;
}

:deep(.prose th), :deep(.prose td) {
  border: 1px solid rgb(226 232 240);
  padding: 0.5em 0.75em;
  text-align: left;
}

:global(.dark) :deep(.prose th), :global(.dark) :deep(.prose td) {
  border-color: rgb(51 65 85);
}

:deep(.prose th) {
  background-color: rgb(248 250 252);
  font-weight: 600;
}

:global(.dark) :deep(.prose th) {
  background-color: rgb(30 41 59);
}

:deep(.prose hr) {
  border: none;
  border-top: 1px solid rgb(226 232 240);
  margin: 2em 0;
}

:global(.dark) :deep(.prose hr) {
  border-top-color: rgb(51 65 85);
}

:deep(.prose img) {
  max-width: 100%;
  height: auto;
  border-radius: 0.5em;
  margin: 1em 0;
}

:deep(.markdown-content) {
  line-height: 1.8;
  font-size: 16px;
}

:global(.dark) :deep(.markdown-content) {
  color: rgb(226 232 240) !important;
}

:deep(.markdown-content h1),
:deep(.markdown-content h2),
:deep(.markdown-content h3),
:deep(.markdown-content h4),
:deep(.markdown-content h5),
:deep(.markdown-content h6) {
  color: rgb(15 23 42) !important;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  font-weight: 700;
}

:deep(.markdown-content h1) { font-size: 1.875rem; }
:deep(.markdown-content h2) { font-size: 1.5rem; }
:deep(.markdown-content h3) { font-size: 1.25rem; }
:deep(.markdown-content h4) { font-size: 1.125rem; }

:deep(.markdown-content p) {
  margin-bottom: 1em;
}

:deep(.markdown-content ul),
:deep(.markdown-content ol) {
  margin-bottom: 1em;
  padding-left: 1.5em;
}

:deep(.markdown-content li) {
  margin-bottom: 0.25em;
}

:deep(.markdown-content code) {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 0.125em 0.25em;
  border-radius: 0.25em;
  font-size: 0.875em;
}

:global(.dark) :deep(.markdown-content code) {
  background-color: rgba(255, 255, 255, 0.1);
}

:deep(.markdown-content pre) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 1em;
  border-radius: 0.5em;
  overflow-x: auto;
  margin: 1em 0;
}

:global(.dark) :deep(.markdown-content pre) {
  background-color: rgba(255, 255, 255, 0.05);
}

:deep(.markdown-content blockquote) {
  border-left: 4px solid #3b82f6;
  padding-left: 1em;
  margin: 1em 0;
  font-style: italic;
}

:deep(.markdown-content strong) {
  font-weight: 600;
}

:deep(.markdown-content em) {
  font-style: italic;
}

:global(.dark) :deep(.markdown-content h1),
:global(.dark) :deep(.markdown-content h2),
:global(.dark) :deep(.markdown-content h3),
:global(.dark) :deep(.markdown-content h4),
:global(.dark) :deep(.markdown-content h5),
:global(.dark) :deep(.markdown-content h6) {
  color: rgb(241 245 249) !important;
}

/* 表格容器样式 */
:deep(.markdown-content table) {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin: 1.5em 0;
  border-radius: 0.75em;
  overflow: hidden;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
  background-color: rgb(255 255 255);
}

:global(.dark) :deep(.markdown-content table) {
  background-color: rgb(30 41 59);
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 1px 2px -1px rgba(0, 0, 0, 0.3);
}

/* 表格单元格基础样式 */
:deep(.markdown-content th),
:deep(.markdown-content td) {
  padding: 0.75em 1em;
  text-align: left;
  border-bottom: 1px solid rgb(226 232 240);
  border-right: 1px solid rgb(226 232 240);
  transition: background-color 0.15s ease;
}

:deep(.markdown-content th:last-child),
:deep(.markdown-content td:last-child) {
  border-right: none;
}

:global(.dark) :deep(.markdown-content th),
:global(.dark) :deep(.markdown-content td) {
  border-bottom-color: rgb(51 65 85);
  border-right-color: rgb(51 65 85);
}

/* 表头样式 */
:deep(.markdown-content thead) {
  background-color: rgb(248 250 252);
}

:global(.dark) :deep(.markdown-content thead) {
  background-color: rgb(30 41 59);
}

:deep(.markdown-content th) {
  background-color: rgb(248 250 252);
  font-weight: 600;
  color: rgb(15 23 42);
  font-size: 0.875rem;
  letter-spacing: 0.025em;
  text-transform: uppercase;
  padding-top: 1em;
  padding-bottom: 1em;
}

:global(.dark) :deep(.markdown-content th) {
  background-color: rgb(30 41 59);
  color: rgb(241 245 249);
}

/* 表格行样式 */
:deep(.markdown-content tbody tr) {
  background-color: rgb(255 255 255);
}

:deep(.markdown-content tbody tr:hover) {
  background-color: rgb(249 250 251);
}

:global(.dark) :deep(.markdown-content tbody tr) {
  background-color: rgb(30 41 59);
}

:global(.dark) :deep(.markdown-content tbody tr:hover) {
  background-color: rgb(51 65 85);
}

/* 最后一行边框 */
:deep(.markdown-content tbody tr:last-child td) {
  border-bottom: none;
}

/* 表格内容样式 */
:deep(.markdown-content td) {
  color: rgb(51 65 85);
  vertical-align: top;
}

:global(.dark) :deep(.markdown-content td) {
  color: rgb(226 232 240);
}

/* 响应式：小屏幕时表格可横向滚动 */
:deep(.markdown-content table) {
  overflow-x: auto;
  max-width: 100%;
  -webkit-overflow-scrolling: touch;
}

@media (max-width: 768px) {
  :deep(.markdown-content table) {
    font-size: 0.875rem;
  }
  
  :deep(.markdown-content th),
  :deep(.markdown-content td) {
    padding: 0.5em 0.75em;
  }
}

:deep(.markdown-content hr) {
  border: none;
  border-top: 1px solid rgb(226 232 240);
  margin: 2em 0;
}

:global(.dark) :deep(.markdown-content hr) {
  border-top-color: rgb(51 65 85);
}

:deep(.markdown-content img) {
  max-width: 100%;
  height: auto;
  border-radius: 0.5em;
  margin: 1em 0;
}
</style>
