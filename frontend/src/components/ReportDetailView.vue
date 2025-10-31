<template>
  <div class="bg-slate-200 dark:bg-slate-800 rounded-2xl shadow-lg h-full flex flex-col min-h-0 max-h-full">
    <header class="relative flex items-center justify-center p-6 border-b border-slate-300 dark:border-slate-700/50 flex-shrink-0">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 dark:text-slate-100">{{ selectedReport.title }}</h1>
        <div class="flex items-center justify-center gap-4 mt-2">
          <button 
            @click="() => onNavigate('prev')" 
            :disabled="!canGoPrev"
            class="p-1 rounded-full text-slate-500 dark:text-slate-400 hover:bg-slate-300 dark:hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed"
            aria-label="Previous report"
          >
            <Icon path="M15.707 17.293a1 1 0 01-1.414 0L8.586 11.586a2 2 0 010-2.828l5.707-5.707a1 1 0 011.414 1.414L10.414 10l5.293 5.293a1 1 0 010 1.414z" class="h-5 w-5" />
          </button>
          <p class="text-sm text-slate-500 dark:text-slate-400 text-center tabular-nums w-40">{{ formatDateTime(selectedReport.create_time) }}</p>
          <button 
            @click="() => onNavigate('next')" 
            :disabled="!canGoNext"
            class="p-1 rounded-full text-slate-500 dark:text-slate-400 hover:bg-slate-300 dark:hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed"
            aria-label="Next report"
          >
            <Icon path="M8.293 17.293a1 1 0 010-1.414L13.586 10 8.293 4.707a1 1 0 011.414-1.414l5.707 5.707a2 2 0 010 2.828l-5.707 5.707a1 1 0 01-1.414 0z" class="h-5 w-5" />
          </button>
        </div>
      </div>
      <button 
        @click="onClose" 
        class="absolute top-4 right-4 p-2 rounded-full text-slate-500 dark:text-slate-400 hover:bg-slate-300 dark:hover:bg-slate-700"
        aria-label="Close report"
      >
        <Icon path="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" class="h-6 w-6" />
      </button>
    </header>
    <main ref="mainContent" class="flex-1 p-8 overflow-y-auto min-h-0" style="height: calc(100vh - 150px); max-height: calc(100vh - 150px);">

      <div class="space-y-8 max-w-4xl mx-auto pb-8 bg-white dark:bg-slate-700 rounded-2xl p-8 shadow-inner" style="min-height: 100%;">

        <section>
          <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100 mb-4 flex items-center gap-3">
            <Icon path="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" class="h-5 w-5 text-teal-500 dark:text-teal-400" />
            Daily Summary
          </h2>
          <div class="rounded-xl p-6">
            <div class="markdown-content" v-html="renderedContent"></div>
          </div>
        </section>
      </div>
      
      <!-- 滚动到顶部按钮 -->
      <button 
        v-show="showScrollToTop"
        @click="scrollToTop"
        class="fixed bottom-6 right-6 p-3 bg-blue-500 hover:bg-blue-600 text-white rounded-full shadow-lg transition-all duration-200 hover:scale-105 z-10"
        aria-label="Scroll to top"
      >
        <Icon path="M7 14l3-3 3 3m0-6l-3 3-3-3" class="h-5 w-5" />
      </button>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { marked } from 'marked';
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

const normalizeMarkdown = (raw: string): string => {
  if (!raw) return '';
  // 处理 Windows 风格与通用的转义换行
  let text = raw.replace(/\\r\\n/g, '\n').replace(/\\n/g, '\n');
  // 去除可能的多余回车符
  text = text.replace(/\r/g, '');
  return text;
};

interface Props {
  reports: DailyReport[];
  selectedReport: DailyReport | null;
  onClose: () => void;
  onNavigate: (direction: 'prev' | 'next') => void;
}

const props = defineProps<Props>();

const currentIndex = computed(() => 
  props.selectedReport ? props.reports.findIndex(r => r.id === props.selectedReport!.id) : -1
);
const canGoPrev = computed(() => currentIndex.value > 0);
const canGoNext = computed(() => currentIndex.value < props.reports.length - 1);

// 将Markdown内容转换为HTML
const renderedContent = computed(() => {
  if (!props.selectedReport?.content) return '';
  marked.setOptions({
    gfm: true,
    breaks: true,
    headerIds: false,
    mangle: false
  });
  const normalized = normalizeMarkdown(props.selectedReport.content);
  return marked(normalized);
});

// 滚动状态管理
const showScrollToTop = ref(false);
const mainContent = ref<HTMLElement | null>(null);

// 滚动到顶部的方法
const scrollToTop = () => {
  if (mainContent.value) {
    mainContent.value.scrollTo({ top: 0, behavior: 'smooth' });
  }
};

// 滚动事件处理
const handleScroll = () => {
  if (mainContent.value) {
    showScrollToTop.value = mainContent.value.scrollTop > 100;
  }
};

// 生命周期钩子
onMounted(() => {
  if (mainContent.value) {
    mainContent.value.addEventListener('scroll', handleScroll);
  }
});

onUnmounted(() => {
  if (mainContent.value) {
    mainContent.value.removeEventListener('scroll', handleScroll);
  }
});
</script>

<style scoped>
main::-webkit-scrollbar {
  width: 6px;
}

