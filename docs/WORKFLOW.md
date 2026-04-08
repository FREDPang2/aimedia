# AIMedia 开发工作流

## 协作模式

```
Fred (岩哥)
    │
    ▼ 需求确认
┌─────────────┐
│  零 (main)  │ ← 需求分析、方案确认、进度把控
└──────┬──────┘
       │ 任务分解
       ▼
┌─────────────┐
│ 代码小一    │ ← 自主开发、Claude Code 辅助、定期汇报
│ (xiaoyi)   │
└──────┬──────┘
       │ 执行
       ▼
┌─────────────┐
│ Claude Code │ ← 代码编写、调试、测试
└─────────────┘
```

## 开发节奏

### 1. 需求确认阶段
- **零**: 分析需求，提出方案
- **Fred**: 确认方向

### 2. 开发执行阶段
- **代码小一**: 
  - 接收任务，明确验收标准
  - 自主实现，小决策不请示
  - 大决策（架构变更）才问零
  - 用 Claude Code 辅助写代码
  - 定期向零汇报进度

### 3. 测试验收阶段
- **代码小一**: 自测、修复 bug
- **Fred**: 验收功能

## Claude Code 使用

### 启动命令
```bash
export PATH="$HOME/.npm-global/bin:$PATH"
export HTTP_PROXY="http://172.29.112.1:7897"
export HTTPS_PROXY="http://172.29.112.1:7897"
export ANTHROPIC_API_KEY="sk-kimi-o5EGW4ylRMFuVdDYa3r6UxBwBPFoegzWxKv4svrjsV7bolyRADdXrbNqVjsuwYUx"
export ANTHROPIC_BASE_URL="https://api.kimi.com/coding"
cd ~/.openclaw/workspace-coding/AIMedia
claude --bare --print "任务描述"
```

### 上下文管理
- **超过 60% 立即处理**：使用 `/compact`
- 主动总结，清理上下文

## Git 工作流

### 分支策略
```
main (稳定版本)
  └── dev (开发主干)
       └── feature/xxx (功能分支)
```

### 提交规范
```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
refactor: 重构
test: 添加测试
```

### 操作流程
```bash
cd ~/.openclaw/workspace-coding
git checkout -b feature/xxx
# 写代码...
git add -A
git commit -m "feat: xxx"
git checkout dev
git merge feature/xxx
```

## 任务优先级

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | AI 工作流 | 大纲→提纲→脚本生成 |
| P0 | 可灵集成 | 视频生成 API |
| P1 | MiniMax TTS | 配音生成 |
| P1 | 视频合成 | FFmpeg 合成 |
| P2 | 前端开发 | Vue3 |

## 汇报模板

定期向零汇报：

```markdown
## [日期] 进度汇报

### ✅ 完成
- ...

### 🔄 进行中
- ...

### ❌ 问题
- ...

### 📋 下一步
- ...
```

## 代码小一职责边界

**负责**：
- AIMedia 项目完整开发
- 代码实现、调试、测试
- 文档同步更新
- 合理使用 Claude Code

**不负责**：
- 需求变更（零处理）
- 方案设计（大决策由零确认）
- 对外沟通（零处理）

---
*最后更新: 2026-04-08*
