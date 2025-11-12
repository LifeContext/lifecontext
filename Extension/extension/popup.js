// 弹窗状态管理
let currentStatus = 'success'; // 'success', 'crawling', 'error'
let floatingChatEnabled = true;
let crawlEnabled = true; // 爬取开关，默认开启（Controls 主开关）
let notificationsEnabled = true; // 通知开关，默认开启
let notificationsPreferred = true; // 记录用户偏好，用于 Controls 重新开启时恢复

// 从存储中加载悬浮球状态
async function loadFloatingChatState() {
  try {
    const result = await chrome.storage.sync.get(['floatingChatEnabled']);
    floatingChatEnabled = result.floatingChatEnabled !== false; // 默认为true
    updateToggleUI();
  } catch (error) {
    console.log('加载悬浮球状态失败，使用默认值');
    floatingChatEnabled = true;
    updateToggleUI();
  }
}

// 保存悬浮球状态到存储
async function saveFloatingChatState(enabled) {
  try {
    await chrome.storage.sync.set({ floatingChatEnabled: enabled });
  } catch (error) {
    console.log('保存悬浮球状态失败:', error);
  }
}

// 接收 content 发来的消息
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'SCRAPED_DATA') {
    // 只有在爬取功能开启时才更新状态
    if (crawlEnabled) {
      if (message.data && message.data.payload) {
        const { title, url } = message.data.payload;
        const isIncremental = message.data.isIncremental;
        
        if (message.data.serverResponse && message.data.serverResponse.ok) {
          updateStatus('success', 'Remembering...', notificationsEnabled ? 'Page content saved' : 'Saved (notifications off)');
        } else {
          updateStatus('error', 'Save Failed', message.data.serverResponse?.error || 'Unknown error');
        }
      } else if (message.data && message.data.error) {
        updateStatus('error', 'Crawl Error', message.data.error);
      }
    }
  }
});

// 更新状态显示（已移除状态显示区域，保留函数以避免错误）
function updateStatus(status, mainText, subText) {
  currentStatus = status;
  // 状态区域已移除，不再更新UI
}

// 悬浮球切换功能
async function toggleFloatingChat() {
  // 先更新本地状态
  floatingChatEnabled = !floatingChatEnabled;
  updateToggleUI();
  
  // 保存到存储
  await saveFloatingChatState(floatingChatEnabled);
  
  // 尝试通知content script
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    try {
      const response = await chrome.tabs.sendMessage(tab.id, {
        type: 'TOGGLE_FLOATING_CHAT',
        enabled: floatingChatEnabled
      });
      
      if (response && response.success !== undefined) {
        console.log(`悬浮聊天球已${floatingChatEnabled ? '启用' : '禁用'}`);
      }
    } catch (firstError) {
      console.log('Content script未响应，尝试重新注入');
      
      // 尝试重新注入content script
      try {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['inject.js']
        });
        
        // 等待一下让content script加载
        await new Promise(resolve => setTimeout(resolve, 200));
        
        // 再次尝试发送消息
        await chrome.tabs.sendMessage(tab.id, {
          type: 'TOGGLE_FLOATING_CHAT',
          enabled: floatingChatEnabled
        });
        
        console.log(`悬浮聊天球已${floatingChatEnabled ? '启用' : '禁用'}`);
      } catch (secondError) {
        console.log('重新注入失败，状态已保存，页面刷新后生效');
      }
    }
  } catch (error) {
    console.log('切换悬浮聊天球失败，状态已保存:', error.message);
  }
}

// 更新切换按钮UI
function updateToggleUI() {
  const toggleSwitch = document.getElementById('toggle-switch');
  if (toggleSwitch) {
    if (floatingChatEnabled) {
      toggleSwitch.classList.remove('off');
    } else {
      toggleSwitch.classList.add('off');
    }
  }
}

// 根据开关状态统一刷新状态文案（已移除状态显示区域，保留函数以避免错误）
function refreshStatusByFlags() {
  // 状态区域已移除，不再更新UI
}

