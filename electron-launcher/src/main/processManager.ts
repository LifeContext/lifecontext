import { spawn, ChildProcess, exec } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import { app } from 'electron';

export class ProcessManager {
  private processes: ChildProcess[] = [];
  private backendProcess: ChildProcess | null = null;

  constructor() {}

  private getBaseDir(): string {
    if (app.isPackaged) {
      return path.join(process.resourcesPath, '..');
    } else {
      return path.join(__dirname, '../../../..');
    }
  }

  public startServices(): { success: boolean; message: string } {
    try {
      // 确定基础目录
      const baseDir = this.getBaseDir();
      const backendDir = path.join(baseDir, 'backend');
      
      // 检查后端可执行文件
      const backendExe = path.join(backendDir, 'LifeContextBackend.exe');
      
      if (fs.existsSync(backendExe)) {
        // 启动后端可执行文件
        this.backendProcess = spawn(backendExe, [], {
          cwd: backendDir,
          detached: true,
          shell: true
        });
      } else {
        // 开发模式启动
        this.backendProcess = spawn('python', ['app.py'], {
          cwd: backendDir,
          detached: true,
          shell: true
        });
      }
      
      if (this.backendProcess) {
        this.processes.push(this.backendProcess);
        
        // 处理输出
        this.backendProcess.stdout?.on('data', (data) => {
          console.log(`Backend stdout: ${data}`);
        });
        
        this.backendProcess.stderr?.on('data', (data) => {
          console.error(`Backend stderr: ${data}`);
        });
        
        this.backendProcess.on('close', (code) => {
          console.log(`Backend process exited with code ${code}`);
          this.removeProcess(this.backendProcess!);
          this.backendProcess = null;
        });
      }
      
      return { success: true, message: '服务启动成功' };
    } catch (error) {
      console.error('启动服务失败:', error);
      return { success: false, message: `启动服务失败: ${error}` };
    }
  }

  public stopServices(): { success: boolean; message: string } {
    try {
      for (const process of this.processes) {
        this.terminateProcess(process);
      }
      
      this.processes = [];
      this.backendProcess = null;
      
      return { success: true, message: '所有服务已停止' };
    } catch (error) {
      console.error('停止服务失败:', error);
      return { success: false, message: `停止服务失败: ${error}` };
    }
  }

  private terminateProcess(process: ChildProcess): void {
    try {
      if (process.pid) {
        if (process.platform === 'win32') {
          // Windows 平台使用 taskkill
          exec(`taskkill /F /T /PID ${process.pid}`);
        } else {
          // Unix 平台使用 kill
          process.kill();
          if (process.pid && process.pid > 0) {
            try {
              process.kill(process.pid, 'SIGTERM');
            } catch (e) {
              console.error(`无法终止进程 ${process.pid}:`, e);
            }
          }
        }
      }
    } catch (error) {
      console.error(`终止进程失败:`, error);
    }
  }

  private removeProcess(process: ChildProcess): void {
    const index = this.processes.indexOf(process);
    if (index !== -1) {
      this.processes.splice(index, 1);
    }
  }
}
