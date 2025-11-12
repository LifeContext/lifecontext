<template>
  <div class="flex h-full w-full gap-4 p-4">
    <aside class="w-72 flex-shrink-0 bg-slate-200 dark:bg-slate-800 rounded-2xl p-4 flex flex-col shadow-lg">
      <h1 class="text-lg font-bold text-slate-900 dark:text-slate-100 px-2 my-2">{{ t('tips.all') }}</h1>
      <nav class="flex-1 overflow-y-auto pr-1">
        <ul>
          <li v-for="tip in props.tips" :key="tip.id">
            <button 
              @click="() => { props.onSelectTip(tip); router.push({ name: 'tipDetail', params: { id: tip.id.toString() } }); }"
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
        @click="() => { props.onClose(); router.push({ name: 'dashboard' }); }" 
        class="absolute top-6 right-6 p-2 rounded-full text-slate-500 dark:text-slate-400 hover:bg-slate-300 dark:hover:bg-slate-700 z-10"
        :aria-label="t('tips.detail.closeAria')"
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
              <span>{{ t('tips.detail.content') }}</span>
            </h2>
            <div class="markdown-content max-w-7xl mx-auto text-slate-700 dark:text-slate-300 h-full">
              <div ref="markdownContainer" v-html="renderedContent"></div>
              
              <!-- 关联网址 -->
              <div v-if="props.selectedTip.source_urls && props.selectedTip.source_urls.length > 0" class="mt-8 pt-6 border-t border-slate-200 dark:border-slate-600">
                <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4 flex items-center gap-2">
                  <Icon path="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" class="h-5 w-5 text-blue-500" />
                  <span>{{ t('tips.detail.relatedLinks') }}</span>
                </h3>
                <ul class="space-y-2">
                  <li v-for="(url, index) in props.selectedTip.source_urls" :key="index" class="flex items-start gap-2">
                    <Icon path="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" class="h-4 w-4 text-slate-400 dark:text-slate-500 mt-1 flex-shrink-0" />
                    <a 
                      :href="url" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 hover:underline break-all"
                    >
                      {{ url }}
                    </a>
                  </li>
                </ul>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { marked } from 'marked';
import mermaid from 'mermaid';
import Icon from './Icon.vue';
import type { Tip, TipCategory } from '../../types';
import { useI18n } from '../i18n';

interface Props {
  tips: Tip[];
  selectedTip: Tip;
  onSelectTip: (tip: Tip) => void;
  onClose: () => void;
}

const props = defineProps<Props>();

const router = useRouter();
const route = useRoute();
const { t, locale } = useI18n();

// Mermaid 容器引用
const markdownContainer = ref<HTMLElement | null>(null);

// 初始化 Mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  themeVariables: {
    darkMode: window.matchMedia('(prefers-color-scheme: dark)').matches
  }
});

// 修复渲染后 HTML 中被分割的单词
const fixSplitWordsInHTML = () => {
  if (!markdownContainer.value) return;
  
  const commonWords = ['notion', 'github', 'javascript', 'typescript', 'docker', 'kubernetes', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'apache', 'nginx', 'react', 'vue', 'angular', 'nodejs', 'python', 'java', 'php', 'ruby', 'swift', 'kotlin', 'scala', 'rust', 'golang', 'flutter', 'reactnative', 'nextjs', 'nuxtjs', 'express', 'django', 'flask', 'laravel', 'spring', 'hibernate', 'graphql', 'restful', 'websocket', 'microservice', 'terraform', 'ansible', 'jenkins', 'gitlab', 'bitbucket', 'jira', 'confluence', 'slack', 'discord', 'telegram', 'whatsapp', 'wechat', 'alipay', 'paypal', 'stripe', 'aws', 'azure', 'gcp', 'heroku', 'vercel', 'netlify', 'Dockerfile', 'bash', 'sql', 'json', 'vue', 'http', 'yaml', 'html'];
  
  const walker = document.createTreeWalker(markdownContainer.value, NodeFilter.SHOW_TEXT, null);
  const textNodes: Text[] = [];
  let node;
  while (node = walker.nextNode()) {
    textNodes.push(node as Text);
  }
  
  textNodes.forEach(textNode => {
    let text = textNode.textContent || '';
    commonWords.forEach(word => {
      for (let i = 3; i < word.length; i++) {
        const part1 = word.substring(0, i);
        const part2 = word.substring(i);
        if (part2.length === 1) {
          const pattern = new RegExp(`(${part1})\\s+(${part2})(?=\\s|$|[.,;:!?\)\\]\\}\\>\\[\\]])`, 'gi');
          if (pattern.test(text)) {
            textNode.textContent = text.replace(pattern, word);
            return;
          }
        }
      }
    });
  });
};

