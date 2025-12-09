import { createApp } from 'vue'
import { SuspendedBallChat } from 'ai-suspended-ball-chat'

// 监听来自父页面的消息
window.addEventListener('message', (event) => {
  if (event.data.type === 'INIT') {
    console.log('收到初始化消息:', event.data.config);
  }
});

const app = createApp({
  components: { SuspendedBallChat },
  template: `
    <SuspendedBallChat
      :url="apiUrl"
      :app-name="appName"
      :domain-name="domainName"
      :enable-streaming="true"
      :enable-context="true"
      :enable-local-storage="true"
      :enable-voice-input="true"
      :callbacks="callbacks"
    />
  `,
  data() {
    return {
      // 构建后前端由 Backend 代理提供，端口 8000
      apiUrl: 'http://localhost:8000/api/agent/chat',
      appName: 'my-crawler',
      domainName: 'user123',
      callbacks: {
        onUserMessage: (msg) => console.log('用户消息:', msg),
        onAssistantMessage: (msg) => console.log('AI回复:', msg),
        onError: (err) => console.error('错误:', err),
        onChatOpen: () => {
          // 聊天框打开时，通知父页面启用指针事件
          if (window.parent !== window) {
            window.parent.postMessage({ type: 'ENABLE_POINTER_EVENTS' }, '*');
          }
        },
        onChatClose: () => {
          // 聊天框关闭时，通知父页面禁用指针事件
          if (window.parent !== window) {
            window.parent.postMessage({ type: 'DISABLE_POINTER_EVENTS' }, '*');
          }
        }
      }
    }
  }
})

app.mount('#app')
