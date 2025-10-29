// background.js
// 引入配置文件
importScripts('config.js');

// 获取API URL的辅助函数
async function getApiUrl() {
    const config = await getConfig();
    return `http://${config.API_HOST}:${config.API_PORT}/api`;
}


chrome.runtime.onInstalled.addListener(() => {
  console.log('Extension installed');
  
  // 请求通知权限
  chrome.notifications.getPermissionLevel((level) => {
    if (level === 'denied') {
      console.log('通知权限被拒绝');
    } else {
      console.log('通知权限状态:', level);
    }
  });
  
  // 设置定时器，每30秒检查一次事件 
  chrome.alarms.create('checkEvents', { 
    delayInMinutes: 0.5, // 30秒后开始
    periodInMinutes: 0.5 // 每30秒执行一次
  });
});

// 监听定时器事件
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'checkEvents') {
    checkEventsAndNotify();
  }
});

// 获取事件数据并显示通知
async function checkEventsAndNotify() {
  try {
    const apiUrl = await getApiUrl();
    const response = await fetch(`${apiUrl}/events/fetch`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    console.log('获取到的事件数据:', data);
    
    if (data.code === 200 && data.data && data.data.events && data.data.events.length > 0) {
      // 有新事件，显示通知
      console.log(`发现 ${data.data.count} 个新事件`);
      for (const event of data.data.events) {
        console.log('处理事件:', event);
        await showEventNotification(event);
      }
    } else {
      console.log('没有新事件或数据格式不正确');
    }
  } catch (error) {
    console.error('获取事件数据失败:', error);
  }
}

// 显示事件通知
async function showEventNotification(event) {
  const notificationId = `event_${event.id || Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  // 根据事件类型生成不同的通知内容
  let title = '新事件提醒';
  let message = '您有新的重要事件需要关注';
  
  if (event.type === 'tip') {
    title = '💡 智能提示';
    message = event.data?.content || event.data?.message || event.data?.title || '您有新的智能提示';
  } else if (event.type === 'todo') {
    title = '📝 待办事项';
    message = event.data?.content || event.data?.message || event.data?.title || '您有新的待办事项';
  } else if (event.type === 'activity') {
    title = '🎯 活动通知';
    message = event.data?.content || event.data?.message || event.data?.title || '您有新的活动通知';
  } else if (event.type === 'report') {
    title = '📊 报告提醒';
    message = event.data?.content || event.data?.message || event.data?.title || '您有新的报告';
  } else if (event.type === 'system_status') {
    title = '⚙️ 系统状态';
    message = event.data?.content || event.data?.message || event.data?.title || '系统状态更新';
  } else {
    title = `📢 ${event.type || '事件通知'}`;
    message = event.data?.content || event.data?.message || event.data?.title || '您有新的重要事件需要关注';
  }
  
  const notificationOptions = {
    type: 'basic',
    iconUrl: 'icon.png',
    title: title,
    message: message,
    contextMessage: `LifeContxt | ${event.type} | ${new Date(event.datetime || Date.now()).toLocaleString('zh-CN')}`,
    priority: 2,
    requireInteraction: true,
    buttons: [
      { title: '查看详情' },
      { title: '稍后提醒' }
    ]
  };
  
  try {
    console.log('准备创建通知:', notificationId, notificationOptions);
    await chrome.notifications.create(notificationId, notificationOptions);
    console.log('通知已发送:', title, event);
  } catch (error) {
    console.error('发送通知失败:', error);
    console.error('通知选项:', notificationOptions);
    
    // 尝试创建简单的通知
    try {
      await chrome.notifications.create(`simple_${Date.now()}`, {
        type: 'basic',
        iconUrl: 'icon.png',
        title: 'LifeContxt 简单测试',
        message: '这是一个简单的测试通知',
        contextMessage: 'LifeContxt'
      });
      console.log('简单通知创建成功');
    } catch (simpleError) {
      console.error('简单通知也创建失败:', simpleError);
    }
  }
}

// 处理通知点击事件
chrome.notifications.onClicked.addListener((notificationId) => {
  console.log('通知被点击:', notificationId);
  
  // 关闭通知
  chrome.notifications.clear(notificationId);
  
  // 可以在这里添加更多处理逻辑，比如打开特定页面
  // chrome.tabs.create({ url: 'https://example.com' });
});

// 处理通知按钮点击事件
chrome.notifications.onButtonClicked.addListener((notificationId, buttonIndex) => {
  console.log('通知按钮被点击:', notificationId, '按钮索引:', buttonIndex);
  
  if (buttonIndex === 0) {
    // 查看详情
    console.log('用户选择查看详情');
    // 可以打开详情页面或执行其他操作
  } else if (buttonIndex === 1) {
    // 稍后提醒
    console.log('用户选择稍后提醒');
    // 可以设置延迟提醒
    setTimeout(() => {
      chrome.notifications.create(`reminder_${Date.now()}`, {
        type: 'basic',
        iconUrl: 'icon.png',
        title: 'LifeContxt 提醒',
        message: '您之前选择稍后提醒的事件',
        contextMessage: 'LifeContxt',
        priority: 1
      });
    }, 5 * 60 * 1000); // 5分钟后提醒
  }
  
  // 关闭原通知
  chrome.notifications.clear(notificationId);
});

// 可以接收来自 content 或 popup 的消息（现在 popup 直接监听了）
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'SCRAPED_DATA') {
    console.log('Received scraped data from content', message.data);
  } else if (message.type === 'CHECK_EVENTS') {
    // 手动触发事件检查
    console.log('手动触发事件检查');
    checkEventsAndNotify();
    sendResponse({ success: true });
  }
});

// 代理内容脚本的上传请求，避免 HTTPS 页面上的混合内容限制
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'UPLOAD_WEB_DATA') {
    (async () => {
      const apiUrl = await getApiUrl();
      const url = `${apiUrl}/upload_web_data`;
      try {
        const resp = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(message.payload)
        });
        const data = await resp.json().catch(() => null);
        sendResponse({ ok: true, data, status: resp.status, corsFallback: false });
      } catch (err) {
        // 若为 CORS/预检失败，降级使用 no-cors，让数据尽量送达
        try {
          await fetch(url, {
            method: 'POST',
            mode: 'no-cors',
            headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
            body: JSON.stringify(message.payload)
          });
          // no-cors 无法读取响应，但数据已发出
          sendResponse({ ok: true, data: null, status: null, corsFallback: true });
        } catch (e2) {
          sendResponse({ ok: false, error: String(e2) });
        }
      }
    })();
    return true; // 异步响应
  }
});

// 代理聊天消息请求，避免 HTTPS 页面上的混合内容限制
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'SEND_CHAT_MESSAGE') {
    (async () => {
      const apiUrl = await getApiUrl();
      const url = `${apiUrl}/agent/chat`;
      try {
        const resp = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(message.payload)
        });
        const data = await resp.json().catch(() => null);
        sendResponse({ ok: true, data, status: resp.status, corsFallback: false });
      } catch (err) {
        // 若为 CORS/预检失败，降级使用 no-cors，让数据尽量送达
        try {
          await fetch(url, {
            method: 'POST',
            mode: 'no-cors',
            headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
            body: JSON.stringify(message.payload)
          });
          // no-cors 无法读取响应，但数据已发出
          sendResponse({ ok: true, data: null, status: null, corsFallback: true });
        } catch (e2) {
          sendResponse({ ok: false, error: String(e2) });
        }
      }
    })();
    return true; // 异步响应
  }
});

// 代理流式聊天消息请求
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'SEND_STREAM_CHAT_MESSAGE') {
    (async () => {
      const apiUrl = await getApiUrl();
      const url = `${apiUrl}/agent/chat/stream`;
      try {
        const resp = await fetch(url, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
          },
          body: JSON.stringify(message.payload)
        });
        
        if (!resp.ok) {
          throw new Error(`HTTP error! status: ${resp.status}`);
        }
        
        // 处理流式响应
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // 保留最后一个不完整的行
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  // 发送流式数据到内容脚本
                  chrome.tabs.sendMessage(sender.tab.id, {
                    type: 'STREAM_CHUNK',
                    data: data
                  });
                } catch (e) {
                  // 忽略解析错误
                }
              }
            }
          }
        } finally {
          reader.releaseLock();
        }
        
        sendResponse({ ok: true, data: null, status: resp.status, corsFallback: false });
      } catch (err) {
        // 如果流式请求失败，回退到普通请求
        try {
          const fallbackUrl = `${apiUrl}/agent/chat`;
          const resp = await fetch(fallbackUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(message.payload)
          });
          const data = await resp.json().catch(() => null);
          // 适配新的数据格式
          sendResponse({ ok: true, data: data, status: resp.status, corsFallback: false });
        } catch (e2) {
          sendResponse({ ok: false, error: String(e2) });
        }
      }
    })();
    return true; // 异步响应
  }
});