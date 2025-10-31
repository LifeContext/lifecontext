//content.js
// 检查 chrome.runtime 是否可用且扩展上下文有效
function isChromeRuntimeAvailable() {
  try {
    return typeof chrome !== 'undefined' && 
           chrome.runtime && 
           chrome.runtime.sendMessage &&
           !chrome.runtime.lastError;
  } catch (e) {
    return false;
  }
}

// DOM变化监听和爬取管理
class DOMCrawlerManager {
  constructor() {
    this.observer = null;
    this.lastCrawlTime = 0;
    this.crawlThrottleDelay = 3000; // 3秒节流
    this.contentHash = '';
    this.isObserving = false;
    this.observedSelectors = [
      'main', 'article', '.content', '.post', '.message', '.chat-message',
      '.conversation', '.thread', '.comment', '.reply', '.update',
      '[role="main"]', '[role="article"]', '.main-content'
    ];
    this.ignoredSelectors = [
      'script', 'style', 'noscript', 'meta', 'link', 'title',
      '.advertisement', '.ads', '.sidebar', '.navigation', '.nav',
      '.header', '.footer', '.menu', '.toolbar'
    ];
  }

  // 初始化DOM监听
  init() {
    if (typeof window !== 'undefined' && window.__LC_SKIP_CRAWL__ === true) {
      console.log('🚫 检测到主网页，跳过 DOM 监听与爬取');
      return;
    }
    if (typeof window !== 'undefined' && window.__LC_CRAWL_ENABLED__ === false) {
      console.log('🚫 爬取功能已禁用');
      return;
    }
    if (this.isObserving) return;
    
    console.log('🔍 初始化DOM变化监听器');
    this.startObserving();
    this.isObserving = true;
  }

