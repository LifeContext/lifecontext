(function () {
  if (window.__my_floating_chat_injected__) return;
  window.__my_floating_chat_injected__ = true;

  // 全局事件拦截器：防止 Claude 在替换输入框内容时自动触发发送
  // 当 suppressInputEvents 为 true 时，拦截所有 input/change 事件
  let suppressInputEvents = false;
  try {
    window.addEventListener('input', (e) => {
      if (suppressInputEvents) {
        e.stopImmediatePropagation();
        e.stopPropagation();
        e.preventDefault();
      }
    }, { capture: true });
    window.addEventListener('change', (e) => {
      if (suppressInputEvents) {
        e.stopImmediatePropagation();
        e.stopPropagation();
        e.preventDefault();
      }
    }, { capture: true });
  } catch (_) {}

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
    let dragStart = { x: 0, y: 0 };
    let hasDragged = false;
    let messages = [];
    let isLoading = false;
    let currentWorkflowId = '';
    let sessionId = `session_${Date.now()}`;
    // 流式状态
    let hasActiveStream = false;
    let activePort = null;
    const workflowIdToElement = Object.create(null);
    const mdBufferByWorkflowId = Object.create(null);
    // 发送按钮原始内容，用于恢复
    let cachedOriginalBtnHTML = null;
      // 记录触发优化的控制条按钮（用于加载态恢复）
      let currentTriggerBtn = null;

    // 切换发送按钮“生成中...”状态
    function setGeneratingState(on) {
      try {
        if (!cachedOriginalBtnHTML) cachedOriginalBtnHTML = sendBtn.innerHTML;
        if (on) {
          sendBtn.disabled = true;
          sendBtn.style.opacity = '0.7';
          sendBtn.style.cursor = 'not-allowed';
          sendBtn.style.borderRadius = '20px';
          sendBtn.style.padding = '8px 12px';
          sendBtn.style.minWidth = '108px';
          sendBtn.innerHTML = `
            <span style="display:inline-flex;align-items:center;gap:8px;">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="display:block;color:white;animation:lc-spin 1s linear infinite">
                <path d="M12 2a10 10 0 1 0 10 10" stroke="currentColor" stroke-width="3" stroke-linecap="round" fill="none"/>
              </svg>
              <span>生成中...</span>
            </span>`;
        } else {
          sendBtn.disabled = false;
          sendBtn.style.opacity = '1';
          sendBtn.style.cursor = 'pointer';
          sendBtn.style.borderRadius = '50%';
          sendBtn.style.padding = '10px';
          sendBtn.style.minWidth = '';
          sendBtn.innerHTML = cachedOriginalBtnHTML || sendBtn.innerHTML;
        }
      } catch (_) {}
    }

    // Markdown 渲染（基础版）：安全转义 + 标题/加粗/斜体/代码块/行内代码/链接/无序列表
    function escapeHtml(s) {
      return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    }
    function renderMarkdown(src) {
      try {
        if (!src) return '';
        let text = String(src).replace(/\r\n/g, '\n');
        // 转义
        text = escapeHtml(text);
        // 代码块 ```lang\n...\n```
        const blocks = [];
        text = text.replace(/```([\w+-]*)\n([\s\S]*?)```/g, function(_, lang, code) {
          const i = blocks.length;
          blocks.push({ lang: (lang || '').toLowerCase(), code });
          return `@@MD_CODE_${i}@@`;
        });
        // 标题
        text = text.replace(/^###\s+(.*)$/gm, '<h3>$1</h3>');
        text = text.replace(/^##\s+(.*)$/gm, '<h2>$1</h2>');
        text = text.replace(/^#\s+(.*)$/gm, '<h1>$1</h1>');
        // 无序列表
        const lines = text.split('\n');
        let outLines = [];
        let inList = false;
        for (const ln of lines) {
          const m = ln.match(/^\s*[-*]\s+(.*)$/);
          if (m) {
            if (!inList) { inList = true; outLines.push('<ul>'); }
            outLines.push('<li>' + m[1] + '</li>');
          } else {
            if (inList) { inList = false; outLines.push('</ul>'); }
            outLines.push(ln);
          }
        }
        if (inList) outLines.push('</ul>');
        text = outLines.join('\n');
        // 行内代码
        text = text.replace(/`([^`\n]+)`/g, '<code>$1</code>');
        // 加粗/斜体
        text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/__(.+?)__/g, '<strong>$1</strong>');
        text = text.replace(/(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)/g, '<em>$1</em>');
        text = text.replace(/(?<!_)_(?!\s)(.+?)(?<!\s)_(?!_)/g, '<em>$1</em>');
        // 链接
        text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, function(_, label, href) {
          const safe = href.replace(/"/g, '&quot;');
          return `<a href="${safe}" target="_blank" rel="noopener noreferrer">${label}</a>`;
        });
        // 段落
        const tmp = text.split('\n');
        const out = [];
        let buf = [];
        const flush = () => {
          if (buf.length) {
            const c = buf.join(' ').trim();
            if (c) out.push('<p>' + c + '</p>');
            buf = [];
          }
        };
        for (const ln of tmp) {
          if (/^\s*$/.test(ln)) { flush(); continue; }
          if (/^\s*<(h1|h2|h3|ul|li|\/ul|pre|blockquote)/.test(ln)) {
            flush(); out.push(ln);
          } else {
            buf.push(ln);
          }
        }
        flush();
        let html = out.join('\n');
        // 还原代码块
        html = html.replace(/@@MD_CODE_(\d+)@@/g, function(_, idxStr) {
          const idx = Number(idxStr);
          const blk = blocks[idx] || { lang: '', code: '' };
          const codeHtml = escapeHtml(blk.code);
          const langClass = blk.lang ? ` class="language-${blk.lang}"` : '';
          return `<pre><code${langClass}>${codeHtml}</code></pre>`;
        });
        return html;
      } catch (e) {
        return '<pre><code>' + escapeHtml(String(src)) + '</code></pre>';
      }
    }

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
          font-size: 15px;
          line-height: 1.7;
          word-wrap: break-word;
          white-space: normal;
        `;
        textBlock.classList.add('ai-text');
        textBlock.innerHTML = renderMarkdown(text);
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
    
    // 建立/复用 Port 长连接并处理流式消息
    function ensureStreamPort() {
      try {
        if (activePort) return activePort;
        activePort = chrome.runtime.connect({ name: 'STREAM_CHAT' });
        activePort.onDisconnect.addListener(() => {
          activePort = null;
          hasActiveStream = false;
          try { setGeneratingState(false); } catch(_) {}
        });
        activePort.onMessage.addListener((msg) => {
          if (!msg || msg.type !== 'STREAM_CHUNK') return;
          const data = msg.data || {};
          const t = String(data.type || '');
          const key = data.workflow_id || 'default';
          if (t === 'start') {
            // 隐藏加载，创建 AI 文本块
            hideLoading();
            const messageContainer = document.createElement('div');
            messageContainer.style.cssText = `display:flex;align-items:flex-start;gap:10px;`;
            const avatar = document.createElement('img');
            avatar.src = logoUrl;
            avatar.onerror = function(){ this.onerror=null; this.src = logoFallbackUrl; };
            avatar.alt = 'LifeContext';
            avatar.style.cssText = `flex-shrink:0;width:32px;height:32px;border-radius:8px;object-fit:cover;margin-top:2px;background:transparent;`;
            messageContainer.appendChild(avatar);
            const textBlock = document.createElement('div');
             textBlock.style.cssText = `max-width:560px;padding:2px 0;background:transparent;font-size:15px;line-height:1.7;white-space:normal;word-wrap:break-word;`;
             textBlock.classList.add('ai-text');
            textBlock.setAttribute('data-has-content', '0');
            textBlock.innerHTML = `<span style="opacity:.7;font-style:italic;">AI 正在思考...</span>`;
            messageContainer.appendChild(textBlock);
            chatMessages.appendChild(messageContainer);
            workflowIdToElement[key] = textBlock;
            mdBufferByWorkflowId[key] = '';
            hasActiveStream = true;
            requestAnimationFrame(() => { chatMessages.scrollTop = chatMessages.scrollHeight; });
            try { updateSendButton(); } catch(_) {}
          } else if (t === 'content') {
            const el = workflowIdToElement[key];
            if (el) {
              if (el.getAttribute('data-has-content') !== '1') {
                el.setAttribute('data-has-content', '1');
                el.innerHTML = '';
              }
              mdBufferByWorkflowId[key] = (mdBufferByWorkflowId[key] || '') + String(data.content || '');
              el.innerHTML = renderMarkdown(mdBufferByWorkflowId[key]);
              requestAnimationFrame(() => { chatMessages.scrollTop = chatMessages.scrollHeight; });
            }
          } else if (t === 'done') {
            hasActiveStream = false;
            try { setGeneratingState(false); } catch(_) {}
            try { updateSendButton(); } catch(_) {}
          } else if (t === 'error') {
            const el = workflowIdToElement[key];
            if (el) {
              if (el.getAttribute('data-has-content') !== '1') {
                el.setAttribute('data-has-content', '1');
                el.innerHTML = '';
              }
              const prev = mdBufferByWorkflowId[key] || '';
              mdBufferByWorkflowId[key] = prev + `\n\n**[Error]** ${String(data.content || '')}`;
              el.innerHTML = renderMarkdown(mdBufferByWorkflowId[key]);
            } else {
              addMessage(`**[Error]** ${data.content || ''}`, 'ai');
            }
            hasActiveStream = false;
            try { setGeneratingState(false); } catch(_) {}
            try { updateSendButton(); } catch(_) {}
          }
        });
        return activePort;
      } catch (_) {
        return null;
      }
    }
    
    // 发送消息函数（流式）
    async function sendMessage() {
      const message = inputField.value.trim();
      if (!message || isLoading || hasActiveStream) return;

      // 添加用户消息
      addMessage(message, 'user');
      inputField.value = '';
      
      // 显示加载状态，等待 start 后隐藏
      showLoading();
      
      try {
        // 提取页面内容（可选）
        let pageContent = null;
        if (usePageContext) {
          try {
            const bodyClone = document.body.cloneNode(true);
            const scripts = bodyClone.querySelectorAll('script, style, noscript');
            scripts.forEach(el => el.remove());
            pageContent = bodyClone.innerText || bodyClone.textContent || '';
            if (pageContent.length > 50000) pageContent = pageContent.substring(0, 50000) + '...';
          } catch (e) {
            console.warn('提取页面内容失败:', e);
          }
        }
        const payload = {
          query: message,
          context: (function(){
            const base = { session_id: sessionId, user_preferences: {} };
            if (usePageContext) {
              base.page = { url: location.href, title: document.title || '', content: pageContent || '' };
            }
            return base;
          })(),
        session_id: sessionId,
        user_id: 'user_123'
        };
        hasActiveStream = true;
        try { setGeneratingState(true); } catch(_) {}
        const port = ensureStreamPort();
        if (port) {
          port.postMessage({ action: 'start', payload });
        } else {
          throw new Error('无法建立流式端口');
        }
      } catch (error) {
        hideLoading();
        hasActiveStream = false;
        try { setGeneratingState(false); } catch(_) {}
        addMessage('抱歉，发送消息时出现错误。请检查网络连接或稍后再试。', 'ai');
        console.error('聊天错误:', error);
        try { updateSendButton(); } catch(_) {}
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
      if (hasDragged) {
        hasDragged = false;
        return;
      }
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
        // 兜底：构建后前端由 Backend 代理，端口 8000
        window.open('http://localhost:8000/', '_blank');
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
      const disabled = !hasText || isLoading || hasActiveStream;
      sendBtn.disabled = disabled;
      sendBtn.style.opacity = disabled ? '0.5' : '1';
      sendBtn.style.cursor = disabled ? 'not-allowed' : 'pointer';
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
      hasDragged = false;
      const rect = ballElement.getBoundingClientRect();
      dragOffset.x = e.clientX - rect.left;
      dragOffset.y = e.clientY - rect.top;
      dragStart.x = e.clientX;
      dragStart.y = e.clientY;
      
      ballElement.style.cursor = 'grabbing';
      ballElement.style.transform = 'scale(0.95)';
    });

    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      
      const moveX = e.clientX - dragStart.x;
      const moveY = e.clientY - dragStart.y;
      if (!hasDragged && Math.hypot(moveX, moveY) > 6) {
        hasDragged = true;
      }

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
          themeSheet.textContent = `
#chat-input::placeholder{color:#94a3b8;opacity:.8}
#chat-messages .ai-text{color:#e2e8f0;}
#chat-messages pre{background:#0f172a;color:#e2e8f0;padding:12px;border-radius:8px;overflow:auto;border:1px solid rgba(71,85,105,0.5);}
#chat-messages code{background:#0b1220;color:#e2e8f0;padding:2px 6px;border-radius:6px;}
#chat-messages h1,#chat-messages h2,#chat-messages h3{margin:10px 0;color:#e2e8f0;}
#chat-messages a{color:#60a5fa;text-decoration:underline;}
@keyframes lc-spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}
          `;
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
          themeSheet.textContent = `
#chat-input::placeholder{color:#64748b;opacity:.9}
#chat-messages .ai-text{color:#0f172a;}
#chat-messages pre{background:#e2e8f0;color:#0f172a;padding:12px;border-radius:8px;overflow:auto;border:1px solid #cbd5e1;}
#chat-messages code{background:#e2e8f0;color:#0f172a;padding:2px 6px;border-radius:6px;}
#chat-messages h1,#chat-messages h2,#chat-messages h3{margin:10px 0;color:#0f172a;}
#chat-messages a{color:#2563eb;text-decoration:underline;}
@keyframes lc-spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}
          `;
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

  // 检查是否应该注入悬浮球
  function shouldInjectFloatingChat() {
    // 1. 检查是否在 iframe 中（不在主窗口）
    if (window.self !== window.top) {
      console.log('[LC] 检测到 iframe，跳过悬浮球注入');
      return false;
    }

    // 2. 检查 URL 是否包含验证相关的关键词
    const url = window.location.href.toLowerCase();
    const verificationKeywords = [
      'recaptcha',
      'captcha',
      'verification',
      'verify',
      'challenge',
      'hcaptcha',
      'turnstile',
      'cloudflare',
      'security-check',
      'bot-detection'
    ];
    
    for (const keyword of verificationKeywords) {
      if (url.includes(keyword)) {
        console.log('[LC] 检测到验证页面 URL，跳过悬浮球注入:', keyword);
        return false;
      }
    }

    // 3. 检查页面标题是否包含验证相关文本
    const title = (document.title || '').toLowerCase();
    const titleKeywords = ['验证', 'verification', 'captcha', 'recaptcha', '人机验证'];
    for (const keyword of titleKeywords) {
      if (title.includes(keyword.toLowerCase())) {
        console.log('[LC] 检测到验证页面标题，跳过悬浮球注入:', keyword);
        return false;
      }
    }

    // 4. 检查页面是否包含 reCAPTCHA 相关的元素或类名
    const recaptchaSelectors = [
      '[id*="recaptcha"]',
      '[class*="recaptcha"]',
      '[id*="captcha"]',
      '[class*="captcha"]',
      'iframe[src*="recaptcha"]',
      'iframe[src*="challenges.cloudflare.com"]',
      'iframe[src*="hcaptcha"]',
      '.g-recaptcha',
      '#recaptcha',
      '[data-sitekey]' // reCAPTCHA 通常有 data-sitekey 属性
    ];

    for (const selector of recaptchaSelectors) {
      try {
        if (document.querySelector(selector)) {
          console.log('[LC] 检测到验证元素，跳过悬浮球注入:', selector);
          return false;
        }
      } catch (e) {
        // 忽略选择器错误
      }
    }

    // 5. 检查页面内容是否包含验证相关的文本（中文和英文）
    // 只在 body 存在时检查，避免性能问题
    if (document.body) {
      const bodyText = (document.body.innerText || document.body.textContent || '').toLowerCase();
      const contentKeywords = [
        '进行人机身份验证',
        '人机验证',
        'i\'m not a robot',
        'verify you\'re human',
        'select all images',
        '选择所有包含',
        'privacy policy - terms of use',
        '隐私权 - 使用条款',
        'reCAPTCHA Enterprise'
      ];
      
      // 只检查前 5000 个字符，提高性能
      const textToCheck = bodyText.substring(0, 5000);
      for (const keyword of contentKeywords) {
        if (textToCheck.includes(keyword.toLowerCase())) {
          console.log('[LC] 检测到验证页面内容，跳过悬浮球注入:', keyword);
          return false;
        }
      }
    }

    // 6. 检查是否在特定的验证域名下
    const hostname = window.location.hostname.toLowerCase();
    const verificationDomains = [
      'recaptcha.net',
      'google.com/recaptcha',
      'hcaptcha.com',
      'challenges.cloudflare.com'
    ];
    
    for (const domain of verificationDomains) {
      if (hostname.includes(domain)) {
        console.log('[LC] 检测到验证域名，跳过悬浮球注入:', domain);
        return false;
      }
    }

    return true;
  }

  (async function main() {
    try {
      // 检查是否应该注入悬浮球
      if (!shouldInjectFloatingChat()) {
        console.log('[LC] 跳过悬浮球注入（验证页面或 iframe）');
        return;
      }

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

  // ==============================
  // 主流 AI 网站输入框右侧优化按钮（圆形 Logo）
  // - 支持：ChatGPT、Gemini、Claude、豆包、Kimi Chat
  // - 功能：读取输入框文本 -> 调用 /api/agent/chat/stream (optimize_prompt) -> 接收 prompt_optimized 事件 -> 覆盖输入框内容
  // ==============================
  function initPromptOptimizeButton() {
    try {
      // 仅在主流 AI 网站生效
      if (!isSupportedAISite(location.hostname)) return;
      // ==============================
      //   新增：排除非聊天页面的路径
      // ==============================
      const blockedPathKeywords = [
        '/settings', '/setting', '/account', '/accounts', '/profile', '/profiles',
        '/index', '/introducing', '/about', '/help', '/support',
        '/privacy', '/terms', '/billing', '/subscription', '/pricing',
        '/login', '/signin', '/signup', '/register', '/logout'
      ];
      const path = location.pathname.toLowerCase();
      for (const keyword of blockedPathKeywords) {
        if (path.includes(keyword)) {
          console.log('[LC] 当前路径被排除，不注入优化按钮：', path);
          return;
        }
      }
      const logoUrl = (typeof chrome !== 'undefined' && chrome.runtime && typeof chrome.runtime.getURL === 'function')
        ? chrome.runtime.getURL('logo.png')
        : '';
      // 站点适配器：根据不同 AI 网站定位稳定的 Controls Bar（附件/语音/发送所在容器）
      function getHostCategory() {
        const h = (location.hostname || '').toLowerCase();
        if (h.includes('chat.openai.com') || h.includes('chatgpt.com') || h.endsWith('openai.com')) return 'chatgpt';
        if (h.includes('claude.ai')) return 'claude';
        if (h.includes('doubao.com') || h.includes('douba.ai')) return 'doubao';
        if (h.includes('gemini.google.com') || h.includes('ai.google.com') || h.includes('aistudio.google.com')) return 'gemini';
        if (h.includes('moonshot.cn') || h.includes('kimi.moonshot.cn') || h.includes('kimi.com')) return 'kimi';
        if (h.includes('x.ai') || h.includes('grok')) return 'grok';
        if (h.includes('perplexity.ai')) return 'perplexity';
        if (h.includes('deepseek.com')) return 'deepseek';
        return '';
      }
      function getControlsBarSelectors(kind) {
        const common = [];
        switch (kind) {
          case 'chatgpt':
            return [
              '[data-testid="composer-actions"]'
            ];
          case 'claude':
            return [
              // Claude: 使用最新的输入栏工具栏（2025 最新结构）
              'div[data-testid="input-composer"] > div.flex.items-center',
              'div[data-testid="input-composer"] div.flex.items-center.gap-2'
            ];
          case 'doubao':
            return [
              // 用户提供：Controls Bar 占位容器，类名带稳定前缀 tools-placeholder-
              'div.tools-placeholder-WzV9jb',
              'div[class^="tools-placeholder-"]'
            ];
          case 'gemini':
            return [
              // Gemini: 使用包含上传按钮和工具箱的容器（leading-actions-wrapper）
              'div.leading-actions-wrapper.ui-ready-fade-in',
              'div.leading-actions-wrapper',
              // 兜底：发送按钮的父容器
              'button[aria-label*="Send" i]::parent'
            ];
          case 'kimi':
            return [
              // Kimi Chat: 底部整条操作栏容器
              'div.chat-editor-action'
            ];
          case 'grok':
            return [
              // Grok: 优先使用模型选择按钮的容器（div.z-20），样式更美观
              'div.z-20:has(button#model-select-trigger)',
              'button#model-select-trigger::parent',
              // 兜底：发送按钮的父容器
              'button[type="submit"]::parent',
              // 最后兜底：包含输入框的容器
              'div.tiptap.ProseMirror::parent'
            ];
          case 'perplexity':
            return [
              // Perplexity: 使用包含所有操作按钮的容器（flex items-center justify-self-end）
              'div.flex.items-center.justify-self-end.col-start-3.row-start-2',
              'div.flex.items-center.justify-self-end:has(button[data-testid="sources-switcher-button"])',
              // 兜底：包含附件按钮的容器
              'div:has(button[data-testid="attach-files-button"])::parent'
            ];
          default:
            return common;
        }
      }
      function findControlsBar(rootDoc = document) {
        const kind = getHostCategory();
        const selectors = getControlsBarSelectors(kind);
        const root = rootDoc || document;
        for (const sel of selectors) {
          if (sel.endsWith('::parent')) {
            const baseSel = sel.replace('::parent', '');
            const nodes = queryAllDeep([baseSel], root);
            for (const n of nodes) {
              if (n && n.parentElement) return n.parentElement;
            }
          } else {
            const nodes = queryAllDeep([sel], root);
            if (nodes && nodes.length) return nodes[0];
          }
        }
        // 兜底：带发送按钮的容器
        try {
          const sendBtn = queryAllDeep(['button[aria-label*="Send" i]', 'button[type="submit"]'], root)[0];
          if (sendBtn && sendBtn.parentElement) return sendBtn.parentElement;
        } catch (_) {}
        return null;
      }
      // Page Context 桥接：通过扩展外链脚本注入（避免 CSP 阻止 inline script）
      function injectPageBridge() {
        try {
          if (document.getElementById('lc-page-bridge')) return;
          const s = document.createElement('script');
          s.id = 'lc-page-bridge';
          s.src = chrome.runtime.getURL('page-context.js');
          (document.documentElement || document.head || document.body).appendChild(s);
          s.onload = () => { try { s.parentNode && s.parentNode.removeChild(s); } catch(_) {} };
        } catch (_) {}
      }
      // 在输入框邻近范围内查找 Controls Bar（优先策略，避免误命中侧边栏）
      function findControlsBarFor(inputEl) {
        try {
          if (!inputEl) return null;
          const root =
            (inputEl.closest && (inputEl.closest('form,[role="form"],[class*="composer"],[class*="Composer"],[class*="editor"],[class*="Input"],[class*="input"]') || inputEl.parentElement))
            || inputEl.parentElement
            || document;
          return findControlsBar(root) || null;
        } catch (_) {
          return null;
        }
      }
      function ensureInlineBtn() {
        const id = 'lc-optimize-btn-inline';
        let b = document.getElementById(id);
        if (b) return b;
        b = document.createElement('button');
        b.id = id;
        b.type = 'button';
        b.style.cssText = `
          width: 34px;
          height: 34px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          border: none;
          background: #ffffff url('${logoUrl}') center/70% no-repeat;
          box-shadow: 0 6px 16px rgba(0,0,0,.2);
          cursor: pointer;
          transition: transform .15s ease, opacity .15s ease;
          margin-left: 6px;
          margin-right: 6px;
        `;
        b.title = '优化提示词（LifeContext）';
        // 防止站点委托的发送事件（click/mouseup/pointerup 等）被触发
        try {
          const swallow = (evt) => {
            try { evt.preventDefault && evt.preventDefault(); } catch(_) {}
            try { evt.stopPropagation && evt.stopPropagation(); } catch(_) {}
            try { evt.stopImmediatePropagation && evt.stopImmediatePropagation(); } catch(_) {}
          };
          ['pointerdown','pointerup','mousedown','mouseup','click','touchstart','touchend'].forEach((t) => {
            b.addEventListener(t, swallow, { capture: true });
          });
        } catch(_) {}
        b.addEventListener('mouseenter', () => { b.style.transform = 'scale(1.05)'; });
        b.addEventListener('mouseleave', () => { b.style.transform = 'scale(1)'; });
        b.addEventListener('click', onOptimizeClick);
        return b;
      }
      function injectIntoControlsBar(bar) {
        try {
          if (!bar) return false;
          const kind = getHostCategory();
          const btnEl = ensureInlineBtn();
          if (kind === 'kimi') {
            // Kimi: 只注入到底部 Controls Bar 的右侧区域，且尽量放在发送按钮之前，避免影响其它控件
            const rightArea = bar.querySelector('div.right-area') || bar;
            // 优先：放在 K2 模型选择（current-model）左侧
            const modelContainer = rightArea.querySelector('div.current-model') || rightArea.querySelector('.current-model') || rightArea.querySelector('.model-name') || null;
            if (modelContainer && modelContainer.parentElement === rightArea) {
              if (btnEl.parentElement !== rightArea || btnEl.nextSibling !== modelContainer) {
                rightArea.insertBefore(btnEl, modelContainer);
              }
            } else {
              // 次选：放在发送按钮之前
              const sendContainer = rightArea.querySelector('div.send-button-container');
              if (sendContainer && sendContainer.parentElement === rightArea) {
                if (btnEl.parentElement !== rightArea || btnEl.nextSibling !== sendContainer) {
                  rightArea.insertBefore(btnEl, sendContainer);
                }
              } else {
                // 兜底：右侧区域末尾
                if (btnEl.parentElement !== rightArea) {
                  rightArea.appendChild(btnEl);
                }
              }
            }
          } else if (kind === 'chatgpt') {
            // ChatGPT：将按钮挂入右侧 controls 父容器（听写/语音/发送所在）
            // 父容器示例：<div class="ms-auto flex items-center gap-1.5"> ... </div>
            // 需求：把按钮放在“听写按钮（composer-btn）”左边
            // 更精确与稳健的选择器：兼容 data-state 变化与 radix 描述前缀含下划线
            // 同时增加 SVG path d 前缀回退（来自提供的 outerHTML）
            let voiceBtn =
              bar.querySelector('span[data-state][aria-describedby^="radix-_"] > button.composer-btn[aria-label="听写按钮"]') ||
              bar.querySelector('span[data-state][aria-describedby^="radix-_"] > button.composer-btn[aria-label*="听写"]') ||
              bar.querySelector('span[data-state][aria-describedby^="radix-"] > button.composer-btn[aria-label="听写按钮"]') ||
              bar.querySelector('span[data-state][aria-describedby^="radix-"] > button.composer-btn[aria-label*="听写"]') ||
              bar.querySelector('button.composer-btn[aria-label="听写按钮"]') ||
              bar.querySelector('button.composer-btn[aria-label*="听写"]') ||
              bar.querySelector('button.composer-btn[aria-label*="语音"]') ||
              null;
            if (!voiceBtn) {
              // Fallback 1: 全局查找（避免 bar 未能涵盖该节点）
              voiceBtn =
                document.querySelector('span[data-state][aria-describedby^="radix-_"] > button.composer-btn[aria-label="听写按钮"]') ||
                document.querySelector('span[data-state][aria-describedby^="radix-_"] > button.composer-btn[aria-label*="听写"]') ||
                document.querySelector('span[data-state][aria-describedby^="radix-"] > button.composer-btn[aria-label="听写按钮"]') ||
                document.querySelector('span[data-state][aria-describedby^="radix-"] > button.composer-btn[aria-label*="听写"]') ||
                document.querySelector('button.composer-btn[aria-label="听写按钮"]') ||
                document.querySelector('button.composer-btn[aria-label*="听写"]') ||
                document.querySelector('button.composer-btn[aria-label*="语音"]') ||
                null;
            }
            if (!voiceBtn) {
              // Fallback 2: 通过独有的 SVG path 前缀定位
              const micPath =
                bar.querySelector('button.composer-btn svg path[d^="M15.7806"]') ||
                document.querySelector('button.composer-btn svg path[d^="M15.7806"]');
              if (micPath && typeof micPath.closest === 'function') {
                const micBtn = micPath.closest('button');
                if (micBtn) voiceBtn = micBtn;
              }
            }
            // 定位父容器（避免命中顶部/侧边栏），优先具有 ms-auto flex items-center 的容器
            const controlsParent = (voiceBtn && ((voiceBtn.closest && voiceBtn.closest('div.ms-auto.flex.items-center')) || (voiceBtn.parentElement && voiceBtn.parentElement))) ||
              bar.querySelector('div.ms-auto.flex.items-center') ||
              bar;
            if (voiceBtn && controlsParent) {
              // 锚点优先取外层 span，以确保插入在该按钮整体左侧
              const anchor = (voiceBtn.closest && (voiceBtn.closest('span[data-state]') || voiceBtn.closest('span'))) || voiceBtn;
              // 让按钮采用站点相同的按钮样式类，视觉一致
              try { btnEl.classList.add('composer-btn'); } catch (_) {}
              if (btnEl.parentElement !== controlsParent || btnEl.nextSibling !== anchor) {
                controlsParent.insertBefore(btnEl, anchor);
              }
            } else {
              // 回退：放到语音容器左侧（旧结构兼容）
              const speechContainer = bar.querySelector('div[data-testid="composer-speech-button-container"]');
              if (speechContainer && speechContainer.parentElement) {
                const parent = speechContainer.parentElement;
                if (btnEl.parentElement !== parent || btnEl.nextSibling !== speechContainer) {
                  parent.insertBefore(btnEl, speechContainer);
                }
              } else if (btnEl.parentElement !== bar) {
                bar.appendChild(btnEl);
              }
            }
          } else if (kind === 'grok') {
            // Grok: 优先使用模型选择按钮的容器（div.z-20），样式更美观
            const modelBtn = bar.querySelector('button#model-select-trigger') || document.querySelector('button#model-select-trigger');
            if (modelBtn && modelBtn.parentElement) {
              const modelContainer = modelBtn.parentElement;
              // 确保是 div.z-20 容器
              if (modelContainer.classList && modelContainer.classList.contains('z-20')) {
                // 调整按钮样式以匹配 Grok 的 UI
                btnEl.style.cssText = '';
                btnEl.className = 'inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium cursor-pointer focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-60 disabled:cursor-not-allowed transition-colors duration-100 select-none hover:bg-button-ghost-hover disabled:hover:bg-transparent border border-transparent h-10 py-1.5 text-sm rounded-full text-primary px-3.5 focus:outline-none';
                // 设置按钮内容：使用图标
                const logoImg = document.createElement('img');
                logoImg.src = logoUrl;
                logoImg.style.cssText = 'width: 18px; height: 18px; display: block;';
                logoImg.onerror = () => {
                  // 如果图片加载失败，使用 SVG 图标作为回退
                  btnEl.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                      <path d="M2 17l10 5 10-5"></path>
                      <path d="M2 12l10 5 10-5"></path>
                    </svg>
                  `;
                };
                if (!btnEl.querySelector('img')) {
                  btnEl.innerHTML = '';
                  btnEl.appendChild(logoImg);
                }
                btnEl.title = '优化提示词（LifeContext）';
                // 将按钮插入到模型选择按钮之前
                if (btnEl.parentElement !== modelContainer || btnEl.nextSibling !== modelBtn) {
                  modelContainer.insertBefore(btnEl, modelBtn);
                }
                return true;
              }
            }
            // 兜底：使用发送按钮的父容器
            const sendBtn = bar.querySelector('button[type="submit"]') || document.querySelector('button[type="submit"]');
            if (sendBtn && sendBtn.parentElement) {
              const controlsParent = sendBtn.parentElement;
              // 将按钮插入到发送按钮之前
              if (btnEl.parentElement !== controlsParent || btnEl.nextSibling !== sendBtn) {
                controlsParent.insertBefore(btnEl, sendBtn);
              }
              return true;
            }
            // 最后兜底：放到 bar 末尾
            if (btnEl.parentElement !== bar) {
              bar.appendChild(btnEl);
            }
          } else if (kind === 'claude') {
            // Claude: 使用最新的输入栏工具栏（2025 最新结构）
            // 安全区域：div[data-testid="input-composer"] > div.flex.items-center
            // 绝对不能插入到 Vue 管控区域（如 Extended thinking 按钮的父容器）
            
            // 确保 bar 是安全的工具栏区域
            if (!bar) return false;
            
            // 检查是否已经插入过（防止重复插入）
            if (bar.querySelector('[data-lc-btn]') !== null) {
              // 如果按钮已经在 bar 中，确保位置正确
              if (btnEl.parentElement === bar) return true;
            }
            
            // 确保 bar 不包含 Vue 管控的按钮（安全检测）
            if (bar.querySelector('button[aria-label="Extended thinking"]')) {
              // 这是 Vue 管控区域，不能插入，查找正确的工具栏
              const toolbar = document.querySelector('div[data-testid="input-composer"] > div.flex.items-center');
              if (!toolbar || toolbar.querySelector('button[aria-label="Extended thinking"]')) {
                return false; // 找不到安全区域，放弃
              }
              bar = toolbar; // 使用正确的工具栏
            }
            
            // 查找左侧按钮组（通常包含 +、设置、历史等按钮）
            // 尝试找到左侧按钮组的最后一个按钮，将我们的按钮插入到它之后
            const leftButtons = bar.querySelectorAll('button[aria-label*="Attach" i], button[aria-label*="Open" i], button[aria-label*="menu" i]');
            let insertAfter = null;
            
            if (leftButtons.length > 0) {
              // 找到左侧按钮组的最后一个按钮
              insertAfter = leftButtons[leftButtons.length - 1];
            }
            
            // 配置按钮样式（匹配 Claude 的按钮风格）
            btnEl.setAttribute('data-lc-btn', '1');
            btnEl.setAttribute('type', 'button');
            btnEl.setAttribute('aria-label', '优化提示词');
            btnEl.title = '优化提示词（LifeContext）';
            
            // 匹配 Claude 按钮的样式：方形、圆角、深色背景、白色图标
            btnEl.style.cssText = `
              width: 32px;
              height: 32px;
              min-width: 32px;
              border-radius: 8px;
              border: none;
              display: inline-flex;
              align-items: center;
              justify-content: center;
              cursor: pointer;
              background: rgba(255, 255, 255, 0.05);
              transition: all 0.15s ease;
              margin: 0 4px;
              padding: 0;
              flex-shrink: 0;
            `;
            
            // 防止触发 Claude 的发送逻辑：使用 pointer-events 方案
            // 将按钮设置为 pointer-events: none，让内部元素处理点击
            // 这样 Claude 的全局监听器不会监听到 button 元素的事件
            btnEl.style.pointerEvents = 'none';
            
            // 清空并重建按钮内容
            btnEl.innerHTML = '';
            
            // 创建内部容器，用于处理点击事件
            const innerContainer = document.createElement('div');
            innerContainer.style.cssText = `
              pointer-events: auto;
              display: flex;
              align-items: center;
              justify-content: center;
              width: 100%;
              height: 100%;
              cursor: pointer;
            `;
            
            // 添加 hover 效果（在内部容器上）
            innerContainer.addEventListener('mouseenter', () => {
              btnEl.style.background = 'rgba(255, 255, 255, 0.1)';
              btnEl.style.transform = 'scale(1.05)';
            });
            innerContainer.addEventListener('mouseleave', () => {
              btnEl.style.background = 'rgba(255, 255, 255, 0.05)';
              btnEl.style.transform = 'scale(1)';
            });
            
            // 创建图标（使用原本的样式）
            const logoImg = document.createElement('img');
            logoImg.src = logoUrl;
            logoImg.alt = 'LifeContext';
            logoImg.style.cssText = 'width: 18px; height: 18px; display: block;';
            logoImg.onerror = () => {
              try {
                // 如果图片加载失败，使用 SVG 图标作为回退
                const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svg.setAttribute('width', '18');
                svg.setAttribute('height', '18');
                svg.setAttribute('viewBox', '0 0 24 24');
                svg.setAttribute('fill', 'none');
                svg.setAttribute('stroke', 'currentColor');
                svg.setAttribute('stroke-width', '2');
                svg.style.cssText = 'width: 18px; height: 18px;';
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                path.setAttribute('d', 'M12 2L2 7l10 5 10-5-10-5z');
                svg.appendChild(path);
                if (logoImg.parentElement === innerContainer) {
                  innerContainer.replaceChild(svg, logoImg);
                } else {
                  innerContainer.appendChild(svg);
                }
              } catch(_) {
                // 最后的回退：使用文本
                innerContainer.textContent = 'LC';
                innerContainer.style.fontSize = '11px';
                innerContainer.style.fontWeight = '600';
              }
            };
            
            // 在内部容器上绑定点击事件，阻止冒泡
            innerContainer.addEventListener('click', (e) => {
              try {
                e.preventDefault && e.preventDefault();
                e.stopPropagation && e.stopPropagation();
                e.stopImmediatePropagation && e.stopImmediatePropagation();
              } catch(_) {}
              onOptimizeClick(e);
            });
            
            // 为内部容器添加其他可能的事件阻止
            ['pointerdown', 'pointerup', 'mousedown', 'mouseup', 'touchstart', 'touchend'].forEach((t) => {
              innerContainer.addEventListener(t, (e) => {
                try {
                  e.preventDefault && e.preventDefault();
                  e.stopPropagation && e.stopPropagation();
                  e.stopImmediatePropagation && e.stopImmediatePropagation();
                } catch(_) {}
              }, { capture: true, passive: false });
            });
            
            innerContainer.appendChild(logoImg);
            btnEl.appendChild(innerContainer);
            
            // 插入按钮到合适的位置
            if (insertAfter && insertAfter.nextSibling) {
              // 插入到左侧按钮组的最后一个按钮之后
              bar.insertBefore(btnEl, insertAfter.nextSibling);
            } else if (insertAfter) {
              // 如果没有下一个兄弟节点，追加到按钮之后
              insertAfter.parentElement.insertBefore(btnEl, insertAfter.nextSibling);
            } else {
              // 兜底：插入到工具栏的开头（左侧）
              if (btnEl.parentElement !== bar) {
                bar.insertBefore(btnEl, bar.firstChild);
              }
            }
            
            return true;
          } else if (kind === 'gemini') {
            // Gemini: 将按钮插入到 leading-actions-wrapper 容器中，放在工具按钮之前
            // 注意：使用安全的 DOM 操作，避免破坏 Angular 的渲染结构
            const toolBtn = bar.querySelector('button.toolbox-drawer-button') || bar.querySelector('.toolbox-drawer-button');
            if (toolBtn && toolBtn.parentElement) {
              // 检查按钮是否已经有正确的 Material Design 结构
              const hasCorrectStructure = btnEl.querySelector('.mat-mdc-button-persistent-ripple') && 
                                         btnEl.querySelector('.mdc-button__label') &&
                                         btnEl.querySelector('.mat-mdc-button-touch-target');
              
              if (!hasCorrectStructure) {
                // 安全地清空按钮内容：只移除我们添加的元素，不影响 Angular 管理的元素
                const existingChildren = Array.from(btnEl.children);
                existingChildren.forEach(child => {
                  // 只移除我们可能添加的元素，保留 Angular 管理的元素
                  if (child.classList && (
                    child.classList.contains('mat-mdc-button-persistent-ripple') ||
                    child.classList.contains('mdc-button__label') ||
                    child.classList.contains('mat-focus-indicator') ||
                    child.classList.contains('mat-mdc-button-touch-target') ||
                    child.classList.contains('mat-ripple') ||
                    child.tagName === 'IMG' ||
                    child.tagName === 'MAT-ICON'
                  )) {
                    try { child.remove(); } catch(_) {}
                  }
                });
                
                // 调整按钮样式以匹配 Gemini 的 Material Design UI
                btnEl.style.cssText = '';
                btnEl.className = 'mdc-button mat-mdc-button-base mat-mdc-button mat-unthemed';
                btnEl.setAttribute('mat-button', '');
                btnEl.setAttribute('type', 'button');
                btnEl.setAttribute('aria-label', '优化提示词');
                btnEl.style.marginLeft = '6px';
                
                // 使用 createElement + appendChild 安全构建 Material Design 结构
                const ripple = document.createElement('span');
                ripple.className = 'mat-mdc-button-persistent-ripple mdc-button__ripple';
                btnEl.appendChild(ripple);
                
                // 使用图标
                const logoImg = document.createElement('img');
                logoImg.src = logoUrl;
                logoImg.alt = 'LifeContext';
                logoImg.style.cssText = 'width: 24px; height: 24px; display: block;';
                logoImg.onerror = () => {
                  // 如果图片加载失败，使用 Material Icon 作为回退
                  try {
                    const matIcon = document.createElement('mat-icon');
                    matIcon.setAttribute('role', 'img');
                    matIcon.className = 'mat-icon notranslate gds-icon-l google-symbols mat-ligature-font mat-icon-no-color';
                    matIcon.setAttribute('aria-hidden', 'true');
                    matIcon.setAttribute('data-mat-icon-type', 'font');
                    matIcon.setAttribute('data-mat-icon-name', 'auto_awesome');
                    matIcon.setAttribute('fonticon', 'auto_awesome');
                    if (logoImg.parentElement === btnEl) {
                      btnEl.replaceChild(matIcon, logoImg);
                    } else {
                      const label = btnEl.querySelector('.mdc-button__label');
                      if (label) {
                        btnEl.insertBefore(matIcon, label);
                      } else {
                        btnEl.appendChild(matIcon);
                      }
                    }
                  } catch(_) {}
                };
                btnEl.appendChild(logoImg);
                
                const label = document.createElement('span');
                label.className = 'mdc-button__label';
                label.textContent = '';
                btnEl.appendChild(label);
                
                const focusIndicator = document.createElement('span');
                focusIndicator.className = 'mat-focus-indicator';
                btnEl.appendChild(focusIndicator);
                
                const touchTarget = document.createElement('span');
                touchTarget.className = 'mat-mdc-button-touch-target';
                btnEl.appendChild(touchTarget);
                
                const ripple2 = document.createElement('span');
                ripple2.className = 'mat-ripple mat-mdc-button-ripple';
                btnEl.appendChild(ripple2);
              }
              
              btnEl.title = '优化提示词（LifeContext）';
              
              // 将按钮插入到工具按钮之前（确保不影响原有按钮）
              const toolBtnContainer = toolBtn.closest('.toolbox-drawer-button-container') || toolBtn.closest('.toolbox-drawer') || toolBtn.parentElement;
              if (toolBtnContainer && toolBtnContainer.parentElement === bar) {
                // 确保按钮不在错误的位置
                if (btnEl.parentElement !== bar || btnEl.nextSibling !== toolBtnContainer) {
                  // 如果按钮已经在 bar 中但位置不对，先移除再插入
                  if (btnEl.parentElement === bar) {
                    btnEl.remove();
                  }
                  bar.insertBefore(btnEl, toolBtnContainer);
                }
              } else if (toolBtn.parentElement === bar) {
                if (btnEl.parentElement !== bar || btnEl.nextSibling !== toolBtn) {
                  if (btnEl.parentElement === bar) {
                    btnEl.remove();
                  }
                  bar.insertBefore(btnEl, toolBtn);
                }
              }
              return true;
            }
            // 兜底：放到 bar 末尾
            if (btnEl.parentElement !== bar) {
              bar.appendChild(btnEl);
            }
          } else if (kind === 'perplexity') {
            // Perplexity: 将按钮插入到容器最左边（第一个按钮之前）
            const firstBtn = bar.querySelector('button[data-testid="sources-switcher-button"]') || bar.querySelector('button[aria-label="选择模型"]') || bar.firstElementChild;
            if (firstBtn) {
              // 创建一个 span 包裹按钮，保持结构一致
              let btnWrapper = btnEl.parentElement;
              if (!btnWrapper || btnWrapper.tagName !== 'SPAN' || btnWrapper.parentElement !== bar) {
                if (btnWrapper && btnWrapper !== bar) {
                  btnEl.remove();
                }
                btnWrapper = document.createElement('span');
                btnWrapper.appendChild(btnEl);
              }
              // 调整按钮样式以匹配 Perplexity 的 UI
              btnEl.style.cssText = '';
              btnEl.className = 'focus-visible:bg-subtle hover:bg-subtle text-quiet hover:text-foreground dark:hover:bg-subtle font-sans focus:outline-none outline-none outline-transparent transition duration-300 ease-out select-none items-center relative group/button font-semimedium justify-center text-center items-center rounded-lg cursor-pointer active:scale-[0.97] active:duration-150 active:ease-outExpo origin-center whitespace-nowrap inline-flex text-sm h-8 aspect-[9/8]';
              btnEl.setAttribute('type', 'button');
              btnEl.setAttribute('aria-label', '优化提示词');
              // 设置按钮内容：使用图标
              const logoImg = document.createElement('img');
              logoImg.src = logoUrl;
              logoImg.style.cssText = 'width: 16px; height: 16px; display: block;';
              logoImg.onerror = () => {
                // 如果图片加载失败，使用 SVG 图标作为回退
                btnEl.innerHTML = `
                  <div class="flex items-center min-w-0 gap-two justify-center">
                    <div class="flex shrink-0 items-center justify-center size-4">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                        <path d="M2 17l10 5 10-5"></path>
                        <path d="M2 12l10 5 10-5"></path>
                      </svg>
                    </div>
                  </div>
                `;
              };
              if (!btnEl.querySelector('img')) {
                btnEl.innerHTML = '';
                const innerDiv = document.createElement('div');
                innerDiv.className = 'flex items-center min-w-0 gap-two justify-center';
                const iconDiv = document.createElement('div');
                iconDiv.className = 'flex shrink-0 items-center justify-center size-4';
                iconDiv.appendChild(logoImg);
                innerDiv.appendChild(iconDiv);
                btnEl.appendChild(innerDiv);
              }
              btnEl.title = '优化提示词（LifeContext）';
              // 将按钮插入到第一个按钮之前（按钮可能在 span 中）
              const firstBtnWrapper = firstBtn.closest('span') || firstBtn;
              if (btnWrapper.parentElement !== bar || btnWrapper.nextSibling !== firstBtnWrapper) {
                bar.insertBefore(btnWrapper, firstBtnWrapper);
              }
              return true;
            }
            // 兜底：放到 bar 末尾
            if (btnEl.parentElement !== bar) {
              bar.appendChild(btnEl);
            }
          } else {
            // 其他站点：优先跟在语音/听写按钮后
            const mic = bar.querySelector('button[data-testid="composer-voice-button"], button[aria-label*="Voice" i], button[aria-label*="Microphone" i], button[aria-label*="语音" i], button[aria-label*="听写" i]');
            if (mic && mic.parentElement === bar) {
              if (btnEl.parentElement !== bar || btnEl.previousSibling !== mic) {
                bar.insertBefore(btnEl, mic.nextSibling);
              }
            } else if (btnEl.parentElement !== bar) {
              bar.appendChild(btnEl);
            }
          }
          return true;
        } catch (_) { return false; }
      }
      function tryInlineMount() {
        const inputEl = (typeof pickChatInput === 'function') ? pickChatInput() : null;
        const bar = findControlsBarFor(inputEl) || findControlsBar();
        if (!bar) {
          // ChatGPT 兜底：直接全局查找“听写”按钮并插入到其左侧
          const kind = getHostCategory();
          if (kind === 'chatgpt') {
            const okDirect = (function tryDirectChatGPTMount() {
              try {
                const btnEl = ensureInlineBtn();
                // 全局稳健选择器（不依赖 data-state），并包含 SVG path 回退
                let voiceBtn =
                  document.querySelector('button.composer-btn[aria-label="听写按钮"]') ||
                  document.querySelector('button.composer-btn[aria-label*="听写"]') ||
                  document.querySelector('button.composer-btn[aria-label*="语音"]') ||
                  document.querySelector('span[aria-describedby^="radix-_"] > button.composer-btn[aria-label*="听写"]') ||
                  document.querySelector('span[aria-describedby^="radix-"] > button.composer-btn[aria-label*="听写"]') ||
                  null;
                if (!voiceBtn) {
                  const micPath = document.querySelector('button.composer-btn svg path[d^="M15.7806"]');
                  if (micPath && typeof micPath.closest === 'function') {
                    const micBtn = micPath.closest('button');
                    if (micBtn) voiceBtn = micBtn;
                  }
                }
                if (!voiceBtn) return false;
                // 父容器与锚点
                const controlsParent =
                  (voiceBtn.closest && voiceBtn.closest('div.ms-auto.flex.items-center')) ||
                  voiceBtn.parentElement ||
                  document.body;
                const anchor =
                  (voiceBtn.closest && (voiceBtn.closest('span[data-state]') || voiceBtn.closest('span'))) ||
                  voiceBtn;
                try { btnEl.classList.add('composer-btn'); } catch (_) {}
                if (btnEl.parentElement !== controlsParent || btnEl.nextSibling !== anchor) {
                  controlsParent.insertBefore(btnEl, anchor);
                }
                return true;
              } catch (_) { return false; }
            })();
            if (!okDirect) return false;
            injectPageBridge();
            return true;
          } else if (kind === 'grok') {
            // Grok 兜底：优先查找模型选择按钮的容器，否则使用发送按钮的父容器
            const okDirect = (function tryDirectGrokMount() {
              try {
                const btnEl = ensureInlineBtn();
                // 优先：查找模型选择按钮的容器（div.z-20）
                const modelBtn = document.querySelector('button#model-select-trigger');
                if (modelBtn && modelBtn.parentElement) {
                  const modelContainer = modelBtn.parentElement;
                  if (modelContainer.classList && modelContainer.classList.contains('z-20')) {
                    // 调整按钮样式以匹配 Grok 的 UI
                    btnEl.style.cssText = '';
                    btnEl.className = 'inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium cursor-pointer focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-60 disabled:cursor-not-allowed transition-colors duration-100 select-none hover:bg-button-ghost-hover disabled:hover:bg-transparent border border-transparent h-10 py-1.5 text-sm rounded-full text-primary px-3.5 focus:outline-none';
                    // 设置按钮内容：使用图标
                    const logoImg = document.createElement('img');
                    logoImg.src = logoUrl;
                    logoImg.style.cssText = 'width: 18px; height: 18px; display: block;';
                    logoImg.onerror = () => {
                      btnEl.innerHTML = `
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                          <path d="M2 17l10 5 10-5"></path>
                          <path d="M2 12l10 5 10-5"></path>
                        </svg>
                      `;
                    };
                    if (!btnEl.querySelector('img')) {
                      btnEl.innerHTML = '';
                      btnEl.appendChild(logoImg);
                    }
                    btnEl.title = '优化提示词（LifeContext）';
                    // 将按钮插入到模型选择按钮之前
                    if (btnEl.parentElement !== modelContainer || btnEl.nextSibling !== modelBtn) {
                      modelContainer.insertBefore(btnEl, modelBtn);
                    }
                    return true;
                  }
                }
                // 兜底：使用发送按钮的父容器
                const sendBtn = document.querySelector('button[type="submit"]');
                if (!sendBtn || !sendBtn.parentElement) return false;
                const controlsParent = sendBtn.parentElement;
                // 将按钮插入到发送按钮之前
                if (btnEl.parentElement !== controlsParent || btnEl.nextSibling !== sendBtn) {
                  controlsParent.insertBefore(btnEl, sendBtn);
                }
                return true;
              } catch (_) { return false; }
            })();
            if (!okDirect) return false;
            injectPageBridge();
            return true;
          } else if (kind === 'claude') {
            // Claude 兜底：使用最新的输入栏工具栏（2025 最新结构）
            const okDirect = (function tryDirectClaudeMount() {
              try {
                const btnEl = ensureInlineBtn();
                // Claude 最新的输入栏工具栏（安全区域）
                const toolbar = document.querySelector('div[data-testid="input-composer"] > div.flex.items-center');
                if (!toolbar) return false; // Claude 还没渲染完成
                
                // 防止插入到 Vue 管控区域（必须只插入 toolbar）
                if (toolbar.querySelector('[data-lc-btn]') !== null) {
                  // 如果按钮已经在 toolbar 中，确保位置正确
                  if (btnEl.parentElement === toolbar) return true;
                }
                
                // 确保 toolbar 不包含 Vue 管控的按钮（安全检测）
                if (toolbar.querySelector('button[aria-label="Extended thinking"]')) {
                  return false; // 这是 Vue 管控区域，不能插入
                }
                
                // 查找左侧按钮组（通常包含 +、设置、历史等按钮）
                const leftButtons = toolbar.querySelectorAll('button[aria-label*="Attach" i], button[aria-label*="Open" i], button[aria-label*="menu" i]');
                let insertAfter = null;
                
                if (leftButtons.length > 0) {
                  // 找到左侧按钮组的最后一个按钮
                  insertAfter = leftButtons[leftButtons.length - 1];
                }
                
                // 配置按钮样式（匹配 Claude 的按钮风格）
                btnEl.setAttribute('data-lc-btn', '1');
                btnEl.setAttribute('type', 'button');
                btnEl.setAttribute('aria-label', '优化提示词');
                btnEl.title = '优化提示词（LifeContext）';
                
                // 匹配 Claude 按钮的样式：方形、圆角、深色背景、白色图标
                btnEl.style.cssText = `
                  width: 32px;
                  height: 32px;
                  min-width: 32px;
                  border-radius: 8px;
                  border: none;
                  display: inline-flex;
                  align-items: center;
                  justify-content: center;
                  cursor: pointer;
                  background: rgba(255, 255, 255, 0.05);
                  transition: all 0.15s ease;
                  margin: 0 4px;
                  padding: 0;
                  flex-shrink: 0;
                `;
                
                // 防止触发 Claude 的发送逻辑：使用 pointer-events 方案
                // 将按钮设置为 pointer-events: none，让内部元素处理点击
                // 这样 Claude 的全局监听器不会监听到 button 元素的事件
                btnEl.style.pointerEvents = 'none';
                
                // 清空并重建按钮内容
                btnEl.innerHTML = '';
                
                // 创建内部容器，用于处理点击事件
                const innerContainer = document.createElement('div');
                innerContainer.style.cssText = `
                  pointer-events: auto;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  width: 100%;
                  height: 100%;
                  cursor: pointer;
                `;
                
                // 添加 hover 效果（在内部容器上）
                innerContainer.addEventListener('mouseenter', () => {
                  btnEl.style.background = 'rgba(255, 255, 255, 0.1)';
                  btnEl.style.transform = 'scale(1.05)';
                });
                innerContainer.addEventListener('mouseleave', () => {
                  btnEl.style.background = 'rgba(255, 255, 255, 0.05)';
                  btnEl.style.transform = 'scale(1)';
                });
                
                // 创建图标（使用原本的样式）
                const logoImg = document.createElement('img');
                logoImg.src = logoUrl;
                logoImg.alt = 'LifeContext';
                logoImg.style.cssText = 'width: 18px; height: 18px; display: block;';
                logoImg.onerror = () => {
                  try {
                    // 如果图片加载失败，使用 SVG 图标作为回退
                    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                    svg.setAttribute('width', '18');
                    svg.setAttribute('height', '18');
                    svg.setAttribute('viewBox', '0 0 24 24');
                    svg.setAttribute('fill', 'none');
                    svg.setAttribute('stroke', 'currentColor');
                    svg.setAttribute('stroke-width', '2');
                    svg.style.cssText = 'width: 18px; height: 18px;';
                    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    path.setAttribute('d', 'M12 2L2 7l10 5 10-5-10-5z');
                    svg.appendChild(path);
                    if (logoImg.parentElement === innerContainer) {
                      innerContainer.replaceChild(svg, logoImg);
                    } else {
                      innerContainer.appendChild(svg);
                    }
                  } catch(_) {
                    // 最后的回退：使用文本
                    innerContainer.textContent = 'LC';
                    innerContainer.style.fontSize = '11px';
                    innerContainer.style.fontWeight = '600';
                  }
                };
                
                // 在内部容器上绑定点击事件，阻止冒泡
                innerContainer.addEventListener('click', (e) => {
                  try {
                    e.preventDefault && e.preventDefault();
                    e.stopPropagation && e.stopPropagation();
                    e.stopImmediatePropagation && e.stopImmediatePropagation();
                  } catch(_) {}
                  onOptimizeClick(e);
                });
                
                // 为内部容器添加其他可能的事件阻止
                ['pointerdown', 'pointerup', 'mousedown', 'mouseup', 'touchstart', 'touchend'].forEach((t) => {
                  innerContainer.addEventListener(t, (e) => {
                    try {
                      e.preventDefault && e.preventDefault();
                      e.stopPropagation && e.stopPropagation();
                      e.stopImmediatePropagation && e.stopImmediatePropagation();
                    } catch(_) {}
                  }, { capture: true, passive: false });
                });
                
                innerContainer.appendChild(logoImg);
                btnEl.appendChild(innerContainer);
                
                // 插入按钮到合适的位置
                if (insertAfter && insertAfter.nextSibling) {
                  // 插入到左侧按钮组的最后一个按钮之后
                  toolbar.insertBefore(btnEl, insertAfter.nextSibling);
                } else if (insertAfter) {
                  // 如果没有下一个兄弟节点，追加到按钮之后
                  insertAfter.parentElement.insertBefore(btnEl, insertAfter.nextSibling);
                } else {
                  // 兜底：插入到工具栏的开头（左侧）
                  if (btnEl.parentElement !== toolbar) {
                    toolbar.insertBefore(btnEl, toolbar.firstChild);
                  }
                }
                
                return true;
              } catch (_) { return false; }
            })();
            if (!okDirect) return false;
            injectPageBridge();
            return true;
          } else if (kind === 'gemini') {
            // Gemini 兜底：全局查找 leading-actions-wrapper 容器，并插入按钮
            const okDirect = (function tryDirectGeminiMount() {
              try {
                const btnEl = ensureInlineBtn();
                const controlsContainer = document.querySelector('div.leading-actions-wrapper.ui-ready-fade-in') || 
                                         document.querySelector('div.leading-actions-wrapper');
                if (!controlsContainer) return false;
                const toolBtn = controlsContainer.querySelector('button.toolbox-drawer-button') || 
                               controlsContainer.querySelector('.toolbox-drawer-button');
                if (!toolBtn) return false;
                // 调整按钮样式以匹配 Gemini 的 Material Design UI
                btnEl.style.cssText = '';
                btnEl.className = 'mdc-button mat-mdc-button-base mat-mdc-button mat-unthemed';
                btnEl.setAttribute('mat-button', '');
                btnEl.setAttribute('type', 'button');
                btnEl.setAttribute('aria-label', '优化提示词');
                btnEl.style.marginLeft = '6px';
                // 设置按钮内容：使用 Material Design 结构
                btnEl.innerHTML = '';
                const ripple = document.createElement('span');
                ripple.className = 'mat-mdc-button-persistent-ripple mdc-button__ripple';
                btnEl.appendChild(ripple);
                // 使用图标
                const logoImg = document.createElement('img');
                logoImg.src = logoUrl;
                logoImg.alt = 'LifeContext';
                logoImg.style.cssText = 'width: 24px; height: 24px; display: block;';
                logoImg.onerror = () => {
                  // 如果图片加载失败，使用 Material Icon 作为回退
                  const matIcon = document.createElement('mat-icon');
                  matIcon.setAttribute('role', 'img');
                  matIcon.className = 'mat-icon notranslate gds-icon-l google-symbols mat-ligature-font mat-icon-no-color';
                  matIcon.setAttribute('aria-hidden', 'true');
                  matIcon.setAttribute('data-mat-icon-type', 'font');
                  matIcon.setAttribute('data-mat-icon-name', 'auto_awesome');
                  matIcon.setAttribute('fonticon', 'auto_awesome');
                  if (logoImg.parentElement === btnEl) {
                    btnEl.replaceChild(matIcon, logoImg);
                  } else {
                    btnEl.insertBefore(matIcon, btnEl.querySelector('.mdc-button__label') || null);
                  }
                };
                btnEl.appendChild(logoImg);
                const label = document.createElement('span');
                label.className = 'mdc-button__label';
                label.textContent = '优化';
                btnEl.appendChild(label);
                const focusIndicator = document.createElement('span');
                focusIndicator.className = 'mat-focus-indicator';
                btnEl.appendChild(focusIndicator);
                const touchTarget = document.createElement('span');
                touchTarget.className = 'mat-mdc-button-touch-target';
                btnEl.appendChild(touchTarget);
                const ripple2 = document.createElement('span');
                ripple2.className = 'mat-ripple mat-mdc-button-ripple';
                btnEl.appendChild(ripple2);
                btnEl.title = '优化提示词（LifeContext）';
                // 将按钮插入到工具按钮之前
                const toolBtnContainer = toolBtn.closest('.toolbox-drawer-button-container') || toolBtn.closest('.toolbox-drawer') || toolBtn.parentElement;
                if (toolBtnContainer && toolBtnContainer.parentElement === controlsContainer) {
                  if (btnEl.parentElement !== controlsContainer || btnEl.nextSibling !== toolBtnContainer) {
                    controlsContainer.insertBefore(btnEl, toolBtnContainer);
                  }
                } else if (toolBtn.parentElement === controlsContainer) {
                  if (btnEl.parentElement !== controlsContainer || btnEl.nextSibling !== toolBtn) {
                    controlsContainer.insertBefore(btnEl, toolBtn);
                  }
                }
                return true;
              } catch (_) { return false; }
            })();
            if (!okDirect) return false;
            injectPageBridge();
            return true;
          } else if (kind === 'perplexity') {
            // Perplexity 兜底：全局查找操作按钮容器，并插入按钮到最左边
            const okDirect = (function tryDirectPerplexityMount() {
              try {
                const btnEl = ensureInlineBtn();
                const controlsContainer = document.querySelector('div.flex.items-center.justify-self-end.col-start-3.row-start-2') || 
                                         document.querySelector('div.flex.items-center.justify-self-end:has(button[data-testid="sources-switcher-button"])');
                if (!controlsContainer) return false;
                const firstBtn = controlsContainer.querySelector('button[data-testid="sources-switcher-button"]') || 
                                controlsContainer.querySelector('button[aria-label="选择模型"]') || 
                                controlsContainer.firstElementChild;
                if (!firstBtn) return false;
                // 创建一个 span 包裹按钮，保持结构一致
                let btnWrapper = btnEl.parentElement;
                if (!btnWrapper || btnWrapper.tagName !== 'SPAN' || btnWrapper.parentElement !== controlsContainer) {
                  if (btnWrapper && btnWrapper !== controlsContainer) {
                    btnEl.remove();
                  }
                  btnWrapper = document.createElement('span');
                  btnWrapper.appendChild(btnEl);
                }
                // 调整按钮样式以匹配 Perplexity 的 UI
                btnEl.style.cssText = '';
                btnEl.className = 'focus-visible:bg-subtle hover:bg-subtle text-quiet hover:text-foreground dark:hover:bg-subtle font-sans focus:outline-none outline-none outline-transparent transition duration-300 ease-out select-none items-center relative group/button font-semimedium justify-center text-center items-center rounded-lg cursor-pointer active:scale-[0.97] active:duration-150 active:ease-outExpo origin-center whitespace-nowrap inline-flex text-sm h-8 aspect-[9/8]';
                btnEl.setAttribute('type', 'button');
                btnEl.setAttribute('aria-label', '优化提示词');
                // 设置按钮内容：使用图标
                const logoImg = document.createElement('img');
                logoImg.src = logoUrl;
                logoImg.style.cssText = 'width: 16px; height: 16px; display: block;';
                logoImg.onerror = () => {
                  btnEl.innerHTML = `
                    <div class="flex items-center min-w-0 gap-two justify-center">
                      <div class="flex shrink-0 items-center justify-center size-4">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                          <path d="M2 17l10 5 10-5"></path>
                          <path d="M2 12l10 5 10-5"></path>
                        </svg>
                      </div>
                    </div>
                  `;
                };
                if (!btnEl.querySelector('img')) {
                  btnEl.innerHTML = '';
                  const innerDiv = document.createElement('div');
                  innerDiv.className = 'flex items-center min-w-0 gap-two justify-center';
                  const iconDiv = document.createElement('div');
                  iconDiv.className = 'flex shrink-0 items-center justify-center size-4';
                  iconDiv.appendChild(logoImg);
                  innerDiv.appendChild(iconDiv);
                  btnEl.appendChild(innerDiv);
                }
                btnEl.title = '优化提示词（LifeContext）';
                // 将按钮插入到第一个按钮之前
                const firstBtnWrapper = firstBtn.closest('span') || firstBtn;
                if (btnWrapper.parentElement !== controlsContainer || btnWrapper.nextSibling !== firstBtnWrapper) {
                  controlsContainer.insertBefore(btnWrapper, firstBtnWrapper);
                }
                return true;
              } catch (_) { return false; }
            })();
            if (!okDirect) return false;
            injectPageBridge();
            return true;
          }
          return false;
        }
        const ok = injectIntoControlsBar(bar);
        injectPageBridge();
        return ok;
      }
      // 监控 SPA 变化并自动回补
      let mountedInline = tryInlineMount();
      const moInline = new MutationObserver(() => { mountedInline = tryInlineMount() || mountedInline; });
      moInline.observe(document.body || document.documentElement, { childList: true, subtree: true });
      const inlineTicker = setInterval(() => { mountedInline = tryInlineMount() || mountedInline; }, 1000);
      // 无论初次是否成功，都采用“仅内嵌”策略，不再使用浮动定位方案
      // 后续若找到 Controls Bar，会自动插入
      // 结束初始化
      // 注意：下面的浮动定位相关旧逻辑将不再使用
      // 为避免误执行，直接 return
      // 但保留后续函数（如流式端口、发送逻辑）供按钮点击时使用
      // 需要在 return 前初始化供后续函数使用的状态变量（避免 TDZ）
      let targetEl = null;
      let optimizerPort = null;
      let optimizing = false;
      let hasWrittenOptimized = false;
      // 存储按钮的原始内容，用于恢复（需要在 return 前定义，供 setBtnLoadingOn 使用）
      const buttonOriginalContent = new WeakMap();
      // 监听来自 Page Context 的点击消息 -> 触发真正的扩展逻辑
      try {
        window.addEventListener('message', (evt) => {
          try {
            console.log('[LC] Message received:', evt.data, 'source:', evt.source);
            // 检查消息来源和类型
            if (evt && evt.data && evt.data.source === 'lc-page' && evt.data.type === 'LC_OPTIMIZE_CLICK') {
              console.log('[LC] Processing LC_OPTIMIZE_CLICK message');
              try { currentTriggerBtn = document.getElementById('lc-optimize-btn-inline'); } catch(_) {}
              if (typeof onOptimizeClick === 'function') {
                console.log('[LC] Calling onOptimizeClick');
                onOptimizeClick(new Event('lc-optimize'));
              } else {
                console.error('[LC] onOptimizeClick is not a function');
              }
            }
          } catch(err) {
            console.error('[LC] Error in message handler:', err);
          }
        }, false);
      } catch(err) {
        console.error('[LC] Error setting up message listener:', err);
      }
      
      // DeepSeek 特殊处理：将提示词优化按钮插入到"联网搜索"按钮右边
      function initDeepSeekInlineButton() {
        try {
          const host = (location.hostname || '').toLowerCase();
          if (!host.includes('deepseek.com')) return;
          
          // ==============================
          //   排除非聊天页面的路径
          // ==============================
          const blockedPathKeywords = [
            '/settings', '/setting', '/account', '/accounts', '/profile', '/profiles',
            '/index', '/introducing', '/about', '/help', '/support',
            '/privacy', '/terms', '/billing', '/subscription', '/pricing',
            '/login', '/signin', '/signup', '/register', '/logout'
          ];
          const path = location.pathname.toLowerCase();
          for (const keyword of blockedPathKeywords) {
            if (path.includes(keyword)) {
              console.log('[LC] 当前路径被排除，不注入优化按钮：', path);
              return;
            }
          }
          
          // 获取 logo URL（与其他站点一致）
          const logoUrl = (typeof chrome !== 'undefined' && chrome.runtime && typeof chrome.runtime.getURL === 'function')
            ? chrome.runtime.getURL('logo.png')
            : '';
          
          let inlineBtn = null;
          let inserted = false;
          
          // 创建优化函数，通过消息机制触发
          function triggerOptimize() {
            try {
              console.log('[LC] triggerOptimize called');
              // 通过消息机制触发（消息监听器会调用 onOptimizeClick）
              window.postMessage({
                source: 'lc-page',
                type: 'LC_OPTIMIZE_CLICK'
              }, '*');
            } catch (err) {
              console.error('[LC] Error in triggerOptimize:', err);
            }
          }
          
          function findNetworkSearchButton() {
            // 查找包含"联网搜索"文本的按钮
            // 使用简化的查询函数（DeepSeek 通常不需要处理 Shadow DOM）
            function queryButtons(root = document) {
              const results = [];
              function walk(node) {
                if (!node) return;
                try {
                  node.querySelectorAll && node.querySelectorAll('button').forEach((e) => {
                    if (!results.includes(e)) results.push(e);
                  });
                } catch (_) {}
                // 遍历子元素
                try {
                  node.children && Array.from(node.children).forEach((c) => walk(c));
                } catch (_) {}
              }
              walk(root);
              return results;
            }
            
            const buttons = queryButtons(document);
            for (const btn of buttons) {
              const text = (btn.textContent || '').trim();
              if (text.includes('联网搜索') || text.includes('联网')) {
                return btn;
              }
            }
            return null;
          }
          
          function createOptimizeButton() {
            if (inlineBtn) return inlineBtn;
            
            const networkBtn = findNetworkSearchButton();
            if (!networkBtn) return null;
            
            // 创建与其他 AI 网站一致的圆形白色按钮样式
            inlineBtn = document.createElement('button');
            inlineBtn.id = 'lc-optimize-btn-inline';
            inlineBtn.type = 'button';
            inlineBtn.setAttribute('aria-disabled', 'false');
            inlineBtn.setAttribute('role', 'button');
            inlineBtn.tabIndex = 0;
            
            // 使用与其他站点一致的样式：圆形白色按钮，带 logo
            inlineBtn.style.cssText = `
              width: 34px;
              height: 34px;
              display: inline-flex;
              align-items: center;
              justify-content: center;
              border-radius: 50%;
              border: none;
              background: #ffffff url('${logoUrl}') center/70% no-repeat;
              box-shadow: 0 6px 16px rgba(0,0,0,.2);
              cursor: pointer;
              transition: transform .15s ease, opacity .15s ease;
              margin-left: 6px;
              margin-right: 6px;
              padding: 0;
              flex-shrink: 0;
              opacity: .95;
            `;
            
            inlineBtn.title = '优化提示词（LifeContext）';
            
            // 如果 logo 加载失败，使用 SVG 图标作为回退
            const logoImg = document.createElement('img');
            logoImg.src = logoUrl;
            logoImg.style.cssText = 'width: 70%; height: 70%; display: block; object-fit: contain;';
            logoImg.onerror = () => {
              // 如果图片加载失败，使用 SVG 图标作为回退
              inlineBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #3b82f6;">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                  <path d="M2 17l10 5 10-5"></path>
                  <path d="M2 12l10 5 10-5"></path>
                </svg>
              `;
            };
            if (!inlineBtn.querySelector('img')) {
              inlineBtn.appendChild(logoImg);
            }
            
            // 添加悬停效果
            inlineBtn.addEventListener('mouseenter', () => {
              inlineBtn.style.transform = 'scale(1.05)';
            });
            inlineBtn.addEventListener('mouseleave', () => {
              inlineBtn.style.transform = 'scale(1)';
            });
            
            // 添加点击事件（在 swallow 之前，使用 capture 阶段确保优先执行）
            inlineBtn.addEventListener('click', (e) => {
              e.preventDefault();
              e.stopPropagation();
              e.stopImmediatePropagation();
              console.log('[LC] DeepSeek button clicked');
              // 直接调用优化函数
              triggerOptimize();
            }, { capture: true });
            
            // 防止站点委托的发送事件被触发（但不阻止 click，因为 click 已经在 capture 阶段处理）
            try {
              const swallow = (evt) => {
                // 如果是 click 事件，不阻止（因为已经在上面处理了）
                if (evt.type === 'click') return;
                try { evt.preventDefault && evt.preventDefault(); } catch(_) {}
                try { evt.stopPropagation && evt.stopPropagation(); } catch(_) {}
                try { evt.stopImmediatePropagation && evt.stopImmediatePropagation(); } catch(_) {}
              };
              ['pointerdown','pointerup','mousedown','mouseup','touchstart','touchend'].forEach((t) => {
                inlineBtn.addEventListener(t, swallow, { capture: true });
              });
            } catch(_) {}
            
            return inlineBtn;
          }
          
          function insertButton() {
            if (inserted && inlineBtn && inlineBtn.parentElement) return;
            
            const networkBtn = findNetworkSearchButton();
            if (!networkBtn) return;
            
            const container = networkBtn.parentElement;
            if (!container) return;
            
            const btn = createOptimizeButton();
            if (!btn) return;
            
            // 插入到"联网搜索"按钮之后
            if (networkBtn.nextSibling) {
              container.insertBefore(btn, networkBtn.nextSibling);
            } else {
              container.appendChild(btn);
            }
            
            inserted = true;
          }
          
          // 初始尝试插入
          setTimeout(() => {
            insertButton();
          }, 500);
          
          // 监听 DOM 变化，确保按钮始终存在
          const observer = new MutationObserver(() => {
            if (!inserted || !inlineBtn || !inlineBtn.parentElement) {
              inserted = false;
              insertButton();
            }
          });
          
          observer.observe(document.body, {
            childList: true,
            subtree: true
          });
          
          // 定期检查（作为兜底）
          setInterval(() => {
            if (!inserted || !inlineBtn || !inlineBtn.parentElement) {
              inserted = false;
              insertButton();
            }
          }, 2000);
          
        } catch (e) {
          console.warn('[LC] DeepSeek inline button init failed:', e);
        }
      }
      
      // 初始化 DeepSeek 内嵌按钮
      try { initDeepSeekInlineButton(); } catch (_) {}
      
      return;  // 仅采用内嵌注入策略，阻断旧的浮动定位逻辑

      function isSupportedAISite(host) {
        const h = String(host || '').toLowerCase();
        return (
          h.includes('chat.openai.com') || h.includes('chatgpt.com') || h.endsWith('openai.com') ||
          h.includes('gemini.google.com') || h.includes('aistudio.google.com') || h.includes('ai.google.com') ||
          h.includes('claude.ai') ||
          h.includes('doubao.com') || h.includes('douba.ai') ||
          h.includes('moonshot.cn') || h.includes('kimi.moonshot.cn') || h.includes('kimi.com') ||
          h.includes('x.ai') || h.includes('grok') ||
          h.includes('perplexity.ai') ||
          h.includes('deepseek.com')
        );
      }

      function isVisible(el) {
        if (!el || !(el instanceof Element)) return false;
        const host = (location.hostname || '').toLowerCase();
        const rect = el.getBoundingClientRect();
        // 豆包页面在输入框加载/重排时可能短暂设置 opacity/transform，导致误判不可见
        if (host.includes('doubao.com') || host.includes('douba.ai')) {
          // 放宽尺寸阈值，避免初次渲染/动画阶段被误过滤
          return rect.width > 10 && rect.height > 10 && rect.bottom > 0 && rect.right > 0 &&
                 rect.left < window.innerWidth && rect.top < window.innerHeight;
        }
        // Claude: contenteditable div 可能在初始渲染时尺寸较小，放宽判定
        if (host.includes('claude.ai')) {
          const style = window.getComputedStyle(el);
          if (style.visibility === 'hidden' || style.display === 'none') return false;
          // 放宽尺寸阈值，避免 Vue 动态渲染阶段被误过滤
          return rect.width > 10 && rect.height > 10 && rect.bottom > 0 && rect.right > 0 &&
                 rect.left < window.innerWidth && rect.top < window.innerHeight;
        }
        // Gemini: Angular Material 输入框可能在初始渲染时尺寸较小，放宽判定
        if (host.includes('gemini.google.com') || host.includes('ai.google.com') || host.includes('aistudio.google.com')) {
          const style = window.getComputedStyle(el);
          if (style.visibility === 'hidden' || style.display === 'none') return false;
          // 放宽尺寸阈值，避免 Angular 动态渲染阶段被误过滤
          return rect.width > 10 && rect.height > 10 && rect.bottom > 0 && rect.right > 0 &&
                 rect.left < window.innerWidth && rect.top < window.innerHeight;
        }
        const style = window.getComputedStyle(el);
        if (style.visibility === 'hidden' || style.display === 'none' || Number(style.opacity) === 0) return false;
        return rect.width > 200 && rect.height > 30 && rect.bottom > 0 && rect.right > 0 &&
               rect.left < window.innerWidth && rect.top < window.innerHeight;
      }

      // 深度查询（遍历开放的 Shadow DOM）
      function queryAllDeep(selectors, root = document) {
        const results = new Set();
        function walk(node) {
          if (!node) return;
          try {
            selectors.forEach((sel) => {
              node.querySelectorAll(sel).forEach((e) => results.add(e));
            });
          } catch (_) {}
          // 递归 shadow roots（仅 open）
          if (node.shadowRoot && node.shadowRoot.mode !== 'closed') {
            walk(node.shadowRoot);
          }
          // 遍历子元素
          try {
            node.children && Array.from(node.children).forEach((c) => walk(c));
          } catch (_) {}
        }
        walk(root);
        return Array.from(results);
      }

      function getCandidateInputs() {
        // 常见选择器集合（多站点尽量命中）
        const baseSelectors = [
          'textarea[data-testid="prompt-textarea"]',
          'textarea[placeholder*="Message"]',
          'textarea[placeholder*="message"]',
          'textarea[placeholder*="Send"]',
          'textarea[placeholder]',
          'form textarea',
          'div[contenteditable="true"][role="textbox"]',
          'div[contenteditable="true"]',
          'div[role="textbox"]'
        ];
        // 站点特定补充
        const host = location.hostname.toLowerCase();
        const siteExtra = [];
        if (host.includes('claude.ai')) {
          // Claude 最新版本（2025）：使用 contenteditable div，位于 input-composer 容器内
          siteExtra.push(
            'div[data-testid="input-composer"] div[contenteditable="true"]',
            'div[data-testid="input-composer"] div.relative.flex.flex-col div[contenteditable="true"]',
            'div[contenteditable="true"].ProseMirror',
            'div[contenteditable="true"]',
            'textarea'
          );
        } else if (host.includes('moonshot.cn') || host.includes('kimi.moonshot.cn') || host.includes('kimi.com')) {
          siteExtra.push('div[contenteditable="true"][data-lexical-editor]', 'div[contenteditable="true"]');
        } else if (host.includes('x.ai') || host.includes('grok')) {
          // Grok: Tiptap/ProseMirror 编辑器
          siteExtra.push(
            'div.tiptap.ProseMirror',
            'div[contenteditable="true"].tiptap',
            'div[contenteditable="true"].ProseMirror',
            'div[contenteditable="true"][data-slate-editor]',
            'div[contenteditable="true"]',
            'textarea'
          );
        } else if (host.includes('doubao.com') || host.includes('douba.ai')) {
          // 豆包：输入框常为 contenteditable，可带 role/placeholder 等属性，且可能在容器内
          siteExtra.push(
            'div[role="textbox"][contenteditable="true"]',
            'div[contenteditable="plaintext-only"]',
            'div[contenteditable][role="textbox"]',
            'div[contenteditable="true"][data-placeholder]',
            '.tools-input div[contenteditable="true"]',
            '.editor div[contenteditable="true"]',
            'div[contenteditable="true"]',
            'textarea[placeholder]',
            'textarea[aria-label]',
            'textarea'
          );
        } else if (host.includes('gemini.google.com') || host.includes('ai.google.com') || host.includes('aistudio.google.com')) {
          // Gemini: Angular Material 输入框，可能是 textarea 或 contenteditable div
          siteExtra.push(
            'textarea[aria-label]',
            'textarea[placeholder]',
            'textarea',
            'div[role="textbox"][contenteditable="true"]',
            'div[contenteditable="true"][aria-label]',
            'div[contenteditable="true"]',
            'div[role="textbox"]',
            'div[contenteditable="plaintext-only"]',
            'div[contenteditable][role="textbox"]'
          );
        } else if (host.includes('perplexity.ai')) {
          // Perplexity: 通常使用 textarea 或 contenteditable div
          siteExtra.push(
            'textarea[placeholder]',
            'textarea[aria-label]',
            'textarea',
            'div[contenteditable="true"][role="textbox"]',
            'div[contenteditable="true"]',
            'div[role="textbox"]'
          );
        }
        const selectors = [...new Set([...baseSelectors, ...siteExtra])];
        const nodes = new Set(queryAllDeep(selectors, document));
        // 豆包：调试可见性与命中情况（便于排障）
        try {
          if (host.includes('doubao.com') || host.includes('douba.ai')) {
            const allBeforeFilter = Array.from(nodes);
            const extraAll = queryAllDeep(['textarea', 'div[contenteditable="true"]'], document);
            extraAll.forEach(n => nodes.add(n));
            const afterUnion = Array.from(nodes);
            // 仅在豆包站点输出一次概要日志（采样：每 3s 内最多一次，可由上层节流）
            console.log(`[LC][Doubao] 候选输入框(初筛): ${allBeforeFilter.length}，并集后: ${afterUnion.length}`);
          }
        } catch (_) {}
        // Gemini：调试可见性与命中情况（便于排障）
        try {
          if (host.includes('gemini.google.com') || host.includes('ai.google.com') || host.includes('aistudio.google.com')) {
            const allBeforeFilter = Array.from(nodes);
            const extraAll = queryAllDeep(['textarea', 'div[contenteditable="true"]', 'div[role="textbox"]'], document);
            extraAll.forEach(n => nodes.add(n));
            const afterUnion = Array.from(nodes);
            const visibleCount = Array.from(nodes).filter(isVisible).length;
            // 仅在 Gemini 站点输出一次概要日志（采样：每 3s 内最多一次，可由上层节流）
            console.log(`[LC][Gemini] 候选输入框(初筛): ${allBeforeFilter.length}，并集后: ${afterUnion.length}，可见: ${visibleCount}`);
          }
        } catch (_) {}
        // Claude：调试可见性与命中情况（便于排障）
        try {
          if (host.includes('claude.ai')) {
            const allBeforeFilter = Array.from(nodes);
            const extraAll = queryAllDeep(['div[data-testid="input-composer"] div[contenteditable="true"]', 'div[contenteditable="true"]', 'textarea'], document);
            extraAll.forEach(n => nodes.add(n));
            const afterUnion = Array.from(nodes);
            const visibleCount = Array.from(nodes).filter(isVisible).length;
            // 仅在 Claude 站点输出一次概要日志（采样：每 3s 内最多一次，可由上层节流）
            console.log(`[LC][Claude] 候选输入框(初筛): ${allBeforeFilter.length}，并集后: ${afterUnion.length}，可见: ${visibleCount}`);
          }
        } catch (_) {}
        // 兜底：页面上最后一个 textarea/可编辑框
        queryAllDeep(['textarea', 'div[contenteditable="true"]'], document).forEach(n => nodes.add(n));
        return Array.from(nodes).filter(isVisible);
      }

      function pickChatInput() {
        const list = getCandidateInputs();
        if (!list.length) return null;
        // 偏好靠近页面底部的较大输入框
        list.sort((a, b) => {
          const ra = a.getBoundingClientRect();
          const rb = b.getBoundingClientRect();
          const scoreA = ra.top + ra.height * 0.5 + (window.innerHeight - ra.bottom); // 越靠下、越高分
          const scoreB = rb.top + rb.height * 0.5 + (window.innerHeight - rb.bottom);
          return scoreB - scoreA;
        });
        return list[0];
      }

      function ensureBtn() {
        if (btn) return btn;
        btn = document.createElement('button');
        btn.id = 'lc-optimize-btn';
        btn.type = 'button';
        btn.style.cssText = `
          position: fixed;
          width: 34px;
          height: 34px;
          border-radius: 50%;
          border: none;
          padding: 0;
          margin: 0;
          background: #ffffff url('${logoUrl}') center/70% no-repeat;
          box-shadow: 0 6px 16px rgba(0,0,0,.2);
          z-index: 2147483646;
          cursor: pointer;
          transition: transform .15s ease, opacity .15s ease;
          opacity: .95;
        `;
        btn.title = '优化提示词（LifeContext）';
        // 防止站点委托的发送事件（click/mouseup/pointerup 等）被触发
        try {
          const swallow = (evt) => {
            try { evt.preventDefault && evt.preventDefault(); } catch(_) {}
            try { evt.stopPropagation && evt.stopPropagation(); } catch(_) {}
            try { evt.stopImmediatePropagation && evt.stopImmediatePropagation(); } catch(_) {}
          };
          ['pointerdown','pointerup','mousedown','mouseup','click','touchstart','touchend'].forEach((t) => {
            btn.addEventListener(t, swallow, { capture: true });
          });
        } catch(_) {}
        btn.addEventListener('mouseenter', () => { btn.style.transform = 'scale(1.05)'; });
        btn.addEventListener('mouseleave', () => { btn.style.transform = 'scale(1)'; });
        btn.addEventListener('click', onOptimizeClick);
        document.body.appendChild(btn);
        return btn;
      }

      function setBtnLoading(on) {
        if (!btn) return;
        // 确保动画已定义
        ensureSpinAnimation();
        if (on) {
          btn.disabled = true;
          btn.style.opacity = '1';
          btn.style.cursor = 'not-allowed';
          // 添加淡蓝色渐变背景和边框，使加载状态更明显
          btn.style.background = 'linear-gradient(135deg, rgba(14, 165, 233, 0.15), rgba(59, 130, 246, 0.2))';
          btn.style.border = '1px solid rgba(14, 165, 233, 0.3)';
          btn.style.boxShadow = '0 0 12px rgba(14, 165, 233, 0.3), 0 0 20px rgba(14, 165, 233, 0.15)';
          btn.innerHTML = `
            <span style="display:inline-block;width:100%;height:100%;border-radius:50%;
                         background: inherit;
                         position:relative;">
              <span style="position:absolute;left:50%;top:50%;width:24px;height:24px;margin:-12px 0 0 -12px;
                           border:4px solid rgba(14, 165, 233, 0.25);
                           border-top-color:#0ea5e9;
                           border-right-color:#3b82f6;
                           border-radius:50%;
                           animation:lc-spin .7s linear infinite;
                           box-shadow: 0 0 10px rgba(14, 165, 233, 0.5), 0 0 15px rgba(14, 165, 233, 0.3);
                           box-sizing:border-box;"></span>
            </span>`;
        } else {
          btn.disabled = false;
          btn.style.opacity = '.95';
          btn.style.cursor = 'pointer';
          // 恢复图标背景和样式
          const logoUrl = (typeof chrome !== 'undefined' && chrome.runtime && typeof chrome.runtime.getURL === 'function')
            ? chrome.runtime.getURL('logo.png')
            : '';
          if (logoUrl) {
            btn.style.background = `#ffffff url('${logoUrl}') center/70% no-repeat`;
          } else {
            btn.style.background = '#ffffff';
          }
          btn.style.border = '';
          btn.style.boxShadow = '';
          btn.innerHTML = '';
        }
      }
      
      // 确保 CSS 动画已定义
      function ensureSpinAnimation() {
        if (document.getElementById('lc-spin-keyframes')) return;
        const style = document.createElement('style');
        style.id = 'lc-spin-keyframes';
        style.textContent = `
          @keyframes lc-spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          @keyframes lc-pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.85; transform: scale(1.05); }
          }
          @keyframes lc-glow {
            0%, 100% { box-shadow: 0 0 8px rgba(14, 165, 233, 0.4), 0 0 12px rgba(14, 165, 233, 0.2); }
            50% { box-shadow: 0 0 12px rgba(14, 165, 233, 0.6), 0 0 18px rgba(14, 165, 233, 0.3); }
          }
          .lc-btn-hidden > *:not(.lc-spinner) {
            opacity: 0 !important;
            visibility: hidden !important;
          }
          .lc-loading-btn {
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.1), rgba(59, 130, 246, 0.15)) !important;
            border: 1px solid rgba(14, 165, 233, 0.3) !important;
            animation: lc-pulse 2s ease-in-out infinite !important;
          }
        `;
        document.head.appendChild(style);
      }
      
      // 针对任意按钮元素设置/取消"加载中"状态（带加载动画）
      function setBtnLoadingOn(el, on) {
        try {
          if (!el) return;
          
          // 确保动画已定义
          ensureSpinAnimation();
          
          // 检测是否为 Perplexity 按钮（通过检查内部结构）
          const hostLower = (location.hostname || '').toLowerCase();
          const isPerplexity = hostLower.includes('perplexity.ai');
          const isPerplexityBtn = isPerplexity && (
            el.querySelector('.flex.items-center.min-w-0.gap-two') ||
            el.querySelector('.flex.shrink-0.items-center.justify-center.size-4') ||
            el.getAttribute('aria-label') === '优化提示词'
          );
          
          if (on) {
            // 保存原始内容（如果还没有保存）
            if (!buttonOriginalContent.has(el)) {
              const computedStyle = window.getComputedStyle(el);
              const original = {
                innerHTML: el.innerHTML,
                className: el.className,
                background: el.style.background || computedStyle.background,
                backgroundImage: el.style.backgroundImage || computedStyle.backgroundImage,
                opacity: el.style.opacity || computedStyle.opacity,
                cursor: el.style.cursor || computedStyle.cursor,
                position: el.style.position || computedStyle.position,
                // 保存所有子元素（特别是图片元素）
                children: Array.from(el.children).map(child => ({
                  tagName: child.tagName,
                  src: child.src || child.getAttribute('src') || '',
                  outerHTML: child.outerHTML,
                  className: child.className
                }))
              };
              buttonOriginalContent.set(el, original);
            }
            
            // 设置加载状态
            el.disabled = true;
            el.style.opacity = '1';
            el.style.cursor = 'not-allowed';
            
            // 添加加载状态类，用于应用统一的加载样式
            el.classList.add('lc-loading-btn');
            
            // 检查是否为圆形按钮
            const computedStyle = window.getComputedStyle(el);
            const borderRadius = el.style.borderRadius || computedStyle.borderRadius;
            const isCircular = borderRadius === '50%' || borderRadius.includes('50%');
            
            // 显示加载动画
            if (isPerplexityBtn) {
              // Perplexity 按钮：使用绝对定位的 spinner，放在按钮最外层，避免被容器裁剪
              // 检查是否已经有 spinner
              let spinner = el.querySelector('.lc-spinner');
              if (!spinner) {
                // 创建 spinner 元素
                spinner = document.createElement('span');
                spinner.className = 'lc-spinner';
                // 设置 spinner 样式：绝对定位在按钮中心，使用蓝色主题
                spinner.style.cssText = `
                  position: absolute;
                  left: 50%;
                  top: 50%;
                  width: 24px;
                  height: 24px;
                  margin-left: -12px;
                  margin-top: -12px;
                  border: 4px solid rgba(14, 165, 233, 0.2);
                  border-top-color: #0ea5e9;
                  border-right-color: #3b82f6;
                  border-radius: 50%;
                  animation: lc-spin .7s linear infinite;
                  z-index: 99999;
                  pointer-events: none;
                  box-sizing: border-box;
                  box-shadow: 0 0 10px rgba(14, 165, 233, 0.4), 0 0 15px rgba(14, 165, 233, 0.2);
                `;
                // 确保按钮有相对定位
                const currentPosition = window.getComputedStyle(el).position;
                if (currentPosition === 'static') {
                  el.style.position = 'relative';
                }
                // 将 spinner 直接插入到按钮最外层（不插入到内部容器）
                el.appendChild(spinner);
              } else {
                // 如果 spinner 已存在，确保它可见
                spinner.style.display = 'block';
                spinner.style.opacity = '1';
                spinner.style.visibility = 'visible';
              }
              // 使用 class 隐藏原内容，而不是逐个修改子元素的 style
              el.classList.add('lc-btn-hidden');
            } else if (isCircular) {
              // 圆形按钮：隐藏图标，显示蓝色转圈动画，添加淡蓝色背景
              // 移除背景图片，添加淡蓝色渐变背景
              el.style.background = 'linear-gradient(135deg, rgba(14, 165, 233, 0.15), rgba(59, 130, 246, 0.2))';
              el.style.backgroundImage = 'none';
              el.style.border = '1px solid rgba(14, 165, 233, 0.3)';
              el.style.boxShadow = '0 0 12px rgba(14, 165, 233, 0.3), 0 0 20px rgba(14, 165, 233, 0.15)';
              el.innerHTML = `
                <span style="display:inline-block;width:100%;height:100%;border-radius:50%;
                             background: inherit;
                             position:relative;">
                  <span style="position:absolute;left:50%;top:50%;width:24px;height:24px;margin:-12px 0 0 -12px;
                               border:4px solid rgba(14, 165, 233, 0.25);
                               border-top-color:#0ea5e9;
                               border-right-color:#3b82f6;
                               border-radius:50%;
                               animation:lc-spin .7s linear infinite;
                               box-shadow: 0 0 10px rgba(14, 165, 233, 0.5), 0 0 15px rgba(14, 165, 233, 0.3);
                               box-sizing:border-box;"></span>
                </span>`;
            } else {
              // 非圆形按钮：显示明显的蓝色旋转动画，带渐变背景和发光效果
              el.innerHTML = `
                <span style="display:inline-flex;align-items:center;justify-content:center;width:100%;height:100%;
                             background: linear-gradient(135deg, rgba(14, 165, 233, 0.15), rgba(59, 130, 246, 0.2));
                             border-radius: 6px;
                             position:relative;
                             animation:lc-pulse 2s ease-in-out infinite;">
                  <span style="width:28px;height:28px;
                               border:4px solid rgba(14, 165, 233, 0.3);
                               border-top-color:#0ea5e9;
                               border-right-color:#3b82f6;
                               border-bottom-color:#0284c7;
                               border-radius:50%;
                               animation:lc-spin .7s linear infinite;
                               box-shadow: 0 0 12px rgba(14, 165, 233, 0.6), 0 0 20px rgba(14, 165, 233, 0.3);
                               box-sizing:border-box;"></span>
                </span>`;
            }
          } else {
            // 移除加载状态类
            el.classList.remove('lc-loading-btn');
            
            // 恢复原始内容
            if (isPerplexityBtn) {
              // Perplexity 按钮：移除 spinner，移除隐藏 class，恢复原内容可见性
              const spinner = el.querySelector('.lc-spinner');
              if (spinner) {
                spinner.remove();
              }
              // 移除隐藏 class，CSS 规则会自动恢复原内容的可见性
              el.classList.remove('lc-btn-hidden');
              // 恢复 position（如果之前设置了）
              const original = buttonOriginalContent.get(el);
              if (original && original.position) {
                el.style.position = original.position;
              } else {
                // 如果没有保存 position，尝试恢复为默认值
                const computedPosition = window.getComputedStyle(el).position;
                if (computedPosition === 'relative' && !el.style.position) {
                  el.style.position = '';
                }
              }
              // 恢复边框和阴影
              el.style.border = '';
              el.style.boxShadow = '';
            } else {
              // 其他按钮：使用原有的恢复逻辑
              const original = buttonOriginalContent.get(el);
              if (original) {
                // 恢复 innerHTML（包括所有子元素）
                el.innerHTML = original.innerHTML;
                
                // 恢复背景样式
                if (original.background && original.background !== 'none' && original.background !== 'rgba(0, 0, 0, 0)') {
                  el.style.background = original.background;
                } else if (original.backgroundImage && original.backgroundImage !== 'none') {
                  el.style.backgroundImage = original.backgroundImage;
                } else {
                  el.style.background = '';
                  el.style.backgroundImage = '';
                }
                
                // 恢复边框和阴影
                el.style.border = '';
                el.style.boxShadow = '';
                
                // 恢复 opacity 和 cursor
                el.style.opacity = original.opacity || '';
                el.style.cursor = original.cursor || '';
                
                // 如果原始内容中有图片，确保图片正确加载和显示
                if (original.children && original.children.length > 0) {
                  original.children.forEach(childInfo => {
                    if (childInfo.tagName === 'IMG' && childInfo.src) {
                      const img = el.querySelector('img');
                      if (img) {
                        // 确保图片 src 正确
                        if (img.src !== childInfo.src) {
                          img.src = childInfo.src;
                        }
                        // 确保图片样式正确
                        const originalImg = childInfo.outerHTML.match(/style="([^"]*)"/);
                        if (originalImg && originalImg[1]) {
                          img.style.cssText = originalImg[1];
                        }
                      } else {
                        // 如果图片不存在，尝试重新创建
                        const newImg = document.createElement('img');
                        newImg.src = childInfo.src;
                        if (childInfo.outerHTML.includes('style=')) {
                          const styleMatch = childInfo.outerHTML.match(/style="([^"]*)"/);
                          if (styleMatch && styleMatch[1]) {
                            newImg.style.cssText = styleMatch[1];
                          }
                        }
                        el.appendChild(newImg);
                      }
                    }
                  });
                }
                
                buttonOriginalContent.delete(el);
              } else {
                // 如果没有保存的原始内容，尝试恢复为默认样式
                const logoUrl = (typeof chrome !== 'undefined' && chrome.runtime && typeof chrome.runtime.getURL === 'function')
                  ? chrome.runtime.getURL('logo.png')
                  : '';
                if (logoUrl) {
                  el.innerHTML = '';
                  el.style.background = `#ffffff url('${logoUrl}') center/70% no-repeat`;
                } else {
                  el.innerHTML = '';
                }
                el.style.opacity = '';
                el.style.cursor = '';
              }
            }
            
            el.disabled = false;
          }
        } catch (err) {
          console.error('[LC] Error in setBtnLoadingOn:', err);
          // 出错时至少恢复基本状态
          try {
            if (!on) {
              el.disabled = false;
              el.style.opacity = '';
              el.style.cursor = '';
            }
          } catch (_) {}
        }
      }

      // 读取元素的易读标签（辅助识别“听写/语音/麦克风”按钮）
      function getElementLabel(el) {
        try {
          const tryAttrs = ['aria-label', 'title', 'data-tooltip', 'alt'];
          for (const a of tryAttrs) {
            const v = (el.getAttribute && el.getAttribute(a)) || '';
            if (v && v.trim()) return v.trim().toLowerCase();
          }
          const txt = (el.textContent || '').trim();
          return txt.length <= 12 ? txt.toLowerCase() : '';
        } catch (_) { return ''; }
      }

      // 在输入框容器内寻找“听写/语音”按钮的矩形
      function findDictationButtonRect(targetEl, inputRect) {
        try {
          const container =
            targetEl.closest('form,[role="form"],[data-testid*="composer"],[class*="composer"],[class*="input"],[class*="editor"]')
            || targetEl.parentElement
            || document;
          const selectors = ['button', '[role="button"]', 'input[type="submit"]'];
          const nodes = new Set(queryAllDeep(selectors, container));
          const micKeywords = ['听写', '语音', '麦克风', 'voice', 'mic', 'microphone', 'dictation', 'speak'];
          let bestRect = null;
          let bestScore = -1e9;
          nodes.forEach((el) => {
            if (!isVisible(el)) return;
            const r = el.getBoundingClientRect();
            // 与输入框右下区域相交
            const verticalOverlap = Math.max(0, Math.min(r.bottom, inputRect.bottom + 40) - Math.max(r.top, inputRect.bottom - 72));
            if (verticalOverlap <= 0) return;
            if (r.left < inputRect.left || r.right > inputRect.right + 220) return;
            const label = getElementLabel(el);
            const hasMicHint = micKeywords.some(k => label.includes(k));
            // 综合评分：关键词优先、越靠近右下角分越高、越小越像圆形按钮
            const diffBottom = Math.abs(inputRect.bottom - r.bottom);
            const diffRight = Math.abs(inputRect.right - r.right);
            const approxSize = Math.min(r.width, r.height);
            let score = 0;
            if (hasMicHint) score += 400;
            score += Math.max(0, 140 - diffBottom) + Math.max(0, 160 - diffRight);
            score += Math.max(0, 60 - Math.abs(approxSize - 32));
            if (score > bestScore) { bestScore = score; bestRect = r; }
          });
          return bestRect;
        } catch (_) { return null; }
      }

      function positionBtn() {
        if (!btn || !targetEl || !isVisible(targetEl)) {
          // 宽限：若刚刚还可见，则保留上次位置一段时间，避免闪烁
          const now = Date.now();
          if (btn && lastTargetRect && now - lastVisibleTimestamp < 1500) {
            btn.style.display = 'block';
            btn.style.top = `${Math.max(0, Math.min(lastTargetRect.top, window.innerHeight - 2))}px`;
            btn.style.left = `${Math.max(0, Math.min(lastTargetRect.left, window.innerWidth - 2))}px`;
          } else {
            if (btn) btn.style.display = 'none';
          }
          return;
        }
        let rect = targetEl.getBoundingClientRect();
        lastTargetRect = rect;
        lastVisibleTimestamp = Date.now();
        const size = parseInt((btn.style.width || '34px'), 10) || 34;
        // 读取 padding-right 作为基线，避免覆盖文字
        let pr = 0;
        try {
          const cs = window.getComputedStyle(targetEl);
          pr = parseFloat(cs.paddingRight || '0') || 0;
        } catch (_) {}
        // 站点与形态（单行/多行）专用偏移
        function getPlacement(host, isMultiline) {
          const h = (host || location.hostname || '').toLowerCase();
          let base = { right: Math.max(52, pr + 12), bottom: 12 };
          if (h.includes('gemini.google.com') || h.includes('ai.google.com') || h.includes('aistudio.google.com')) {
            base = { right: Math.max(72, pr + 10), bottom: 14 };
          } else if (h.includes('claude.ai')) {
            base = { right: Math.max(64, pr + 10), bottom: 12 };
          } else if (h.includes('moonshot.cn') || h.includes('kimi.moonshot.cn')) {
            base = { right: Math.max(64, pr + 10), bottom: 14 };
          } else if (h.includes('x.ai') || h.includes('grok')) {
            base = { right: Math.max(60, pr + 10), bottom: 12 };
          } else if (h.includes('doubao.com') || h.includes('douba.ai')) {
            base = { right: Math.max(60, pr + 10), bottom: 12 };
          }
          if (!isMultiline) base.right += 2;
          return base;
        }
        const isMultiline = rect.height > 64;
        const place = getPlacement(location.hostname, isMultiline);

        let finalTop;
        let finalLeft;

        // 统一策略：多行与单行一致（居中、上移 10px、右移 1.5×）
        const top = Math.round(rect.top + rect.height / 2 - size / 2);
        const left = Math.round(rect.right - Math.max(place.right, pr + 12) - size);
        finalTop = top - 10;
        finalLeft = left + Math.round(size * 1.5);

        // Grok/x.ai 定制偏移：
        // - 单行：向下 10px
        // - 多行：向上 5px，且额外再向右 1.5 × 按钮宽度
        const hostLower = (location.hostname || '').toLowerCase();
        if (hostLower.includes('x.ai') || hostLower.includes('grok')) {
          if (isMultiline) {
            finalLeft += Math.round(size * 1.5);
            finalTop -= 10;
          } else {
            finalTop += 10;
          }
        }
        // Kimi Chat 定制偏移：垂直以“距输入框底部 5px”为准，水平左移 6× 按钮宽度
        if (hostLower.includes('moonshot.cn') || hostLower.includes('kimi.moonshot.cn') || hostLower.includes('kimi.com')) {
          finalTop = Math.round(rect.bottom - size - 10);
          // 追加：在当前基础上再向下 1.5 × 按钮高度
          finalTop += Math.round(size * 1.5);
          finalLeft -= Math.round(size * 6);
          // 再向右移动 1 × 按钮宽度
          finalLeft += Math.round(size * 1);
        }

        const clampedLeft = Math.max(0, Math.min(finalLeft, window.innerWidth - size - 2));
        const clampedTop = Math.max(0, Math.min(finalTop, window.innerHeight - size - 2));
        btn.style.display = 'block';
        btn.style.top = `${clampedTop}px`;
        btn.style.left = `${clampedLeft}px`;
      }

      function readTextFrom(el) {
        if (!el) return '';
        if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') return el.value || '';
        if (el.getAttribute('contenteditable') === 'true') return el.innerText || el.textContent || '';
        return '';
      }

      function writeTextTo(el, text) {
        if (!el) return;
        const hostLower = (location.hostname || '').toLowerCase();
        const isChrome = /Chrome/.test(navigator.userAgent) && !/Edge|Edg/.test(navigator.userAgent);
        const isKimi = hostLower.includes('moonshot.cn') || hostLower.includes('kimi.moonshot.cn') || hostLower.includes('kimi.com');
        const isPerplexity = hostLower.includes('perplexity.ai');

        // 若传入的是容器，尝试寻找内部可编辑节点
        let target = el;
        try {
          if (!(target instanceof Element)) return;
          const isCE = target.getAttribute && (target.getAttribute('contenteditable') === 'true' || target.isContentEditable);
          if (!isCE && target.tagName !== 'TEXTAREA' && target.tagName !== 'INPUT') {
            const innerCE = target.querySelector && target.querySelector('div[contenteditable="true"],[contenteditable="plaintext-only"],[contenteditable][role="textbox"]');
            if (innerCE) target = innerCE;
          }
        } catch (_) {}

        // React/受控组件：通过原生 setter 设置值，确保 onInput/onChange 被正确感知
        function setNativeValue(node, value) {
          try {
            const desc = Object.getOwnPropertyDescriptor(node, 'value');
            const proto = Object.getPrototypeOf(node);
            const protoDesc = Object.getOwnPropertyDescriptor(proto, 'value');
            if (desc && desc.set) {
              desc.set.call(node, value);
            } else if (protoDesc && protoDesc.set) {
              protoDesc.set.call(node, value);
            } else {
              node.value = value;
            }
          } catch (_) {
            try { node.value = value; } catch(__) {}
          }
        }

        // Perplexity 的特殊处理：对所有浏览器都使用原生 setter + 模拟真实用户输入
        if (isPerplexity && target && (target.tagName === 'TEXTAREA' || target.tagName === 'INPUT')) {
          try {
            // 1. 聚焦元素
            target.focus && target.focus();
            
            // 2. 选中所有现有内容（模拟用户 Ctrl+A）
            if (typeof target.selectionStart === 'number' && typeof target.selectionEnd === 'number') {
              target.selectionStart = 0;
              target.selectionEnd = (target.value || '').length;
            }
            
            // 3. 使用原生 setter 设置值
            setNativeValue(target, text);
            
            // 4. 触发 beforeinput 事件（模拟真实输入流程）
            try {
              target.dispatchEvent(new InputEvent('beforeinput', { 
                bubbles: true, 
                cancelable: true,
                inputType: 'insertReplacementText',
                data: text,
                dataTransfer: null
              }));
            } catch (_) {}
            
            // 5. 触发 input 事件（使用 insertReplacementText 类型，表示替换操作）
            try {
              target.dispatchEvent(new InputEvent('input', { 
                bubbles: true, 
                cancelable: false,
                inputType: 'insertReplacementText',
                data: text,
                dataTransfer: null
              }));
            } catch (_) {
              try { 
                target.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertFromPaste', data: text }));
              } catch(__) {
                try { target.dispatchEvent(new Event('input', { bubbles: true })); } catch(___) {}
              }
            }
            
            // 6. 触发 change 事件
            try { target.dispatchEvent(new Event('change', { bubbles: true })); } catch(_) {}
            
            // 7. 再次触发 input 事件确保 React 受控组件更新（某些情况下需要多次触发）
            setTimeout(() => {
              try {
                target.dispatchEvent(new InputEvent('input', { 
                  bubbles: true, 
                  cancelable: false,
                  inputType: 'insertReplacementText',
                  data: text,
                  dataTransfer: null
                }));
              } catch (_) {}
            }, 0);
            
            // 8. 光标移至末尾
            if (typeof target.selectionStart === 'number') {
              target.selectionStart = target.selectionEnd = (target.value || '').length;
            }
            
            return;
          } catch (_) {
            // 如果出错，回退到标准处理
          }
        }
        
        // Perplexity contenteditable 的特殊处理
        if (isPerplexity && target && (target.getAttribute && (target.getAttribute('contenteditable') === 'true' || target.isContentEditable))) {
          try {
            // 1. 聚焦元素
            target.focus && target.focus();
            
            // 2. 获取当前选择范围
            const sel = window.getSelection && window.getSelection();
            if (!sel) {
              throw new Error('No Selection API');
            }
            
            // 3. 选中所有现有内容（模拟用户 Ctrl+A）
            const range = document.createRange();
            range.selectNodeContents(target);
            sel.removeAllRanges();
            sel.addRange(range);
            
            // 4. 删除选中的内容（模拟用户删除操作）
            try {
              range.deleteContents();
            } catch (_) {
              // 如果 deleteContents 失败，尝试直接清空
              target.textContent = '';
              // 重新创建 range
              const newRange = document.createRange();
              newRange.selectNodeContents(target);
              newRange.collapse(false);
              sel.removeAllRanges();
              sel.addRange(newRange);
            }
            
            // 5. 创建文本节点并插入（模拟用户输入）
            const textNode = document.createTextNode(text);
            let insertSuccess = false;
            try {
              // 尝试获取当前 range
              let currentRange;
              if (sel.rangeCount > 0) {
                currentRange = sel.getRangeAt(0);
              } else {
                // 如果没有 range，创建一个新的
                currentRange = document.createRange();
                currentRange.selectNodeContents(target);
                currentRange.collapse(false);
              }
              currentRange.insertNode(textNode);
              insertSuccess = true;
            } catch (_) {
              // 如果插入失败，直接设置文本内容
              target.textContent = text;
              // 重新创建 range 用于光标定位
              const newRange = document.createRange();
              newRange.selectNodeContents(target);
              newRange.collapse(false);
              sel.removeAllRanges();
              sel.addRange(newRange);
            }
            
            // 6. 将光标移至文本末尾（仅在成功插入文本节点时执行）
            if (insertSuccess) {
              try {
                const finalRange = document.createRange();
                finalRange.setStartAfter(textNode);
                finalRange.collapse(true);
                sel.removeAllRanges();
                sel.addRange(finalRange);
              } catch (_) {
                // 如果设置光标失败，使用简单的方式
                const simpleRange = document.createRange();
                simpleRange.selectNodeContents(target);
                simpleRange.collapse(false);
                sel.removeAllRanges();
                sel.addRange(simpleRange);
              }
            }
            
            // 7. 触发 beforeinput 事件（模拟真实输入流程）
            try {
              target.dispatchEvent(new InputEvent('beforeinput', { 
                bubbles: true, 
                cancelable: true,
                inputType: 'insertReplacementText',
                data: text,
                dataTransfer: null
              }));
            } catch (_) {}
            
            // 8. 触发 input 事件（使用 insertReplacementText 类型，表示替换操作）
            try {
              target.dispatchEvent(new InputEvent('input', { 
                bubbles: true, 
                cancelable: false,
                inputType: 'insertReplacementText',
                data: text,
                dataTransfer: null
              }));
            } catch (_) {
              try { 
                target.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
              } catch(__) {
                try { target.dispatchEvent(new Event('input', { bubbles: true })); } catch(___) {}
              }
            }
            
            // 9. 触发 change 事件
            try { target.dispatchEvent(new Event('change', { bubbles: true })); } catch(_) {}
            
            // 10. 再次触发 input 事件确保 React 受控组件更新
            setTimeout(() => {
              try {
                target.dispatchEvent(new InputEvent('input', { 
                  bubbles: true, 
                  cancelable: false,
                  inputType: 'insertReplacementText',
                  data: text,
                  dataTransfer: null
                }));
              } catch (_) {}
            }, 0);
            
            return;
          } catch (_) {
            // 如果出错，回退到通用处理
          }
        }

        // 针对不同类型分别处理
        if (target && (target.tagName === 'TEXTAREA' || target.tagName === 'INPUT')) {
          try {
            target.focus && target.focus();
          } catch (_) {}
          setNativeValue(target, text);
          try {
            // 更像"粘贴"的输入类型，提升兼容性
            target.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertFromPaste', data: text }));
          } catch (_) {
            try { target.dispatchEvent(new Event('input', { bubbles: true })); } catch(__) {}
          }
          try { target.dispatchEvent(new Event('change', { bubbles: true })); } catch(_) {}
          try {
            // 光标移至末尾
            if (typeof target.selectionStart === 'number') {
              target.selectionStart = target.selectionEnd = (target.value || '').length;
            }
          } catch (_) {}
          return;
        }

        // contenteditable（Kimi: Lexical；豆包：部分场景下使用 CE 或 textarea；Grok: Tiptap/ProseMirror）
        if (target && (target.getAttribute && (target.getAttribute('contenteditable') === 'true' || target.isContentEditable))) {
          // Claude: 使用安全方式替换内容，避免触发自动发送
          const isClaude = hostLower.includes('claude.ai');
          if (isClaude) {
            try {
              // 方案 A + B + C：暂停事件监听、失焦、安全替换、恢复焦点
              const prevActive = document.activeElement;
              
              // 1. 失焦，让 Claude 不会自动发送
              target.blur && target.blur();
              
              // 2. 暂停事件监听（保存原始监听器）
              const originalInput = target.oninput;
              const originalChange = target.onchange;
              target.oninput = null;
              target.onchange = null;
              
              // 3. 启用全局事件拦截
              suppressInputEvents = true;
              
              // 4. 安全替换内容（不触发任何事件）
              // 使用 innerText 而不是 textContent，确保 Vue 能正确更新
              target.innerText = text;
              
              // 5. 如果 contenteditable 有 value 属性，也更新它（某些 Vue 实现会用到）
              try {
                const descriptor = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(target), 'value');
                if (descriptor && descriptor.set) {
                  descriptor.set.call(target, text);
                }
              } catch (_) {}
              
              // 6. 光标移至末尾（不触发事件）
              const sel = window.getSelection && window.getSelection();
              if (sel) {
                const range = document.createRange();
                range.selectNodeContents(target);
                range.collapse(false);
                sel.removeAllRanges();
                sel.addRange(range);
              }
              
              // 7. 恢复事件监听
              target.oninput = originalInput;
              target.onchange = originalChange;
              
              // 8. 禁用全局事件拦截
              suppressInputEvents = false;
              
              // 9. 恢复焦点（如果需要）
              if (prevActive && prevActive !== target) {
                setTimeout(() => {
                  try {
                    prevActive.focus && prevActive.focus();
                  } catch (_) {}
                }, 0);
              }
              
              return;
            } catch (_) {
              // 如果出错，确保恢复状态
              suppressInputEvents = false;
            }
          }

          // Grok (Tiptap/ProseMirror): 使用 innerHTML 方式，确保编辑器正确更新
          const isGrok = hostLower.includes('x.ai') || hostLower.includes('grok');
          if (isGrok && target.classList && (target.classList.contains('tiptap') || target.classList.contains('ProseMirror'))) {
            try {
              // Tiptap/ProseMirror 需要保持 <p> 标签结构
              target.innerHTML = `<p>${text}</p>`;
              target.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertFromPaste', data: text }));
              target.dispatchEvent(new Event('change', { bubbles: true }));
              // 光标移至末尾
              const sel = window.getSelection && window.getSelection();
              if (sel) {
                const range = document.createRange();
                range.selectNodeContents(target);
                range.collapse(false);
                sel.removeAllRanges();
                sel.addRange(range);
              }
              return;
            } catch (_) {}
          }

          // Chrome 中 Kimi (contenteditable + Lexical) 的特殊处理：模拟真实用户输入
          if (isChrome && isKimi) {
            try {
              // 1. 聚焦元素
              target.focus && target.focus();
              
              // 2. 获取当前选择范围
              const sel = window.getSelection && window.getSelection();
              if (!sel) {
                // 如果没有 Selection API，回退到通用处理
                throw new Error('No Selection API');
              }
              
              // 3. 选中所有现有内容（模拟用户 Ctrl+A）
              const range = document.createRange();
              range.selectNodeContents(target);
              sel.removeAllRanges();
              sel.addRange(range);
              
              // 4. 删除选中的内容（模拟用户删除操作）
              try {
                range.deleteContents();
                // 删除后，range 会自动收缩到删除点，保持选中状态
              } catch (_) {
                // 如果 deleteContents 失败，尝试直接清空
                target.textContent = '';
                // 重新创建 range
                const newRange = document.createRange();
                newRange.selectNodeContents(target);
                newRange.collapse(false);
                sel.removeAllRanges();
                sel.addRange(newRange);
              }
              
              // 5. 创建文本节点并插入（模拟用户输入）
              const textNode = document.createTextNode(text);
              let insertSuccess = false;
              try {
                // 尝试获取当前 range
                let currentRange;
                if (sel.rangeCount > 0) {
                  currentRange = sel.getRangeAt(0);
                } else {
                  // 如果没有 range，创建一个新的
                  currentRange = document.createRange();
                  currentRange.selectNodeContents(target);
                  currentRange.collapse(false);
                }
                currentRange.insertNode(textNode);
                insertSuccess = true;
              } catch (_) {
                // 如果插入失败，直接设置文本内容
                target.textContent = text;
                // 重新创建 range 用于光标定位
                const newRange = document.createRange();
                newRange.selectNodeContents(target);
                newRange.collapse(false);
                sel.removeAllRanges();
                sel.addRange(newRange);
              }
              
              // 6. 将光标移至文本末尾（仅在成功插入文本节点时执行）
              if (insertSuccess) {
                try {
                  const finalRange = document.createRange();
                  finalRange.setStartAfter(textNode);
                  finalRange.collapse(true);
                  sel.removeAllRanges();
                  sel.addRange(finalRange);
                } catch (_) {
                  // 如果设置光标失败，使用简单的方式
                  const simpleRange = document.createRange();
                  simpleRange.selectNodeContents(target);
                  simpleRange.collapse(false);
                  sel.removeAllRanges();
                  sel.addRange(simpleRange);
                }
              }
              
              // 7. 触发 beforeinput 事件（模拟真实输入流程）
              try {
                target.dispatchEvent(new InputEvent('beforeinput', { 
                  bubbles: true, 
                  cancelable: true,
                  inputType: 'insertReplacementText',
                  data: text,
                  dataTransfer: null
                }));
              } catch (_) {}
              
              // 8. 触发 input 事件（使用 insertReplacementText 类型，表示替换操作）
              try {
                target.dispatchEvent(new InputEvent('input', { 
                  bubbles: true, 
                  cancelable: false,
                  inputType: 'insertReplacementText',
                  data: text,
                  dataTransfer: null
                }));
              } catch (_) {
                try { 
                  target.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
                } catch(__) {
                  try { target.dispatchEvent(new Event('input', { bubbles: true })); } catch(___) {}
                }
              }
              
              // 9. 触发 change 事件
              try { target.dispatchEvent(new Event('change', { bubbles: true })); } catch(_) {}
              
              return;
            } catch (_) {
              // 如果出错，回退到通用处理
            }
          }

          // 其他站点：优先使用 execCommand 以兼容富文本编辑器的内部状态（Lexical/Slate/ProseMirror 等）
          let ok = false;
          try {
            // 选中全部
            try { document.execCommand('selectAll', false, null); } catch (_) {}
            // 插入文本
            ok = document.execCommand('insertText', false, text);
          } catch (_) { ok = false; }

          if (!ok) {
            // 回退：直接替换文本内容
            try { target.innerHTML = ''; } catch (_) {}
            try { target.textContent = text; } catch (_) {}
          }

        // 触发站点监听
          try { target.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertFromPaste', data: text })); } catch (_) {
            try { target.dispatchEvent(new Event('input', { bubbles: true })); } catch(__) {}
          }
          try { target.dispatchEvent(new Event('change', { bubbles: true })); } catch(_) {}

          // 将光标移至末尾
          try {
            const sel = window.getSelection && window.getSelection();
            if (sel) {
            const range = document.createRange();
              range.selectNodeContents(target);
            range.collapse(false);
            sel.removeAllRanges();
            sel.addRange(range);
          }
        } catch (_) {}
          return;
        }

        // 兜底：无法识别类型时直接覆盖文本
        try { target.textContent = text; } catch (_) {}
        try { target.dispatchEvent && target.dispatchEvent(new Event('input', { bubbles: true })); } catch(_) {}
      }

       // 尝试触发站点原生“发送”按钮，确保内部状态同步（React/Vue/Angular）
       function tryClickSiteSend() {
         try {
           const host = (location.hostname || '').toLowerCase();
           // ChatGPT
           if (host.includes('chat.openai.com') || host.includes('chatgpt.com') || host.endsWith('openai.com')) {
             const bar = findControlsBar();
             const sendBtn = (bar && (bar.querySelector('#composer-submit-button') || bar.querySelector('button[data-testid="send-button"]'))) || null;
             if (sendBtn && typeof sendBtn.click === 'function') { sendBtn.click(); return true; }
           }
           // Kimi
           if (host.includes('kimi.com') || host.includes('moonshot.cn')) {
             const bar = findControlsBar();
             const sendBtn = bar && (bar.querySelector('div.send-button-container .send-button') || bar.querySelector('div.send-button'));
             if (sendBtn && typeof sendBtn.click === 'function') { sendBtn.click(); return true; }
           }
           // 豆包
           if (host.includes('doubao.com') || host.includes('douba.ai')) {
             const btn = document.querySelector('#flow-end-msg-send') || document.querySelector('button[data-testid="chat_input_send_button"]');
             if (btn && typeof btn.click === 'function') { btn.click(); return true; }
           }
           // Gemini（Material 按钮）
           if (host.includes('gemini.google.com') || host.includes('ai.google.com') || host.includes('aistudio.google.com')) {
             const bar = findControlsBar();
             const sendBtn = bar && (bar.querySelector('button mat-icon[fonticon="send"]') ? bar.querySelector('button:has(mat-icon[fonticon="send"])') : null);
             if (sendBtn && typeof sendBtn.click === 'function') { sendBtn.click(); return true; }
           }
           // Claude（尽量保守）
           if (host.includes('claude.ai')) {
             const btn = document.querySelector('button[aria-label*="发送" i],button[aria-label*="Send" i],button[type="submit"]');
             if (btn && typeof btn.click === 'function') { btn.click(); return true; }
           }
           return false;
         } catch (_) { return false; }
       }

      function ensureOptimizePort() {
        if (optimizerPort) return optimizerPort;
        optimizerPort = chrome.runtime.connect({ name: 'STREAM_CHAT' });
        optimizerPort.onDisconnect.addListener(() => {
          optimizerPort = null;
          optimizing = false;
          setBtnLoadingOn(currentTriggerBtn, false);
        });
        optimizerPort.onMessage.addListener((msg) => {
          if (!msg || msg.type !== 'STREAM_CHUNK') return;
          const data = msg.data || {};
          const t = String(data.type || '');
          if (!optimizing) return;
          if (t === 'start') {
            activeWorkflowId = data.workflow_id || '';
            promptOptimizedBuffer = '';
            contentBuffer = '';
          } else if (t === 'prompt_optimized') {
            // 仅处理当前会话
            if (activeWorkflowId && data.workflow_id && data.workflow_id !== activeWorkflowId) return;
            const optimized = (data.optimized_query || data.content || '').toString();
            if (optimized) {
              // 流中可能多次出现，累积
              promptOptimizedBuffer += optimized;
            }
          } else if (t === 'content') {
            if (activeWorkflowId && data.workflow_id && data.workflow_id !== activeWorkflowId) return;
            const piece = (data.content || '').toString();
            if (piece) contentBuffer += piece;
          } else if (t === 'error') {
            optimizing = false;
            setBtnLoadingOn(currentTriggerBtn, false);
          } else if (t === 'done') {
            if (activeWorkflowId && data.workflow_id && data.workflow_id !== activeWorkflowId) return;
            // 优先顺序：prompt_optimized 累积 > full_response > content 累积
            let finalText = '';
            if (promptOptimizedBuffer && promptOptimizedBuffer.trim()) {
              finalText = promptOptimizedBuffer.trim();
            } else if (typeof data.full_response === 'string' && data.full_response.trim()) {
              finalText = data.full_response.trim();
            } else if (contentBuffer && contentBuffer.trim()) {
              finalText = contentBuffer.trim();
            }
            if (finalText && targetEl) {
              writeTextTo(targetEl, finalText);
              hasWrittenOptimized = true;
            }
            optimizing = false;
            setBtnLoadingOn(currentTriggerBtn, false);
          } else {
            // 忽略其他事件（避免影响悬浮聊天）
          }
        });
        return optimizerPort;
      }

      // 从某元素出发，寻找最近的可编辑输入框（作为兜底）
      function findNearestChatInput(fromEl) {
        try {
          const candidates = getCandidateInputs();
          if (!candidates || !candidates.length) return null;
          const srcRect = (fromEl && typeof fromEl.getBoundingClientRect === 'function')
            ? fromEl.getBoundingClientRect()
            : { left: 0, top: 0, right: 0, bottom: 0, x: 0, y: 0 };
          let best = null;
          let bestDist = Infinity;
          for (const el of candidates) {
            try {
              const r = el.getBoundingClientRect();
              const cx = r.left + r.width / 2;
              const cy = r.top + r.height / 2;
              const sx = srcRect.left + (srcRect.width || 0) / 2;
              const sy = srcRect.top + (srcRect.height || 0) / 2;
              const dist = Math.hypot(cx - sx, cy - sy);
              if (dist < bestDist) {
                bestDist = dist;
                best = el;
              }
            } catch (_) {}
          }
          return best || null;
        } catch (_) {
          return null;
        }
      }

      async function onOptimizeClick(e) {
        // 保存原内容（在函数作用域，错误处理中也能访问）
        let savedContent = '';
        let targetEl = null;
        
        try {
          // 双保险：阻断默认与冒泡，避免触发站点发送逻辑（豆包/Kimi/Claude 等）
          try { e && e.preventDefault && e.preventDefault(); } catch(_) {}
          try { e && e.stopPropagation && e.stopPropagation(); } catch(_) {}
          try { e && e.stopImmediatePropagation && e.stopImmediatePropagation(); } catch(_) {}
          
          currentTriggerBtn = (e && (e.currentTarget || e.target)) ? (e.currentTarget || e.target) : document.getElementById('lc-optimize-btn-inline');
          
          // 1) 首选全局策略
          targetEl = pickChatInput();
          // 2) 兜底：从按钮出发就近查找
          if (!targetEl && currentTriggerBtn) {
            targetEl = findNearestChatInput(currentTriggerBtn);
          }
          // 3) 再兜底：全局最后一个可见输入框
          if (!targetEl) {
            const all = getCandidateInputs();
            targetEl = all && all.length ? all[0] : null;
          }
          console.log('[LC] Optimize click -> target input:', targetEl);
          if (!targetEl) {
            console.warn('[LC] 未找到可写入的输入框，取消本次优化。');
            return;
          }
          
          // 保存原内容（重要：防止失败时丢失）
          const text = (readTextFrom(targetEl) || '').trim();
          savedContent = text; // 保存原内容到函数作用域
          console.log('[LC] Original text length:', text.length);
          
          if (!text) {
            console.warn('[LC] 输入框为空，取消本次优化。');
            return;
          }
          setBtnLoadingOn(currentTriggerBtn, true);
          optimizing = true;

          const pageUrl = (typeof location !== 'undefined' && location.href) ? String(location.href) : '';
          // 通过后台代理，避免 https 页面的 CORS 限制
          const resp = await new Promise((resolve) => {
            try {
              chrome.runtime.sendMessage({
                type: 'OPTIMIZE_PROMPT',
                prompt: text,
                url: pageUrl
              }, (r) => {
                // 检查 chrome.runtime.lastError（扩展上下文失效时会设置）
                if (chrome.runtime.lastError) {
                  const errorMsg = chrome.runtime.lastError.message || String(chrome.runtime.lastError);
                  if (errorMsg.includes('Extension context invalidated') || errorMsg.includes('message port closed')) {
                    resolve({ 
                      ok: false, 
                      error: 'Extension context invalidated',
                      contextInvalidated: true 
                    });
                  } else {
                    resolve({ ok: false, error: errorMsg });
                  }
                } else {
                  resolve(r || { ok: false, error: 'No response' });
                }
              });
            } catch (err) {
              const errorMsg = String(err);
              if (errorMsg.includes('Extension context invalidated') || errorMsg.includes('message port closed')) {
                resolve({ 
                  ok: false, 
                  error: 'Extension context invalidated',
                  contextInvalidated: true 
                });
              } else {
                resolve({ ok: false, error: errorMsg });
              }
            }
          });
          console.log('[LC] OPTIMIZE_PROMPT resp:', resp);

          // 检查扩展上下文是否失效
          if (resp && resp.contextInvalidated) {
            console.error('[LC] 扩展程序上下文已失效，请刷新页面后重试。');
            // 恢复原内容
            if (savedContent && targetEl) {
              writeTextTo(targetEl, savedContent);
            }
            // 可选：显示用户提示（如果需要）
            // alert('扩展程序已更新，请刷新页面后重试优化功能。');
            setBtnLoadingOn(currentTriggerBtn, false);
            optimizing = false;
            return;
          }

          // 兼容后端返回结构：
          // { ok:true, status:200, data: { code:200, data: { optimized_prompt: '...' }, message:'success' } }
          // 或 { ok:true, status:200, data: { optimized_prompt: '...' } }
          let optimized = null;
          try {
            const root = resp && resp.data ? resp.data : null;
            if (root) {
              if (typeof root.optimized_prompt === 'string' && root.optimized_prompt.trim()) {
                optimized = root.optimized_prompt.trim();
              } else if (root.data && typeof root.data.optimized_prompt === 'string' && root.data.optimized_prompt.trim()) {
                optimized = root.data.optimized_prompt.trim();
              } else if (root.result && typeof root.result.optimized_prompt === 'string' && root.result.optimized_prompt.trim()) {
                optimized = root.result.optimized_prompt.trim();
              }
            }
          } catch (_) {}
          console.log('[LC] Extracted optimized length:', optimized ? optimized.length : 0);

          if (typeof optimized === 'string' && optimized.trim()) {
            // 安全替换内容（不会触发 Claude 的自动发送）
            writeTextTo(targetEl, String(optimized).trim());
            hasWrittenOptimized = true;
            
            // 严格不触发站点发送逻辑的站点：豆包、Kimi、Claude
            // Claude 会在内容替换时自动发送，所以绝对不能触发发送
            try {
              const kind = (typeof getHostCategory === 'function') ? getHostCategory() : '';
              if (kind !== 'doubao' && kind !== 'kimi' && kind !== 'claude') {
                // 其他站点：默认自动触发一次原生发送以驱动内部状态
             tryClickSiteSend();
          } else {
                // 在豆包、Kimi、Claude 上，严格不触发任何站点发送逻辑
                console.log('[LC] 站点', kind, '不触发自动发送');
              }
            } catch(_) {}
          } else {
            // 未返回有效优化结果：恢复原内容
            if (savedContent) {
              writeTextTo(targetEl, savedContent);
            }
            const errorMsg = resp && resp.error ? resp.error : '未知错误';
            console.warn('[LC] 未获得优化结果，已恢复原文。错误:', errorMsg);
          }

          setBtnLoadingOn(currentTriggerBtn, false);
          optimizing = false;
        } catch (err) {
          optimizing = false;
          setBtnLoadingOn(currentTriggerBtn, false);
          // 出错时恢复原内容
          try {
            if (targetEl && savedContent) {
              writeTextTo(targetEl, savedContent);
            }
          } catch(_) {}
          console.error('[LC] onOptimizeClick error:', err);
        }
      }

      function rescan() {
        const el = pickChatInput();
        if (el !== lastEl) {
          lastEl = el;
          targetEl = el;
        }
        if (el) {
          ensureBtn();
          positionBtn();
        } else if (btn) {
          btn.style.display = 'none';
        }
      }

      // 事件绑定与周期性检测
      window.addEventListener('scroll', () => positionBtn(), { passive: true });
      window.addEventListener('resize', () => positionBtn(), { passive: true });
      document.addEventListener('focusin', () => { targetEl = pickChatInput(); positionBtn(); });
      document.addEventListener('input', () => positionBtn());
      const mo = new MutationObserver(() => rescan());
      mo.observe(document.documentElement, { childList: true, subtree: true });
      setInterval(rescan, 1000);
      // 初始执行
      rescan();
    } catch (e) {
      // 静默失败，避免影响宿主站点
      console.warn('Init optimize button failed:', e);
    }
  }

  // 在主入口执行初始化
  try { initPromptOptimizeButton(); } catch (_) {}

})();