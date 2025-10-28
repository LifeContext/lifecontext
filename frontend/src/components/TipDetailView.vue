<template>
  <div class="flex h-full w-full gap-4">
    <aside class="w-72 flex-shrink-0 bg-slate-200 dark:bg-slate-800 rounded-2xl p-4 flex flex-col shadow-lg">
      <h1 class="text-lg font-bold text-slate-900 dark:text-slate-100 px-2 my-2">All Tips</h1>
      <nav class="flex-1 overflow-y-auto pr-1">
        <ul>
          <li v-for="tip in tips" :key="tip.id">
            <button 
              @click="() => onSelectTip(tip)"
              :class="`w-full text-left flex items-center gap-3 p-3 rounded-lg font-medium text-sm transition-colors ${
                selectedTip.id === tip.id 
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

    <main class="relative flex-1 bg-slate-200 dark:bg-slate-800 rounded-2xl p-8 overflow-y-auto shadow-lg">
      <button 
        @click="onClose" 
        class="absolute top-6 right-6 p-2 rounded-full text-slate-500 dark:text-slate-400 hover:bg-slate-300 dark:hover:bg-slate-700"
        aria-label="Close tips view"
      >
        <Icon path="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" class="h-6 w-6" />
      </button>
      <h1 class="text-3xl font-bold text-slate-900 dark:text-slate-100">{{ selectedTip.title }}</h1>
      <p class="text-sm text-slate-500 dark:text-slate-400 mt-1 mb-8">{{ new Date(selectedTip.create_time).toLocaleString([], { dateStyle: 'long' }) }}</p>
      
      <div class="space-y-8">
        <section>
          <h2 class="text-xl font-bold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-3">
            <Icon path="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7z" class="h-5 w-5 text-yellow-400" />
            <span>Tip Content</span>
          </h2>
          <div class="prose max-w-none dark:prose-invert text-slate-700 dark:text-slate-300">
            <div v-html="selectedTip.content"></div>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import Icon from './Icon.vue';
import type { Tip, TipCategory } from '../../types';

interface Props {
  tips: Tip[];
  selectedTip: Tip;
  onSelectTip: (tip: Tip) => void;
  onClose: () => void;
}

defineProps<Props>();

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

const getCategoryIcon = (category: TipCategory) => {
  const defaultCategory = 'suggestion'; // 默认分类
  const validCategory = category && tipCategoryConfig[category] ? category : defaultCategory;
  return tipCategoryConfig[validCategory].icon;
};

const getCategoryColor = (category: TipCategory) => {
  const defaultCategory = 'suggestion'; // 默认分类
  const validCategory = category && tipCategoryConfig[category] ? category : defaultCategory;
  return tipCategoryConfig[validCategory].color;
};
</script>

<style scoped>
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
  max-height: calc(100vh - 2rem);
  overflow-y: auto;
}

/* 侧边栏高度限制 */
aside {
  max-height: calc(100vh - 2rem);
}

aside nav {
  max-height: calc(100vh - 8rem); /* 减去标题和padding的高度 */
}

/* 内容区域的内边距调整 */
main .space-y-8 {
  padding-bottom: 2rem; /* 底部留出空间 */
}

/* 响应式调整 */
@media (max-width: 768px) {
  .flex {
    flex-direction: column;
  }
  
  aside {
    width: 100%;
    max-height: 40vh;
  }
  
  main {
    max-height: 60vh;
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
</style>