  // 开始监听DOM变化
  startObserving() {
    if (this.observer) {
      this.observer.disconnect();
    }

    this.observer = new MutationObserver((mutations) => {
      this.handleMutations(mutations);
    });

    // 监听整个文档的变化
    this.observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: false,
      characterData: true
    });

    console.log('✅ DOM变化监听器已启动');
  }

  // 处理DOM变化
  handleMutations(mutations) {
    let hasSignificantChange = false;
    let changeCount = 0;

    for (const mutation of mutations) {
      // 检查是否有新增的节点
      if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
        for (const node of mutation.addedNodes) {
          if (this.isSignificantNode(node)) {
            hasSignificantChange = true;
            changeCount++;
          }
        }
      }
      
      // 检查文本内容变化
      if (mutation.type === 'characterData') {
        const textContent = mutation.target.textContent?.trim();
        if (textContent && textContent.length > 10) {
          hasSignificantChange = true;
          changeCount++;
        }
      }
    }

    if (hasSignificantChange) {
      console.log(`📝 检测到 ${changeCount} 个重要DOM变化`);
      this.scheduleCrawl();
    }
  }

  // 判断节点是否重要
  isSignificantNode(node) {
    if (!node || node.nodeType !== Node.ELEMENT_NODE) return false;
    
    const element = node;
    
    // 检查是否在忽略列表中
    for (const selector of this.ignoredSelectors) {
      if (element.matches && element.matches(selector)) return false;
      if (element.closest && element.closest(selector)) return false;
    }

    // 检查是否在重要选择器中
    for (const selector of this.observedSelectors) {
      if (element.matches && element.matches(selector)) return true;
      if (element.closest && element.closest(selector)) return true;
    }

    // 检查是否有足够的文本内容
    const textContent = element.textContent?.trim();
    if (textContent && textContent.length > 20) {
      return true;
    }

    // 检查是否有子元素包含重要内容
    for (const child of element.children || []) {
      if (this.isSignificantNode(child)) return true;
    }

    return false;
  }

  // 安排爬取任务（带节流）
  scheduleCrawl() {
    const now = Date.now();
    const timeSinceLastCrawl = now - this.lastCrawlTime;

    if (timeSinceLastCrawl < this.crawlThrottleDelay) {
      console.log(`⏱️ 节流中，还需等待 ${this.crawlThrottleDelay - timeSinceLastCrawl}ms`);
      return;
    }

    this.lastCrawlTime = now;
    console.log('🚀 触发增量爬取');
    this.performIncrementalCrawl();
  }

  // 执行增量爬取
  async performIncrementalCrawl() {
    try {
      if (typeof window !== 'undefined' && window.__LC_SKIP_CRAWL__ === true) {
        console.log('🚫 检测到主网页，跳过增量爬取');
        return;
      }
      if (typeof window !== 'undefined' && window.__LC_CRAWL_ENABLED__ === false) {
        console.log('🚫 爬取功能已禁用，跳过增量爬取');
        return;
      }
      if (!isChromeRuntimeAvailable()) {
        console.log('Chrome runtime 不可用，跳过增量爬取');
        return;
      }

      // 获取当前页面内容
      const currentContent = this.extractPageContent();
      const currentHash = this.calculateContentHash(currentContent);

      // 如果内容没有实质性变化，跳过爬取
      if (currentHash === this.contentHash) {
        console.log('📄 内容无实质性变化，跳过爬取');
        return;
      }

      this.contentHash = currentHash;

      // 如果内容太少，跳过爬取
      if (currentContent.length < 50) {
        console.log('📄 内容太少，跳过增量爬取');
        return;
      }

      console.log('📊 执行增量爬取，内容长度:', currentContent.length);

      // 提取标签
      const keywordsContent = (document.querySelector('meta[name="keywords"]')?.getAttribute('content') || '').trim();
      const tags = keywordsContent
        ? keywordsContent.split(/,|，/).map(s => s.trim()).filter(Boolean)
        : [];

      // 组织请求数据
      const title = document.title || '';
      const contentObj = { title, content: currentContent };
      const payload = {
        title,
        url: location.href,
        content: contentObj,
        source: 'web-crawler-incremental',
        tags,
        timestamp: new Date().toISOString(),
        changeType: 'dom-mutation'
      };

      // 发送到后台脚本
      const response = await new Promise((resolve) => {
        try {
          // 先检查扩展上下文是否有效
          if (!isChromeRuntimeAvailable()) {
            resolve({ ok: false, error: 'Extension context invalidated' });
            return;
          }
          
          chrome.runtime.sendMessage({ type: 'UPLOAD_WEB_DATA', payload }, (resp) => {
            if (chrome.runtime.lastError) {
              console.log('Chrome runtime error:', chrome.runtime.lastError.message);
              resolve({ ok: false, error: chrome.runtime.lastError.message });
            } else {
              resolve(resp || null);
            }
          });
        } catch (e) {
          console.log('Send message error:', e);
          resolve({ ok: false, error: String(e) });
        }
      });

      // 通知后台脚本
      try {
        if (isChromeRuntimeAvailable()) {
          chrome.runtime.sendMessage({ 
            type: 'SCRAPED_DATA', 
            data: { payload, serverResponse: response, isIncremental: true } 
          });
        }
      } catch (e) {
        console.error('发送增量爬取消息到后台失败:', e);
      }

      if (response && response.ok) {
        console.log('✅ 增量爬取成功');
      } else {
        console.log('❌ 增量爬取失败:', response?.error || '未知错误');
      }

    } catch (error) {
      console.error('增量爬取失败:', error);
    }
  }

  // 提取页面内容
  extractPageContent() {
    try {
      // 优先从重要区域提取内容
      let content = '';
      
      for (const selector of this.observedSelectors) {
        const elements = document.querySelectorAll(selector);
        for (const element of elements) {
          const text = element.innerText?.trim();
          if (text && text.length > 20) {
            content += text + '\n';
          }
        }
      }

      // 如果没有找到重要区域，使用整个页面内容
      if (!content.trim()) {
        content = document.body?.innerText || '';
      }

      return content.trim();
    } catch (e) {
      console.error('提取页面内容失败:', e);
      return '';
    }
  }

  // 计算内容哈希
  calculateContentHash(content) {
    // 简单的哈希算法，用于检测内容变化
    let hash = 0;
    if (content.length === 0) return hash.toString();
    
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // 转换为32位整数
    }
    
    return hash.toString();
  }

  // 停止监听
  stop() {
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }
    this.isObserving = false;
    console.log('🛑 DOM变化监听器已停止');
  }

  // 更新配置
  updateConfig(config) {
    if (config.throttleDelay) {
      this.crawlThrottleDelay = config.throttleDelay;
    }
    if (config.observedSelectors) {
      this.observedSelectors = config.observedSelectors;
    }
    if (config.ignoredSelectors) {
      this.ignoredSelectors = config.ignoredSelectors;
    }
    console.log('⚙️ DOM监听配置已更新');
  }
}