main::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 3px;
}

main::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.4) 0%, rgba(148, 163, 184, 0.2) 100%);
  border-radius: 3px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.2s ease;
}

main::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.6) 0%, rgba(148, 163, 184, 0.4) 100%);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transform: scaleX(1.2);
}

main::-webkit-scrollbar-thumb:active {
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.8) 0%, rgba(148, 163, 184, 0.6) 100%);
}

/* 暗色模式滚动条 */
.dark main::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(71, 85, 105, 0.4) 0%, rgba(71, 85, 105, 0.2) 100%);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.dark main::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, rgba(71, 85, 105, 0.6) 0%, rgba(71, 85, 105, 0.4) 100%);
  border: 1px solid rgba(0, 0, 0, 0.2);
}

.dark main::-webkit-scrollbar-thumb:active {
  background: linear-gradient(180deg, rgba(71, 85, 105, 0.8) 0%, rgba(71, 85, 105, 0.6) 100%);
}

/* Firefox 滚动条样式 */
main {
  scrollbar-width: thin;
  scrollbar-color: rgba(148, 163, 184, 0.3) transparent;
}

.dark main {
  scrollbar-color: rgba(71, 85, 105, 0.3) transparent;
}

/* 滚动条淡入淡出效果 */
main {
  transition: scrollbar-color 0.3s ease;
}

/* 当内容不需要滚动时隐藏滚动条 */
main:not(:hover)::-webkit-scrollbar-thumb {
  opacity: 0;
  transition: opacity 0.3s ease;
}

main:hover::-webkit-scrollbar-thumb {
  opacity: 1;
  transition: opacity 0.3s ease;
}

/* Markdown内容样式 */
:deep(.prose h1), :deep(.prose h2), :deep(.prose h3), :deep(.prose h4), :deep(.prose h5), :deep(.prose h6) {
  color: rgb(15 23 42);
  font-weight: 600;
  line-height: 1.25;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

:global(.dark) .markdown-content h1,
:global(.dark) .markdown-content h2,
:global(.dark) .markdown-content h3,
:global(.dark) .markdown-content h4,
:global(.dark) .markdown-content h5,
:global(.dark) .markdown-content h6 {
  color: rgb(241 245 249) !important;
}

:global(.dark) .markdown-content {
  color: rgb(226 232 240) !important;
}

:global(.dark) .markdown-content {
  --tw-prose-body: 226 232 240;
  --tw-prose-headings: 241 245 249;
  --tw-prose-links: 241 245 249;
  --tw-prose-bold: 241 245 249;
  --tw-prose-counters: 203 213 225;
  --tw-prose-bullets: 203 213 225;
  --tw-prose-hr: 51 65 85;
  --tw-prose-quotes: 226 232 240;
  --tw-prose-quote-borders: 96 165 250;
  --tw-prose-captions: 203 213 225;
  --tw-prose-code: 241 245 249;
  --tw-prose-pre-code: 226 232 240;
  --tw-prose-pre-bg: 30 41 59;
  --tw-prose-th-borders: 51 65 85;
  --tw-prose-td-borders: 51 65 85;
}

:deep(.prose h1) {
  font-size: 1.875em;
  margin-top: 0;
}

:deep(.prose h2) {
  font-size: 1.5em;
}

:deep(.prose h3) {
  font-size: 1.25em;
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

:deep(.dark .prose blockquote) {
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

:deep(.dark .prose code) {
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

:deep(.dark .prose pre) {
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

:deep(.dark .prose a) {
  color: rgb(96 165 250);
}

:deep(.dark .prose a:hover) {
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

:deep(.dark .prose th), :deep(.dark .prose td) {
  border-color: rgb(51 65 85);
}

:deep(.prose th) {
  background-color: rgb(248 250 252);
  font-weight: 600;
}

:deep(.dark .prose th) {
  background-color: rgb(30 41 59);
}

:deep(.prose hr) {
  border: none;
  border-top: 1px solid rgb(226 232 240);
  margin: 2em 0;
}

:deep(.dark .prose hr) {
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

:deep(.markdown-content h1),
:deep(.markdown-content h2),
:deep(.markdown-content h3),
:deep(.markdown-content h4),
:deep(.markdown-content h5),
:deep(.markdown-content h6) {
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
  padding-left: 1.5rem;
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

:deep(.dark .markdown-content code) {
  background-color: rgba(255, 255, 255, 0.1);
}

:deep(.markdown-content pre) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 1em;
  border-radius: 0.5em;
  overflow-x: auto;
  margin: 1em 0;
}

:deep(.dark .markdown-content pre) {
  background-color: rgba(255, 255, 255, 0.05);
}

:deep(.markdown-content blockquote) {
  border-left: 4px solid #3b82f6;
  padding-left: 1em;
  margin: 1em 0;
  font-style: italic;
}

:deep(.markdown-content strong) {
  font-weight: 700;
}

:deep(.markdown-content em) {
  font-style: italic;
}
</style>

<style>
.dark .markdown-content {
  --tw-prose-body: 226 232 240;
  --tw-prose-headings: 255 255 255;
  --tw-prose-links: 255 255 255;
  --tw-prose-bold: 255 255 255;
}

.dark .markdown-content :where(h1,h2,h3,h4,h5,h6) {
  color: #ffffff !important;
}
</style>
