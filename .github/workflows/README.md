# GitHub Actions Workflows

本目录包含项目的所有自动化工作流配置。

## 📋 Workflow 列表

### ci.yml - 持续集成测试

**触发条件：**
- Push 到 `main` 或 `develop` 分支
- Pull Request 到 `main` 或 `develop` 分支
- 当以下目录发生变化时：
  - `backend/`
  - `frontend/`
  - `Extension/`
  - `.github/workflows/ci.yml`

**包含的测试：**

#### 1. Backend Tests (Python 3.10)
- Python 语法检查 (flake8)
- 模块导入验证
- 依赖项安装验证
- 代码覆盖率收集 (可选)
- 结果上传到 Codecov

**关键检查：**
- ✓ `config.py` 配置加载
- ✓ `routes/` 路由模块导入
- ✓ `utils/` 工具模块导入
- ✓ `tools/` 工具集导入

#### 2. Frontend Tests (Node.js 18.x, 20.x)
- 依赖项安装 (`npm ci`)
- TypeScript 编译检查 (`tsc --noEmit`)
- 项目构建 (`npm run build`)
- 测试执行 (如果配置)
- 构建产物存档

**构建产物：**
- 存档名称：`frontend-dist-{node-version}`
- 保留期限：5 天

#### 3. Extension Tests (Node.js 18.x, 20.x)
- 依赖项安装 (`npm ci`)
- JavaScript 代码检查 (ESLint - 非关键)
- `manifest.json` 验证
- 测试执行 (如果配置)

**Manifest 验证：**
- 检查 JSON 格式有效性
- 验证必要字段存在
- 显示扩展名称、版本、Manifest 版本

#### 4. Test Summary
- 汇总所有测试结果
- 生成最终的 Pass/Fail 状态

## 🚀 工作流详解

### Backend Tests (backend-tests)

```yaml
strategy:
  matrix:
    python-version: ['3.10']
```
- 使用 Python 3.10 运行测试（与 `environment.yml` 一致）

**步骤：**
1. 检出代码
2. 安装 Python 3.10
3. 安装 requirements.txt 中的依赖
4. 安装额外的开发工具 (pytest, flake8)
5. 运行 flake8 代码风格检查
6. 验证所有模块可以成功导入
7. 运行 pytest 测试 (如果存在)
8. 生成代码覆盖率报告
9. 上传覆盖率数据到 Codecov

### Frontend Tests (frontend-tests)

```yaml
strategy:
  matrix:
    node-version: [18.x, 20.x]
```
- 在两个 Node.js 版本上测试以确保兼容性

**步骤：**
1. 检出代码
2. 安装 Node.js (18.x 和 20.x)
3. 使用 `npm ci` 安装依赖 (确保一致性)
4. 运行 `npm run build` 构建项目
5. 运行 TypeScript 编译检查
6. 运行测试 (如果配置)
7. 上传 dist/ 产物到 Artifacts

### Extension Tests (extension-tests)

**步骤：**
1. 检出代码
2. 安装 Node.js
3. 使用 `npm ci` 安装依赖
4. 运行 ESLint 检查
5. 验证 manifest.json 合法性
6. 运行测试 (如果配置)

## 📊 Status Badges

在 README.md 中添加 CI 状态徽章：

```markdown
![CI Tests](https://github.com/YOUR_USERNAME/lifetcontext/actions/workflows/ci.yml/badge.svg)
```

## 🔧 自定义配置

### 添加更多 Python 版本

编辑 `backend-tests` 的 `strategy.matrix`：

```yaml
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11']
```

### 添加自定义测试命令

在相应的测试步骤中添加命令，例如为 Backend 添加 pytest：

```yaml
- name: Run specific tests
  working-directory: ./backend
  run: pytest tests/ -v --cov=app
```

### 修改触发条件

修改 `on` 部分以改变触发条件：

```yaml
on:
  push:
    branches: [ main, develop, feature/* ]
    paths:
      - 'backend/**'
      - 'frontend/**'
      - 'Extension/**'
  pull_request:
    branches: [ main ]
```

### 添加环境变量

如果需要向 CI 环境传入密钥或配置：

```yaml
env:
  NODE_ENV: test
  PYTHON_ENV: testing
```

或使用 GitHub Secrets：

```yaml
env:
  API_KEY: ${{ secrets.TEST_API_KEY }}
```

## 🔐 GitHub Secrets 配置

对于需要密钥或敏感数据的测试，在 GitHub 仓库设置中添加 Secrets：

1. 转到 Repository Settings → Secrets and variables → Actions
2. 点击 "New repository secret"
3. 添加所需的密钥，如 `CODECOV_TOKEN`

**在 Workflow 中使用：**
```yaml
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
```

## 📝 日志和调试

### 查看 Workflow 日志

1. 转到 GitHub 仓库
2. 点击 "Actions" 标签
3. 选择具体的 Workflow 运行
4. 查看每个 Job 和 Step 的日志

### 启用调试日志

在 Repository Settings → Secrets and variables → Actions 中添加：
- 变量名：`ACTIONS_STEP_DEBUG`
- 值：`true`

### 本地测试 Workflow

使用 [act](https://github.com/nektos/act) 在本地运行 Workflow：

```bash
# 安装 act
brew install act  # macOS
# 或其他系统的安装方法

# 在项目根目录运行
act -j backend-tests
act -j frontend-tests
act -j extension-tests
```

## ⚙️ 性能优化

### 使用 Actions Cache

当前 Workflow 已配置了 npm 和 pip 的缓存：

```yaml
- uses: actions/setup-python@v4
  with:
    cache: 'pip'

- uses: actions/setup-node@v4
  with:
    cache: 'npm'
    cache-dependency-path: 'frontend/package-lock.json'
```

这会显著加快依赖安装速度。

### 并行执行

三个主要测试作业 (backend, frontend, extension) 并行运行，提高效率。

## 🆘 常见问题

### Q: 某个 Job 持续失败

**A:** 检查以下几点：
1. 查看 Workflow 日志了解具体错误
2. 确保本地开发环境可以通过相同的测试
3. 检查依赖版本是否在 CI 中正确安装

### Q: 如何跳过 CI 检查

**A:** 在 Commit 消息中添加 `[skip ci]`：
```bash
git commit -m "Update docs [skip ci]"
```

### Q: 如何只运行特定的 Workflow

**A:** 修改 `on.paths` 部分，或在 Commit 只修改特定目录。

### Q: GitHub Actions 如何计费

**A:** 
- 公开仓库：免费无限制
- 私有仓库：每月免费 2,000 分钟

## 📚 相关资源

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Workflow 语法参考](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [用于 CI/CD 的常用 Actions](https://github.com/actions)

## 🎯 下一步

1. **添加更多测试**：为 Backend、Frontend、Extension 添加单元测试
2. **配置代码覆盖率**：集成 Codecov 或 Coveralls
3. **添加部署工作流**：创建自动化部署流程
4. **集成代码质量检查**：添加 SonarQube 或类似工具