// 创建全局DOM爬取管理器实例
const domCrawler = new DOMCrawlerManager();

// 全局爬取开关
window.__LC_CRAWL_ENABLED__ = true; // 默认开启

// 从存储中加载爬取开关状态
async function loadCrawlEnabledState() {
  try {
    const result = await chrome.storage.sync.get(['crawlEnabled']);
    window.__LC_CRAWL_ENABLED__ = result.crawlEnabled !== false; // 默认为true
  } catch (error) {
    console.log('加载爬取开关状态失败，使用默认值');
    window.__LC_CRAWL_ENABLED__ = true;
  }
}

// 初始化时加载爬取开关状态
(async () => { await loadCrawlEnabledState(); })();

// 读取主站配置并设置是否跳过当前页面的爬取
window.__LC_SKIP_CRAWL__ = false;
async function evaluateSkipCrawlForThisPage() {
  try {
    const defaults = { FRONTEND_HOST: 'localhost', FRONTEND_PORT: '3000' };
    const cfg = await new Promise((resolve) => {
      try {
        chrome.storage.sync.get(defaults, (res) => resolve(res || defaults));
      } catch (e) {
        resolve(defaults);
      }
    });

    const expectedHost = String(cfg.FRONTEND_HOST || '').toLowerCase();
    const expectedPort = String(cfg.FRONTEND_PORT || '').trim();
    const currentHost = String(location.hostname || '').toLowerCase();
    const currentPort = String(location.port || (location.protocol === 'https:' ? '443' : '80'));

    const isSameHost = currentHost === expectedHost || location.host.toLowerCase() === `${expectedHost}:${expectedPort}`;
    const isSamePort = expectedPort === '' ? true : currentPort === expectedPort;
    const shouldSkip = Boolean(expectedHost) && isSameHost && isSamePort;

    if (shouldSkip) {
      window.__LC_SKIP_CRAWL__ = true;
      console.log(`🚫 当前为主网页(${expectedHost}:${expectedPort})，将跳过所有爬取与监听`);
    }
  } catch (_) {
    // 忽略异常，保持默认 false
  }
}

// 尽早评估是否跳过
(async () => { await evaluateSkipCrawlForThisPage(); })();

