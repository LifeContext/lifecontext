<template>
  <div class="chat-container h-full flex flex-col">
    <!-- 聊天消息区域 -->
    <div class="flex-1 overflow-y-auto py-6 messagesContainer" ref="messagesContainer">
      <div class="max-w-4xl mx-auto px-8 h-full flex flex-col">
        <!-- 如果没有消息，显示欢迎界面 -->
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center flex-1">
          <!-- AI Avatar -->
          <div class="ai-avatar-container w-16 h-16 rounded-full flex items-center justify-center mb-6">
            <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-500 rounded-full flex items-center justify-center">
              <img src="../../Logo.png" class="w-8 h-8 text-white" />
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
              class="max-w-4xl px-4 py-3 rounded-lg message-bubble"
              :class="message.sender === 'user' 
                ? 'user-message ml-12' 
                : 'ai-message mr-12'"
            >
              <div class="flex items-start space-x-3">                
                <div class="flex-1">
                  <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ message.content }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- 加载指示器 -->
          <div v-if="isLoading" class="flex justify-start">
            <div class="loading-message mr-12 px-4 py-3 rounded-lg">
              <div class="flex items-center space-x-3">
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
    </div>

    <!-- 输入区域 -->
    <div class="pb-6">
      <div class="max-w-4xl mx-auto px-8">
        <div class="relative">
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
.chat-container {
  background-color: #0f172a;
}

.ai-avatar-container {
  background-color: #1e293b;
}

.main-title {
  color: white;
}

.user-message {
  background-color: #2563eb;
  color: white;
}

.ai-message {
  /* background-color: #1e293b; */
  color: white;
  width: 100%;
  margin: 0;
}

.user-avatar {
  background-color: #475569;
}

.loading-message {
  color: white;
}

.loading-dot {
  background-color: #94a3b8;
}

.chat-input {
  background-color: #1e293b;
  color: white;
  border: 1px solid #334155;
}

.chat-input::placeholder {
  color: #94a3b8;
}

/* 滚动条样式 - 暗色模式 */
.messagesContainer::-webkit-scrollbar {
  width: 8px;
}

.messagesContainer::-webkit-scrollbar-track {
  background: transparent;
}

.messagesContainer::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 4px;
}

.messagesContainer::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

/* Firefox滚动条样式 */
.messagesContainer {
  scrollbar-width: thin;
  scrollbar-color: #475569 transparent;
}

/* 亮色模式样式 */
@media (prefers-color-scheme: light) {
  .chat-container {
    background-color: #f9fafb;
  }

  .ai-avatar-container {
    background-color: #e5e7eb;
  }

  .main-title {
    color: #111827;
  }

  .user-message {
    background-color: #2563eb;
    color: white;
  }

  .ai-message {
    color: #111827;
  }

  .user-avatar {
    background-color: #9ca3af;
  }

  .loading-message {
    color: #111827;
  }

  .loading-dot {
    background-color: #9ca3af;
  }

  .chat-input {
    background-color: white;
    color: #111827;
    border: 1px solid #d1d5db;
  }

  .chat-input::placeholder {
    color: #6b7280;
  }

  /* 亮色模式滚动条样式 */
  .messagesContainer::-webkit-scrollbar-thumb {
    background: #cbd5e1;
  }

  .messagesContainer::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
  }

  .messagesContainer {
    scrollbar-color: #cbd5e1 transparent;
  }
}
</style>
