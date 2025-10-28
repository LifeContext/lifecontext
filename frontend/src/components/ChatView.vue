<template>
  <div class="chat-container h-full flex flex-col">
    <!-- 聊天消息区域 -->
    <div class="flex-1 overflow-y-auto px-8 py-6" ref="messagesContainer">
      <!-- 如果没有消息，显示欢迎界面 -->
      <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full">
        <!-- AI Avatar -->
        <div class="ai-avatar-container w-16 h-16 rounded-full flex items-center justify-center mb-6">
          <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <Icon path="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" class="w-8 h-8 text-white" />
          </div>
        </div>
        
        <!-- Main Title -->
        <h1 class="main-title text-4xl font-bold mb-8 text-center">Chat with your life</h1>
      </div>

      <!-- 消息列表 -->
      <div v-else class="space-y-4">
        <div 
          v-for="message in messages" 
          :key="message.workflow_id"
          class="flex"
          :class="message.sender === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div 
            class="max-w-3xl px-4 py-3 rounded-lg message-bubble"
            :class="message.sender === 'user' 
              ? 'user-message ml-12' 
              : 'ai-message mr-12'"
          >
            <div class="flex items-start space-x-3">
              <!-- AI头像 -->
              <div v-if="message.sender === 'ai'" class="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <Icon path="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" class="w-4 h-4 text-white" />
              </div>
              
              <!-- 用户头像 -->
              <div v-if="message.sender === 'user'" class="user-avatar w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <Icon path="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" class="w-4 h-4 text-white" />
              </div>
              
              <div class="flex-1">
                <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ message.content }}</p>
                <p class="text-xs mt-2 opacity-70">
                  {{ formatTime(message.timestamp) }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- 加载指示器 -->
        <div v-if="isLoading" class="flex justify-start">
          <div class="loading-message mr-12 px-4 py-3 rounded-lg">
            <div class="flex items-center space-x-3">
              <div class="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <Icon path="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" class="w-4 h-4 text-white" />
              </div>
              <div class="flex space-x-1">
                <div class="loading-dot w-2 h-2 rounded-full animate-bounce"></div>
                <div class="loading-dot w-2 h-2 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                <div class="loading-dot w-2 h-2 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="px-8 pb-6">
      <div class="w-full max-w-4xl mx-auto relative">
        <input 
          type="text" 
          placeholder="Ask, search, or make anything..."
          class="chat-input w-full rounded-xl px-6 py-4 pr-16 text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          v-model="inputMessage"
          @keypress.enter="handleSend"
          :disabled="isLoading"
        />
        <button 
          @click="handleSend"
          :disabled="isLoading || !inputMessage.trim()"
          class="absolute right-2 top-1/2 transform -translate-y-1/2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-full p-3 transition-colors"
        >
          <Icon path="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" class="w-5 h-5" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onBeforeUnmount, watch } from 'vue';
import Icon from './Icon.vue';
import { chatService } from '../api/chatService';
import { chatHistoryService } from '../api/chatHistoryService';
import type { ChatMessage, ChatSession } from '../../types';

const inputMessage = ref('');
const messages = ref<ChatMessage[]>([]);
const isLoading = ref(false);
const messagesContainer = ref<HTMLElement>();
const currentWorkflowId = ref<string>('');
const hasUnsavedMessages = ref(false);

// 格式化时间显示
const formatTime = (timestamp: string) => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  });
};

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

// 保存当前对话到历史记录
const saveCurrentChat = () => {
  if (messages.value.length > 0 && hasUnsavedMessages.value) {
    chatHistoryService.saveChatSession(messages.value);
    hasUnsavedMessages.value = false;
    console.log('对话已自动保存到历史记录');
  }
};

// 监听消息变化，标记为未保存
watch(messages, (newMessages) => {
  if (newMessages.length > 0) {
    hasUnsavedMessages.value = true;
  }
}, { deep: true });

// 组件卸载前自动保存
onBeforeUnmount(() => {
  saveCurrentChat();
});