// 自动爬取网页内容（初始爬取）
async function autoCrawlPage() {
  try {
    if (typeof window !== 'undefined' && window.__LC_SKIP_CRAWL__ === true) {
      console.log('🚫 检测到主网页，跳过初始爬取');
      return;
    }
    if (typeof window !== 'undefined' && window.__LC_CRAWL_ENABLED__ === false) {
      console.log('🚫 爬取功能已禁用，跳过初始爬取');
      return;
    }
    // 检查 chrome.runtime 是否可用
    if (!isChromeRuntimeAvailable()) {
      console.log('Chrome runtime 不可用，跳过自动爬取');
      return;
    }

    // 等待页面完全加载
    if (document.readyState !== 'complete') {
      await new Promise(resolve => {
        if (document.readyState === 'loading') {
          document.addEventListener('DOMContentLoaded', resolve);
        } else {
          resolve();
        }
      });
    }

    // 额外等待2秒确保动态内容加载完成
    await new Promise(resolve => setTimeout(resolve, 2000));

    // 再次检查 chrome.runtime 是否可用
    if (!isChromeRuntimeAvailable()) {
      console.log('Chrome runtime 在等待后仍不可用，跳过自动爬取');
      return;
    }

    // 1) 仅抓取页面可见纯文本
    const pageText = (function() {
      try {
        return (document.body?.innerText || '').trim();
      } catch (e) {
        return '';
      }
    })();

    // 如果页面内容太少，跳过爬取
    if (pageText.length < 50) {
      console.log('页面内容太少，跳过自动爬取');
      return;
    }

    // 2) 提取 <meta name="keywords"> 作为 tags（按中英文逗号分割并去空白）
    const keywordsContent = (document.querySelector('meta[name="keywords"]')?.getAttribute('content') || '').trim();
    const tags = keywordsContent
      ? keywordsContent.split(/,|，/).map(s => s.trim()).filter(Boolean)
      : [];

    // 3) 组织接口请求体
    const title = document.title || '';
    const contentObj = { title, content: pageText };
    const payload = {
      title,
      url: location.href,
      content: contentObj,
      source: 'web-crawler-initial',
      tags,
      timestamp: new Date().toISOString(),
      changeType: 'initial-load'
    };

    console.log('🚀 开始初始页面爬取:', title);

    // 4) 通过后台脚本代理上传，避免 HTTPS -> HTTP 混合内容被拦截
    const j = await new Promise((resolve) => {
      try {
        // 先检查扩展上下文是否有效
        if (!isChromeRuntimeAvailable()) {
          resolve({ ok: false, error: 'Extension context invalidated' });
          return;
        }
        
        chrome.runtime.sendMessage({ type: 'UPLOAD_WEB_DATA', payload }, (resp) => {
          if (chrome.runtime.lastError) {
            console.log('Chrome runtime error:', chrome.runtime.lastError.message);
            resolve({ ok: false, error: chrome.runtime.lastError.message });
          } else {
            resolve(resp || null);
          }
        });
      } catch (e) {
        console.log('Send message error:', e);
        resolve({ ok: false, error: String(e) });
      }
    });

    // 5) 通知 popup/background 显示
    try {
      if (isChromeRuntimeAvailable()) {
        chrome.runtime.sendMessage({ type: 'SCRAPED_DATA', data: { payload, serverResponse: j, isIncremental: false } });
      }
    } catch (e) {
      console.error('发送消息到后台失败:', e);
    }
    
    if (j && j.ok) {
      console.log('✅ 初始页面爬取成功:', title);
      // 初始化DOM监听器
      domCrawler.init();
    } else {
      console.log('❌ 初始页面爬取失败:', j?.error || '未知错误');
    }
  } catch (err) {
    console.error('自动爬取页面失败:', err);
    try {
      if (isChromeRuntimeAvailable()) {
        chrome.runtime.sendMessage({ type: 'SCRAPED_DATA', data: { error: String(err) } });
      }
    } catch (e) {
      console.error('发送错误消息到后台失败:', e);
    }
  }
}

// 页面可见性管理
class PageVisibilityManager {
  constructor() {
    this.isPageVisible = !document.hidden;
    this.setupVisibilityListeners();
  }

