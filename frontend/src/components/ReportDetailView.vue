<template>
  <div class="bg-slate-200 dark:bg-slate-800 rounded-2xl shadow-lg h-full flex flex-col min-h-0 max-h-full">
    <header class="relative flex items-center justify-center p-6 flex-shrink-0">
      <button 
        @click="onClose" 
        class="absolute top-4 right-4 p-2 rounded-full text-slate-500 dark:text-slate-400 hover:bg-slate-300 dark:hover:bg-slate-700"
        :aria-label="t('report.detail.aria.close')"
      >
        <Icon path="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" class="h-6 w-6" />
      </button>
    </header>
    <main class="flex-1 p-8 overflow-hidden min-h-0 flex flex-col" style="height: calc(100vh - 150px);">

      <div class="flex gap-6 flex-1 min-h-0">
        <aside class="report-list-panel w-80 flex-shrink-0 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 flex flex-col overflow-hidden">
          <div class="flex items-center justify-between gap-3 pb-4">
            <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100 uppercase tracking-wide">
              {{ t('report.detail.dailySummary') }}
            </h3>
          </div>

          <div class="report-list flex-1 min-h-0 overflow-y-auto mt-4 space-y-3 pr-1">
            <p v-if="reportList.length === 0" class="text-sm text-slate-500 dark:text-slate-400 text-center py-6">
              {{ t('report.detail.generatedListEmpty') }}
            </p>
            <button
              v-for="(report, index) in reportList"
              :key="report.id"
              type="button"
              class="report-list-card group"
              :class="{ 'border-2 border-blue-500': report.id === selectedReport?.id }"
              @click="() => handleSelectReport(report)"
              :aria-current="report.id === selectedReport?.id ? 'true' : 'false'"
            >
              <div class="report-card-background" :class="getCardGradient(index)"></div>
              <img 
                v-if="report.cover"
                :src="report.cover"
                :alt="report.title"
                class="report-card-cover"
                loading="lazy"
              />
              <div class="absolute bottom-0 left-0 right-0">
                <div class="report-card-content bg-black/800 backdrop-blur-md rounded-b-xl px-4 pt-2 pb-2">
                  <div class="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wide text-slate-200">
                    <Icon :path="getReportTypeIcon(report.type)" class="h-4 w-4 text-orange-300" />
                    <span class="line-clamp-1">{{ report.type || 'Daily Report' }}</span>
                  </div>
                  <p class="text-sm font-semibold text-white leading-snug line-clamp-2">{{ report.title }}</p>
                </div>
              </div>
            </button>
          </div>
        </aside>

        <div class="flex-1 min-h-0 overflow-hidden flex flex-col">
          <div class="flex-1 min-h-0">
            <div ref="detailContent" class="detail-content-scroll h-full overflow-y-auto bg-white dark:bg-slate-700 rounded-2xl shadow-inner">
              <div class="space-y-8 pb-8 p-8 detail-content-wrapper">
                <section>
                  <div class="border-b border-slate-200 dark:border-slate-600 pb-4 mb-8">
                    <h1 class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                      {{ selectedReport.title }}
                    </h1>
                  </div>
                  <!-- 封面图片 -->
                  <div v-if="selectedReport?.cover">
                    <img 
                      :src="selectedReport.cover"
                      :alt="selectedReport.title"
                      class="w-2/3 h-auto rounded-xl object-cover shadow-lg mx-auto"
                      loading="lazy"
                      @error="handleImageError"
                    />
                  </div>
                  <div class="rounded-xl p-6">
                    <div class="markdown-content" v-if="renderedContent" v-html="renderedContent"></div>
                    <p v-else class="text-sm text-slate-500 dark:text-slate-300">{{ t('report.detail.emptyContentTip') }}</p>
                  </div>
                </section>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 滚动到顶部按钮 -->
      <button 
        v-show="showScrollToTop"
        @click="scrollToTop"
        class="scroll-to-top-btn fixed bottom-6 right-6 z-50"
        :aria-label="t('report.detail.aria.scrollTop')"
      >
        <div class="scroll-to-top-inner">
          <Icon path="M5 15l7-7 7 7" class="h-5 w-5" />
        </div>
      </button>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch } from 'vue';
import { marked, type MarkedOptions } from 'marked';
import Icon from './Icon.vue';
import type { DailyReport } from '../../types';
import { useI18n } from '../i18n';

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
  onSelectReport?: (report: DailyReport) => void;
}

const props = defineProps<Props>();

const { t } = useI18n();

type ReportWithTime = DailyReport & { create_time?: string };

const selectedReport = computed<ReportWithTime | null>(() => props.selectedReport as ReportWithTime | null);
const reportList = computed(() => props.reports ?? []);
const onClose = props.onClose;

