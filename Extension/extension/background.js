// background.js
// 引入配置文件
importScripts('config.js');

// 获取API URL的辅助函数
async function getApiUrl() {
    const config = await getConfig();
    return `http://${config.API_HOST}:${config.API_PORT}/api`;
}

// ================= Prompt Language sync =================
const PROMPT_LANG_ALARM = 'sendPromptLanguage';

function getBrowserPromptLanguage() {
  try {
    const lang = (chrome && chrome.i18n && typeof chrome.i18n.getUILanguage === 'function')
      ? chrome.i18n.getUILanguage()
      : (navigator.language || 'en');
    return (lang || '').toLowerCase().startsWith('zh') ? 'zh' : 'en';
  } catch (_) {
    return 'en';
  }
}

async function trySendPromptLanguage() {
  try {
    const flags = await new Promise((resolve) => {
      chrome.storage.sync.get({ promptLanguageSent: false }, (res) => resolve(res));
    });
    if (flags.promptLanguageSent) return true;
    const apiUrl = await getApiUrl();
    const payload = { prompt_language: getBrowserPromptLanguage() };
    const resp = await fetch(`${apiUrl}/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (resp && resp.ok) {
      await new Promise((resolve) => chrome.storage.sync.set({ promptLanguageSent: true }, resolve));
      chrome.alarms.clear(PROMPT_LANG_ALARM);
      return true;
    }
  } catch (_) {}
  return false;
}

function ensurePromptLanguageAlarm() {
  chrome.storage.sync.get({ promptLanguageSent: false }, (res) => {
    if (!res.promptLanguageSent) {
      // 立即尝试一次
      trySendPromptLanguage();
      // 1 分钟重试一次
      chrome.alarms.create(PROMPT_LANG_ALARM, { delayInMinutes: 0.1, periodInMinutes: 1 });
    }
  });
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
  try {
    if (chrome.notifications && typeof chrome.notifications.getPermissionLevel === 'function') {
      chrome.notifications.getPermissionLevel((level) => {
        if (level === 'denied') {
          console.log('通知权限被拒绝');
        } else {
          console.log('通知权限状态:', level);
        }
      });
    }
  } catch (_) {}
  
  // 设置定时器，每30秒检查一次事件 
  chrome.alarms.create('checkEvents', { 
    delayInMinutes: 0.5, // 30秒后开始
    periodInMinutes: 0.5 // 每30秒执行一次
  });

  // 安装后同步 prompt_language（重试直到成功）
  ensurePromptLanguageAlarm();
});

// 监听定时器事件
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'checkEvents') {
    checkEventsAndNotify();
  } else if (alarm.name === PROMPT_LANG_ALARM) {
    trySendPromptLanguage();
  }
});

// ===== URL 黑名单：集中在后台代理，统一 API 基址与 CORS 处理 =====
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'URL_BLACKLIST_ADD') {
    (async () => {
      try {
        const apiUrl = await getApiUrl(); // 形如 http://host:port/api
        const resp = await fetch(`${apiUrl}/url-blacklist`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: message.url })
        });
        let data = null;
        try { data = await resp.json(); } catch (_) {}
        sendResponse({ ok: resp.status === 201, status: resp.status, data });
      } catch (e) {
        sendResponse({ ok: false, error: String(e) });
      }
    })();
    return true;
  }
  if (message.type === 'URL_BLACKLIST_DELETE') {
    (async () => {
      try {
        const apiUrl = await getApiUrl();
        const resp = await fetch(`${apiUrl}/url-blacklist/${message.id}`, { method: 'DELETE' });
        let data = null;
        try { data = await resp.json(); } catch (_) {}
        const ok = resp.status === 200 || resp.status === 404;
        sendResponse({ ok, status: resp.status, data });
      } catch (e) {
        sendResponse({ ok: false, error: String(e) });
      }
    })();
    return true;
  }
  if (message.type === 'URL_BLACKLIST_LIST') {
    (async () => {
      try {
        const apiUrl = await getApiUrl();
        const limit = Number.isFinite(message.limit) && message.limit > 0 ? message.limit : 1000;
        const offset = Number.isFinite(message.offset) && message.offset >= 0 ? message.offset : 0;
        const resp = await fetch(`${apiUrl}/url-blacklist?limit=${limit}&offset=${offset}`);
        const data = await resp.json().catch(() => []);
        sendResponse({ ok: resp.ok, status: resp.status, data });
      } catch (e) {
        sendResponse({ ok: false, error: String(e) });
      }
    })();
    return true;
  }
});
// 浏览器启动时也确保重试存在
chrome.runtime.onStartup.addListener(() => {
  ensurePromptLanguageAlarm();
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
  if (!chrome.notifications || typeof chrome.notifications.create !== 'function') {
    console.warn('通知 API 不可用或未授予权限，跳过通知。');
    return;
  }
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
      iconUrl: 'logo.png',
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
      iconUrl: 'logo.png',
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
        iconUrl: 'logo.png',

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

// 处理通知点击事件（在 API 可用时才注册）
if (chrome.notifications && chrome.notifications.onClicked) {
  chrome.notifications.onClicked.addListener((notificationId) => {
    console.log('通知被点击:', notificationId);
    try { chrome.notifications.clear(notificationId); } catch (_) {}
    (async () => {
      try { await openFrontendPage(); } catch (e) { console.error('处理通知点击跳转失败:', e); }
    })();
  });
}

// 处理通知按钮点击事件（在 API 可用时才注册）
if (chrome.notifications && chrome.notifications.onButtonClicked) {
  chrome.notifications.onButtonClicked.addListener((notificationId, buttonIndex) => {
    console.log('通知按钮被点击:', notificationId, '按钮索引:', buttonIndex);
    if (buttonIndex === 0) {
      console.log('用户选择查看详情，跳转到主页面');
      (async () => { try { await openFrontendPage(); } catch (error) { console.error('跳转到主页面失败:', error); } })();
    } else if (buttonIndex === 1) {
      console.log('用户选择稍后提醒，3分钟后重新提醒');
      setTimeout(() => {
        (async () => {
          const [pluginOn, notifOn] = await Promise.all([ isPluginEnabled(), areNotificationsEnabled() ]);
          if (!pluginOn || !notifOn) return;
          const locale = getLocale();
          const t = I18N[locale] || I18N.en;
          try {
            if (chrome.notifications && chrome.notifications.create) {
              chrome.notifications.create(`reminder_${Date.now()}`, {
                type: 'basic',
                iconUrl: 'logo.png',
                title: t.reminderTitle,
                message: t.reminderMessage,
                contextMessage: 'LifeContext',
                priority: 1,
                buttons: [ { title: t.viewDetails }, { title: t.remindLater } ]
              });
            }
          } catch (_) {}
        })();
      }, 30 * 1000);
    }
    try { chrome.notifications.clear(notificationId); } catch (_) {}
  });
}

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

// ✅ 兼容旧消息调用
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'SEND_STREAM_CHAT_MESSAGE') {
    try { sendResponse({ ok: true, usePort: true }); } catch (_) {}
    return;
  }
});

// ✅ Port 持久通道：支持流式聊天
chrome.runtime.onConnect.addListener((port) => {
  if (port.name !== 'STREAM_CHAT') return;

  let disconnected = false;
  port.onDisconnect.addListener(() => { disconnected = true; });

  port.onMessage.addListener(async (msg) => {
    if (!msg || msg.action !== 'start' || disconnected) return;
    const payload = msg.payload || {};
    const apiUrl = await getApiUrl();
    const url = `${apiUrl}/agent/chat/stream`;

    try {
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
        body: JSON.stringify(payload)
      });
      if (!resp.ok) throw new Error(`HTTP error! status: ${resp.status}`);

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          if (disconnected || !port.sender) break;
          const { done, value } = await reader.read();
          if (done) break;
          console.log('🔹 Read chunk', value?.length, new TextDecoder().decode(value || new Uint8Array()));

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith('data:')) continue;

            try {
              const jsonText = trimmed.replace(/^data:\s*/, '').trim();
              if (!jsonText || jsonText === '[DONE]') continue;
              const data = JSON.parse(jsonText);
              port.postMessage({ type: 'STREAM_CHUNK', data });
            } catch (e) {
              console.debug('Stream parse skipped:', trimmed);
            }
          }
        }
      } finally {
        try { reader.releaseLock(); } catch (_) {}
      }
    } catch (err) {
      // ⚙️ 回退：普通模式
      try {
        const fallbackUrl = `${apiUrl}/agent/chat`;
        const resp = await fetch(fallbackUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await resp.json().catch(() => null);
        const txt = data?.data?.response || data?.data?.message || '';
        port.postMessage({ type: 'STREAM_CHUNK', data: { type: 'start', workflow_id: data?.data?.workflow_id || '' } });
        if (txt) port.postMessage({ type: 'STREAM_CHUNK', data: { type: 'content', content: txt } });
        port.postMessage({ type: 'STREAM_CHUNK', data: { type: 'done', full_response: txt } });
      } catch (e2) {
        port.postMessage({ type: 'STREAM_CHUNK', data: { type: 'error', content: String(e2) } });
      }
    }
  });
});
