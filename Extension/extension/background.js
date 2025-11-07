// background.js
// 引入配置文件
importScripts('config.js');

// 获取API URL的辅助函数
async function getApiUrl() {
    const config = await getConfig();
    return `http://${config.API_HOST}:${config.API_PORT}/api`;
}

// 打开前端主页并确保窗口被唤起
async function openFrontendPage() {
  try {
    const cfg = await getConfig();
    const frontendUrl = `http://${cfg.FRONTEND_HOST}:${cfg.FRONTEND_PORT}/`;

    // 查询现有窗口
    chrome.windows.getAll({ populate: false }, (wins) => {
      const hasWindow = Array.isArray(wins) && wins.length > 0;
      if (!hasWindow) {
        // 没有任何窗口时创建新窗口
        chrome.windows.create({ url: frontendUrl, focused: true, state: 'maximized' });
        return;
      }

      // 使用最近聚焦的窗口
      chrome.windows.getLastFocused((last) => {
        const targetWindowId = last && last.id ? last.id : wins[0].id;
        try {
          chrome.tabs.create({ windowId: targetWindowId, url: frontendUrl, active: true }, () => {
            // 唤起并聚焦窗口
            chrome.windows.update(targetWindowId, { focused: true, state: 'normal' });
          });
        } catch (_) {
          // 回退：直接创建新窗口
          chrome.windows.create({ url: frontendUrl, focused: true, state: 'normal' });
        }
      });
    });
  } catch (e) {
    // 兜底：使用默认地址
    try {
      chrome.windows.create({ url: 'http://localhost:3000/', focused: true, state: 'normal' });
    } catch (_) {}
  }
}

// 主总开关（Controls）- 使用 crawlEnabled 作为插件全局开关
async function isPluginEnabled() {
  try {
    const result = await new Promise((resolve) => {
      chrome.storage.sync.get({ crawlEnabled: true }, (cfg) => resolve(cfg));
    });
    return result.crawlEnabled !== false;
  } catch (_) {
    return true; // 默认开启
  }
}

// 读取通知开关
async function areNotificationsEnabled() {
  try {
    const result = await new Promise((resolve) => {
      chrome.storage.sync.get({ notificationsEnabled: true }, (cfg) => resolve(cfg));
    });
    return result.notificationsEnabled !== false;
  } catch (_) {
    return true; // 默认开启
  }
}


// 语言与文案
function getLocale() {
  try {
    const lang = (chrome && chrome.i18n && typeof chrome.i18n.getUILanguage === 'function')
      ? chrome.i18n.getUILanguage()
      : (navigator.language || 'en');
    return (lang || '').toLowerCase().startsWith('zh') ? 'zh' : 'en';
  } catch (e) {
    return 'en';
  }
}

const I18N = {
  zh: {
    genericTitle: '新事件提醒',
    genericMessage: '您有新的重要事件需要关注',
    listMessage: (count) => `您有 ${count} 条新的智能提示`,
    tipTitle: (count) => `您有 ${count} 条新的智能提示`,
    tipMessageFallback: '您有新的智能提示',
    todoTitle: '📝 待办事项',
    todoMessageFallback: '您有新的待办事项',
    activityTitle: '🎯 活动通知',
    activityMessageFallback: '您有新的活动通知',
    reportTitle: '📊 报告提醒',
    reportMessageFallback: '您有新的报告',
    systemStatusTitle: '⚙️ 系统状态',
    systemStatusMessageFallback: '系统状态更新',
    defaultTitle: (type) => `📢 ${type || '事件通知'}`,
    defaultMessageFallback: '您有新的重要事件需要关注',
    viewDetails: '查看详情',
    remindLater: '稍后提醒',
    simpleTestTitle: 'LifeContext 简单测试',
    simpleTestMessage: '这是一个简单的测试通知',
    reminderTitle: 'LifeContext 提醒',
    reminderMessage: '您之前选择稍后提醒的事件',
    dateLocale: 'zh-CN'
  },
  en: {
    genericTitle: 'New Event',
    genericMessage: 'You have new important updates',
    listMessage: (count) => `You have ${count} new tips`,
    tipTitle: (count) => `You have ${count} new tips`,
    tipMessageFallback: 'You have new tips',
    todoTitle: '📝 Todo',
    todoMessageFallback: 'You have a new todo',
    activityTitle: '🎯 Activity',
    activityMessageFallback: 'You have a new activity notification',
    reportTitle: '📊 Report',
    reportMessageFallback: 'You have a new report',
    systemStatusTitle: '⚙️ System Status',
    systemStatusMessageFallback: 'System status updated',
    defaultTitle: (type) => `📢 ${type || 'Event'}`,
    defaultMessageFallback: 'You have new important updates',
    viewDetails: 'View details',
    remindLater: 'Remind me later',
    simpleTestTitle: 'LifeContext Simple Test',
    simpleTestMessage: 'This is a simple test notification',
    reminderTitle: 'LifeContext Reminder',
    reminderMessage: 'Reminder for a previously deferred event',
    dateLocale: 'en-US'
  }
};


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
    // 需要 Controls 和 Notifications 同时开启
    const [pluginOn, notifOn] = await Promise.all([
      isPluginEnabled(),
      areNotificationsEnabled()
    ]);
    if (!pluginOn || !notifOn) {
      return;
    }
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
    
    if (data.code === 200 && data.data && Array.isArray(data.data.events) && data.data.events.length > 0) {
      // 有新事件，显示通知
      console.log(`发现 ${data.data.count} 个新事件`);
      for (const event of data.data.events) {
        console.log('处理事件:', event);
        await showEventNotification(event);
      }
    } else if (data.code === 200 && data.data && Array.isArray(data.data.events)) {
      console.log(`没有新事件（count=${data.data.count || 0}）`);
    } else {
      console.log('数据格式不正确:', data);
    }
  } catch (error) {
    console.error('获取事件数据失败:', error);
  }
}