const currentIndex = computed(() => 
  props.selectedReport ? props.reports.findIndex(r => r.id === props.selectedReport!.id) : -1
);

// 将Markdown内容转换为HTML
const renderedContent = computed(() => {
  if (!props.selectedReport?.content) return '';
  marked.setOptions({
    gfm: true,
    breaks: true,
    headerIds: false,
    mangle: false
  } as unknown as MarkedOptions);
  const normalized = normalizeMarkdown(props.selectedReport.content);
  return marked(normalized);
});

// 滚动状态管理
const showScrollToTop = ref(false);
const detailContent = ref<HTMLElement | null>(null);

// 滚动到顶部的方法
const scrollToTop = () => {
  if (detailContent.value) {
    detailContent.value.scrollTo({ top: 0, behavior: 'smooth' });
  }
};

// 滚动事件处理
const handleScroll = () => {
  if (detailContent.value) {
    showScrollToTop.value = detailContent.value.scrollTop > 100;
  }
};

// 生命周期钩子
const registerScrollListener = (el: HTMLElement | null) => {
  if (!el) return;
  el.addEventListener('scroll', handleScroll);
};

const unregisterScrollListener = (el: HTMLElement | null) => {
  if (!el) return;
  el.removeEventListener('scroll', handleScroll);
};

watch(
  () => detailContent.value,
  (newEl, oldEl) => {
    if (oldEl) {
      unregisterScrollListener(oldEl);
    }
    if (newEl) {
      registerScrollListener(newEl);
      showScrollToTop.value = newEl.scrollTop > 100;
    }
  },
  { immediate: true }
);

onUnmounted(() => {
  unregisterScrollListener(detailContent.value);
});

const handleSelectReport = (report: DailyReport) => {
  if (props.selectedReport?.id === report.id) {
    return;
  }

  if (props.onSelectReport) {
    props.onSelectReport(report);
    return;
  }

  if (!props.selectedReport) return;

  const targetIndex = props.reports.findIndex(r => r.id === report.id);
  const current = currentIndex.value;
  if (targetIndex === -1 || current === -1) return;

  const direction: 'prev' | 'next' = targetIndex < current ? 'prev' : 'next';
  const steps = Math.abs(targetIndex - current);
  for (let i = 0; i < steps; i++) {
    props.onNavigate(direction);
  }
};

const getCardGradient = (index: number): string => {
  const gradients = [
    'from-slate-700 via-slate-800 to-slate-900',
    'from-blue-900/80 via-slate-800 to-slate-900',
    'from-purple-900/70 via-slate-800 to-slate-900',
    'from-teal-900/70 via-slate-800 to-slate-900',
    'from-rose-900/70 via-slate-800 to-slate-900',
  ];
  return `bg-gradient-to-br ${gradients[index % gradients.length]}`;
};

const getReportTypeIcon = (type?: string): string => {
  if (!type) {
    return 'M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zM9 14H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2z';
  }

  const normalizedType = type.toUpperCase();

  if (normalizedType.includes('SUMMARY') || normalizedType.includes('总结')) {
    return 'M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z';
  }

  if (normalizedType.includes('TODO') || normalizedType.includes('待办') || normalizedType.includes('TASK')) {
    return 'M14 10H2v2h12v-2zm0-4H2v2h12V6zM2 16h8v-2H2v2zm19.5-4.5L23 13l-6.99 7-4.51-4.5L13 14l3.01 3L21.5 11.5z';
  }

  if (normalizedType.includes('NEWS') || normalizedType.includes('新闻')) {
    return 'M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z';
  }

  return 'M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zM9 14H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2z';
};

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement;
  if (img) {
    img.style.display = 'none';
  }
};
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
  color: rgb(15 23 42) !important;
  font-weight: 600;
  line-height: 1.25;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

