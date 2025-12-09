import React, { useState, useEffect } from 'react';
import ConfigTab from './components/ConfigTab';
import LogTab from './components/LogTab';
import StatusBar from './components/StatusBar';
import './App.css';

interface Config {
  LLM_API_KEY: string;
  LLM_BASE_URL: string;
  LLM_MODEL: string;
  EMBEDDING_API_KEY: string;
  EMBEDDING_BASE_URL: string;
  EMBEDDING_MODEL: string;
  PROMPT_LANGUAGE: string;
}

function App() {
  const [config, setConfig] = useState<Config>({
    LLM_API_KEY: '',
    LLM_BASE_URL: 'https://api.openai.com/v1',
    LLM_MODEL: 'gpt-4o-mini',
    EMBEDDING_API_KEY: '',
    EMBEDDING_BASE_URL: 'https://api.openai.com/v1',
    EMBEDDING_MODEL: 'text-embedding-3-small',
    PROMPT_LANGUAGE: 'zh'
  });
  const [activeTab, setActiveTab] = useState<'config' | 'logs'>('config');
  const [logs, setLogs] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  // 加载配置
  useEffect(() => {
    const electronAPI = (window as any).electronAPI;
    if (electronAPI) {
      // 1. 加载配置
      electronAPI.loadConfig().then((loadedConfig: any) => {
        if (loadedConfig) setConfig(loadedConfig);
      });

      // 2. 注册日志监听器
      // 每次收到日志，都会执行这个回调
      electronAPI.onLog((message: string) => {
        // 简单的日志级别判断逻辑
        let level = 'INFO';
        if (message.includes('错误') || message.includes('Error') || message.includes('失败')) level = 'ERROR';
        else if (message.includes('成功') || message.includes('完成')) level = 'SUCCESS';

        // 更新日志状态
        setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${message}`].slice(-100));
      });

      // 3. 注册状态监听器
      electronAPI.onServiceStatus((status: boolean) => {
        setIsRunning(status);
      });

      // 4. 清理监听器 (组件卸载时执行)
      return () => {
        electronAPI.removeAllLogListeners();
        electronAPI.removeAllStatusListeners();
      };
    }

    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'log-message') {
        const msg = event.data.message;
        setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`].slice(-100));
      }
      if (event.data.type === 'service-status') {
        setIsRunning(event.data.status);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  // 保存配置
  const handleSaveConfig = (newConfig: Config) => {
    const electronAPI = (window as any).electronAPI;
    if (electronAPI) {
      const success = electronAPI.saveConfig(newConfig);
      if (success) {
        setConfig(newConfig);
        log('配置已成功保存');
      }
      return { success };
    }
    return { success: false };
  };

  // 启动服务
  const handleStart = async () => {
    const electronAPI = (window as any).electronAPI;
    if (electronAPI) {
      try {
        const result = await electronAPI.startServices();
        if (result.success) {
          setIsRunning(true);
          log('服务已成功启动');
        } else {
          log(`服务启动失败: ${result.message}`);
        }
      } catch (error) {
        log(`启动服务时出错: ${error}`);
      }
    }
  };

  // 停止服务
  const handleStop = async () => {
    const electronAPI = (window as any).electronAPI;
    if (electronAPI) {
      try {
        const result = await electronAPI.stopServices();
        if (result.success) {
          setIsRunning(false);
          log('服务已成功停止');
        } else {
          log(`服务停止失败: ${result.message}`);
        }
      } catch (error) {
        log(`停止服务时出错: ${error}`);
      }
    }
  };

  // 打开浏览器
  const handleOpenBrowser = async () => {
    const electronAPI = (window as any).electronAPI;
    if (electronAPI) {
      try {
        await electronAPI.openBrowser();
        log('已打开浏览器访问主页');
      } catch (error) {
        log(`打开浏览器时出错: ${error}`);
      }
    }
  };

  // 日志记录函数
  const log = (message: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${message}`].slice(-100));
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>LifeContext 启动器</h1>
      </header>
      
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'config' ? 'active' : ''}`}
          onClick={() => setActiveTab('config')}
        >
          ⚙️ 配置
        </button>
        <button 
          className={`tab ${activeTab === 'logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          📝 日志
        </button>
      </div>

      <main className="main-content">
        {activeTab === 'config' && (
          <ConfigTab 
            config={config} 
            onSaveConfig={handleSaveConfig} 
          />
        )}
        {activeTab === 'logs' && (
          <LogTab logs={logs} />
        )}
      </main>

      <StatusBar 
        isRunning={isRunning}
        onStart={handleStart}
        onStop={handleStop}
        onOpenBrowser={handleOpenBrowser}
      />
    </div>
  );
}

export default App;