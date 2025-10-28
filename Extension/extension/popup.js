// 弹窗状态管理
let currentStatus = 'success'; // 'success', 'crawling', 'error'
let floatingChatEnabled = true;

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
    if (message.data && message.data.payload) {
      const { title, url } = message.data.payload;
      const isIncremental = message.data.isIncremental;
      
      if (message.data.serverResponse && message.data.serverResponse.ok) {
        updateStatus('success', 'Page remembered', 'Successfully added to memory');
      } else {
        updateStatus('error', 'Failed to remember', message.data.serverResponse?.error || 'Unknown error');
      }
    } else if (message.data && message.data.error) {
      updateStatus('error', 'Crawl error', message.data.error);
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
  // 初始化状态显示
  updateStatus('success', 'Page remembered', 'Successfully added to memory');
  
  // 获取悬浮球状态
  await getFloatingChatStatus();
  
  // 添加按钮事件监听
  const homeBtn = document.getElementById('home-btn');
  if (homeBtn) {
    homeBtn.addEventListener('click', handleHomeClick);
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
  
  // 模拟初始爬取状态
  setTimeout(() => {
    updateStatus('crawling', 'Crawling page...', 'Analyzing content');
  }, 1000);
  
  // 模拟成功状态
  setTimeout(() => {
    updateStatus('success', 'Page remembered', 'Successfully added to memory');
  }, 3000);
});