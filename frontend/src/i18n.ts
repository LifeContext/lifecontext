import type { App as VueApp, ComputedRef } from 'vue';
import { computed, inject, ref } from 'vue';

type Locale = 'en' | 'zh-CN';
type MessageLeaf = string;
interface MessageNode {
  [key: string]: MessageLeaf | MessageNode;
}
type Messages = Record<Locale, MessageNode>;

const I18N_SYMBOL = Symbol('i18n');
const FALLBACK_LOCALE: Locale = 'en';

const messages: Messages = {
  en: {
    app: {
      title: 'LifeContext',
      subtitle: 'Your Proactive Life Search Engine',
    },
    header: {
      logoAlt: 'LifeContext',
      nav: {
        home: 'Home',
        chat: 'Chat',
        timeline: 'Timeline',
        settings: 'Settings',
      },
    },
    dashboard: {
      sectionTitle: 'Daily',
      loading: 'Loading reports...',
      moreReports: '+{count} more reports',
      emptyTitle: 'No daily report yet',
      waiting: 'Waiting for generation',
    },
    tips: {
      title: 'Tips',
      loading: 'Loading...',
      retry: 'Retry',
      emptyTitle: 'No tips yet',
      emptySubtitle: 'Waiting for generation',
      all: 'All Tips',
      detail: {
        content: 'Tip Content',
        relatedLinks: 'Related links',
        closeAria: 'Close tips view',
      },
    },
    chat: {
      welcomeTitle: 'Chat with your life',
      placeholder: 'Ask, search, or make anything...',
      loading: 'Searching browser memories',
      error: 'Sorry, an error occurred while sending the message. Please try again later.',
    },
    chatHistory: {
      title: 'Chat history',
      empty: 'No chat history yet',
      closeTitle: 'Collapse chat history',
      messageCount: '{count} messages',
    },
    languageSwitcher: {
      label: 'Language',
      english: 'English',
      chineseSimplified: '简体中文',
    },
    todo: {
      title: 'Todo',
      loading: 'Loading tasks...',
      retry: 'Try Again',
      progressLabel: 'Progress',
      progressValue: '{completed} / {total} Completed',
      emptyTitle: 'No tasks yet',
      emptySubtitle: 'Waiting for generation',
      completedDivider: 'Completed',
      priority: {
        low: 'Low',
        medium: 'Medium',
        high: 'High',
        lowPriority: 'Low Priority',
        mediumPriority: 'Medium Priority',
        highPriority: 'High Priority',
      },
      buttons: {
        add: 'Add',
        edit: 'Edit',
        delete: 'Delete',
        save: 'Save',
        cancel: 'Cancel',
      },
      addPlaceholder: 'Add a new task...',
      deleteConfirm: 'Are you sure you want to delete this task?',
    },
    timeline: {
      clearHistory: 'Clear History',
      clearLast24h: 'Clear last 24 hours',
      clearAll: 'Clear all history',
      analyzing: 'Analyzing activity...',
      noActivity: 'No activity recorded for this day.',
      dateOption: {
        today: 'Today',
        yesterday: 'Yesterday',
      },
    },
    report: {
      plusMore: '+{count} more reports',
      detail: {
        dailySummary: 'Daily Summary',
        aria: {
          prev: 'Previous report',
          next: 'Next report',
          close: 'Close report',
          scrollTop: 'Scroll to top',
        },
      },
    },
    time: {
      justNow: 'Just now',
      minutesAgo: '{count} minutes ago',
      hoursAgo: '{count} hours ago',
      daysAgo: '{count} days ago',
      fallback: '{value}',
    },
    settings: {
      title: 'Settings',
      loading: 'Loading settings...',
      retry: 'Retry',
      fields: {
        tipsInterval: 'Tips Generation Interval (minutes)',
        todoInterval: 'Todo Generation Interval (minutes)',
        dailyReportTime: 'Daily Report Generation Time',
        dailyReportHint: 'Set the time for generating daily reports',
      },
      labels: {
        minutes: 'minutes',
        hour: 'Hour',
        minute: 'Minute',
      },
      placeholders: {
        minutes: 'Enter minutes',
        hour: 'HH',
        minute: 'MM',
      },
      errors: {
        intervalPositive: 'Interval must be greater than 0',
        hourRange: 'Hour must be between 0-23',
        minuteRange: 'Minute must be between 0-59',
        load: 'Failed to load settings',
        save: 'Failed to save settings',
      },
      buttons: {
        cancel: 'Cancel',
        save: 'Save',
        saving: 'Saving...',
      },
    },
    errors: {
      loadReports: 'Failed to load reports. Please try again later.',
      loadTodos: 'Failed to load tasks. Please try again later.',
      loadTips: 'Failed to load tips. Please try again later.',
    },
    common: {
      retry: 'Retry',
      cancel: 'Cancel',
      add: 'Add',
      delete: 'Delete',
      save: 'Save',
      saving: 'Saving...',
      loading: 'Loading...',
      close: 'Close',
      moreReports: '+{count} more reports',
    },
  },
  'zh-CN': {
    app: {
      title: 'LifeContext',
      subtitle: '你的主动式生活搜索引擎',
    },
    header: {
      logoAlt: 'LifeContext',
      nav: {
        home: '主页',
        chat: '对话',
        timeline: '时间线',
        settings: '设置',
      },
    },
    dashboard: {
      sectionTitle: '每日摘要',
      loading: '加载报告中...',
      moreReports: '+{count} 个更多报告',
      emptyTitle: '暂时没有日报',
      waiting: '等待生成',
    },
    tips: {
      title: '灵感提示',
      loading: '加载中...',
      retry: '重试',
      emptyTitle: '暂时没有提示',
      emptySubtitle: '等待生成',
      all: '全部提示',
      detail: {
        content: '提示内容',
        relatedLinks: '关联网址',
        closeAria: '关闭提示详情',
      },
    },
    chat: {
      welcomeTitle: '和你的生活对话',
      placeholder: '提问、搜索或创建任何内容...',
      loading: '正在检索浏览器记忆',
      error: '抱歉，发送消息时出现错误，请稍后再试。',
    },
    chatHistory: {
      title: '聊天历史',
      empty: '暂无聊天历史',
      closeTitle: '折叠聊天历史',
      messageCount: '{count} 条消息',
    },
    languageSwitcher: {
      label: '语言',
      english: '英语',
      chineseSimplified: '简体中文',
    },
    todo: {
      title: '任务清单',
      loading: '正在加载任务...',
      retry: '重试',
      progressLabel: '进度',
      progressValue: '{completed} / {total} 已完成',
      emptyTitle: '暂时没有任务',
      emptySubtitle: '等待生成',
      completedDivider: '已完成',
      priority: {
        low: '低',
        medium: '中',
        high: '高',
        lowPriority: '低优先级',
        mediumPriority: '中优先级',
        highPriority: '高优先级',
      },
      buttons: {
        add: '添加',
        edit: '编辑',
        delete: '删除',
        save: '保存',
        cancel: '取消',
      },
      addPlaceholder: '新增任务...',
      deleteConfirm: '确认删除这条任务吗？',
    },
    timeline: {
      clearHistory: '清除历史',
      clearLast24h: '清除最近 24 小时',
      clearAll: '清除全部历史',
      analyzing: '正在分析活动...',
      noActivity: '这一天没有记录到活动。',
      dateOption: {
        today: '今天',
        yesterday: '昨天',
      },
    },
    report: {
      plusMore: '+{count} 个更多报告',
      detail: {
        dailySummary: '每日摘要',
        aria: {
          prev: '上一份报告',
          next: '下一份报告',
          close: '关闭报告',
          scrollTop: '回到顶部',
        },
      },
    },
    time: {
      justNow: '刚刚',
      minutesAgo: '{count} 分钟前',
      hoursAgo: '{count} 小时前',
      daysAgo: '{count} 天前',
      fallback: '{value}',
    },
    settings: {
      title: '设置',
      loading: '正在加载设置...',
      retry: '重试',
      fields: {
        tipsInterval: '提示生成间隔（分钟）',
        todoInterval: '任务生成间隔（分钟）',
        dailyReportTime: '日报生成时间',
        dailyReportHint: '设置每日生成日报的时间',
      },
      labels: {
        minutes: '分钟',
        hour: '小时',
        minute: '分钟',
      },
      placeholders: {
        minutes: '输入分钟数',
        hour: 'HH',
        minute: 'MM',
      },
      errors: {
        intervalPositive: '间隔必须大于 0',
        hourRange: '小时必须在 0-23 之间',
        minuteRange: '分钟必须在 0-59 之间',
        load: '加载设置失败',
        save: '保存设置失败',
      },
      buttons: {
        cancel: '取消',
        save: '保存',
        saving: '保存中...',
      },
    },
    errors: {
      loadReports: '加载报告失败，请稍后重试。',
      loadTodos: '加载任务失败，请稍后重试。',
      loadTips: '加载提示失败，请稍后重试。',
    },
    common: {
      retry: '重试',
      cancel: '取消',
      add: '添加',
      delete: '删除',
      save: '保存',
      saving: '保存中...',
      loading: '加载中...',
      close: '关闭',
      moreReports: '+{count} 个更多报告',
    },
  },
};

