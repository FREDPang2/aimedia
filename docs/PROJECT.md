# AIMedia - AI 视频生产管线

## 项目愿景

一个**系列化 AI 视频生产平台**，让创作者能够：
- 输入一个选题 → 自动生成系列视频大纲
- 为每集生成详细提纲和脚本
- 自动生成视频 + 配音 + 字幕 + 特效
- 单集独立控制，成片质量可调

**一句话**：让"一个人+AI"能批量生产专业级视频内容。

---

## 核心需求（Fred 确认）

### 1. 视频生成
- **纯文本生成**（T2V），不需要素材准备
- 优先使用**可灵 (Kling)**，备选即梦 (Jimeng)
- 支持多种视频尺寸（9:16 竖屏 / 16:9 横屏）

### 2. 配音和字幕
- **MiniMax TTS** 生成配音，支持中文
- 自动生成字幕（SRT 格式）
- 可选背景音乐

### 3. 系列化管理
- **Project** → **Series** → **Episode** 三级结构
- 单集独立生成，方便控制质量
- 支持批量生成和单独重做

### 4. 工作流
```
选题 → 生成系列大纲 → 分集详细提纲 → 脚本+分镜 → 视频片段 → 配音合成 → 成片
```
每步都可**暂停、修改、重新生成**。

### 5. 用户群体
- **目标用户可选、可定义**（V1 暂不实现用户系统）
- 初期面向 AI 视频创作者、独立开发者

### 6. 技术约束
- **Web 端**，可远程访问
- **无需登录认证**（V1）
- 预算不限制，优先国内 AI 服务

---

## 技术选型

### AI 服务

| 功能 | 推荐 | 备选 |
|------|------|------|
| 视频生成 | 可灵 (Kling) | 即梦 (Jimeng) |
| 语音合成 | MiniMax TTS | Edge-TTS |
| 大模型 | Kimi K2.5 | MiniMax M2.7 |

### 基础架构

| 组件 | 技术 | 说明 |
|------|------|------|
| 后端 | Python + FastAPI | 高性能异步 |
| 前端 | Vue3 + Element Plus | 待开发 |
| 数据库 | SQLite | 轻量，单文件 |
| 任务队列 | Celery + Redis | 异步任务 |
| 视频合成 | FFmpeg + MoviePy | 稳定可靠 |
| 部署 | Docker Compose | 一键启动 |

### MoneyPrinterTurbo 参考

- **源码**：`MoneyPrinterTurbo-Reference/`
- **可复用**：llm/voice/subtitle/video services
- **需改造**：系列分集管理、OpenClaw 接口、可灵视频源

---

## 项目位置

**路径**: `~/Aiproject/AIMedia/` (即 `/home/fredrog/Aiproject/AIMedia/`)

## 项目结构

```
AIMedia/
├── src/
│   ├── backend/           # FastAPI 后端
│   │   ├── app/
│   │   │   ├── main.py          # 应用入口
│   │   │   ├── models.py        # 数据模型
│   │   │   ├── database.py      # 数据库配置
│   │   │   └── routers/         # API 路由
│   │   │       ├── projects.py   # 项目
│   │   │       ├── series.py    # 系列
│   │   │       ├── episodes.py  # 分集
│   │   │       └── openclaw.py # OpenClaw 控制
│   │   └── services/            # 业务逻辑
│   │       ├── workflow.py      # AI 工作流
│   │       ├── video.py         # 视频合成
│   │       ├── voice.py         # 配音生成
│   │       ├── kling.py         # 可灵 API
│   │       ├── voice_tts.py     # MiniMax TTS
│   │       └── video_compose.py # 视频合成
│   └── frontend/         # Vue3 前端
├── config/               # 配置文件
├── assets/               # 素材/BGM
├── docs/                # 开发文档
└── tests/               # 测试用例
```

---

## 当前状态

| 模块 | 状态 | 说明 |
|------|------|------|
| 数据模型 | ✅ 完成 | Project/Series/Episode/VideoTask |
| API 路由 | ✅ 完成 | 23 个路由 |
| FastAPI 服务 | ✅ 运行中 | localhost:4000 |
| AI 工作流 | ❌ 待开发 | LLM 生成大纲/脚本 |
| 可灵集成 | ❌ 待开发 | 视频生成 |
| MiniMax TTS | ❌ 待开发 | 配音生成 |
| 前端 | ❌ 待开发 | Vue3 |

---

## 开发优先级

1. **P0**：AI 工作流（大纲→提纲→脚本）
2. **P0**：可灵视频生成集成
3. **P1**：MiniMax TTS 集成
4. **P1**：视频合成（FFmpeg）
5. **P2**：前端开发
6. **P3**：字幕生成、特效

---

*最后更新: 2026-04-08*
*负责人: 代码小一 (xiaoyi)*
