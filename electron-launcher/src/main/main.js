import { app, BrowserWindow, ipcMain, shell } from 'electron';
import path from 'path';
import fs from 'fs';
import { spawn, exec } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// --- 路径配置 ---
const isDev = !app.isPackaged;
const projectRoot = isDev 
  ? path.join(__dirname, '../../')
  : path.join(process.resourcesPath); 

const BACKEND_DIR = path.join(projectRoot, '../backend');
const ENV_FILE = path.join(BACKEND_DIR, '.env');

let mainWindow = null;
let backendProcess = null;

// --- 辅助函数：日志发送 ---
function sendLog(message) {
  if (mainWindow) {
    mainWindow.webContents.send('log-message', message);
    console.log(message); // 同时打印到终端
  }
}

// --- 窗口创建 ---
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 700,
    icon: path.join(projectRoot, 'Logo.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false
    }
  });

  // 环境变量处理
  if (process.env.ELECTRON_START_URL) {
    mainWindow.loadURL(process.env.ELECTRON_START_URL);
  } else {
    mainWindow.loadFile(path.join(__dirname, '../../dist/index.html'));
  }

  // 开发环境打开 DevTools
  if (isDev) {
    // mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// --- 应用生命周期 ---
app.whenReady().then(() => {
  setupIpcHandlers(); // 注册 IPC 监听
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  stopBackendService(); // 确保关闭窗口时杀掉后端进程
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  stopBackendService();
});

// --- 核心功能实现 ---

function setupIpcHandlers() {
  // 1. 加载配置
  ipcMain.handle('load-config', async () => {
    try {
      if (!fs.existsSync(ENV_FILE)) {
        sendLog(`配置文件未找到: ${ENV_FILE}`);
        return null;
      }
      
      const content = fs.readFileSync(ENV_FILE, 'utf-8');
      const config = {};
      
      content.split('\n').forEach(line => {
        line = line.trim();
        if (line && !line.startsWith('#') && line.includes('=')) {
          const [key, ...values] = line.split('=');
          const value = values.join('=').trim().replace(/^["']|["']$/g, ''); // 去除引号
          config[key.trim()] = value;
        }
      });
      
      return config;
    } catch (error) {
      sendLog(`加载配置出错: ${error.message}`);
      return null;
    }
  });

  // 2. 保存配置
  ipcMain.handle('save-config', async (event, newConfig) => {
    try {
      if (!fs.existsSync(BACKEND_DIR)) {
        fs.mkdirSync(BACKEND_DIR, { recursive: true });
      }

      const content = [
        "# LifeContext 配置文件",
        "",
        "# LLM API 配置（用于内容分析和智能对话）",
        `LLM_API_KEY = "${newConfig.LLM_API_KEY}"`,
        `LLM_BASE_URL = "${newConfig.LLM_BASE_URL}"`,
        `LLM_MODEL = "${newConfig.LLM_MODEL}"`,
        "",
        "# 向量化 Embedding API 配置（用于向量数据库）",
        `EMBEDDING_API_KEY = "${newConfig.EMBEDDING_API_KEY}"`,
        `EMBEDDING_BASE_URL = "${newConfig.EMBEDDING_BASE_URL}"`,
        `EMBEDDING_MODEL = "${newConfig.EMBEDDING_MODEL}"`,
        "",
        "# 提示词语言",
        `PROMPT_LANGUAGE = "${newConfig.PROMPT_LANGUAGE}"`
      ].join('\n');

      fs.writeFileSync(ENV_FILE, content, 'utf-8');
      sendLog('配置已成功保存到 .env 文件');
      return true;
    } catch (error) {
      sendLog(`保存配置失败: ${error.message}`);
      return false;
    }
  });

  // 3. 启动服务
  ipcMain.handle('start-services', async () => {
    if (backendProcess) {
      sendLog('⚠️ 服务已经在运行中');
      return { success: true, message: 'Already running' };
    }

    sendLog('🚀 正在启动 Backend 服务...');

    // 检查是否有打包好的 exe (优先级高)
    const exePath = path.join(BACKEND_DIR, 'LifeContextBackend.exe');
    const pyScript = path.join(BACKEND_DIR, 'app.py');
    
    let cmd, args;

    if (fs.existsSync(exePath)) {
      sendLog(`发现可执行文件: ${exePath}`);
      cmd = exePath;
      args = [];
    } else if (fs.existsSync(pyScript)) {
      sendLog(`未找到 exe，尝试运行 Python 脚本: ${pyScript}`);
      // 检查 python 命令，可能是 python 或 python3
      cmd = 'python'; 
      args = ['app.py'];
    } else {
      const msg = `❌ 无法找到后端文件。请确认路径: ${BACKEND_DIR}`;
      sendLog(msg);
      return { success: false, message: msg };
    }

    try {
      // 启动子进程
      backendProcess = spawn(cmd, args, {
        cwd: BACKEND_DIR,
        shell: false, // 设为 false 以便更好地控制进程
        windowsHide: true, // Windows下隐藏黑框
        env: {
          ...process.env, // 继承系统原有的环境变量
          PYTHONIOENCODING: 'utf-8', // 强制 Python 使用 UTF-8 编码输出
          LANG: 'zh_CN.UTF-8'
        }
      });

      // 监听标准输出
      backendProcess.stdout.on('data', (data) => {
        const msg = data.toString().trim();
        if (msg) sendLog(`[Backend] ${msg}`);
      });

      // 监听错误输出
      backendProcess.stderr.on('data', (data) => {
        const msg = data.toString().trim();
        if (msg) {
          if (msg.includes("werkzeug") && (msg.includes("INFO") || msg.includes("GET"))) {
            // 这是正常日志，使用 INFO 级别标签
            sendLog(`[Backend INFO] ${msg}`); 
          } else {
            // 否则视为真正的错误
            sendLog(`[Backend ERROR] ${msg}`); // 使用 [Backend ERROR] 标签
          }
        }
      });

      backendProcess.on('close', (code) => {
        sendLog(`Backend 服务已退出，代码: ${code}`);
        backendProcess = null;
        // 通知渲染进程服务已停止
        if (mainWindow) mainWindow.webContents.send('service-status', false);
      });

      backendProcess.on('error', (err) => {
        sendLog(`❌ 启动进程失败: ${err.message}`);
        backendProcess = null;
      });

      if (mainWindow) mainWindow.webContents.send('service-status', true);
      return { success: true };

    } catch (error) {
      return { success: false, message: error.message };
    }
  });

  // 4. 停止服务
  ipcMain.handle('stop-services', async () => {
    stopBackendService();
    return { success: true };
  });

  // 5. 打开浏览器
  ipcMain.handle('open-browser', async () => {
    await shell.openExternal('http://localhost:8000');
  });
}

function stopBackendService() {
  if (backendProcess) {
    sendLog('🛑 正在停止服务...');
    
    if (process.platform === 'win32') {
      // Windows 上使用 taskkill 强制结束进程树 (类似 launcher.py)
      exec(`taskkill /pid ${backendProcess.pid} /T /F`, (err) => {
        if (err) sendLog(`结束进程树失败 (可能已退出): ${err.message}`);
      });
    } else {
      // Linux/Mac
      backendProcess.kill(); 
    }
    
    backendProcess = null;
    if (mainWindow) mainWindow.webContents.send('service-status', false);
  }
}