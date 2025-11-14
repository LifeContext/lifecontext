<template>
  <div class="chat-container h-screen flex flex-col">
    <!-- 聊天消息区域 -->
    <div
      class="flex-1 overflow-y-auto messagesContainer"
      ref="messagesContainer"
      :style="messageListStyle"
    >
      <div class="max-w-4xl mx-auto px-8 h-full flex flex-col">
        <!-- 如果没有消息，显示欢迎界面 -->
        <div v-if="!conversationStarted && messages.length === 0" class="flex flex-col items-center justify-center flex-1 min-h-full">
          <!-- AI Avatar -->
          <div class="ai-avatar-container w-16 h-16 rounded-full flex items-center justify-center mb-4">
            <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-500 rounded-full flex items-center justify-center">
              <img src="../../Logo.png" class="w-8 h-8 text-white" />
            </div>
          </div>
          
          <!-- Main Title -->
          <h1 class="main-title text-4xl font-bold mb-4 text-center">{{ t('chat.welcomeTitle') }}</h1>
          
          <!-- 输入区域（仅在无消息时显示在欢迎界面中） -->
          <div class="w-full mt-4">
            <div class="relative">
              <input 
                type="text" 
                :placeholder="t('chat.placeholder')"
                class="chat-input w-full rounded-xl px-6 py-4 pr-32 text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                v-model="inputMessage"
                @keypress.enter="handleSend"
                :disabled="isLoading || isQuickProcessing"
              />
              <button 
                @click="handleQuickSend"
                :disabled="isLoading || isQuickProcessing || !inputMessage.trim()"
                class="secondary-button"
              >
                <img src="../../Logo.png" class="secondary-icon" />
              </button>
              <button 
                @click="handleSend"
                :disabled="isLoading || isQuickProcessing || !inputMessage.trim()"
                class="send-button"
              >
                <Icon :path="SEND_ICON_PATH" class="send-icon" />
              </button>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-else class="messages-wrapper">
          <div 
            v-for="pair in messagePairs" 
            :key="pair.id"
            class="fullscreen-pair"
          >
            <div class="pair-bubble pair-bubble-user" v-if="pair.user">
              <div class="max-w-3xl px-6 py-4 rounded-lg message-bubble user-message">
                <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ pair.user.content }}</p>
              </div>
            </div>
            <div class="pair-bubble pair-bubble-ai" v-if="pair.ai || pair.isLoading">
              <div class="max-w-3xl px-6 py-4 rounded-lg message-bubble ai-message">
                <template v-if="pair.ai && pair.ai.content && pair.ai.content.trim().length > 0">
                  <div class="markdown-body" v-html="renderMarkdown(pair.ai.content)"></div>
                </template>
                <template v-else>
                  <div class="ai-loading-placeholder">
                    <span class="loading-text">{{ t('chat.loading') }}</span>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域（仅在有消息时显示在底部） -->
    <div v-if="conversationStarted" class="pb-6" ref="inputAreaRef">
      <div class="max-w-4xl mx-auto px-8">
        <div class="relative">
          <input 
            type="text" 
            :placeholder="t('chat.placeholder')"
            class="chat-input w-full rounded-xl px-6 py-4 pr-32 text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            v-model="inputMessage"
            @keypress.enter="handleSend"
            :disabled="isLoading || isQuickProcessing"
          />
          <button 
            @click="handleQuickSend"
            :disabled="isLoading || isQuickProcessing || !inputMessage.trim()"
            class="secondary-button"
          >
            <img src="../../Logo.png" class="secondary-icon" />
          </button>
          <button 
            @click="handleSend"
            :disabled="isLoading || isQuickProcessing || !inputMessage.trim()"
            class="send-button"
          >
            <Icon :path="SEND_ICON_PATH" class="send-icon" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onBeforeUnmount, watch, onMounted, computed, reactive } from 'vue';
import Icon from './Icon.vue';
import { chatService } from '../api/chatService';
import { chatHistoryService } from '../api/chatHistoryService';
import type { ChatMessage, ChatSession } from '../../types';
import { useI18n } from '../i18n';
import { marked, Renderer, type Tokens } from 'marked';