// 加载历史会话
const loadChatSession = (session: ChatSession) => {
  // 先保存当前对话
  saveCurrentChat();
  
  // 加载新的会话
  messages.value = [...session.messages];
  currentWorkflowId.value = session.messages[session.messages.length - 1]?.workflow_id || '';
  hasUnsavedMessages.value = false;
  
  // 滚动到底部
  nextTick(() => {
    scrollToBottom();
  });
};

// 监听页面可见性变化，当页面隐藏时自动保存
const handleVisibilityChange = () => {
  if (document.hidden) {
    saveCurrentChat();
  }
};

// 监听页面卸载事件
const handleBeforeUnload = () => {
  saveCurrentChat();
};

// 添加事件监听器
document.addEventListener('visibilitychange', handleVisibilityChange);
window.addEventListener('beforeunload', handleBeforeUnload);

// 清理事件监听器
onBeforeUnmount(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange);
  window.removeEventListener('beforeunload', handleBeforeUnload);
});

const handleSend = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return;

  const userMessage = inputMessage.value.trim();
  
  // 添加用户消息
  const userMsg: ChatMessage = {
    workflow_id: '',
    content: userMessage,
    sender: 'user',
    timestamp: new Date().toISOString()
  };
  
  messages.value.push(userMsg);
  inputMessage.value = '';
  
  // 滚动到底部
  await scrollToBottom();
  
  // 设置加载状态
  isLoading.value = true;
  
  try {
    // 发送消息到后端并获取回复
    const aiResponse = await chatService.sendMessage(userMessage, currentWorkflowId.value || undefined);
    messages.value.push(aiResponse);
    
    // 更新当前的workflow_id
    if (aiResponse.workflow_id) {
      currentWorkflowId.value = aiResponse.workflow_id;
    }
  } catch (error) {
    console.error('Error sending message:', error);
    // 添加错误消息
    const errorMsg: ChatMessage = {
      workflow_id: '',
      content: '抱歉，发送消息时出现错误。请稍后再试。',
      sender: 'ai',
      timestamp: new Date().toISOString()
    };
    messages.value.push(errorMsg);
  } finally {
    isLoading.value = false;
    // 滚动到底部
    await scrollToBottom();
  }
};
</script>

<style scoped>
/* 暗色模式样式（默认） */
.chat-container {
  background-color: #0f172a; /* bg-slate-900 */
}

.ai-avatar-container {
  background-color: #1e293b; /* bg-slate-800 */
}

.main-title {
  color: white;
}

.user-message {
  background-color: #2563eb; /* bg-blue-600 */
  color: white;
}

.ai-message {
  background-color: #1e293b; /* bg-slate-800 */
  color: white;
}

.user-avatar {
  background-color: #475569; /* bg-slate-600 */
}

.loading-message {
  background-color: #1e293b; /* bg-slate-800 */
  color: white;
}

.loading-dot {
  background-color: #94a3b8; /* bg-slate-400 */
}

.chat-input {
  background-color: #1e293b; /* bg-slate-800 */
  color: white;
  border: 1px solid #334155; /* border-slate-700 */
}

.chat-input::placeholder {
  color: #94a3b8; /* placeholder-slate-400 */
}

/* 亮色模式样式 */
@media (prefers-color-scheme: light) {
  .chat-container {
    background-color: #f9fafb; /* bg-gray-50 */
  }

  .ai-avatar-container {
    background-color: #e5e7eb; /* bg-gray-200 */
  }

  .main-title {
    color: #111827; /* text-gray-900 */
  }

  .user-message {
    background-color: #2563eb; /* bg-blue-600 */
    color: white;
  }

  .ai-message {
    background-color: white;
    color: #111827; /* text-gray-900 */
    border: 1px solid #e5e7eb; /* border-gray-200 */
  }

  .user-avatar {
    background-color: #9ca3af; /* bg-gray-400 */
  }

  .loading-message {
    background-color: white;
    color: #111827; /* text-gray-900 */
    border: 1px solid #e5e7eb; /* border-gray-200 */
  }

  .loading-dot {
    background-color: #9ca3af; /* bg-gray-400 */
  }

  .chat-input {
    background-color: white;
    color: #111827; /* text-gray-900 */
    border: 1px solid #d1d5db; /* border-gray-300 */
  }

  .chat-input::placeholder {
    color: #6b7280; /* placeholder-gray-500 */
  }
}
</style>
