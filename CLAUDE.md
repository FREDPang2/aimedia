# CLAUDE.md - AIMedia 开发指南

## 项目概述

AIMedia 是一个基于 MoneyPrinterTurbo 二次开发的 AI 视频生产管线。

**核心功能**：选题 → 系列大纲 → 分集提纲 → 脚本+分镜 → 视频片段 → 配音合成 → 成片

**技术栈**：Python + FastAPI, Vue3 + Element Plus, SQLite, Celery + Redis, Docker Compose

---

## 开发环境

```bash
# 启动 Claude Code（已配置 Kimi/MiniMax API）
./scripts/start-claude.sh

# 或手动配置
export HTTP_PROXY=http://172.29.112.1:7897
export HTTPS_PROXY=http://172.29.112.1:7897
export ANTHROPIC_API_KEY=sk-kimi-o5EGW4ylRMFuVdDYa3r6UxBwBPFoegzWxKv4svrjsV7bolyRADdXrbNqVjsuwYUx
export ANTHROPIC_BASE_URL=https://api.kimi.com/coding
```

---

## 代码规范

### Git 提交规范
```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
refactor: 重构代码
test: 添加测试
```

### 文件命名
- Python: `snake_case.py`
- Vue: `PascalCase.vue`
- 配置: `kebab-case.yaml`

### 代码风格
- Python: PEP 8，使用 Black 格式化
- Vue: ESLint + Prettier
- 注释: 中文说明关键逻辑

---

## 项目结构

```
AIMedia/
├── docs/           # 项目文档
│   ├── PROJECT.md      # 项目概述
│   ├── ARCHITECTURE.md # 系统架构
│   ├── API-SPEC.md     # 接口规范
│   └── WORKFLOW.md     # 开发流程
├── src/            # 源代码
├── config/         # 配置文件
├── assets/         # 素材
├── tests/          # 测试
└── scripts/        # 脚本
```

---

## 工作流程

1. **理解需求** - 读 docs/ 下的相关文档
2. **创建分支** - `git checkout -b feature/xxx`
3. **实现代码** - 边写边测
4. **更新文档** - 代码变则文档同步
5. **提交代码** - `git commit`
6. **汇报结果** - 告知零完成情况

---

## 重要约束

- **修改 docs/ 前先确认**：文档变更影响其他开发者
- **上下文超 60% 立即处理**：用 `/compact` 或总结清理
- **生产环境操作前报备**：确认后再执行
- **外部 API 调用要记录**：方便排查问题

---

## 文档更新规则

当发生以下情况时，必须更新对应文档：

| 代码变更 | 文档更新 |
|----------|----------|
| 新增 API 接口 | 更新 API-SPEC.md |
| 修改架构 | 更新 ARCHITECTURE.md |
| 新增功能 | 更新 PROJECT.md + CHANGELOG.md |
| 修改流程 | 更新 WORKFLOW.md |

---

## 联系

- 协调者：零 (main agent) - 负责需求和方案
- 开发者：代码小一 (xiaoyi) - 执行开发任务