@media (prefers-color-scheme: dark) {
  :deep(.markdown-content h1),
  :deep(.markdown-content h2),
  :deep(.markdown-content h3),
  :deep(.markdown-content h4),
  :deep(.markdown-content h5),
  :deep(.markdown-content h6) {
    color: rgb(241 245 249) !important;
  }

  :deep(.markdown-content) {
    color: rgb(226 232 240);
  }

  :deep(.markdown-content) {
    --tw-prose-body: 226 232 240;
  }

  :deep(.markdown-content) {
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

/* 滚动到顶部按钮样式 */
.scroll-to-top-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0;
  outline: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.scroll-to-top-btn:focus-visible {
  outline: 2px solid rgba(59, 130, 246, 0.5);
  outline-offset: 2px;
  border-radius: 50%;
}

.scroll-to-top-inner {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border-radius: 50%;
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.scroll-to-top-inner::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, transparent 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.scroll-to-top-btn:hover .scroll-to-top-inner {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 
    0 10px 15px -3px rgba(0, 0, 0, 0.1),
    0 4px 6px -2px rgba(0, 0, 0, 0.05),
    0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
}

.scroll-to-top-btn:hover .scroll-to-top-inner::before {
  opacity: 1;
}

.scroll-to-top-btn:active .scroll-to-top-inner {
  transform: translateY(0) scale(0.98);
  box-shadow: 
    0 2px 4px -1px rgba(0, 0, 0, 0.1),
    0 1px 2px -1px rgba(0, 0, 0, 0.06);
}

/* 暗色模式样式 */
.dark .scroll-to-top-inner {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.3),
    0 2px 4px -1px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
}

.dark .scroll-to-top-btn:hover .scroll-to-top-inner {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  box-shadow: 
    0 10px 15px -3px rgba(0, 0, 0, 0.4),
    0 4px 6px -2px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.15) inset;
}

/* 图标样式 */
.scroll-to-top-inner svg {
  position: relative;
  z-index: 1;
  transition: transform 0.3s ease;
}

.scroll-to-top-btn:hover .scroll-to-top-inner svg {
  transform: translateY(-2px);
}

.scroll-to-top-btn:active .scroll-to-top-inner svg {
  transform: translateY(0);
}

/* 淡入淡出动画 */
.scroll-to-top-btn {
  animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.report-list-panel {
  min-height: 100%;
  backdrop-filter: blur(6px);
}

.report-list {
  scrollbar-width: thin;
  scrollbar-color: rgba(148, 163, 184, 0.3) transparent;
}

.report-list::-webkit-scrollbar {
  width: 6px;
}

.report-list::-webkit-scrollbar-track {
  background: transparent;
}

.report-list::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.4) 0%, rgba(148, 163, 184, 0.2) 100%);
  border-radius: 3px;
}

.dark .report-list {
  scrollbar-color: rgba(71, 85, 105, 0.3) transparent;
}

.detail-content-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgba(148, 163, 184, 0.3) transparent;
}

.detail-content-scroll::-webkit-scrollbar {
  width: 6px;
}

.detail-content-scroll::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 3px;
}

.detail-content-scroll::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.4) 0%, rgba(148, 163, 184, 0.2) 100%);
  border-radius: 3px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.2s ease;
}

.detail-content-scroll::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.6) 0%, rgba(148, 163, 184, 0.4) 100%);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transform: scaleX(1.2);
}

.detail-content-scroll::-webkit-scrollbar-thumb:active {
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.8) 0%, rgba(148, 163, 184, 0.6) 100%);
}

.dark .detail-content-scroll {
  scrollbar-color: rgba(71, 85, 105, 0.3) transparent;
}

.dark .detail-content-scroll::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(71, 85, 105, 0.4) 0%, rgba(71, 85, 105, 0.2) 100%);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.dark .detail-content-scroll::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, rgba(71, 85, 105, 0.6) 0%, rgba(71, 85, 105, 0.4) 100%);
  border: 1px solid rgba(0, 0, 0, 0.2);
}

.dark .detail-content-scroll::-webkit-scrollbar-thumb:active {
  background: linear-gradient(180deg, rgba(71, 85, 105, 0.8) 0%, rgba(71, 85, 105, 0.6) 100%);
}

.detail-content-scroll:not(:hover)::-webkit-scrollbar-thumb {
  opacity: 0;
  transition: opacity 0.3s ease;
}

.detail-content-scroll:hover::-webkit-scrollbar-thumb {
  opacity: 1;
  transition: opacity 0.3s ease;
}

.report-list-card {
  position: relative;
  width: 100%;
  min-height: 224px;
  border-radius: 1rem;
  overflow: hidden;
  transition: all 0.25s ease;
  text-align: left;
}

.report-list-card:focus-visible {
  outline: 2px solid rgba(59, 130, 246, 0.7);
  outline-offset: 2px;
}

.report-list-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.25);
}

.report-card-background,
.report-card-cover {
  position: absolute;
  inset: 0;
}

.report-card-cover {
  width: 100%;
  height: 100%;
}

.report-card-content {
  position: relative;
  z-index: 1;
  padding: 1.25rem;
  gap: 0.5rem;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

/* 封面图片样式 */
.detail-content-wrapper img {
  max-height: 400px;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.detail-content-wrapper img:hover {
  transform: scale(1.01);
}
</style>

<style>
.dark .markdown-content {
  --tw-prose-body: 226 232 240;
  --tw-prose-headings: 255 255 255;
  --tw-prose-links: 255 255 255;
  --tw-prose-bold: 255 255 255;
}
</style>
