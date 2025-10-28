// config.js
// 注意：不要写 export，这里用 var 定义方便 background.js 用 importScripts 引入

// 默认配置
var DEFAULT_CONFIG = {
    API_HOST: "localhost",
    API_PORT: "8000",
    FRONTEND_HOST: "localhost", 
    FRONTEND_PORT: "3000"
};

// 从存储中获取配置，如果没有则使用默认配置
function getConfig() {
    return new Promise((resolve) => {
        chrome.storage.sync.get(DEFAULT_CONFIG, (config) => {
            resolve(config);
        });
    });
}

// 保存配置
function saveConfig(config) {
    return new Promise((resolve) => {
        chrome.storage.sync.set(config, () => {
            resolve();
        });
    });
}

// 生成API URL
async function getApiUrl() {
    const config = await getConfig();
    return `http://${config.API_HOST}:${config.API_PORT}/api`;
}

// 生成前端URL  
async function getFrontendUrl() {
    const config = await getConfig();
    return `http://${config.FRONTEND_HOST}:${config.FRONTEND_PORT}`;
}

// 兼容性：保持原有的API_CONFIG对象
var API_CONFIG = {
    BASE_URL: "http://localhost:8000/api"  // 默认使用localhost
};
  