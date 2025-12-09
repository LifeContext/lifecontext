import React from 'react';
import '../styles/StatusBar.css';

interface StatusBarProps {
  isRunning: boolean;
  onStart: () => void;
  onStop: () => void;
  onOpenBrowser: () => void;
}

const StatusBar: React.FC<StatusBarProps> = ({ 
  isRunning, 
  onStart, 
  onStop, 
  onOpenBrowser 
}) => {
  return (
    <div className="status-bar">
      <div className="buttons">
        <button 
          className="start-button" 
          onClick={onStart} 
          disabled={isRunning}
        >
          ▶️ 启动服务
        </button>
        <button 
          className="stop-button" 
          onClick={onStop} 
          disabled={!isRunning}
        >
          ⏹️ 停止服务
        </button>
        <button 
          className="browser-button" 
          onClick={onOpenBrowser} 
          disabled={!isRunning}
        >
          🌐 打开主页
        </button>
      </div>
      
      <div className="status">
        <span className={`status-indicator ${isRunning ? 'running' : 'stopped'}`}>
          ● {isRunning ? '运行中' : '未启动'}
        </span>
      </div>
    </div>
  );
};

export default StatusBar;