  setupVisibilityListeners() {
    // 监听页面可见性变化
    document.addEventListener('visibilitychange', () => {
      const wasVisible = this.isPageVisible;
      this.isPageVisible = !document.hidden;
      
      if (!wasVisible && this.isPageVisible) {
        console.log('📱 页面变为可见，重新激活DOM监听');
        // 页面重新可见时，重新初始化DOM监听
        if (domCrawler && !domCrawler.isObserving && window.__LC_SKIP_CRAWL__ !== true) {
          domCrawler.init();
        }
      } else if (wasVisible && !this.isPageVisible) {
        console.log('📱 页面变为隐藏，暂停DOM监听');
        // 页面隐藏时，暂停DOM监听以节省资源
        if (domCrawler && domCrawler.isObserving) {
          domCrawler.stop();
        }
      }
    });

    // 监听窗口焦点变化
    window.addEventListener('focus', () => {
      console.log('🎯 窗口获得焦点，检查DOM监听状态');
      if (domCrawler && !domCrawler.isObserving && window.__LC_SKIP_CRAWL__ !== true) {
        domCrawler.init();
      }
    });

    window.addEventListener('blur', () => {
      console.log('🎯 窗口失去焦点');
      // 可以选择在失去焦点时暂停监听，但通常保持监听
    });
  }

  isVisible() {
    return this.isPageVisible;
  }
}

// 创建页面可见性管理器
const visibilityManager = new PageVisibilityManager();

// 延迟执行，确保页面和扩展环境完全就绪
function delayedAutoCrawl() {
  setTimeout(() => {
    if (isChromeRuntimeAvailable()) {
      autoCrawlPage();
    } else {
      console.log('Chrome runtime 不可用，延迟重试...');
      // 再次延迟重试
      setTimeout(() => {
        if (isChromeRuntimeAvailable()) {
          autoCrawlPage();
        } else {
          console.log('Chrome runtime 仍不可用，跳过自动爬取');
        }
      }, 3000);
    }
  }, 1000);
}

// 监听来自popup或background的消息
if (isChromeRuntimeAvailable()) {
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'TOGGLE_CRAWL') {
      // 切换全局爬取开关
      window.__LC_CRAWL_ENABLED__ = message.enabled;
      if (message.enabled) {
        console.log('✅ 爬取功能已启用');
        // 如果之前被禁用了，现在重新启用
        if (domCrawler && !domCrawler.isObserving && window.__LC_SKIP_CRAWL__ !== true) {
          domCrawler.init();
        }
      } else {
        console.log('🛑 爬取功能已禁用');
        // 停止DOM监听
        if (domCrawler && domCrawler.isObserving) {
          domCrawler.stop();
        }
      }
      sendResponse({ success: true });
    } else if (message.type === 'GET_CRAWL_STATUS') {
      sendResponse({
        enabled: window.__LC_CRAWL_ENABLED__ !== false
      });
    } else if (message.type === 'TOGGLE_DOM_OBSERVER') {
      if (message.enabled) {
        domCrawler.init();
        console.log('✅ DOM监听器已启用');
      } else {
        domCrawler.stop();
        console.log('🛑 DOM监听器已禁用');
      }
      sendResponse({ success: true });
    } else if (message.type === 'UPDATE_DOM_CONFIG') {
      domCrawler.updateConfig(message.config);
      sendResponse({ success: true });
    } else if (message.type === 'GET_DOM_STATUS') {
      sendResponse({
        isObserving: domCrawler.isObserving,
        throttleDelay: domCrawler.crawlThrottleDelay,
        lastCrawlTime: domCrawler.lastCrawlTime
      });
    } else if (message.type === 'MANUAL_CRAWL') {
      // 手动触发爬取
      console.log('🔄 执行手动爬取');
      autoCrawlPage().then(() => {
        sendResponse({ success: true });
      }).catch((error) => {
        console.error('手动爬取失败:', error);
        sendResponse({ success: false, error: error.message });
      });
      return true; // 异步响应
    }
  });
}

// 页面加载完成后自动触发爬取
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', delayedAutoCrawl);
} else {
  // 页面已经加载完成，延迟执行
  delayedAutoCrawl();
}

// 页面卸载时清理资源
window.addEventListener('beforeunload', () => {
  if (domCrawler) {
    domCrawler.stop();
  }
});
