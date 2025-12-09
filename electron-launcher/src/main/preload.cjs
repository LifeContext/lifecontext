// src/main/preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // --- 功能调用 (Renderer -> Main) ---
  loadConfig: () => ipcRenderer.invoke('load-config'),
  saveConfig: (config) => ipcRenderer.invoke('save-config', config),
  startServices: () => ipcRenderer.invoke('start-services'),
  stopServices: () => ipcRenderer.invoke('stop-services'),
  openBrowser: () => ipcRenderer.invoke('open-browser'),

  // --- 事件监听 (Main -> Renderer) ---
  
  // 监听日志消息：允许前端传入回调函数接收日志
  onLog: (callback) => ipcRenderer.on('log-message', (_event, message) => callback(message)),
  
  // 监听服务状态：允许前端传入回调函数接收 true/false
  onServiceStatus: (callback) => ipcRenderer.on('service-status', (_event, status) => callback(status)),

  // --- 清理函数 ---
  // 建议在 useEffect 的 cleanup 中调用，防止重复绑定
  removeAllLogListeners: () => ipcRenderer.removeAllListeners('log-message'),
  removeAllStatusListeners: () => ipcRenderer.removeAllListeners('service-status')
});