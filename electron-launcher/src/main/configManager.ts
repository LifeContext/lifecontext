import * as fs from 'fs';
import * as path from 'path';
import { app } from 'electron';

export interface Config {
  LLM_API_KEY: string;
  LLM_BASE_URL: string;
  LLM_MODEL: string;
  EMBEDDING_API_KEY: string;
  EMBEDDING_BASE_URL: string;
  EMBEDDING_MODEL: string;
  PROMPT_LANGUAGE: string;
}

export class ConfigManager {
  private baseDir: string;
  private backendDir: string;
  private envFile: string;

  constructor() {
    // 确定基础目录
    if (app.isPackaged) {
      this.baseDir = path.join(process.resourcesPath, '..');
    } else {
      this.baseDir = path.join(__dirname, '../../../..');
    }
    
    this.backendDir = path.join(this.baseDir, 'backend');
    this.envFile = path.join(this.backendDir, '.env');
    
    // 确保目录存在
    if (!fs.existsSync(this.backendDir)) {
      fs.mkdirSync(this.backendDir, { recursive: true });
    }
    if (!fs.existsSync(path.join(this.backendDir, 'data'))) {
      fs.mkdirSync(path.join(this.backendDir, 'data'), { recursive: true });
    }
  }

  public loadConfig(): Config {
    const defaultConfig: Config = {
      LLM_API_KEY: '',
      LLM_BASE_URL: 'https://api.openai.com/v1',
      LLM_MODEL: 'gpt-4o-mini',
      EMBEDDING_API_KEY: '',
      EMBEDDING_BASE_URL: 'https://api.openai.com/v1',
      EMBEDDING_MODEL: 'text-embedding-3-small',
      PROMPT_LANGUAGE: 'zh'
    };

    if (fs.existsSync(this.envFile)) {
      try {
        const content = fs.readFileSync(this.envFile, 'utf-8');
        const config = { ...defaultConfig };
        
        content.split('\n').forEach(line => {
          line = line.trim();
          if (line && !line.startsWith('#') && line.includes('=')) {
            const [key, ...values] = line.split('=');
            const trimmedKey = key.trim();
            let trimmedValue = values.join('=').trim();
            
            // 移除引号
            if ((trimmedValue.startsWith('"') && trimmedValue.endsWith('"')) || 
                (trimmedValue.startsWith("'") && trimmedValue.endsWith("'"))) {
              trimmedValue = trimmedValue.slice(1, -1);
            }
            
            if (trimmedKey in config) {
              (config as any)[trimmedKey] = trimmedValue;
            }
          }
        });
        
        return config;
      } catch (error) {
        console.error('加载配置文件失败:', error);
        return defaultConfig;
      }
    }
    
    return defaultConfig;
  }

  public saveConfig(config: Config): boolean {
    try {
      const content = `# LifeContext 配置文件\n\n` +
        `# LLM API 配置（用于内容分析和智能对话）\n` +
        `LLM_API_KEY = "${config.LLM_API_KEY}"\n` +
        `LLM_BASE_URL = "${config.LLM_BASE_URL}"\n` +
        `LLM_MODEL = "${config.LLM_MODEL}"\n\n` +
        `# 向量化 Embedding API 配置（用于向量数据库）\n` +
        `EMBEDDING_API_KEY = "${config.EMBEDDING_API_KEY}"\n` +
        `EMBEDDING_BASE_URL = "${config.EMBEDDING_BASE_URL}"\n` +
        `EMBEDDING_MODEL = "${config.EMBEDDING_MODEL}"\n\n` +
        `# 提示词语言\n` +
        `PROMPT_LANGUAGE = "${config.PROMPT_LANGUAGE}"`;
      
      fs.writeFileSync(this.envFile, content, 'utf-8');
      return true;
    } catch (error) {
      console.error('保存配置文件失败:', error);
      return false;
    }
  }
}
