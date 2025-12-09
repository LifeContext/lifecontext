import React from 'react';
import '../styles/LogTab.css';

interface LogTabProps {
  logs: string[];
}

const LogTab: React.FC<LogTabProps> = ({ logs }) => {
  return (
    <div className="log-tab">
      <div className="log-container">
        {logs.map((log, index) => (
          <div key={index} className="log-entry">
            {log}
          </div>
        ))}
        {logs.length === 0 && (
          <div className="log-entry empty">暂无日志记录</div>
        )}
      </div>
    </div>
  );
};

export default LogTab;