// 获取悬浮球状态
async function getFloatingChatStatus() {
  // 从存储中加载状态
  await loadFloatingChatState();
  
  // 尝试同步content script状态（可选）
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: 'GET_FLOATING_CHAT_STATUS'
    });
    
    if (response && response.enabled !== undefined) {
      // 如果content script状态与存储状态不同，更新存储
      if (response.enabled !== floatingChatEnabled) {
        floatingChatEnabled = response.enabled;
        await saveFloatingChatState(floatingChatEnabled);
        updateToggleUI();
      }
    }
  } catch (error) {
    // Content script未加载，使用存储中的状态
    console.log('Content script未加载，使用存储状态');
  }
}

// 从存储中加载爬取开关状态
async function loadCrawlState() {
  try {
    const result = await chrome.storage.sync.get(['crawlEnabled']);
    crawlEnabled = result.crawlEnabled !== false; // 默认为true
    updateCrawlToggleUI();
  } catch (error) {
    console.log('加载爬取开关状态失败，使用默认值');
    crawlEnabled = true;
    updateCrawlToggleUI();
  }
}

// 保存爬取开关状态到存储
async function saveCrawlState(enabled) {
  try {
    await chrome.storage.sync.set({ crawlEnabled: enabled });
  } catch (error) {
    console.log('保存爬取开关状态失败:', error);
  }
}

// 切换爬取功能
async function toggleCrawl() {
  // 先更新本地状态
  crawlEnabled = !crawlEnabled;
  updateCrawlToggleUI();
  
  
  // 保存到存储
  await saveCrawlState(crawlEnabled);
  
  // Controls 关闭时：强制关闭通知并禁用 UI；开启时：恢复用户偏好
  if (!crawlEnabled) {
    // 记录当前偏好，再强制关闭
    notificationsPreferred = notificationsEnabled;
    notificationsEnabled = false;
    await saveNotificationsPreferred(notificationsPreferred);
    await saveNotificationsState(false);
  } else {
    // 恢复到用户偏好（默认 true）
    const stored = await chrome.storage.sync.get(['notificationsPreferred']);
    notificationsPreferred = (typeof stored.notificationsPreferred === 'boolean')
      ? stored.notificationsPreferred
      : notificationsPreferred;
    notificationsEnabled = notificationsPreferred;
    await saveNotificationsState(notificationsEnabled);
  }
  updateNotificationsToggleUI();
  refreshStatusByFlags();
  
  // 尝试通知content script
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    try {
      const response = await chrome.tabs.sendMessage(tab.id, {
        type: 'TOGGLE_CRAWL',
        enabled: crawlEnabled
      });
      
      if (response && response.success !== undefined) {
        console.log(`爬取功能已${crawlEnabled ? '启用' : '禁用'}`);
      }
    } catch (firstError) {
      console.log('Content script未响应，尝试重新注入');
      
      // 尝试重新注入content script
      try {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content.js']
        });
        
        // 等待一下让content script加载
        await new Promise(resolve => setTimeout(resolve, 200));
        
        // 再次尝试发送消息
        await chrome.tabs.sendMessage(tab.id, {
          type: 'TOGGLE_CRAWL',
          enabled: crawlEnabled
        });
        
        console.log(`爬取功能已${crawlEnabled ? '启用' : '禁用'}`);
      } catch (secondError) {
        console.log('重新注入失败，状态已保存，页面刷新后生效');
      }
    }
  } catch (error) {
    console.log('切换爬取功能失败，状态已保存:', error.message);
  }
}

// 更新爬取开关按钮UI
function updateCrawlToggleUI() {
  const crawlToggleBtn = document.getElementById('crawl-toggle-btn');
  if (crawlToggleBtn) {
    if (crawlEnabled) {
      crawlToggleBtn.classList.add('enabled');
      crawlToggleBtn.title = 'Disable Recording';
    } else {
      crawlToggleBtn.classList.remove('enabled');
      crawlToggleBtn.title = 'Enable Recording';
    }
  }
}