const isChineseLocale = (locale: string | undefined | null): boolean => {
  if (!locale) return false;
  const normalized = locale.toLowerCase();
  return normalized === 'zh' || normalized.startsWith('zh-');
};

const detectBrowserLocale = (): Locale => {
  if (typeof navigator !== 'undefined') {
    const candidates = Array.isArray((navigator as any).languages) && (navigator as any).languages.length > 0
      ? (navigator as any).languages
      : [navigator.language];

    if (candidates.some(isChineseLocale)) {
      return 'zh-CN';
    }
  }
  return 'en';
};

const currentLocale = ref<Locale>(detectBrowserLocale());

const format = (template: string, params?: Record<string, string | number>): string => {
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (_, key) => {
    const value = params[key];
    return value === undefined || value === null ? '' : String(value);
  });
};

const resolve = (locale: Locale, key: string): MessageLeaf | MessageNode | null => {
  const segments = key.split('.');
  let result: any = messages[locale];
  for (const segment of segments) {
    if (result && typeof result === 'object' && segment in result) {
      result = result[segment];
    } else {
      return null;
    }
  }
  return result as MessageLeaf | MessageNode;
};

const setDocumentLanguage = (locale: Locale) => {
  if (typeof document !== 'undefined') {
    document.documentElement.lang = locale;
  }
};

