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

  // ==============================
  // 主流 AI 网站输入框右侧优化按钮（圆形 Logo）
  // - 支持：ChatGPT、Gemini、Claude、豆包、Kimi Chat
  // - 功能：读取输入框文本 -> 调用 /api/agent/chat/stream (optimize_prompt) -> 接收 prompt_optimized 事件 -> 覆盖输入框内容
  // ==============================
  function initPromptOptimizeButton() {
    try {
      // 仅在主流 AI 网站生效
      if (!isSupportedAISite(location.hostname)) return;
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
              'button[aria-label*="Attach" i]::parent'
            ];
          case 'doubao':
            return [
              // 用户提供：Controls Bar 占位容器，类名带稳定前缀 tools-placeholder-
              'div.tools-placeholder-WzV9jb',
              'div[class^="tools-placeholder-"]'
            ];
          case 'gemini':
            return [
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
      // 监听来自 Page Context 的点击消息 -> 触发真正的扩展逻辑
      try {
        window.addEventListener('message', (evt) => {
          try {
            if (evt && evt.source === window && evt.data && evt.data.source === 'lc-page' && evt.data.type === 'LC_OPTIMIZE_CLICK') {
              try { currentTriggerBtn = document.getElementById('lc-optimize-btn-inline'); } catch(_) {}
              onOptimizeClick(new Event('lc-optimize'));
            }
          } catch(_) {}
        }, false);
      } catch(_) {}
      return;  // 仅采用内嵌注入策略，阻断旧的浮动定位逻辑

      function isSupportedAISite(host) {
        const h = String(host || '').toLowerCase();
        return (
          h.includes('chat.openai.com') || h.includes('chatgpt.com') || h.endsWith('openai.com') ||
          h.includes('gemini.google.com') || h.includes('aistudio.google.com') || h.includes('ai.google.com') ||
          h.includes('claude.ai') ||
          h.includes('doubao.com') || h.includes('douba.ai') ||
          h.includes('moonshot.cn') || h.includes('kimi.moonshot.cn') || h.includes('kimi.com') ||
          h.includes('x.ai') || h.includes('grok')
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
          siteExtra.push('div[contenteditable="true"].ProseMirror', 'textarea');
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
          // Gemini 可能在 open shadow 内
          siteExtra.push('textarea', 'div[role="textbox"][contenteditable="true"]', 'textarea[aria-label], div[contenteditable="true"][aria-label]');
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
        if (on) {
          btn.disabled = true;
          btn.style.opacity = '.7';
          btn.style.cursor = 'not-allowed';
          btn.innerHTML = `
            <span style="display:inline-block;width:100%;height:100%;border-radius:50%;
                         background: radial-gradient(circle at 50% 50%, rgba(0,0,0,0.06), rgba(0,0,0,0.12));
                         position:relative;">
              <span style="position:absolute;left:50%;top:50%;width:16px;height:16px;margin:-8px 0 0 -8px;
                           border:2px solid rgba(0,0,0,.2);border-top-color:#0ea5e9;border-radius:50%;
                           animation:lc-spin .8s linear infinite;"></span>
            </span>`;
        } else {
          btn.disabled = false;
          btn.style.opacity = '.95';
          btn.style.cursor = 'pointer';
          btn.innerHTML = '';
        }
      }
      // 针对任意按钮元素设置/取消“加载中”状态
      function setBtnLoadingOn(el, on) {
        try {
          if (!el) return;
          if (on) {
            el.disabled = true;
            el.style.opacity = '0.7';
            el.style.cursor = 'not-allowed';
          } else {
            el.disabled = false;
            el.style.opacity = '';
            el.style.cursor = '';
          }
        } catch (_) {}
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

        // 针对不同类型分别处理
        if (target && (target.tagName === 'TEXTAREA' || target.tagName === 'INPUT')) {
          try {
            target.focus && target.focus();
          } catch (_) {}
          setNativeValue(target, text);
          try {
            // 更像“粘贴”的输入类型，提升兼容性
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
          try { target.focus && target.focus(); } catch (_) {}

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
        try {
          // 双保险：阻断默认与冒泡，避免触发站点发送逻辑（豆包/Kimi 等）
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
          const text = (readTextFrom(targetEl) || '').trim();
          console.log('[LC] Original text length:', text.length);
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
              }, (r) => resolve(r));
            } catch (err) {
              resolve({ ok: false, error: String(err) });
            }
          });
          console.log('[LC] OPTIMIZE_PROMPT resp:', resp);

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
            writeTextTo(targetEl, String(optimized).trim());
            hasWrittenOptimized = true;
              // 非豆包/Kimi：默认自动触发一次原生发送以驱动内部状态
              try {
                const kind = (typeof getHostCategory === 'function') ? getHostCategory() : '';
                if (kind !== 'doubao' && kind !== 'kimi') {
                  tryClickSiteSend();
                } else {
                  // 在豆包与 Kimi 上，严格不触发任何站点发送逻辑
                }
              } catch(_) {}
          } else {
            // 未返回有效优化结果：保留原文（若原文为空则不改动）
            if (text) writeTextTo(targetEl, text);
            console.warn('[LC] 未获得优化结果，保持原文。');
          }

          setBtnLoadingOn(currentTriggerBtn, false);
          optimizing = false;
        } catch (_) {
          optimizing = false;
          setBtnLoadingOn(currentTriggerBtn, false);
          // 出错时回滚原始文本
          try { if (targetEl) writeTextTo(targetEl, readTextFrom(targetEl) || ''); } catch(_) {}
          console.error('[LC] onOptimizeClick error:', _);
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