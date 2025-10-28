// 自动爬取状态显示
let crawlCount = 0;
let lastCrawlTime = null;
let domObserverEnabled = true;
let domObserverStatus = null;
let currentCrawlStatus = 'initializing'; // 'initializing', 'crawling', 'success', 'error'

// 接收 content 发来的消息
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'SCRAPED_DATA') {
    crawlCount++;
    lastCrawlTime = new Date().toLocaleTimeString();
    
    if (message.data && message.data.payload) {
      const { title, url } = message.data.payload;
      const isIncremental = message.data.isIncremental;
      
      if (message.data.serverResponse && message.data.serverResponse.ok) {
        const crawlType = isIncremental ? '增量爬取' : '初始爬取';
        updateCrawlStatus('success', `${crawlType}成功`, title);
      } else {
        updateCrawlStatus('error', '爬取失败', message.data.serverResponse?.error || '未知错误');
      }
    } else if (message.data && message.data.error) {
      updateCrawlStatus('error', '爬取错误', message.data.error);
    }
    
    // 更新统计信息
    updateStats();
  }
});

// 更新爬取状态显示
function updateCrawlStatus(status, message, details = '') {
  currentCrawlStatus = status;
  
  const indicator = document.getElementById('status-indicator');
  const statusMessage = document.getElementById('status-message');
  const statusDetails = document.getElementById('status-details');
  
  if (indicator) {
    indicator.className = 'status-indicator';
    if (status === 'crawling') {
      indicator.classList.add('crawling');
    } else if (status === 'success') {
      indicator.classList.add('success');
    } else if (status === 'error') {
      indicator.classList.add('error');
    }
  }
  
  if (statusMessage) {
    statusMessage.textContent = message;
  }
  
  if (statusDetails) {
    statusDetails.textContent = details;
  }
}

// 更新统计信息
function updateStats() {
  const statsElement = document.getElementById('stats');
  if (statsElement) {
    const domStatus = domObserverStatus ? 
      `DOM监听: ${domObserverStatus.isObserving ? '✅ 启用' : '❌ 禁用'}` : 
      'DOM监听: 未知';
    
    statsElement.innerHTML = `
      <div style="margin: 0 15px 15px 15px; padding: 16px; background: #1e293b; border-radius: 16px; border: 1px solid rgba(71, 85, 105, 0.5); font-size: 12px;">
        <strong style="color: #f1f5f9;">爬取统计:</strong><br>
        <span style="color: #cbd5e1;">总爬取次数: ${crawlCount}</span><br>
        <span style="color: #cbd5e1;">最后爬取: ${lastCrawlTime || '无'}</span><br>
        <span style="color: #94a3b8;">${domStatus}</span>
      </div>
    `;
  }
}

// DOM监听器控制函数
async function toggleDOMObserver() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: 'TOGGLE_DOM_OBSERVER',
      enabled: domObserverEnabled
    });
    
    if (response && response.success) {
      domObserverEnabled = !domObserverEnabled;
      updateDOMObserverUI();
      console.log(`DOM监听器已${domObserverEnabled ? '启用' : '禁用'}`);
    }
  } catch (error) {
    console.error('切换DOM监听器失败:', error);
  }
}

// 更新DOM监听器状态
async function updateDOMObserverStatus() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: 'GET_DOM_STATUS'
    });
    
    if (response) {
      domObserverStatus = response;
      domObserverEnabled = response.isObserving;
      updateDOMObserverUI();
    }
  } catch (error) {
    console.error('获取DOM监听器状态失败:', error);
  }
}

// 更新DOM监听器UI
function updateDOMObserverUI() {
  const toggleBtn = document.getElementById('toggleDOMObserver');
  if (toggleBtn) {
    toggleBtn.textContent = domObserverEnabled ? '禁用DOM监听' : '启用DOM监听';
    toggleBtn.className = domObserverEnabled ? 'btn btn-warning' : 'btn btn-success';
  }
  
  updateStats();
}

// 主页面按钮事件
function handleHomeClick() {
  // 跳转到主网页
  chrome.tabs.create({ url: 'http://192.168.22.24:3000/' });
}

// 关闭按钮事件
function handleCloseClick() {
  // 关闭当前popup窗口
  window.close();
}