// 获取爬取状态
async function getCrawlStatus() {
  // 从存储中加载状态
  await loadCrawlState();
  refreshStatusByFlags();
  
  // 尝试同步content script状态（可选）
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: 'GET_CRAWL_STATUS'
    });
    
    if (response && response.enabled !== undefined) {
      // 如果content script状态与存储状态不同，更新存储
      if (response.enabled !== crawlEnabled) {
        crawlEnabled = response.enabled;
        await saveCrawlState(crawlEnabled);
        updateCrawlToggleUI();
        refreshStatusByFlags();
      }
    }
  } catch (error) {
    // Content script未加载，使用存储中的状态
    console.log('Content script未加载，使用存储状态');
  }
}

// ===== 通知开关：存储、UI与事件处理 =====
async function loadNotificationsState() {
  try {
    const result = await chrome.storage.sync.get(['notificationsEnabled', 'notificationsPreferred']);
    notificationsEnabled = result.notificationsEnabled !== false; // 默认为true
    notificationsPreferred = (typeof result.notificationsPreferred === 'boolean')
      ? result.notificationsPreferred
      : notificationsEnabled;
    updateNotificationsToggleUI();
    refreshStatusByFlags();
  } catch (error) {
    console.log('加载通知开关状态失败，使用默认值');
    notificationsEnabled = true;
    notificationsPreferred = true;
    updateNotificationsToggleUI();
    refreshStatusByFlags();
  }
}

async function saveNotificationsState(enabled) {
  try {
    await chrome.storage.sync.set({ notificationsEnabled: enabled });
  } catch (error) {
    console.log('保存通知开关状态失败:', error);
  }
}

async function saveNotificationsPreferred(preferred) {
  try {
    await chrome.storage.sync.set({ notificationsPreferred: preferred });
  } catch (error) {
    console.log('保存通知偏好失败:', error);
  }
}

function updateNotificationsToggleUI() {
  const notifBtn = document.getElementById('notif-btn');
  if (notifBtn) {
    // Controls 关闭时，禁用并强制显示为 off
    if (!crawlEnabled) {
      notifBtn.classList.add('off');
      notifBtn.classList.remove('on');
      notifBtn.classList.add('disabled');
      notifBtn.title = 'Enable Recording first';
      return;
    }
    // Controls 开启时，可用
    notifBtn.classList.remove('disabled');
    if (notificationsEnabled) {
      notifBtn.classList.add('on');
      notifBtn.classList.remove('off');
      notifBtn.title = 'Disable Notifications';
    } else {
      notifBtn.classList.add('off');
      notifBtn.classList.remove('on');
      notifBtn.title = 'Enable Notifications';
    }
  }
}

async function toggleNotifications() {
  // Controls 关闭时不可切换
  if (!crawlEnabled) return;
  notificationsEnabled = !notificationsEnabled;
  notificationsPreferred = notificationsEnabled; // 同步偏好
  updateNotificationsToggleUI();
  await saveNotificationsState(notificationsEnabled);
  await saveNotificationsPreferred(notificationsPreferred);
  refreshStatusByFlags();
}

// 主页面按钮事件
async function handleHomeClick() {
  // 跳转到主网页
  const config = await getConfig();
  const frontendUrl = `http://${config.FRONTEND_HOST}:${config.FRONTEND_PORT}/`;
  chrome.tabs.create({ url: frontendUrl });
}

// 关闭按钮事件
function handleCloseClick() {
  // 关闭当前popup窗口
  window.close();
}

// 默认配置
const DEFAULT_CONFIG = {
  API_HOST: "localhost",
  API_PORT: "8000",
  FRONTEND_HOST: "localhost", 
  FRONTEND_PORT: "3000"
};

// 从存储中获取配置，如果没有则使用默认配置
async function getConfig() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(DEFAULT_CONFIG, (config) => {
      resolve(config);
    });
  });
}