// 渲染 Mermaid 图表
const renderMermaid = async () => {
  await nextTick();
  if (!markdownContainer.value) return;
  
  // 先修复被分割的单词
  fixSplitWordsInHTML();
  
  // 查找所有 mermaid 代码块
  const mermaidCodeBlocks = markdownContainer.value.querySelectorAll('code.language-mermaid');
  
  mermaidCodeBlocks.forEach((codeElement, index) => {
    // 检查是否已经渲染过
    if (codeElement.closest('.mermaid-rendered')) return;
    
    const codeText = codeElement.textContent || '';
    if (codeText.trim()) {
      const preElement = codeElement.parentElement; // <pre> 元素
      if (!preElement || preElement.tagName !== 'PRE') return;
      
      // 创建 Mermaid 容器
      const mermaidDiv = document.createElement('div');
      mermaidDiv.className = 'mermaid mermaid-rendered';
      mermaidDiv.textContent = codeText.trim();
      
      // 替换整个 <pre> 元素
      preElement.replaceWith(mermaidDiv);
      
      // 渲染 Mermaid 图表
      mermaid.run({
        nodes: [mermaidDiv]
      }).catch(err => {
        console.error('Mermaid 渲染错误:', err, codeText);
        // 渲染失败时显示原始代码
        mermaidDiv.textContent = codeText;
      });
    }
  });
};

