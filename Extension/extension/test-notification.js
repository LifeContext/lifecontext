// 测试通知功能的简单脚本
console.log('开始测试通知功能...');

// 检查通知权限
chrome.notifications.getPermissionLevel((level) => {
  console.log('通知权限级别:', level);
  
  if (level === 'granted') {
    console.log('通知权限已授予，尝试创建测试通知...');
    
    // 创建简单测试通知
    chrome.notifications.create('test_simple', {
      type: 'basic',
      iconUrl: 'icon.png',
      title: '🔔 通知测试',
      message: '如果您看到这个通知，说明通知功能正常工作！'
    }, (notificationId) => {
      if (chrome.runtime.lastError) {
        console.error('创建通知失败:', chrome.runtime.lastError);
      } else {
        console.log('测试通知创建成功，ID:', notificationId);
      }
    });
  } else {
    console.log('通知权限未授予，当前级别:', level);
  }
});

// 监听通知事件
chrome.notifications.onClicked.addListener((notificationId) => {
  console.log('通知被点击:', notificationId);
  chrome.notifications.clear(notificationId);
});

chrome.notifications.onClosed.addListener((notificationId, byUser) => {
  console.log('通知被关闭:', notificationId, '用户关闭:', byUser);
});