// 显示事件通知
async function showEventNotification(event) {
  const notificationId = `event_${event.id || Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const locale = getLocale();
  const t = I18N[locale] || I18N.en;
    // 若为智能提示，且后端提供 tips 列表，则使用列表型通知展示每条标题
    const tipTitles = (event.type === 'tip' && event.data && Array.isArray(event.data.tips))
    ? event.data.tips.map(t => String(t?.title || '').trim()).filter(Boolean)
    : null;
  const tipsCount = event?.data?.count ?? (tipTitles ? tipTitles.length : 0);

  // 根据事件类型生成不同的通知内容
  let title = t.genericTitle;
  let message = t.genericMessage;
  
  if (event.type === 'tip') {
    title = t.tipTitle(tipsCount);
    message = event.data?.content || event.data?.message || event.data?.title || t.tipMessageFallback;
  } else if (event.type === 'todo') {
    title = t.todoTitle;
    message = event.data?.content || event.data?.message || event.data?.title || t.todoMessageFallback;
  } else if (event.type === 'activity') {
    title = t.activityTitle;
    message = event.data?.content || event.data?.message || event.data?.title || t.activityMessageFallback;
  } else if (event.type === 'report') {
    title = t.reportTitle;
    message = event.data?.content || event.data?.message || event.data?.title || t.reportMessageFallback;
  } else if (event.type === 'system_status') {
    title = t.systemStatusTitle;
    message = event.data?.content || event.data?.message || event.data?.title || t.systemStatusMessageFallback;
  } else {
    title = (typeof t.defaultTitle === 'function') ? t.defaultTitle(event.type) : t.genericTitle;
    message = event.data?.content || event.data?.message || event.data?.title || t.defaultMessageFallback;
  }
  

  let notificationOptions;
  if (tipTitles && tipTitles.length > 0) {
    const items = tipTitles.slice(0, 5).map((t, idx) => ({ title: `${idx + 1}.`, message: t }));
    notificationOptions = {
      type: 'list',
      iconUrl: 'icon.png',
      title: title,
      message: t.listMessage(tipsCount),
      items: items,
      contextMessage: `LifeContext | ${event.type} | ${new Date(event.datetime || Date.now()).toLocaleString(t.dateLocale)}`,
      priority: 2,
      requireInteraction: true,
      buttons: [
        { title: t.viewDetails },
        { title: t.remindLater }
      ]
    };
  } else {
    if (event.type === 'tip' && tipsCount > 0) {
      message = t.listMessage(tipsCount);
    }
    notificationOptions = {
      type: 'basic',
      iconUrl: 'icon.png',
      title: title,
      message: message,
      contextMessage: `LifeContext | ${event.type} | ${new Date(event.datetime || Date.now()).toLocaleString(t.dateLocale)}`,
      priority: 2,
      requireInteraction: true,
      buttons: [
        { title: t.viewDetails },
        { title: t.remindLater }
      ]
    };
  }
  
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

        title: t.simpleTestTitle,
        message: t.simpleTestMessage,
        contextMessage: 'LifeContext'

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
  
  // 默认点击也跳转到主页并唤起浏览器
  (async () => {
    try {
      await openFrontendPage();
    } catch (e) {
      console.error('处理通知点击跳转失败:', e);
    }
  })();
});

// 处理通知按钮点击事件
chrome.notifications.onButtonClicked.addListener((notificationId, buttonIndex) => {
  console.log('通知按钮被点击:', notificationId, '按钮索引:', buttonIndex);
  
  if (buttonIndex === 0) {
    // 查看详情 - 跳转到主页面并确保浏览器被唤起
    console.log('用户选择查看详情，跳转到主页面');
    (async () => {
      try {
        await openFrontendPage();
      } catch (error) {
        console.error('跳转到主页面失败:', error);
      }
    })();
  } else if (buttonIndex === 1) {
    // 稍后提醒 - 3分钟后重新提醒
    console.log('用户选择稍后提醒，3分钟后重新提醒');

    setTimeout(() => {
      (async () => {
        const [pluginOn, notifOn] = await Promise.all([
          isPluginEnabled(),
          areNotificationsEnabled()
        ]);
        if (!pluginOn || !notifOn) return;
        const locale = getLocale();
        const t = I18N[locale] || I18N.en;
        chrome.notifications.create(`reminder_${Date.now()}`, {
          type: 'basic',
          iconUrl: 'icon.png',

          title: t.reminderTitle,
          message: t.reminderMessage,
          contextMessage: 'LifeContext',
          priority: 1,
          buttons: [
            { title: t.viewDetails },
            { title: t.remindLater }
          ]
        });
      })();
    }, 30 * 1000); // 3分钟后提醒

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