// 规范化后端返回的 Markdown 文本中的换行/回车和转义字符
const normalizeMarkdown = (raw: string): string => {
  if (!raw) return '';
  
  let text = raw;
  const commonLanguages = ['sh', 'css', 'java', 'cpp', 'c', 'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'xml', 'markdown', 'dockerfile', 'makefile', 'ini', 'toml', 'diff', 'plaintext', 'text'];
  
  // 修复被分割的语言标识（在转义处理之前处理转义序列格式）
  text = text.replace(/```(\w+)\\n\s*([a-z])\\n/g, (match, p1, p2) => {
    const combined = p1 + p2;
    return commonLanguages.includes(combined) ? `\`\`\`${combined}\\n` : match;
  });
  
  text = text.replace(/```(\w+)\\n\s*([a-z])(?=\s|graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|gitgraph|[A-Z])/g, (match, p1, p2) => {
    const combined = p1 + p2;
    return commonLanguages.includes(combined) ? `\`\`\`${combined}\\n` : match;
  });
  
  // 1. 处理所有 JSON 字符串转义序列（转换为实际字符）
  text = text.replace(/\\r\\n/g, '\n');
  text = text.replace(/\\n/g, '\n');
  text = text.replace(/\\r/g, '\n');
  text = text.replace(/\\"/g, '"');
  text = text.replace(/\\'/g, "'");
  text = text.replace(/\\`/g, '`');
  text = text.replace(/\\\*/g, '*');
  text = text.replace(/\\_/g, '_');
  text = text.replace(/\\\(/g, '(');
  text = text.replace(/\\\)/g, ')');
  text = text.replace(/\\\[/g, '[');
  text = text.replace(/\\\]/g, ']');
  text = text.replace(/\\#/g, '#');
  text = text.replace(/\\-/g, '-');
  text = text.replace(/\\\\/g, '\\');
  
  // 修复被分割的常见单词（在代码块格式处理之前）
  const commonWords = ['notion', 'bash', 'github', 'javascript', 'typescript', 'docker', 'kubernetes', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'apache', 'nginx', 'react', 'vue', 'angular', 'nodejs', 'python', 'java', 'php', 'ruby', 'swift', 'kotlin', 'scala', 'rust', 'golang', 'flutter', 'reactnative', 'nextjs', 'nuxtjs', 'express', 'django', 'flask', 'laravel', 'spring', 'hibernate', 'graphql', 'restful', 'websocket', 'microservice', 'terraform', 'ansible', 'jenkins', 'gitlab', 'bitbucket', 'jira', 'confluence', 'slack', 'discord', 'telegram', 'whatsapp', 'wechat', 'alipay', 'paypal', 'stripe', 'aws', 'azure', 'gcp', 'heroku', 'vercel', 'netlify', 'sql', 'http'];
  
  // 修复被分割单词的通用函数
  const fixSplitWords = (inputText: string): string => {
    // 保护代码块
    const codeBlockRegex = /```[\s\S]*?```/g;
    const codeBlocks: string[] = [];
    let protectedText = inputText.replace(codeBlockRegex, (match) => {
      codeBlocks.push(match);
      return `__CODE_BLOCK_${codeBlocks.length - 1}__`;
    });
    
    // 修复被分割的单词（多种模式）
    protectedText = protectedText.replace(/(\w{3,})\n\s*([a-z])\s*\n/g, (match, p1, p2) => {
      const combined = p1 + p2;
      return commonWords.includes(combined.toLowerCase()) ? combined + '\n' : match;
    });
    
    protectedText = protectedText.replace(/(\w{3,})\n\s*([a-z])\s*(?=\s|[.,;:!?\)\]\}>\[]|$)/g, (match, p1, p2) => {
      const combined = p1 + p2;
      return commonWords.includes(combined.toLowerCase()) ? combined : match;
    });
    
    protectedText = protectedText.replace(/(\w{3,})\n+\s*([a-z])\s*(?=\s|\n|[.,;:!?\)\]\}>\[]|$)/g, (match, p1, p2) => {
      const combined = p1 + p2;
      return commonWords.includes(combined.toLowerCase()) ? combined : match;
    });
    
    // 修复 Markdown 链接中的文本
    protectedText = protectedText.replace(/\[([^\]]*?)(\w{3,})\n\s*([a-z])([^\]]*?)\]\(/g, (match, before, p1, p2, after) => {
      const combined = p1 + p2;
      return commonWords.includes(combined.toLowerCase()) ? `[${before}${combined}${after}](` : match;
    });
    
    // 修复 URL 中的单词
    protectedText = protectedText.replace(/https?:\/\/notio\s*\n*\s*n([\w.-]+)/gi, (match, rest) => `https://notion${rest}`);
    
    // 恢复代码块
    return protectedText.replace(/__CODE_BLOCK_(\d+)__/g, (match, index) => codeBlocks[parseInt(index)]);
  };
  
  text = fixSplitWords(text);
  
  // 2. 修复被分割的语言标识（处理实际换行符的情况）
  const fixSplitLanguage = (match: string, p1: string, p2: string) => {
    const combined = p1 + p2;
    if (commonLanguages.includes(combined)) {
      return `\`\`\`${combined}\n`;
    }
    const matchedLang = commonLanguages.find(lang => {
      const langStart = lang.substring(0, combined.length);
      return langStart === combined && lang.length <= combined.length + 2;
    });
    return matchedLang ? `\`\`\`${matchedLang}\n` : match;
  };
  
  // 修复转义后的分割语言标识
  text = text.replace(/```(\w+)\n\s*([a-z])\s*\n/g, fixSplitLanguage);
  text = text.replace(/```(\w+)\n\s*([a-z])(?=\s|graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|gitgraph|[A-Z])/g, fixSplitLanguage);
  text = text.replace(/```\n+\s*(\w+)\s*\n+\s*([a-z])\s*\n+\s*(?=(?:graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|gitgraph|[A-Z]))/g, fixSplitLanguage);
  
  // 3. 处理代码块格式
  text = text.replace(/```(\w+)([^\n\r\s`])/g, (match, lang, next) => {
    return !next.match(/[`]/) ? `\`\`\`${lang}\n${next}` : match;
  });
  text = text.replace(/```([^\n\r\s`])/g, '```\n$1');
  text = text.replace(/([^\n\r])```/g, '$1\n```');
  text = text.replace(/([^\n\r])\n```/g, '$1\n\n```');
  text = text.replace(/```(\w+)\n([^\n\r])/g, '```$1\n\n$2');
  text = text.replace(/```\n([^\n\r`])/g, '```\n\n$1');
  
  // 4. 在代码块格式处理之后再次修复被分割的语言标识
  text = text.replace(/```\n+\s*(\w+)\s*\n+\s*([a-z])\s*\n+\s*(?=(?:graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|gitgraph|[A-Z]))/g, fixSplitLanguage);
  
  // 5. 修复被分割的单词（处理代码块格式处理可能影响的情况）
  text = fixSplitWords(text);
  
  // 6. 清理多余的空行
  text = text.replace(/\n{4,}/g, '\n\n\n');
  
  return text;
};

// Markdown 渲染
const renderedContent = computed(() => {
  if (!props.selectedTip?.content) return '';

  const normalized = normalizeMarkdown(props.selectedTip.content);
  
  // 配置marked选项
  marked.setOptions({
    gfm: true,        // 启用GitHub Flavored Markdown
    breaks: true      // 允许回车换行
  });
  
  try {
    // 尝试渲染Markdown
    const html = marked.parse(normalized);
    
    // 在下一个 tick 渲染 Mermaid 图表
    nextTick(() => {
      renderMermaid();
    });
    
    return html;
  } catch (error) {
    console.error('Markdown渲染错误:', error);
    // 渲染失败时显示原始内容，确保转义HTML字符
    return normalized.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
});

// 监听内容变化，重新渲染 Mermaid
watch(() => props.selectedTip?.id, () => {
  // 当切换 tip 时，延迟渲染以确保 DOM 已更新
  setTimeout(() => {
    renderMermaid();
  }, 100);
}, { immediate: true });

        // 也监听 renderedContent 的变化
        watch(() => renderedContent.value, () => {
          nextTick(() => {
            fixSplitWordsInHTML();
            renderMermaid();
          });
        });

// 分类图标配置 - 使用与种类含义对应的图标
const TIP_CATEGORY_ICONS = {
  // DEEP_DIVE: 深入探索图标 (search/explore)
  deepDive: 'M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z',
  // RESOURCE_RECOMMENDATION: 推荐/链接图标 (link)
  resourceRecommendation: 'M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z',
  // RISK_ANALYSIS: 警告图标 (warning)
  riskAnalysis: 'M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z',
  // KNOWLEDGE_EXPANSION: 知识/书籍图标 (menu_book)
  knowledgeExpansion: 'M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 4h5v8l-2.5-1.5L6 12V4z',
  // ALTERNATIVE_PERSPECTIVE: 视角/视图图标 (visibility)
  alternativePerspective: 'M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z'
};

const tipCategoryConfig: { [key in TipCategory]: { icon: string; color: string; } } = {
  DEEP_DIVE: { icon: TIP_CATEGORY_ICONS.deepDive, color: 'text-red-500 dark:text-red-400' },
  RESOURCE_RECOMMENDATION: { icon: TIP_CATEGORY_ICONS.resourceRecommendation, color: 'text-blue-500 dark:text-blue-400' },
  RISK_ANALYSIS: { icon: TIP_CATEGORY_ICONS.riskAnalysis, color: 'text-green-500 dark:text-green-400' },
  KNOWLEDGE_EXPANSION: { icon: TIP_CATEGORY_ICONS.knowledgeExpansion, color: 'text-yellow-500 dark:text-yellow-400' },
  ALTERNATIVE_PERSPECTIVE: { icon: TIP_CATEGORY_ICONS.alternativePerspective, color: 'text-purple-500 dark:text-purple-400' }
};

const getCategoryIcon = (category: string) => {
  const defaultCategory = 'RISK_ANALYSIS'; // 默认分类
  const validCategory = category && tipCategoryConfig[category as TipCategory] ? category as TipCategory : defaultCategory;
  return tipCategoryConfig[validCategory].icon;
};

const getCategoryColor = (category: string) => {
  const defaultCategory = 'RISK_ANALYSIS'; // 默认分类
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
    return t('time.justNow');
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return t('time.minutesAgo', { count: minutes });
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return t('time.hoursAgo', { count: hours });
  } else if (diffInSeconds < 2592000) {
    const days = Math.floor(diffInSeconds / 86400);
    return t('time.daysAgo', { count: days });
  } else {
    const lang = locale.value === 'zh-CN' ? 'zh-CN' : 'en-US';
    return date.toLocaleDateString(lang);
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

:deep(.prose code) {
  background-color: rgb(241 245 249);
  padding: 0.125em 0.25em;
  border-radius: 0.25em;
  font-size: 0.875em;
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace;
}

:deep(.prose pre) {
  background-color: rgb(241 245 249);
  border-radius: 0.5em;
  padding: 1em;
  overflow-x: auto;
  margin: 1.5em 0;
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

:deep(.prose th) {
  background-color: rgb(248 250 252);
  font-weight: 600;
}

:deep(.prose hr) {
  border: none;
  border-top: 1px solid rgb(226 232 240);
  margin: 2em 0;
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
  color: rgb(51 65 85);
  /* 防止单词被意外分割 */
  word-break: keep-all;
  overflow-wrap: break-word;
  hyphens: none;
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
  color: rgb(15 23 42) !important;
}

:deep(.markdown-content h1) { font-size: 1.875rem; }
:deep(.markdown-content h2) { font-size: 1.5rem; }
:deep(.markdown-content h3) { font-size: 1.25rem; }
:deep(.markdown-content h4) { font-size: 1.125rem; }

:deep(.markdown-content p) {
  margin-bottom: 1em;
  color: rgb(51 65 85);
  word-break: keep-all;
  overflow-wrap: break-word;
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
  padding: 0.125em 0.25em;
  border-radius: 0.25em;
  font-size: 0.875em;
}

:deep(.markdown-content pre) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 1em;
  border-radius: 0.5em;
  overflow-x: auto;
  margin: 1em 0;
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

:deep(.markdown-content a) {
  word-break: keep-all;
  overflow-wrap: break-word;
  white-space: normal;
}

@media (prefers-color-scheme: dark) {
  :deep(.prose blockquote) {
    color: rgb(148 163 184);
    border-left-color: rgb(96 165 250);
  }

  :deep(.prose code) {
    background-color: rgb(30 41 59);
    color: rgb(241 245 249);
  }

  :deep(.prose pre) {
    background-color: rgb(30 41 59);
  }

  :deep(.prose a) {
    color: rgb(96 165 250);
  }

  :deep(.prose a:hover) {
    color: rgb(147 197 253);
  }

  :deep(.prose th),
  :deep(.prose td) {
    border-color: rgb(51 65 85);
  }

  :deep(.prose th) {
    background-color: rgb(30 41 59);
  }

  :deep(.prose hr) {
    border-top-color: rgb(51 65 85);
  }

  :deep(.markdown-content) {
    color: rgb(226 232 240);
    word-break: keep-all;
    overflow-wrap: break-word;
    hyphens: none;
  }

  /* 深色模式下的标题颜色 */
  :deep(.markdown-content h1),
  :deep(.markdown-content h2),
  :deep(.markdown-content h3),
  :deep(.markdown-content h4),
  :deep(.markdown-content h5),
  :deep(.markdown-content h6) {
    color: #ffffff !important;
  }
  
  /* 深色模式下的段落颜色 */
  :deep(.markdown-content p) {
    color: rgb(226 232 240);
    word-break: keep-all;
    overflow-wrap: break-word;
  }
  
  :deep(.markdown-content pre) {
    background-color: rgba(255, 255, 255, 0.05);
  }

  :deep(.markdown-content table) {
    background-color: rgb(30 41 59);
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 1px 2px -1px rgba(0, 0, 0, 0.3);
  }

  :deep(.markdown-content th),
  :deep(.markdown-content td) {
    border-bottom-color: rgb(51 65 85);
    border-right-color: rgb(51 65 85);
  }

  :deep(.markdown-content thead) {
    background-color: rgb(30 41 59);
  }

  :deep(.markdown-content th) {
    background-color: rgb(30 41 59);
    color: rgb(241 245 249);
  }

  :deep(.markdown-content tbody tr) {
    background-color: rgb(30 41 59);
  }

  :deep(.markdown-content tbody tr:hover) {
    background-color: rgb(51 65 85);
  }

  :deep(.markdown-content td) {
    color: rgb(226 232 240);
  }

  :deep(.markdown-content hr) {
    border-top-color: rgb(51 65 85);
  }
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

/* 表头样式 */
:deep(.markdown-content thead) {
  background-color: rgb(248 250 252);
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

/* 表格行样式 */
:deep(.markdown-content tbody tr) {
  background-color: rgb(255 255 255);
}

:deep(.markdown-content tbody tr:hover) {
  background-color: rgb(249 250 251);
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

:deep(.markdown-content img) {
  max-width: 100%;
  height: auto;
  border-radius: 0.5em;
  margin: 1em 0;
}

/* Mermaid 图表样式 */
:deep(.markdown-content .mermaid) {
  margin: 1.5em 0;
  padding: 1em;
  background-color: rgba(255, 255, 255, 0.5);
  border-radius: 0.5em;
  overflow-x: auto;
  text-align: center;
}

.dark :deep(.markdown-content .mermaid) {
  background-color: rgba(0, 0, 0, 0.2);
}

:deep(.markdown-content .mermaid svg) {
  max-width: 100%;
  height: auto;
}
</style>
