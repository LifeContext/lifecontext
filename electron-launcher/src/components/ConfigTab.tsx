import React, { useState } from 'react';
import '../styles/ConfigTab.css';

interface Config {
  LLM_API_KEY: string;
  LLM_BASE_URL: string;
  LLM_MODEL: string;
  EMBEDDING_API_KEY: string;
  EMBEDDING_BASE_URL: string;
  EMBEDDING_MODEL: string;
  PROMPT_LANGUAGE: string;
}

interface ConfigTabProps {
  config: Config;
  onSaveConfig: (config: Config) => { success: boolean };
}

const ConfigTab: React.FC<ConfigTabProps> = ({ config, onSaveConfig }) => {
  const [localConfig, setLocalConfig] = useState<Config>(config);
  const [showApiKeys, setShowApiKeys] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setLocalConfig(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleLanguageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalConfig(prev => ({
      ...prev,
      PROMPT_LANGUAGE: e.target.value
    }));
  };

  const handleSave = () => {
    const result = onSaveConfig(localConfig);
    if (result.success) {
      alert('配置已成功保存！');
    } else {
      alert('保存配置失败，请查看日志获取详细信息。');
    }
  };

  return (
    <div className="config-tab">
      <div className="section">
        <h2>LLM 配置</h2>
        
        <div className="input-group">
          <label htmlFor="LLM_API_KEY">API Key:</label>
          <input
            id="LLM_API_KEY"
            name="LLM_API_KEY"
            type={showApiKeys ? "text" : "password"}
            value={localConfig.LLM_API_KEY}
            onChange={handleInputChange}
            placeholder="请输入 LLM API Key"
          />
        </div>

        <div className="input-group">
          <label htmlFor="LLM_BASE_URL">Base URL:</label>
          <input
            id="LLM_BASE_URL"
            name="LLM_BASE_URL"
            type="text"
            value={localConfig.LLM_BASE_URL}
            onChange={handleInputChange}
            placeholder="https://api.openai.com/v1"
          />
        </div>

        <div className="input-group">
          <label htmlFor="LLM_MODEL">Model:</label>
          <input
            id="LLM_MODEL"
            name="LLM_MODEL"
            type="text"
            value={localConfig.LLM_MODEL}
            onChange={handleInputChange}
            placeholder="gpt-4o-mini"
          />
        </div>
      </div>

      <hr />

      <div className="section">
        <h2>Embedding 配置</h2>
        
        <div className="input-group">
          <label htmlFor="EMBEDDING_API_KEY">API Key:</label>
          <input
            id="EMBEDDING_API_KEY"
            name="EMBEDDING_API_KEY"
            type={showApiKeys ? "text" : "password"}
            value={localConfig.EMBEDDING_API_KEY}
            onChange={handleInputChange}
            placeholder="请输入 Embedding API Key"
          />
        </div>

        <div className="input-group">
          <label htmlFor="EMBEDDING_BASE_URL">Base URL:</label>
          <input
            id="EMBEDDING_BASE_URL"
            name="EMBEDDING_BASE_URL"
            type="text"
            value={localConfig.EMBEDDING_BASE_URL}
            onChange={handleInputChange}
            placeholder="https://api.openai.com/v1"
          />
        </div>

        <div className="input-group">
          <label htmlFor="EMBEDDING_MODEL">Model:</label>
          <input
            id="EMBEDDING_MODEL"
            name="EMBEDDING_MODEL"
            type="text"
            value={localConfig.EMBEDDING_MODEL}
            onChange={handleInputChange}
            placeholder="text-embedding-3-small"
          />
        </div>
      </div>

      <hr />

      <div className="section">
        <h2>提示词语言</h2>
        
        <div className="radio-group">
          <label>
            <input
              type="radio"
              name="language"
              value="zh"
              checked={localConfig.PROMPT_LANGUAGE === 'zh'}
              onChange={handleLanguageChange}
            />
            中文
          </label>
          <label>
            <input
              type="radio"
              name="language"
              value="en"
              checked={localConfig.PROMPT_LANGUAGE === 'en'}
              onChange={handleLanguageChange}
            />
            English
          </label>
        </div>
      </div>

      <div className="options">
        <label>
          <input
            type="checkbox"
            checked={showApiKeys}
            onChange={(e) => setShowApiKeys(e.target.checked)}
          />
          显示 API Key
        </label>
      </div>

      <button className="save-button" onClick={handleSave}>
        💾 保存配置
      </button>
    </div>
  );
};

export default ConfigTab;