setDocumentLanguage(currentLocale.value);

const setLocale = (locale: Locale | string) => {
  const normalized: Locale = isChineseLocale(locale) ? 'zh-CN' : 'en';
  currentLocale.value = normalized;
  setDocumentLanguage(normalized);
};

const translate = (key: string, params?: Record<string, string | number>): string => {
  const locale = currentLocale.value;
  const message = resolve(locale, key) ?? resolve(FALLBACK_LOCALE, key);
  if (typeof message === 'string') {
    return format(message, params);
  }
  if (message === null) {
    return key;
  }
  return key;
};

interface I18nContext {
  locale: ComputedRef<Locale>;
  t: (key: string, params?: Record<string, string | number>) => string;
  setLocale: (locale: Locale | string) => void;
}

const createContext = (): I18nContext => {
  const localeComputed = computed(() => currentLocale.value);
  return {
    locale: localeComputed,
    t: translate,
    setLocale,
  };
};

export const installI18n = (app: VueApp) => {
  app.provide(I18N_SYMBOL, createContext());
};

export const useI18n = (): I18nContext => {
  const ctx = inject<I18nContext>(I18N_SYMBOL);
  if (!ctx) {
    throw new Error('i18n context not provided');
  }
  return ctx;
};

export const getCurrentLocale = (): Locale => currentLocale.value;
export const setAppLocale = setLocale;
export const initializeLocaleFromBrowser = (): void => {
  setLocale(detectBrowserLocale());
};
