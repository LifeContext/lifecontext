// 弹窗状态管理
let currentStatus = 'success'; // 'success', 'crawling', 'error'
let floatingChatEnabled = true;
let crawlEnabled = true; // 爬取开关，默认开启

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
          updateStatus('success', 'Remembering...', 'Page content saved');
        } else {
          updateStatus('error', 'Save Failed', message.data.serverResponse?.error || 'Unknown error');
        }
      } else if (message.data && message.data.error) {
        updateStatus('error', 'Crawl Error', message.data.error);
      }
    }
  }
});

// 更新状态显示
function updateStatus(status, mainText, subText) {
  currentStatus = status;
  
  const statusBox = document.getElementById('status-box');
  const statusMain = document.getElementById('status-main');
  const statusSub = document.getElementById('status-sub');
  
  if (statusBox) {
    statusBox.className = 'status-box';
    if (status === 'crawling') {
      statusBox.classList.add('crawling');
    } else if (status === 'error') {
      statusBox.classList.add('error');
    } else if (status === 'disabled') {
      statusBox.classList.add('disabled');
    }
  }
  
  if (statusMain) {
    statusMain.textContent = mainText;
  }
  
  if (statusSub) {
    statusSub.textContent = subText;
  }
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
  
  // 更新状态显示
  if (crawlEnabled) {
    updateStatus('success', 'Remembering...', 'Saving page content');
  } else {
    updateStatus('disabled', 'Memory Disabled', 'Page saving stopped');
  }
  
  // 保存到存储
  await saveCrawlState(crawlEnabled);
  
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
    const icon = crawlToggleBtn.querySelector('.crawl-icon');
    const iconStatic = crawlToggleBtn.querySelector('.crawl-icon-static');
    
    if (crawlEnabled) {
      crawlToggleBtn.classList.add('enabled');
      crawlToggleBtn.title = 'Disable Memory';
      // 显示启用图标
      if (icon) icon.style.display = 'block';
      if (iconStatic) iconStatic.style.display = 'none';
    } else {
      crawlToggleBtn.classList.remove('enabled');
      crawlToggleBtn.title = 'Enable Memory';
      // 显示静态图标
      if (icon) icon.style.display = 'none';
      if (iconStatic) iconStatic.style.display = 'block';
    }
  }
}

// 获取爬取状态
async function getCrawlStatus() {
  // 从存储中加载状态
  await loadCrawlState();
  
  // 根据爬取状态更新显示
  if (crawlEnabled) {
    updateStatus('success', 'Remembering...', 'Saving page content');
  } else {
    updateStatus('disabled', 'Memory Disabled', 'Page saving stopped');
  }
  
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
  // 更新状态显示
  if (crawlEnabled) {
    updateStatus('success', 'Remembering...', 'Saving page content');
  } else {
    updateStatus('disabled', 'Memory Disabled', 'Page saving stopped');
  }
      }
    }
  } catch (error) {
    // Content script未加载，使用存储中的状态
    console.log('Content script未加载，使用存储状态');
  }
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

// 页面初始化
document.addEventListener('DOMContentLoaded', async () => {
  // 获取爬取开关状态（会自动设置初始状态显示）
  await getCrawlStatus();
  
  // 获取悬浮球状态
  await getFloatingChatStatus();
  
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
});