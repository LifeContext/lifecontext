(function () {
  if (window.__my_floating_chat_injected__) return;
  window.__my_floating_chat_injected__ = true;

  // 悬浮球与聊天框功能暂时禁用（保留全部代码以便后续恢复）。
  // 如需恢复，请删除/注释掉下方的 return 语句。
  //return;

  // 创建悬浮球和聊天框组件
  function createFloatingChat() {
    // 创建主容器
    const container = document.createElement('div');
    container.id = 'my-floating-chat-container';
    container.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 2147483647;
      background: transparent;
      overflow: visible;
    `;

    // 创建悬浮球
    const ballElement = document.createElement('div');
    ballElement.id = 'floating-ball';
    ballElement.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 64px;
      height: 64px;
      background: linear-gradient(135deg, #3b82f6 0%, #14b8a6 100%);
      border-radius: 50%;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 10px 25px rgba(0,0,0,0.2);
      transition: transform 0.2s ease-in-out;
      pointer-events: auto;
      user-select: none;
      color: white;
      z-index: 30;
    `;
    ballElement.innerHTML = `
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="color: white;">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" fill="currentColor"/>
      </svg>
      `;

    // 创建聊天框
    const chatBox = document.createElement('div');
    chatBox.id = 'chat-box';
    chatBox.style.cssText = `
      position: fixed;
      top: 24px;
      bottom: 24px;
      right: 24px;
      width: calc(100vw - 3rem);
      max-width: 420px;
      min-width: 320px;
      background: #1e293b;
      border-radius: 16px;
      box-shadow: 0 25px 50px rgba(0,0,0,0.5);
      display: none;
      flex-direction: column;
      pointer-events: auto;
      overflow: hidden;
      transition: all 0.3s ease-in-out;
      z-index: 40;
    `;

    // 创建聊天框头部
    const chatHeader = document.createElement('div');
    chatHeader.style.cssText = `
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px;
      border-bottom: 1px solid rgba(71, 85, 105, 0.5);
    `;
    const logoUrl = (typeof chrome !== 'undefined' && chrome.runtime && typeof chrome.runtime.getURL === 'function')
      ? chrome.runtime.getURL('logo.png')
      : '';
    const logoFallbackUrl = logoUrl;
    chatHeader.innerHTML = `
      <div style="display: flex; align-items: center; gap: 12px;">
        <button id=\"home-btn\" style=\"display:flex;align-items:center;gap:10px;padding:8px;border-radius:8px;color:#94a3b8;background:transparent;border:none;cursor:pointer;transition:opacity .2s\" aria-label=\"Open LifeContext Home\"> 
          <img src=\"${logoUrl}\" alt=\"LifeContext\" width=\"22\" height=\"22\" onerror=\"this.onerror=null;this.src='${logoFallbackUrl}'\" style=\"display:block;border-radius:6px\"/>
          <span id=\"lc-app-name\" style=\"font-size:16px;font-weight:600;background:linear-gradient(135deg,#3b82f6,#14b8a6);-webkit-background-clip:text;background-clip:text;color:transparent\">LifeContext</span>
        </button>
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        <button id="toggle-chat" style="padding: 8px; border-radius: 50%; color: #94a3b8; background: transparent; border: none; cursor: pointer; transition: background-color 0.2s;" aria-label="Expand chat">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M15.707 17.293a1 1 0 01-1.414 0L8.586 11.586a2 2 0 010-2.828l5.707-5.707a1 1 0 011.414 1.414L10.414 10l5.293 5.293a1 1 0 010 1.414z" fill="currentColor"/>
          </svg>
        </button>
        <button id="close-chat" style="padding: 8px; border-radius: 50%; color: #94a3b8; background: transparent; border: none; cursor: pointer; transition: background-color 0.2s;" aria-label="Close">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" fill="currentColor"/>
          </svg>
        </button>
      </div>
    `;

    // 主题检测函数（供后续使用）
    function isDarkMode() {
      try {
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      } catch (_) {
        return true;
      }
    }

    // 页面上下文展示 Pill（默认隐藏，打开聊天时显示）
    const contextPill = document.createElement('div');
    contextPill.id = 'page-context-pill';
    contextPill.style.cssText = `
      flex-shrink: 0;
      align-self: flex-start; /* 不拉伸，占内容宽度 */
      width: auto;
      max-width: min(70%, 560px); /* 上限，避免太宽 */
      margin: 8px 16px 0 16px;
      display: none;
      align-items: center;
      gap: 8px;
      padding: 6px 12px;
      border-radius: 12px;
      background: rgba(15, 23, 42, 0.85);
      color: #e2e8f0;
      border: 1px solid rgba(71,85,105,0.5);
      box-shadow: 0 6px 14px rgba(0,0,0,0.25);
      backdrop-filter: saturate(150%) blur(6px);
      pointer-events: auto;
    `;
    contextPill.innerHTML = `
      <div style="display:flex; align-items:center; gap:8px; min-width:0;">
        <span style="display:inline-flex; width:20px; height:20px; align-items:center; justify-content:center; color:#60a5fa;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 5h16v14H4z" stroke="currentColor" stroke-width="1.6" fill="none"/>
            <path d="M4 9h16" stroke="currentColor" stroke-width="1.6"/>
          </svg>
        </span>
        <span id="page-context-text" style="font-size:13px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width: 360px;"></span>
      </div>
      <button id="page-context-close" aria-label="Remove page context" title="Remove page context" style="margin-left:6px; border:none; background:transparent; color:#94a3b8; cursor:pointer; padding:2px; border-radius:6px;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" fill="currentColor"/>
        </svg>
      </button>
    `;

    // 创建消息区域
    const chatMessages = document.createElement('div');
    chatMessages.id = 'chat-messages';
    chatMessages.style.cssText = `
      flex: 1;
      padding: 16px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    `;
    
    // 不显示初始欢迎消息

    // 创建输入区域
    const chatInput = document.createElement('div');
    chatInput.style.cssText = `
      flex-shrink: 0;
      padding: 16px;
      background: #1e293b;
      display: flex;
      gap: 12px;
    `;
    
    const inputField = document.createElement('input');
    inputField.type = 'text';
    inputField.placeholder = 'Ask anything...';
    inputField.id = 'chat-input';
    inputField.style.cssText = `
      flex: 1;
       padding: 8px 16px;
      background: #334155;
      border: 1px solid transparent;
      border-radius: 8px;
      outline: none;
      font-size: 14px;
      color: #e2e8f0;
      transition: border-color 0.2s;
    `;

    const sendBtn = document.createElement('button');
    sendBtn.id = 'send-btn';
    sendBtn.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" fill="currentColor"/>
      </svg>
    `;
    sendBtn.style.cssText = `
      flex-shrink: 0;
      background: #3b82f6;
      color: white;
      border: none;
      padding: 10px;
      border-radius: 50%;
      cursor: pointer;
      transition: background-color 0.2s;
      display: flex;
      align-items: center;
      justify-content: center;
    `;

    chatInput.appendChild(inputField);
    chatInput.appendChild(sendBtn);

    // 组装聊天框（Pill 放在消息区与输入框之间）
    chatBox.appendChild(chatHeader);
    chatBox.appendChild(chatMessages);
    chatBox.appendChild(contextPill);
    chatBox.appendChild(chatInput);

    container.appendChild(ballElement);
    container.appendChild(chatBox);

    // 状态变量
    let isChatOpen = false;
    let isChatExpanded = false; // 初始为收缩状态，匹配小窗样式
    let isDragging = false;
    let dragOffset = { x: 0, y: 0 };
    let messages = [];
    let isLoading = false;
    let currentWorkflowId = '';
    let sessionId = `session_${Date.now()}`;

    // 保证布局与滚动正确的辅助函数
    function ensureLayout() {
      try {
        chatMessages.style.flex = '1 1 auto';
        chatMessages.style.minHeight = '0';
        chatMessages.style.overflowY = 'auto';
        // 延迟到下一帧滚动到最新
        requestAnimationFrame(() => {
          chatMessages.scrollTop = chatMessages.scrollHeight;
        });
      } catch (_) {}
    }

    function scrollToLatest() {
      try {
        requestAnimationFrame(() => {
          chatMessages.scrollTop = chatMessages.scrollHeight;
        });
      } catch (_) {}
    }
    // 添加消息函数（用户=气泡，AI=无边框文本）
    function addMessage(text, sender, timestamp = null) {
      const messageContainer = document.createElement('div');
      messageContainer.style.cssText = `
        display: flex;
        align-items: flex-start;
        gap: 10px;
        ${sender === 'user' ? 'justify-content: flex-end;' : ''}
      `;

      const darkNow = isDarkMode();

      if (sender !== 'user') {
        const avatar = document.createElement('img');
        avatar.src = logoUrl;
        avatar.onerror = function(){ this.onerror=null; this.src = logoFallbackUrl; };
        avatar.alt = 'LifeContext';
        avatar.style.cssText = `
          flex-shrink: 0;
          width: 32px;
          height: 32px;
          border-radius: 8px;
          object-fit: cover;
          margin-top: 2px;
          background: transparent;
        `;
        messageContainer.appendChild(avatar);
      }

      if (sender === 'user') {
        const bubble = document.createElement('div');
        bubble.style.cssText = `
          max-width: 420px;
          padding: 12px;
          border-radius: 16px;
          background: #2563eb;
          color: white;
          font-size: 14px;
          line-height: 1.5;
          word-wrap: break-word;
          border-bottom-right-radius: 0;
        `;
        bubble.textContent = text;
        messageContainer.appendChild(bubble);
      } else {
        // AI 文本：不使用气泡，只显示纯文本块（ChatGPT 风格）
        const textBlock = document.createElement('div');
        textBlock.style.cssText = `
          max-width: 560px;
          padding: 2px 0;
          background: transparent;
          color: ${darkNow ? '#e2e8f0' : '#0f172a'};
          font-size: 15px;
          line-height: 1.7;
          word-wrap: break-word;
          white-space: pre-wrap;
        `;
        textBlock.textContent = text;
        messageContainer.appendChild(textBlock);
      }

      chatMessages.appendChild(messageContainer);
      scrollToLatest();
    }

    // 显示加载状态
    function showLoading() {
      if (isLoading) return;
      
      isLoading = true;
      const loadingContainer = document.createElement('div');
      loadingContainer.id = 'loading-message';
      loadingContainer.style.cssText = `
        display: flex;
        justify-content: flex-start;
        margin-bottom: 16px;
      `;
      
      const lbBg = isDarkMode() ? '#1e293b' : '#e2e8f0';
      const dot = isDarkMode() ? '#64748b' : '#94a3b8';
      loadingContainer.innerHTML = `
        <div style="
          background: ${lbBg};
          color: inherit;
          padding: 12px 16px;
          border-radius: 18px;
          max-width: 80%;
          box-shadow: 0 2px 8px rgba(0,0,0,0.2);
          display: flex;
          align-items: flex-start;
          gap: 12px;
        ">
          
          <div style="flex: 1;">
            <div style="display: flex; gap: 4px; align-items: center;">
              <div style="width: 6px; height: 6px; background: ${dot}; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out;"></div>
              <div style="width: 6px; height: 6px; background: ${dot}; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out; animation-delay: 0.2s;"></div>
              <div style="width: 6px; height: 6px; background: ${dot}; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out; animation-delay: 0.4s;"></div>
            </div>
          </div>
        </div>
      `;
      
      chatMessages.appendChild(loadingContainer);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // 隐藏加载状态
    function hideLoading() {
      const loadingElement = document.getElementById('loading-message');
      if (loadingElement) {
        loadingElement.remove();
      }
      isLoading = false;
    }
    
    // 发送消息到后端API（通过后台脚本代理）
    async function sendMessageToAPI(message) {
      try {
        const response = await new Promise((resolve, reject) => {
          try {
            // 提取当前页面内容（如果需要）
            let pageContent = null;
            if (usePageContext) {
              try {
                // 克隆body以避免修改原始DOM
                const bodyClone = document.body.cloneNode(true);
                // 移除script和style标签
                const scripts = bodyClone.querySelectorAll('script, style, noscript');
                scripts.forEach(el => el.remove());
                // 获取文本内容
                pageContent = bodyClone.innerText || bodyClone.textContent || '';
                // 限制长度（避免发送过大内容）
                if (pageContent.length > 50000) {
                  pageContent = pageContent.substring(0, 50000) + '...';
                }
              } catch (e) {
                console.warn('提取页面内容失败:', e);
              }
            }
            
            chrome.runtime.sendMessage({ 
              type: 'SEND_CHAT_MESSAGE', 
              payload: {
                query: message,
                context: (function(){
                  const base = { session_id: sessionId, user_preferences: {} };
                  if (usePageContext) {
                    base.page = { 
                      url: location.href, 
                      title: document.title || '',
                      content: pageContent || ''  // 添加页面内容
                    };
                  }
                  return base;
                })(),
                session_id: sessionId,
                user_id: 'user_123'
              }
            }, (resp) => {
              if (chrome.runtime.lastError) {
                reject(new Error(chrome.runtime.lastError.message));
              } else {
                resolve(resp);
              }
            });
          } catch (e) {
            reject(e);
          }
        });
        
        if (!response || !response.ok) {
          throw new Error(response?.error || '发送消息失败');
        }
        
        return response.data;
      } catch (error) {
        console.error('发送消息失败:', error);
        throw error;
      }
    }
    
    // 发送消息函数
    async function sendMessage() {
      const message = inputField.value.trim();
      if (!message || isLoading) return;

      // 添加用户消息
      addMessage(message, 'user');
      inputField.value = '';
      
      // 显示加载状态
      showLoading();
      
      try {
        // 发送到后端API
        const response = await sendMessageToAPI(message);
        
        // 隐藏加载状态
        hideLoading();
        
        // 处理API响应 - 适配新的数据格式
        if (response && response.data && response.data.success) {
          // 更新workflow_id
          if (response.data.workflow_id) {
            currentWorkflowId = response.data.workflow_id;
          }
          
          // 显示AI回复 - 新格式直接使用 response 字段
          let aiResponse = '抱歉，我无法理解您的问题。请稍后再试。';
          
          if (response.data.response) {
            aiResponse = response.data.response;
          } else if (response.data.message) {
            aiResponse = response.data.message;
          }
          
          addMessage(aiResponse, 'ai');
        } else {
          addMessage('抱歉，我无法理解您的问题。请稍后再试。', 'ai');
        }
      } catch (error) {
        // 隐藏加载状态
        hideLoading();
        
        // 添加错误消息
        addMessage('抱歉，发送消息时出现错误。请检查网络连接或稍后再试。', 'ai');
        console.error('聊天错误:', error);
      }
    }

    // 切换聊天框显示
    function toggleChat() {
      isChatOpen = !isChatOpen;
      chatBox.style.display = isChatOpen ? 'flex' : 'none';
      
      if (isChatOpen) {
        // 展开聊天框时隐藏悬浮球
        ballElement.style.display = 'none';
        container.style.pointerEvents = 'auto';
        inputField.focus();
        // 展示页面上下文 pill
        usePageContext = true;
        updateContextPill();
        ensureLayout();
        scrollToLatest();
      } else {
        // 关闭聊天框时显示悬浮球
        ballElement.style.display = 'flex';
        container.style.pointerEvents = 'none';
        ballElement.style.pointerEvents = 'auto';
      }
    }

    // 展开/收缩聊天框
    function toggleChatExpanded() {
      isChatExpanded = !isChatExpanded;
      const toggleBtn = chatHeader.querySelector('#toggle-chat');
      const chatMessages = document.getElementById('chat-messages');
      const chatInput = document.getElementById('chat-input');
      // 确保只做水平展开动画
      chatBox.style.transitionProperty = 'left, right, width, max-width';
      chatBox.style.transitionDuration = '0.3s';
      chatBox.style.transitionTimingFunction = 'ease-in-out';
      chatBox.style.transformOrigin = 'right center';
      
      if (isChatExpanded) {
        // 展开状态 - 仅水平扩大，保持高度与初始一致
        // 不固定高度，使用自适应高度以确保内容占满
        chatBox.style.height = '';
        // 不改变 top/bottom，保持与初始相同高度
        // 水平方向展开
        chatBox.style.left = '50px';
        chatBox.style.right = '50px';
        chatBox.style.width = 'auto';
        chatBox.style.maxWidth = 'none';
        chatMessages.style.display = 'flex';
        chatInput.style.display = 'flex';
        toggleBtn.innerHTML = `
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8.293 17.293a1 1 0 010-1.414L13.586 10 8.293 4.707a1 1 0 011.414-1.414l5.707 5.707a2 2 0 010 2.828l-5.707 5.707a1 1 0 01-1.414 0z" fill="currentColor"/>
          </svg>
        `;
        toggleBtn.title = '收缩';

        ensureLayout();
        scrollToLatest();
      } else {
        // 收缩状态 - 小窗口
        // 恢复自动高度
        chatBox.style.height = '';
        // 位置保持初始上下边距不变
        chatBox.style.top = '24px';
        chatBox.style.bottom = '24px';
        chatBox.style.left = 'auto';
        chatBox.style.right = '24px';
        chatBox.style.width = 'calc(100vw - 3rem)';
        chatBox.style.maxWidth = '420px';
        chatBox.style.minWidth = '320px';
        chatMessages.style.display = 'flex';
        chatInput.style.display = 'flex';
        toggleBtn.innerHTML = `
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M15.707 17.293a1 1 0 01-1.414 0L8.586 11.586a2 2 0 010-2.828l5.707-5.707a1 1 0 011.414 1.414L10.414 10l5.293 5.293a1 1 0 010 1.414z" fill="currentColor"/>
          </svg>
        `;
        toggleBtn.title = '展开';
        ensureLayout();
        scrollToLatest();
      }
    }

    // 悬浮球点击事件
    ballElement.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleChat();
    });

    // 主页面按钮事件
    // 根据扩展配置打开主页
    async function openHome() {
      try {
        const defaults = { FRONTEND_HOST: 'localhost', FRONTEND_PORT: '3000' };
        const cfg = await new Promise((resolve) => {
          try { chrome.storage.sync.get(defaults, (res) => resolve(res || defaults)); }
          catch(_) { resolve(defaults); }
        });
        const url = `http://${cfg.FRONTEND_HOST}:${cfg.FRONTEND_PORT}/`;
        window.open(url, '_blank');
      } catch (_) {
        window.open('http://localhost:3000/', '_blank');
      }
    }
    chatHeader.querySelector('#home-btn').addEventListener('click', openHome);

    // 关闭按钮事件
    chatHeader.querySelector('#close-chat').addEventListener('click', () => {
      toggleChat();
    });

    // 展开/收缩按钮事件
    chatHeader.querySelector('#toggle-chat').addEventListener('click', (e) => {
      e.stopPropagation();
      toggleChatExpanded();
    });

    // 添加按钮悬停效果
    const homeBtn = chatHeader.querySelector('#home-btn');
    const toggleBtn = chatHeader.querySelector('#toggle-chat');
    const closeBtn = chatHeader.querySelector('#close-chat');
    
   homeBtn.addEventListener('mouseenter', () => {
     const dark = isDarkMode();
     homeBtn.style.backgroundColor = dark ? '#334155' : '#e2e8f0';
     homeBtn.style.color = dark ? '#e2e8f0' : '#0f172a';
   });
   homeBtn.addEventListener('mouseleave', () => {
     const dark = isDarkMode();
     homeBtn.style.backgroundColor = 'transparent';
     homeBtn.style.color = dark ? '#94a3b8' : '#64748b';
   });
   toggleBtn.addEventListener('mouseenter', () => {
     const dark = isDarkMode();
     toggleBtn.style.backgroundColor = dark ? '#334155' : '#e2e8f0';
     toggleBtn.style.color = dark ? '#e2e8f0' : '#0f172a';
   });
   toggleBtn.addEventListener('mouseleave', () => {
     const dark = isDarkMode();
     toggleBtn.style.backgroundColor = 'transparent';
     toggleBtn.style.color = dark ? '#94a3b8' : '#64748b';
   });
   closeBtn.addEventListener('mouseenter', () => {
     const dark = isDarkMode();
     closeBtn.style.backgroundColor = dark ? '#334155' : '#e2e8f0';
     closeBtn.style.color = dark ? '#e2e8f0' : '#0f172a';
   });
   closeBtn.addEventListener('mouseleave', () => {
     const dark = isDarkMode();
     closeBtn.style.backgroundColor = 'transparent';
     closeBtn.style.color = dark ? '#94a3b8' : '#64748b';
   });

    // 悬浮球悬停效果
    ballElement.addEventListener('mouseenter', () => {
      ballElement.style.transform = 'scale(1.1)';
    });
    
    ballElement.addEventListener('mouseleave', () => {
      ballElement.style.transform = 'scale(1)';
    });

    // 发送按钮事件
    sendBtn.addEventListener('click', sendMessage);

    // 输入框回车事件
    inputField.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
    
    // 禁用发送按钮当输入为空或正在加载时
    function updateSendButton() {
      const hasText = inputField.value.trim().length > 0;
      sendBtn.disabled = !hasText || isLoading;
      sendBtn.style.opacity = (!hasText || isLoading) ? '0.5' : '1';
      sendBtn.style.cursor = (!hasText || isLoading) ? 'not-allowed' : 'pointer';
    }
    
    // 监听输入变化
    inputField.addEventListener('input', updateSendButton);
    // 监听窗口尺寸变化，保持滚动与占满
    window.addEventListener('resize', () => {
      ensureLayout();
    });
    
    // 初始化按钮状态
    updateSendButton();
    ensureLayout();

    // 页面上下文逻辑
    let usePageContext = true;

    function updateContextPill() {
      const textEl = contextPill.querySelector('#page-context-text');
      if (!usePageContext) {
        contextPill.style.display = 'none';
        return;
      }
      try {
        const title = document.title || '';
        const host = location.hostname || '';
        const display = title || host || location.href;
        if (textEl) textEl.textContent = display;
        contextPill.style.display = 'flex';
      } catch (_) {
        contextPill.style.display = 'none';
      }
    }

    const pillCloseBtn = contextPill.querySelector('#page-context-close');
    if (pillCloseBtn) {
      pillCloseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        usePageContext = false;
        updateContextPill();
        ensureLayout();
      });
    }

    // 悬浮球拖拽功能
    ballElement.addEventListener('mousedown', (e) => {
      e.preventDefault();
      isDragging = true;
      const rect = ballElement.getBoundingClientRect();
      dragOffset.x = e.clientX - rect.left;
      dragOffset.y = e.clientY - rect.top;
      
      ballElement.style.cursor = 'grabbing';
      ballElement.style.transform = 'scale(0.95)';
    });

    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      
      const newX = e.clientX - dragOffset.x;
      const newY = e.clientY - dragOffset.y;
      
      // 限制在视窗内
      const maxX = window.innerWidth - 60;
      const maxY = window.innerHeight - 60;
      
      ballElement.style.left = Math.max(0, Math.min(newX, maxX)) + 'px';
      ballElement.style.top = Math.max(0, Math.min(newY, maxY)) + 'px';
      ballElement.style.bottom = 'auto';
      ballElement.style.right = 'auto';
    });

    document.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        ballElement.style.cursor = 'pointer';
        ballElement.style.transform = 'scale(1)';
      }
    });

    // 主题（浅/深）自适应：根据浏览器设置调整背景与文本
    const themeSheet = document.createElement('style');
    chatBox.appendChild(themeSheet);
    const headerTitle = chatHeader.querySelector('h2');
    const iconBtns = [chatHeader.querySelector('#home-btn'), chatHeader.querySelector('#toggle-chat'), chatHeader.querySelector('#close-chat')];
    const mq = (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)')) || null;
    function applyTheme(isDark) {
      try {
        if (isDark) {
          chatBox.style.background = '#1e293b';
          chatHeader.style.borderBottom = '1px solid rgba(71, 85, 105, 0.5)';
          headerTitle && (headerTitle.style.color = '#f1f5f9');
          iconBtns.forEach(b => b && (b.style.color = '#94a3b8'));
          chatInput.style.background = '#1e293b';
          inputField.style.background = '#334155';
          inputField.style.color = '#e2e8f0';
          contextPill.style.background = 'rgba(15, 23, 42, 0.85)';
          contextPill.style.border = '1px solid rgba(71,85,105,0.5)';
          contextPill.style.color = '#e2e8f0';
          ballElement.style.boxShadow = '0 10px 25px rgba(0,0,0,0.3)';
          themeSheet.textContent = `#chat-input::placeholder{color:#94a3b8;opacity:.8}`;
        } else {
          chatBox.style.background = '#f8fafc';
          chatHeader.style.borderBottom = '1px solid #e2e8f0';
          headerTitle && (headerTitle.style.color = '#0f172a');
          iconBtns.forEach(b => b && (b.style.color = '#64748b'));
          chatInput.style.background = '#ffffff';
          inputField.style.background = '#e2e8f0';
          inputField.style.color = '#0f172a';
          contextPill.style.background = 'rgba(241,245,249,0.95)';
          contextPill.style.border = '1px solid #cbd5e1';
          contextPill.style.color = '#0f172a';
          ballElement.style.boxShadow = '0 10px 25px rgba(0,0,0,0.12)';
          themeSheet.textContent = `#chat-input::placeholder{color:#64748b;opacity:.9}`;
        }
      } catch (_) {}
    }
    if (mq) {
      applyTheme(mq.matches);
      const handler = (e) => applyTheme(e.matches);
      if (typeof mq.addEventListener === 'function') mq.addEventListener('change', handler);
      else if (typeof mq.addListener === 'function') mq.addListener(handler);
    } else {
      applyTheme(true);
    }

    return container;
  } 

  // 悬浮球状态管理
  let floatingChatEnabled = true;
  let chatContainer = null;

  // 从存储中加载悬浮球状态
  async function loadFloatingChatState() {
    try {
      const result = await chrome.storage.sync.get(['floatingChatEnabled']);
      floatingChatEnabled = result.floatingChatEnabled !== false; // 默认为true
    } catch (error) {
      console.log('加载悬浮球状态失败，使用默认值');
      floatingChatEnabled = true;
    }
  }

  (async function main() {
    try {
      // 先加载悬浮球状态
      await loadFloatingChatState();
      
      // 创建并添加悬浮聊天组件
      chatContainer = createFloatingChat();
      (document.body || document.documentElement).appendChild(chatContainer);
      
      // 根据状态决定是否显示悬浮球
      if (!floatingChatEnabled) {
        hideFloatingChat();
      }
      
      console.log('✅ 悬浮聊天组件已加载');
    } catch (err) {
      console.error('inject error', err);
    }
  })();

  // 获取悬浮球容器
  function getChatContainer() {
    if (!chatContainer) {
      chatContainer = document.getElementById('my-floating-chat-container');
    }
    return chatContainer;
  }

  // 显示悬浮球
  function showFloatingChat() {
    const container = getChatContainer();
    if (container) {
      container.style.display = 'block';
      floatingChatEnabled = true;
      console.log('悬浮聊天球已显示');
    }
  }

  // 隐藏悬浮球
  function hideFloatingChat() {
    const container = getChatContainer();
    if (container) {
      container.style.display = 'none';
      floatingChatEnabled = false;
      console.log('悬浮聊天球已隐藏');
    }
  }

  // 切换悬浮球状态
  function toggleFloatingChat(enabled) {
    if (enabled) {
      showFloatingChat();
    } else {
      hideFloatingChat();
    }
  }

  // 监听来自popup的消息
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'TOGGLE_FLOATING_CHAT') {
      toggleFloatingChat(message.enabled);
      sendResponse({ success: true, enabled: floatingChatEnabled });
    } else if (message.type === 'GET_FLOATING_CHAT_STATUS') {
      sendResponse({ enabled: floatingChatEnabled });
    }
    return true;
  });

})();