// 手动触发爬取
async function triggerManualCrawl() {
  try {
    updateCrawlStatus('crawling', '正在爬取...', '手动触发页面内容爬取');
    
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: 'MANUAL_CRAWL'
    });
    
    if (response && response.success) {
      console.log('手动爬取已触发');
    } else {
      updateCrawlStatus('error', '爬取失败', response?.error || '未知错误');
    }
  } catch (error) {
    console.error('手动爬取失败:', error);
    updateCrawlStatus('error', '爬取失败', error.message);
  }
}

// 测试桌面通知
document.getElementById('testNotification').addEventListener('click', async () => {
  try {
    await chrome.notifications.create('test_notification', {
      type: 'basic',
      iconUrl: 'icon.png',
      title: '🔔 测试通知',
      message: '这是一个测试通知，验证桌面弹窗功能是否正常工作！',
      contextMessage: 'LifeContxt 测试',
      priority: 2,
      requireInteraction: true,
      buttons: [
        { title: '查看详情' },
        { title: '稍后提醒' }
      ]
    });
    console.log('测试通知已发送');
  } catch (error) {
    console.error('发送测试通知失败:', error);
    alert('发送测试通知失败: ' + error.message);
  }
});

// 创建测试事件
document.getElementById('createTestEvent').addEventListener('click', async () => {
  try {
    const response = await fetch('http://192.168.22.111:8000/api/events/publish', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        event_type: 'tip',
        data: {
          title: '扩展测试事件',
          message: '这是一个通过扩展创建的测试事件，用于验证通知功能！'
        }
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('测试事件创建成功:', result);
      alert('测试事件创建成功！请等待30秒内收到通知。');
    } else {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  } catch (error) {
    console.error('创建测试事件失败:', error);
    alert('创建测试事件失败: ' + error.message);
  }
});

// 手动检查事件
document.getElementById('checkEvents').addEventListener('click', async () => {
  try {
    const response = await chrome.runtime.sendMessage({ type: 'CHECK_EVENTS' });
    console.log('手动检查事件响应:', response);
    alert('已触发事件检查，请查看控制台日志和桌面通知');
  } catch (error) {
    console.error('手动检查事件失败:', error);
    alert('手动检查事件失败: ' + error.message);
  }
});

// 测试通知权限
document.getElementById('testPermission').addEventListener('click', async () => {
  try {
    // 检查通知权限
    const permission = await new Promise((resolve) => {
      chrome.notifications.getPermissionLevel(resolve);
    });
    
    console.log('当前通知权限:', permission);
    
    if (permission === 'granted') {
      // 创建测试通知
      await chrome.notifications.create('permission_test', {
        type: 'basic',
        iconUrl: 'icon.png',
        title: '🔧 权限测试',
        message: '通知权限正常！如果您看到这个通知，说明权限配置正确。',
        contextMessage: 'LifeContxt'
      });
      alert('通知权限正常，测试通知已发送！');
    } else {
      alert(`通知权限问题：${permission}\n请检查浏览器设置中的通知权限。`);
    }
  } catch (error) {
    console.error('测试通知权限失败:', error);
    alert('测试通知权限失败: ' + error.message);
  }
});

// 页面加载时显示当前状态
document.addEventListener('DOMContentLoaded', () => {
  // 初始化状态显示
  updateCrawlStatus('initializing', '正在初始化...', '准备开始爬取页面内容');
  
  // 初始化DOM监听器状态
  updateDOMObserverStatus();
  
  // 添加按钮事件监听
  const homeBtn = document.getElementById('home-btn');
  if (homeBtn) {
    homeBtn.addEventListener('click', handleHomeClick);
  }
  
  const closeBtn = document.getElementById('close-btn');
  if (closeBtn) {
    closeBtn.addEventListener('click', handleCloseClick);
  }
  
  // 添加DOM监听器切换按钮事件
  const toggleBtn = document.getElementById('toggleDOMObserver');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', toggleDOMObserver);
  }
  
  updateStats();
  
  // 添加手动爬取功能（双击状态框触发）
  const statusBox = document.querySelector('.status-box');
  if (statusBox) {
    statusBox.addEventListener('dblclick', triggerManualCrawl);
    statusBox.style.cursor = 'pointer';
    statusBox.title = '双击手动触发爬取';
  }
  
  // 模拟初始爬取状态
  setTimeout(() => {
    updateCrawlStatus('crawling', '正在爬取...', '自动检测页面内容变化');
  }, 1000);
});