// ====== i18n ======
function getUILang() {
  try {
    const lang = chrome.i18n && chrome.i18n.getUILanguage ? chrome.i18n.getUILanguage() : (navigator.language || 'en');
    return (lang || '').toLowerCase().startsWith('zh') ? 'zh' : 'en';
  } catch (_) { return 'en'; }
}
const TEXT = {
  zh: {
    recording: '记录',
    notifications: '通知',
    domainAllowed: '✔',
    domainBlocked: '✖',
    toggleRecordingTitle: '记录开关',
    toggleNotificationsTitle: '通知开关'
  },
  en: {
    recording: 'Record',
    notifications: 'Notifications',
    domainAllowed: '✔',
    domainBlocked: '✖',
    toggleRecordingTitle: 'Toggle Recording',
    toggleNotificationsTitle: 'Toggle Notifications'
  }
};
function localizeUI() {
  const t = TEXT[getUILang()] || TEXT.en;
  const elR = document.getElementById('label-recording');
  const elN = document.getElementById('label-notifications');
  if (elR) elR.textContent = t.recording;
  if (elN) elN.textContent = t.notifications;
  const recBtn = document.getElementById('crawl-toggle-btn');
  const notifBtn = document.getElementById('notif-btn');
  if (recBtn) { recBtn.title = t.toggleRecordingTitle; recBtn.setAttribute('aria-label', t.toggleRecordingTitle); }
  if (notifBtn) { notifBtn.title = t.toggleNotificationsTitle; notifBtn.setAttribute('aria-label', t.toggleNotificationsTitle); }
}

// 页面初始化
document.addEventListener('DOMContentLoaded', async () => {
  // 获取爬取开关状态（会自动设置初始状态显示）
  await getCrawlStatus();
  
  // 获取悬浮球状态
  await getFloatingChatStatus();
  
  // 获取通知开关状态
  await loadNotificationsState();

  // 本地化标签
  try { localizeUI(); } catch (_) {}
  
  // 添加按钮事件监听 - logo和文字都可以点击打开主页
  const logoSection = document.getElementById('logo-section');
  if (logoSection) {
    logoSection.addEventListener('click', handleHomeClick);
  }
  
  // 添加爬取开关按钮事件
  const crawlToggleBtn = document.getElementById('crawl-toggle-btn');
  if (crawlToggleBtn) {
    crawlToggleBtn.addEventListener('click', toggleCrawl);
  }
  
  const closeBtn = document.getElementById('close-btn');
  if (closeBtn) {
    closeBtn.addEventListener('click', handleCloseClick);
  }
  
  // 添加悬浮球切换按钮事件
  const toggleSwitch = document.getElementById('toggle-switch');
  if (toggleSwitch) {
    toggleSwitch.addEventListener('click', toggleFloatingChat);
  }

  // 通知开关事件
  const notifBtn = document.getElementById('notif-btn');
  if (notifBtn) {
    notifBtn.addEventListener('click', toggleNotifications);
  }

  // 初始化域名 chip
  try { await initDomainChip(); } catch (_) {}
});

// ====== Domain chip ======
async function getActiveHostname() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  try {
    const url = new URL(tab.url);
    return (url.hostname || '').toLowerCase();
  } catch (_) {
    return '';
  }
}