const inputMessage = ref('');
const messages = ref<ChatMessage[]>([]);
const isLoading = ref(false);
const isQuickProcessing = ref(false);
const conversationStarted = ref(false);
const messagesContainer = ref<HTMLElement>();
const inputAreaRef = ref<HTMLElement>();
const currentWorkflowId = ref<string>('');
const hasUnsavedMessages = ref(false);
const messageViewportHeight = ref<number>(typeof window !== 'undefined' ? window.innerHeight : 0);

const { t } = useI18n();

const SEND_ICON_PATH = 'M12 5a.75.75 0 01.53.22l5.25 5.25a.75.75 0 11-1.06 1.06L12.75 8.56V18a.75.75 0 01-1.5 0V8.56l-3.97 3.97a.75.75 0 11-1.06-1.06L11.47 5.22A.75.75 0 0112 5z';

type MessagePair = {
  id: string;
  user?: ChatMessage;
  ai?: ChatMessage;
  isLoading?: boolean;
};

const updateViewportHeight = () => {
  if (messagesContainer.value) {
    messageViewportHeight.value = Math.max(messagesContainer.value.clientHeight, 0);
  } else if (typeof window !== 'undefined') {
    messageViewportHeight.value = window.innerHeight;
  }
};

const handleResize = () => {
  updateViewportHeight();
};

const messagePairs = computed<MessagePair[]>(() => {
  const pairs: MessagePair[] = [];
  let currentPair: MessagePair | null = null;

  messages.value.forEach((msg, index) => {
    const pairId = `${msg.workflow_id || msg.timestamp || index}`;

    if (msg.sender === 'user') {
      if (currentPair && !currentPair.ai) {
        pairs.push(currentPair);
      }
      currentPair = {
        id: `${pairId}-pair`,
        user: msg
      };
    } else {
      if (!currentPair) {
        currentPair = {
          id: `${pairId}-pair`,
          ai: msg
        };
        pairs.push(currentPair);
        currentPair = null;
      } else if (!currentPair.ai) {
        currentPair.ai = msg;
        pairs.push(currentPair);
        currentPair = null;
      } else {
        pairs.push(currentPair);
        currentPair = {
          id: `${pairId}-pair`,
          ai: msg
        };
        pairs.push(currentPair);
        currentPair = null;
      }
    }
  });

  if (currentPair) {
    pairs.push(currentPair);
  }

  if (isLoading.value) {
    if (pairs.length > 0 && !pairs[pairs.length - 1].ai) {
      pairs[pairs.length - 1] = {
        ...pairs[pairs.length - 1],
        isLoading: true
      };
    } else if (pairs.length === 0) {
      pairs.push({
        id: 'loading-pair',
        isLoading: true
      });
    }
  }

  return pairs;
});

const messageListStyle = computed(() => ({
  '--message-viewport-height': `${messageViewportHeight.value || (typeof window !== 'undefined' ? window.innerHeight : 0)}px`
}));

