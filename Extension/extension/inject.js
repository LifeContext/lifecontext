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
      
      let btn = null;
      let targetEl = null;
      let optimizerPort = null;
      let optimizing = false;
      let lastTargetRect = null;
      let lastEl = null;
      let clearedTextCache = '';
      let hasWrittenOptimized = false;
      // 本次优化会话状态
      let activeWorkflowId = '';
      let promptOptimizedBuffer = '';
      let contentBuffer = '';

      function isSupportedAISite(host) {
        const h = String(host || '').toLowerCase();
        return (
          h.includes('chat.openai.com') || h.includes('chatgpt.com') || h.endsWith('openai.com') ||
          h.includes('gemini.google.com') || h.includes('aistudio.google.com') || h.includes('ai.google.com') ||
          h.includes('claude.ai') ||
          h.includes('doubao.com') || h.includes('douba.ai') ||
          h.includes('moonshot.cn') || h.includes('kimi.moonshot.cn')
        );
      }

      function isVisible(el) {
        if (!el || !(el instanceof Element)) return false;
        const style = window.getComputedStyle(el);
        if (style.visibility === 'hidden' || style.display === 'none' || Number(style.opacity) === 0) return false;
        const rect = el.getBoundingClientRect();
        return rect.width > 200 && rect.height > 30 && rect.bottom > 0 && rect.right > 0 &&
               rect.left < window.innerWidth && rect.top < window.innerHeight;
      }

      function getCandidateInputs() {
        // 常见选择器集合（多站点尽量命中）
        const selectors = [
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
        const nodes = new Set();
        for (const sel of selectors) {
          document.querySelectorAll(sel).forEach(n => nodes.add(n));
        }
        // 兜底：页面上最后一个 textarea/可编辑框
        document.querySelectorAll('textarea, div[contenteditable="true"]').forEach(n => nodes.add(n));
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

      function positionBtn() {
        if (!btn || !targetEl || !isVisible(targetEl)) {
          if (btn) btn.style.display = 'none';
          return;
        }
        const rect = targetEl.getBoundingClientRect();
        lastTargetRect = rect;
        const size = parseInt((btn.style.width || '34px'), 10) || 34;
        // 读取 padding-right，避免覆盖文字；另外预留空间给站点自带按钮（语音/发送等）
        let pr = 0;
        try {
          const cs = window.getComputedStyle(targetEl);
          pr = parseFloat(cs.paddingRight || '0') || 0;
        } catch (_) {}
        const reservedRight = Math.max(52, pr + 12); // 至少 52px，或比 padding 多 12px
        // 垂直位置：单行输入框垂直居中；多行输入框靠右下方（距底 12px）
        let top;
        if (rect.height > 64) {
          top = Math.round(rect.bottom - size - 12);
        } else {
          top = Math.round(rect.top + rect.height / 2 - size / 2);
        }
        const left = Math.round(rect.right - reservedRight - size);
        // 边界保护
        const clampedLeft = Math.max(0, Math.min(left, window.innerWidth - size - 2));
        const clampedTop = Math.max(0, Math.min(top, window.innerHeight - size - 2));
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
        if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
          el.value = text;
        } else if (el.getAttribute('contenteditable') === 'true') {
          el.innerHTML = '';
          el.textContent = text;
        }
        // 触发站点监听
        try {
          el.dispatchEvent(new InputEvent('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
          // 将光标移至末尾（contenteditable 简单处理）
          if (el.getAttribute && el.getAttribute('contenteditable') === 'true') {
            const sel = window.getSelection();
            const range = document.createRange();
            range.selectNodeContents(el);
            range.collapse(false);
            sel.removeAllRanges();
            sel.addRange(range);
          } else if (typeof el.selectionStart === 'number') {
            el.selectionStart = el.selectionEnd = (el.value || '').length;
          }
        } catch (_) {}
      }

      function ensureOptimizePort() {
        if (optimizerPort) return optimizerPort;
        optimizerPort = chrome.runtime.connect({ name: 'STREAM_CHAT' });
        optimizerPort.onDisconnect.addListener(() => {
          optimizerPort = null;
          optimizing = false;
          setBtnLoading(false);
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
            setBtnLoading(false);
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
            setBtnLoading(false);
          } else {
            // 忽略其他事件（避免影响悬浮聊天）
          }
        });
        return optimizerPort;
      }

      async function onOptimizeClick(e) {
        try {
          e.preventDefault();
          targetEl = pickChatInput();
          if (!targetEl) return;
          const text = readTextFrom(targetEl).trim();
          if (!text) return;
          // 清空输入框，等待优化结果
          clearedTextCache = text;
          hasWrittenOptimized = false;
          writeTextTo(targetEl, '');
          ensureBtn();
          setBtnLoading(true);
          optimizing = true;
          const payload = {
            query: text,
            optimize_prompt: true
          };
          const port = ensureOptimizePort();
          if (port) {
            port.postMessage({ action: 'start', payload });
          } else {
            optimizing = false;
            setBtnLoading(false);
            // 端口不可用时回滚原始文本
            writeTextTo(targetEl, clearedTextCache);
          }
        } catch (_) {
          optimizing = false;
          setBtnLoading(false);
          // 出错时回滚原始文本
          try { if (targetEl && !hasWrittenOptimized) writeTextTo(targetEl, clearedTextCache); } catch(_) {}
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
      setInterval(rescan, 1500);
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