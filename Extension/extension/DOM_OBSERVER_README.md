# DOM动态监听功能说明

## 功能概述

新增的DOM动态监听功能可以实时检测网页内容的变化，自动触发增量爬取，特别适用于以下场景：

- 🤖 **AI聊天网站**: 监听新消息的添加
- 📚 **在线文档**: 检测文档内容的实时更新
- 💬 **论坛/社区**: 捕获新帖子和回复
- 📊 **数据仪表板**: 监控数据变化
- 🔄 **单页应用**: 监听动态加载的内容

## 核心特性

### 1. 智能DOM监听
- 使用 `MutationObserver` API 监听DOM变化
- 只监听重要内容区域，忽略广告、导航等无关元素
- 支持文本内容变化和节点添加检测

### 2. 节流控制
- 默认3秒节流，避免频繁爬取
- 可配置节流时间
- 内容哈希检测，避免重复爬取相同内容

### 3. 页面可见性管理
- 页面隐藏时自动暂停监听，节省资源
- 页面重新可见时自动恢复监听
- 窗口焦点变化时智能调整监听状态

### 4. 增量爬取
- 区分初始爬取和增量爬取
- 增量爬取标记为 `web-crawler-incremental`
- 包含时间戳和变化类型信息

## 配置选项

### 监听区域选择器
```javascript
observedSelectors: [
  'main', 'article', '.content', '.post', '.message', '.chat-message',
  '.conversation', '.thread', '.comment', '.reply', '.update',
  '[role="main"]', '[role="article"]', '.main-content'
]
```

### 忽略区域选择器
```javascript
ignoredSelectors: [
  'script', 'style', 'noscript', 'meta', 'link', 'title',
  '.advertisement', '.ads', '.sidebar', '.navigation', '.nav',
  '.header', '.footer', '.menu', '.toolbar'
]
```

### 节流配置
- `crawlThrottleDelay`: 爬取间隔时间（毫秒），默认3000ms

## 使用方法

### 1. 自动启用
- 页面加载完成后，初始爬取成功会自动启用DOM监听
- 无需手动配置，开箱即用

### 2. 手动控制
- 通过扩展popup界面可以手动启用/禁用DOM监听
- 实时显示监听状态和统计信息

### 3. 编程控制
```javascript
// 启用DOM监听
chrome.tabs.sendMessage(tabId, {
  type: 'TOGGLE_DOM_OBSERVER',
  enabled: true
});

// 更新配置
chrome.tabs.sendMessage(tabId, {
  type: 'UPDATE_DOM_CONFIG',
  config: {
    throttleDelay: 5000,
    observedSelectors: ['custom-selector']
  }
});

// 获取状态
chrome.tabs.sendMessage(tabId, {
  type: 'GET_DOM_STATUS'
});
```

## 测试方法

1. 打开 `test-dom-observer.html` 测试页面
2. 点击各种按钮模拟动态内容更新
3. 观察浏览器控制台和扩展popup界面的状态变化
4. 检查服务器端是否收到增量爬取数据

## 性能优化

### 1. 智能过滤
- 只监听包含足够文本内容的节点
- 忽略样式、脚本等无关元素
- 基于选择器精确控制监听范围

### 2. 资源管理
- 页面隐藏时自动暂停监听
- 页面卸载时清理资源
- 避免内存泄漏

### 3. 节流机制
- 防止过于频繁的爬取请求
- 内容哈希检测避免重复处理
- 可配置的节流时间

## 日志输出

控制台会输出详细的日志信息：

```
🔍 初始化DOM变化监听器
✅ DOM变化监听器已启动
📝 检测到 3 个重要DOM变化
⏱️ 节流中，还需等待 2000ms
🚀 触发增量爬取
📊 执行增量爬取，内容长度: 1234
✅ 增量爬取成功
```

## 注意事项

1. **兼容性**: 需要支持 `MutationObserver` 的现代浏览器
2. **性能**: 在内容变化频繁的页面上可能消耗较多资源
3. **准确性**: 依赖选择器配置，可能需要根据具体网站调整
4. **网络**: 增量爬取会发送网络请求，注意服务器负载

## 故障排除

### DOM监听器未启动
- 检查页面是否完全加载
- 确认Chrome扩展权限正常
- 查看控制台错误信息

### 内容变化未检测到
- 检查选择器配置是否匹配目标元素
- 确认变化的内容在监听范围内
- 调整节流时间设置

### 爬取失败
- 检查网络连接
- 确认服务器接口正常
- 查看后台脚本日志