const renderer = new Renderer();
const escapeAttribute = (value: string) =>
  value.replace(/"/g, '&quot;').replace(/'/g, '&#39;');

renderer.link = function ({ href = '', title, tokens }: Tokens.Link) {
  if (!href) {
    return this.parser.parseInline(tokens, renderer);
  }

  const sanitizedHref = escapeAttribute(href);
  const attrs = [
    `href="${sanitizedHref}"`,
    'target="_blank"',
    'rel="noopener noreferrer"'
  ];
  if (title) {
    attrs.push(`title="${escapeAttribute(title)}"`);
  }

  const innerHtml = this.parser.parseInline(tokens, renderer);
  const rawText = tokens?.map((token) => token.raw ?? '').join('') ?? '';

  if (
    rawText &&
    rawText !== href &&
    rawText.includes(href) &&
    typeof DOMParser !== 'undefined'
  ) {
    const domParser = new DOMParser();
    const doc = domParser.parseFromString(`<div>${innerHtml}</div>`, 'text/html');
    const container = doc.body.firstElementChild as HTMLElement | null;

    if (container) {
      let replaced = false;
      const walker = doc.createTreeWalker(container, NodeFilter.SHOW_TEXT);

      while (walker.nextNode()) {
        const textNode = walker.currentNode as Text;
        const textValue = textNode.nodeValue ?? '';
        const matchIndex = textValue.indexOf(href);

        if (matchIndex === -1) continue;

        const parent = textNode.parentNode;
        if (!parent) continue;

        const before = textValue.slice(0, matchIndex);
        const after = textValue.slice(matchIndex + href.length);

        if (before) {
          parent.insertBefore(doc.createTextNode(before), textNode);
        }

        const anchorEl = doc.createElement('a');
        anchorEl.setAttribute('href', href);
        anchorEl.setAttribute('target', '_blank');
        anchorEl.setAttribute('rel', 'noopener noreferrer');
        anchorEl.textContent = href;
        parent.insertBefore(anchorEl, textNode);

        if (after) {
          parent.insertBefore(doc.createTextNode(after), textNode);
        }

        parent.removeChild(textNode);
        replaced = true;
      }

      if (replaced) {
        return container.innerHTML;
      }
    }
  }

  const linkContent = innerHtml || sanitizedHref;
  return `<a ${attrs.join(' ')}>${linkContent}</a>`;
};

marked.use({ renderer });

const renderMarkdown = (content: string) => {
  if (!content) return '';
  return marked.parse(content) as string;
};

let rafId: number | null = null;
const scheduleViewportUpdate = () => {
  if (rafId !== null) return;
  rafId = window.requestAnimationFrame(() => {
    rafId = null;
    nextTick(() => {
      scrollToBottom();
      updateViewportHeight();
    });
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

watch(
  () => messages.value.length,
  async () => {
    await nextTick();
    updateViewportHeight();
  }
);

watch(
  () => messagePairs.value.length,
  async () => {
    await nextTick();
    updateViewportHeight();
  }
);

watch(isLoading, async () => {
  await nextTick();
  updateViewportHeight();
});

onMounted(async () => {
  await nextTick();
  updateViewportHeight();
  window.addEventListener('resize', handleResize);
});

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
  conversationStarted.value = session.messages.length > 0;
  
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
  window.removeEventListener('resize', handleResize);
  if (rafId !== null) {
    window.cancelAnimationFrame(rafId);
    rafId = null;
  }
});

const handleSend = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return;

  const userMessage = inputMessage.value.trim();
  conversationStarted.value = true;
  
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
    const streamingMessage = reactive<ChatMessage>({
      workflow_id: '',
      content: '',
      sender: 'ai',
      timestamp: new Date().toISOString()
    }) as ChatMessage;

    messages.value.push(streamingMessage);
    await nextTick();
    await scrollToBottom();

    const finalMessage = await chatService.sendMessageStream(
      userMessage,
      currentWorkflowId.value || undefined,
      {
        onToken: (token) => {
          streamingMessage.content += token;
          scheduleViewportUpdate();
        },
        onWorkflowId: (workflowId) => {
          if (!workflowId) return;
          currentWorkflowId.value = workflowId;
          streamingMessage.workflow_id = workflowId;
        }
      }
    );

    streamingMessage.content = finalMessage.content;
    streamingMessage.workflow_id = finalMessage.workflow_id;
    streamingMessage.timestamp = finalMessage.timestamp;
  } catch (error) {
    console.error('Error sending message:', error);
    // 添加错误消息
    const errorMsg: ChatMessage = {
      workflow_id: '',
      content: t('chat.error'),
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

const handleQuickSend = async () => {
  const originalContent = inputMessage.value.trim();
  if (!originalContent || isLoading.value || isQuickProcessing.value) {
    return;
  }

  conversationStarted.value = true;
  isQuickProcessing.value = true;

  let userMessage: ChatMessage | null = null;
  let streamingMessage: ChatMessage | null = null;
  let streamingAdded = false;
  let loadingVisible = false;

  const ensureStreamingMessage = () => {
    if (streamingAdded) return;
    streamingMessage = reactive<ChatMessage>({
      workflow_id: '',
      content: '',
      sender: 'ai',
      timestamp: new Date().toISOString()
    }) as ChatMessage;
    streamingAdded = true;
    messages.value.push(streamingMessage);
  };

  const showLoadingAfterUser = () => {
    if (loadingVisible) return;
    loadingVisible = true;
    isQuickProcessing.value = false;
    isLoading.value = true;
    ensureStreamingMessage();
  };

  const insertUserMessage = (content: string, workflowId?: string) => {
    if (userMessage) {
      userMessage.content = content;
      if (workflowId) {
        userMessage.workflow_id = workflowId;
      }
      return userMessage;
    }

    const newUserMessage = reactive<ChatMessage>({
      workflow_id: workflowId || '',
      content,
      sender: 'user',
      timestamp: new Date().toISOString()
    }) as ChatMessage;

    const insertIndex =
      streamingAdded && streamingMessage
        ? messages.value.indexOf(streamingMessage)
        : -1;

    if (insertIndex === -1) {
      messages.value.push(newUserMessage);
    } else {
      messages.value.splice(insertIndex, 0, newUserMessage);
    }

    userMessage = newUserMessage;
    showLoadingAfterUser();
    return newUserMessage;
  };

  try {
    const finalMessage = await chatService.sendMessageStream(
      originalContent,
      currentWorkflowId.value || undefined,
      {
        onPromptOptimized: (payload) => {
          const optimized =
            typeof payload?.optimized_query === 'string'
              ? payload.optimized_query
              : originalContent;
          inputMessage.value = optimized;
          insertUserMessage(
            optimized,
            typeof payload?.workflow_id === 'string' ? payload.workflow_id : undefined
          );
          nextTick(() => {
            inputMessage.value = '';
          });
          scheduleViewportUpdate();
        },
        onToken: (token) => {
          if (!streamingAdded) {
            insertUserMessage(originalContent);
          }
          ensureStreamingMessage();
          if (streamingMessage) {
            streamingMessage.content += token;
          }
          scheduleViewportUpdate();
        },
        onWorkflowId: (workflowId) => {
          if (!workflowId) return;
          currentWorkflowId.value = workflowId;
          if (streamingMessage) {
            streamingMessage.workflow_id = workflowId;
          }
          if (userMessage && !userMessage.workflow_id) {
            userMessage.workflow_id = workflowId;
          }
        }
      },
      { optimize_prompt: true }
    );

    if (!userMessage) {
      insertUserMessage(originalContent);
      inputMessage.value = '';
    }

    ensureStreamingMessage();
    if (streamingMessage) {
      streamingMessage.content = finalMessage.content;
      streamingMessage.workflow_id = finalMessage.workflow_id;
      streamingMessage.timestamp = finalMessage.timestamp;
    }
  } catch (error) {
    console.error('发送当前输入内容失败:', error);
    const errorMsg: ChatMessage = {
      workflow_id: '',
      content: t('chat.error'),
      sender: 'ai',
      timestamp: new Date().toISOString()
    };
    messages.value.push(errorMsg);
  } finally {
    if (!loadingVisible) {
      isQuickProcessing.value = false;
    }
    isLoading.value = false;
    await scrollToBottom();
  }
};
</script>

<style scoped>
.chat-container {
  background-color: #0f172a;
}

.messagesContainer {
  scroll-snap-type: y mandatory;
}

.messages-wrapper {
  display: flex;
  flex-direction: column;
}

.fullscreen-pair {
  min-height: var(--message-viewport-height, 100vh);
  scroll-snap-align: start;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding: 4rem 0 4rem;
  gap: 2rem;
}

.pair-bubble {
  display: flex;
}

.pair-bubble-user {
  justify-content: flex-end;
}

.pair-bubble-ai {
  justify-content: flex-start;
}

.ai-loading-placeholder {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  font-weight: 600;
  color: #e2e8f0;
  margin: 1.25rem 0 0.75rem;
}

.markdown-body :deep(p) {
  margin: 0.75rem 0;
  line-height: 1.8;
  color: inherit;
}

.markdown-body :deep(code) {
  background-color: rgba(148, 163, 184, 0.18);
  padding: 0.2rem 0.4rem;
  border-radius: 0.375rem;
  font-family: 'Fira Code', 'JetBrains Mono', Consolas, monospace;
  font-size: 0.95rem;
}

.markdown-body :deep(pre code) {
  display: block;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 1.25rem;
  background-color: rgba(15, 23, 42, 0.8);
  border-radius: 0.75rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 1.5rem;
  margin: 0.75rem 0;
}

.markdown-body :deep(li) {
  margin: 0.5rem 0;
}

.markdown-body :deep(a) {
  color: #60a5fa;
  text-decoration: underline;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid rgba(148, 163, 184, 0.2);
  padding: 0.6rem 0.75rem;
  text-align: left;
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid rgba(96, 165, 250, 0.6);
  padding-left: 1rem;
  margin: 0.75rem 0;
  color: rgba(226, 232, 240, 0.85);
  font-style: italic;
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
  color: white;
  width: 100%;
  margin: 0;
}

.user-avatar {
  background-color: #475569;
}

.loading-text {
  font-size: 0.95rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: transparent;
  background-image: linear-gradient(90deg, rgba(255, 255, 255, 0.92) 0%, rgba(226, 232, 240, 0.95) 40%, rgba(255, 255, 255, 0.88) 75%, rgba(226, 232, 240, 0.95) 100%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  background-clip: text;
  animation: loading-gradient 2.4s linear infinite;
}

@keyframes loading-gradient {
  0% {
    background-position: 0% 50%;
  }
  100% {
    background-position: -200% 50%;
  }
}

.secondary-button {
  position: absolute;
  right: 3.75rem;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 9999px;
  color: #bfdbfe;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, border-color 0.18s ease;
  backdrop-filter: blur(6px);
  cursor: pointer;
}

.secondary-button:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.28);
  border-color: rgba(96, 165, 250, 0.45);
  box-shadow: 0 10px 24px rgba(59, 130, 246, 0.25);
}

.secondary-button:active:not(:disabled) {
  transform: translateY(-50%) scale(0.95);
}

.secondary-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.secondary-icon {
  width: 22px;
  height: 22px;
  color: #bfdbfe;
  transition: transform 0.18s ease, color 0.18s ease;
}

.secondary-button:hover:not(:disabled) .secondary-icon {
  transform: translateY(-1px);
  color: #e0f2fe;
}

.send-button {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 9999px;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #ffffff;
  border: none;
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.35);
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
  cursor: pointer;
}

.send-button:hover:not(:disabled) {
  transform: translateY(-50%) scale(1.05);
  box-shadow: 0 16px 28px rgba(59, 130, 246, 0.45);
}

.send-button:active:not(:disabled) {
  transform: translateY(-50%) scale(0.95);
}

.send-button:focus-visible {
  outline: 2px solid rgba(59, 130, 246, 0.6);
  outline-offset: 4px;
}

.send-button:disabled {
  background: linear-gradient(135deg, #475569, #334155);
  box-shadow: none;
  color: #cbd5f5;
  cursor: not-allowed;
}

.send-icon {
  width: 30px;
  height: 30px;
  color: #e2eeff;
  filter: drop-shadow(0 0 8px rgba(96, 165, 250, 0.75));
  transition: transform 0.18s ease, filter 0.18s ease;
}

.send-button:hover:not(:disabled) .send-icon {
  transform: translateY(-1px) translateX(1px) scale(1.05);
  filter: drop-shadow(0 0 12px rgba(147, 197, 253, 0.9));
}

.send-button:active:not(:disabled) .send-icon {
  transform: translateY(1px) translateX(-1px) scale(0.95);
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

  .secondary-button {
    border-color: rgba(59, 130, 246, 0.28);
    color: #1d4ed8;
  }

  .secondary-button:hover:not(:disabled) {
    background: rgba(59, 130, 246, 0.2);
    border-color: rgba(59, 130, 246, 0.38);
  }

  .secondary-icon {
    color: #1d4ed8;
  }

  .secondary-button:hover:not(:disabled) .secondary-icon {
    color: #1e40af;
  }

  .user-avatar {
    background-color: #9ca3af;
  }

  .markdown-body :deep(h1),
  .markdown-body :deep(h2),
  .markdown-body :deep(h3),
  .markdown-body :deep(h4),
  .markdown-body :deep(h5),
  .markdown-body :deep(h6) {
    color: #1f2937;
  }

  .markdown-body :deep(p) {
    color: #1f2937;
  }

  .markdown-body :deep(code) {
    background-color: rgba(59, 130, 246, 0.1);
  }

  .markdown-body :deep(pre code) {
    background-color: rgba(15, 23, 42, 0.06);
    border-color: rgba(148, 163, 184, 0.3);
  }

  .markdown-body :deep(a) {
    color: #1d4ed8;
  }

  .markdown-body :deep(blockquote) {
    border-left-color: rgba(59, 130, 246, 0.6);
    color: rgba(31, 41, 55, 0.8);
  }

  .loading-text {
    background-image: linear-gradient(90deg, rgba(17, 24, 39, 0.95) 0%, rgba(55, 65, 81, 0.9) 45%, rgba(31, 41, 55, 0.92) 75%, rgba(17, 24, 39, 0.95) 100%);
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