async function initDomainChip() {
  const chip = document.getElementById('domain-chip');
  const chipIcon = document.getElementById('domain-chip-icon');
  const chipText = document.getElementById('domain-chip-text');
  if (!chip || !chipIcon || !chipText) return;

  const host = await getActiveHostname();
  chipText.textContent = host || 'unknown';
  // 保证可点击的交互体验
  try { chip.style.cursor = 'pointer'; chip.style.pointerEvents = 'auto'; chip.style.userSelect = 'none'; } catch (_) {}

  // 先与服务端同步一次本地黑名单
  try {
    await syncBlockedDomainsFromServer();
  } catch (_) {}

  const { blockedDomains = [] } = await new Promise((resolve) => {
    chrome.storage.sync.get({ blockedDomains: [] }, (res) => resolve(res || { blockedDomains: [] }));
  });
  const isBlocked = Array.isArray(blockedDomains) && blockedDomains.map(d=>String(d||'').toLowerCase()).includes(host);
  applyDomainChipUI(!isBlocked);
  try { chip.disabled = false; chip.removeAttribute('disabled'); chip.setAttribute('aria-disabled', 'false'); chip.setAttribute('tabindex', '0'); } catch (_) {}

  const handleChipClick = async () => {
    chip.disabled = true;
    try {
      const { blockedDomains: bds = [] } = await new Promise((resolve) => {
        chrome.storage.sync.get({ blockedDomains: [] }, (res) => resolve(res || { blockedDomains: [] }));
      });
      const list = Array.isArray(bds) ? [...bds] : [];
      const lowerList = list.map(d=>String(d||'').toLowerCase());
      const idx = lowerList.indexOf(host);

      if (idx >= 0) {
        // 阻止 -> 允许（服务端尽力删除，本地必定移除）
        try {
          const entries = await getServerBlacklist();
          if (entries && Array.isArray(entries)) {
            const toDelete = entries
              .filter(e => normalizeHostname(e?.url) === host)
              .map(e => e.id)
              .filter(id => Number.isFinite(id));

            for (const id of toDelete) {
              await new Promise((resolve) => {
                chrome.runtime.sendMessage({ type: 'URL_BLACKLIST_DELETE', id }, (resp) => resolve(resp));
              });
            }
          }
        } catch (_) {}

        list.splice(idx, 1);
        await new Promise((resolve) => chrome.storage.sync.set({ blockedDomains: list }, resolve));
        applyDomainChipUI(true);
      } else {
        // 允许 -> 阻止（服务端尽力新增，本地必定加入）
        const toUrl = host.includes('://') ? host : `https://${host}`;
        const resp = await new Promise((resolve) => {
          chrome.runtime.sendMessage({ type: 'URL_BLACKLIST_ADD', url: toUrl }, (r) => resolve(r || { ok: false }));
        });
        // 无论服务端是否成功，都先本地生效，确保“✖”后立即不再爬取
        if (!lowerList.includes(host)) list.push(host);
        await new Promise((resolve) => chrome.storage.sync.set({ blockedDomains: list }, resolve));
        applyDomainChipUI(false);
      }

      // 通知当前标签刷新爬取策略
      try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        await chrome.tabs.sendMessage(tab.id, { type: 'REFRESH_CRAWL_POLICY' });
      } catch (_) {}
    } finally {
      chip.disabled = false;
    }
  };
  chip.addEventListener('click', handleChipClick);

  function applyDomainChipUI(allowed) {
    const t = TEXT[getUILang()] || TEXT.en;
    chipIcon.textContent = allowed ? t.domainAllowed : t.domainBlocked;
    chip.style.opacity = allowed ? '1' : '0.5';
  }
}

// ====== Helpers for URL Blacklist API sync via background ======
function normalizeHostname(input) {
  try {
    const s = String(input || '').trim();
    if (!s) return '';
    // Try parse as full URL first
    try {
      const u = new URL(s);
      return (u.hostname || '').toLowerCase();
    } catch (_) {
      // Not a full URL; treat as hostname
      return s.toLowerCase();
    }
  } catch (_) {
    return '';
  }
}

async function getServerBlacklist() {
  const resp = await new Promise((resolve) => {
    chrome.runtime.sendMessage({ type: 'URL_BLACKLIST_LIST', limit: 1000, offset: 0 }, (r) => resolve(r || { ok: false, data: [] }));
  });
  if (resp && resp.ok && Array.isArray(resp.data)) return resp.data;
  return null; // 标记失败，避免上层误清空本地
}

async function syncBlockedDomainsFromServer() {
  try {
    const entries = await getServerBlacklist();
    if (!entries) return; // 仅在成功时覆盖本地，避免 404 时清空
    const hostnames = [...new Set(entries.map(e => normalizeHostname(e?.url)).filter(Boolean))];
    await new Promise((resolve) => chrome.storage.sync.set({ blockedDomains: hostnames }, resolve));
  } catch (_) {
    // ignore sync errors
  }
}