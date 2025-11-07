<template>
  <div class="history-panel rounded-lg flex flex-col h-full w-80 min-w-80">
    <!-- 头部 -->
    <div class="history-header flex items-center justify-between p-4">
      <h3 class="history-title text-lg font-semibold">{{ t('chatHistory.title') }}</h3>
      <button 
        @click="onClose()"
        class="close-button p-2 transition-colors"
        :title="t('chatHistory.closeTitle')"
        :aria-label="t('chatHistory.closeTitle')"
      >
        <!-- 左箭头 -->
        <Icon path="M15.707 17.293a1 1 0 01-1.414 0L8.586 11.586a2 2 0 010-2.828l5.707-5.707a1 1 0 011.414 1.414L10.414 10l5.293 5.293a1 1 0 010 1.414z" class="h-4 w-4 transition-transform duration-200" />
      </button>
    </div>

    <!-- 历史列表 -->
    <div class="flex-1 overflow-y-auto p-4">
      <div v-if="sessions.length === 0" class="empty-state text-center py-8">
        <Icon path="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" class="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p class="empty-text">{{ t('chatHistory.empty') }}</p>
      </div>
      
      <div v-else class="space-y-2">
        <div 
          v-for="session in sessions" 
          :key="session.id"
          class="session-item rounded-lg p-3 cursor-pointer transition-colors group"
          :class="session.id === activeSessionId ? 'ring-2 ring-blue-500' : ''"
          @click="onSelectSession(session)"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <h4 class="session-title font-medium truncate mb-1">{{ session.title }}</h4>
              <p class="session-date text-sm">{{ formatDate(session.createdAt) }}</p>
              <p class="session-count text-xs mt-1">{{ t('chatHistory.messageCount', { count: session.messages.length }) }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Icon from './Icon.vue';
import type { ChatSession } from '../../types';
import { useI18n } from '../i18n';

interface Props {
  sessions: ChatSession[];
  activeSessionId?: number | null;
  onSelectSession: (session: ChatSession) => void;
  onClose: () => void;
}

const props = defineProps<Props>();
const { sessions, activeSessionId, onSelectSession, onClose } = props;

const { t } = useI18n();

// 格式化日期显示
const formatDate = (dateTime: string): string => {
  if (!dateTime) return '';
  // 如果包含微秒部分，则截取到秒
  if (dateTime.includes('.')) {
    return dateTime.split('.')[0];
  }
  return dateTime;
};
</script>

<style scoped>
/* 暗色模式样式（默认） */
.history-panel {
  background-color: #1e293b; /* bg-slate-800 */
}

.history-header {
  border-bottom: 1px solid #334155; /* border-slate-700 */
}

.history-title {
  color: white;
}

.close-button {
  color: #94a3b8; /* text-slate-400 */
}

.close-button:hover {
  color: white;
}

.empty-state {
  color: #94a3b8; /* text-slate-400 */
}

.empty-text {
  color: #94a3b8; /* text-slate-400 */
}

.session-item {
  background-color: #334155; /* bg-slate-700 */
}

.session-item:hover {
  background-color: #475569; /* hover:bg-slate-600 */
}

.session-title {
  color: white;
}

.session-date {
  color: #94a3b8; /* text-slate-400 */
}

.session-count {
  color: #64748b; /* text-slate-500 */
}

/* 亮色模式样式 */
@media (prefers-color-scheme: light) {
  .history-panel {
    background-color: white;
    border: 1px solid #e5e7eb; /* border-gray-200 */
  }

  .history-header {
    border-bottom: 1px solid #e5e7eb; /* border-gray-200 */
  }

  .history-title {
    color: #111827; /* text-gray-900 */
  }

  .close-button {
    color: #6b7280; /* text-gray-500 */
  }

  .close-button:hover {
    color: #111827; /* text-gray-900 */
  }

  .empty-state {
    color: #6b7280; /* text-gray-500 */
  }

  .empty-text {
    color: #6b7280; /* text-gray-500 */
  }

  .session-item {
    background-color: #f9fafb; /* bg-gray-50 */
    border: 1px solid #e5e7eb; /* border-gray-200 */
  }

  .session-item:hover {
    background-color: #f3f4f6; /* hover:bg-gray-100 */
  }

  .session-title {
    color: #111827; /* text-gray-900 */
  }

  .session-date {
    color: #6b7280; /* text-gray-500 */
  }

  .session-count {
    color: #9ca3af; /* text-gray-400 */
  }
}
</style>