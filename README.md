# AIMedia — AI 系列视频生产管线

> 输入一个选题，自动生成系列视频大纲 → 分集提纲 → 脚本+分镜 → 视频片段 → 配音合成 → 成片

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi)
![Vue3](https://img.shields.io/badge/Vue3-4FC08D?style=flat-square&logo=vuedotjs)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 核心特性

- **三级内容管理** — Project → Series → Episode，系列化生产支持单集独立控制
- **AI 全流程自动化** — Moonshot Kimi 生成大纲/脚本/分镜，可灵生成视频，MiniMax TTS 配音
- **FFmpeg 管线合成** — 视频片段 + 配音 + 字幕自动合成成片
- **Vue3 前端** — 实时状态轮询，进度一目了然
- **Docker 一键部署** — `docker compose up` 即可运行
- **OpenClaw 集成** — 可通过 OpenClaw 远程触发任务

---

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    Vue3 Frontend                        │
│   Projects  /  Series  /  Episodes  /  Video Player     │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP REST
┌──────────────────────▼──────────────────────────────────┐
│                  FastAPI Backend                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Routers  │  │ Services │  │   Video Pipeline     │  │
│  │ Projects │  │Workflow  │  │ voice_tts            │  │
│  │ Series   │  │ Kling    │  │ kling (视频生成)     │  │
│  │ Episodes │  │ FFmpeg   │  │ video_compose        │  │
│  └──────────┘  └──────────┘  └──────────────────────┘  │
│                         │                               │
│  ┌──────────────────────▼──────────────────────────┐   │
│  │              SQLite Database                      │   │
│  │   Project / Series / Episode / VideoTask        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 核心技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python 3.11 + FastAPI + SQLAlchemy |
| 前端 | Vue 3.4 + Element Plus + Vite |
| 数据库 | SQLite |
| 任务队列 | Celery + Redis |
| 视频生成 | 可灵 Kling API |
| 语音合成 | MiniMax TTS API |
| 大模型 | Moonshot Kimi API |
| 视频合成 | FFmpeg + MoviePy |
| 部署 | Docker Compose |

---

## 快速开始

### 前置要求

- Docker & Docker Compose
- API Keys（见下方配置）

### 1. 克隆项目

```bash
git clone https://github.com/FREDPang2/aimedia.git
cd aimedia
```

### 2. 配置 API Keys

创建 `config/.env`：

```bash
cp config/.env.example config/.env
# 编辑 config/.env，填入以下 key：
# MOONSHOT_API_KEY=sk-xxxxx      # Moonshot Kimi，大纲/脚本/分镜生成
# KLING_API_KEY=xxxx              # 可灵视频生成
# MINIMAX_API_KEY=xxxx            # MiniMax TTS 配音
# PROXY_URL=http://host.docker.internal:7897  # Docker 内代理
```

### 3. 启动服务

```bash
docker compose up -d
```

服务启动后访问：
- **前端**: http://localhost:5173
- **后端 API**: http://localhost:4000
- **API 文档**: http://localhost:4000/api/v1/docs

---

## 项目结构

```
AIMedia/
├── src/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py              # FastAPI 应用入口
│   │   │   ├── models.py            # SQLAlchemy 数据模型
│   │   │   ├── database.py          # 数据库配置
│   │   │   └── routers/             # API 路由
│   │   │       ├── projects.py      # 项目 CRUD
│   │   │       ├── series.py        # 系列 + generate-outline
│   │   │       ├── episodes.py      # 分集 + generate-script/video
│   │   │       └── openclaw.py      # OpenClaw 控制接口
│   │   └── services/
│   │       ├── workflow.py          # Moonshot AI 工作流
│   │       ├── kling.py            # 可灵视频 API
│   │       ├── voice_tts.py         # MiniMax TTS
│   │       └── video_compose.py     # FFmpeg 视频合成
│   └── frontend/
│       ├── views/                   # Vue 页面
│       │   ├── Projects.vue
│       │   ├── Series.vue
│       │   ├── Episodes.vue
│       │   └── VideoPlayer.vue
│       └── test-*.cjs              # Playwright 测试
├── config/
│   └── .env.example                # 环境变量示例
├── docs/                            # 开发文档
│   ├── ARCHITECTURE.md             # 系统架构详解
│   ├── API-SPEC.md                 # 接口规范
│   ├── ROADMAP.md                  # 开发路线图
│   └── WORKFLOW.md                 # 开发流程
├── docker-compose.yml
└── README.md
```

---

## API 概览

### Projects

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/projects` | 列出所有项目 |
| POST | `/api/v1/projects` | 创建项目 |
| GET | `/api/v1/projects/{id}` | 获取项目详情 |
| PUT | `/api/v1/projects/{id}` | 更新项目 |
| DELETE | `/api/v1/projects/{id}` | 删除项目 |

### Series

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/series` | 列出所有系列 |
| POST | `/api/v1/series` | 创建系列 |
| GET | `/api/v1/series/{id}` | 获取系列详情 |
| PUT | `/api/v1/series/{id}` | 更新系列 |
| DELETE | `/api/v1/series/{id}` | 删除系列 |
| POST | `/api/v1/series/{id}/generate-outline` | AI 生成系列大纲 |

### Episodes

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/episodes` | 列出所有分集 |
| POST | `/api/v1/episodes` | 创建分集 |
| GET | `/api/v1/episodes/{id}` | 获取分集详情 |
| PUT | `/api/v1/episodes/{id}` | 更新分集 |
| DELETE | `/api/v1/episodes/{id}` | 删除分集 |
| POST | `/api/v1/episodes/{id}/generate-script` | AI 生成脚本+分镜 |
| POST | `/api/v1/episodes/{id}/generate-video` | 触发视频生成管线 |
| GET | `/api/v1/episodes/{id}/stream-status` | SSE 流式状态推送 |

完整 API 文档：http://localhost:4000/api/v1/docs

---

## 工作流

```
选题
  │
  ▼
[创建 Project] ──► [创建 Series] ──► [生成系列大纲]（AI）
                                              │
                                              ▼
                                    [创建 Episode] × N
                                              │
                                              ▼
                                    [生成脚本+分镜]（AI）
                                              │
                                              ▼
                                    [生成视频]（AI + FFmpeg）
                                              │
                                              ▼
                                           成片
```

### Episode 状态流转

```
draft
  │
  ├─► outline_generating ──► outline_generated
  │
  ├─► script_generating ───► script_generated
  │
  └─► video_generating ────► video_completed
                                │
                                └─► video_failed（Kling 等 API 失败时）
```

---

## 开发指南

### 本地开发

```bash
# 后端
cd src/backend
pip install -r requirements.txt
python -m app.main

# 前端
cd src/frontend
npm install
npm run dev

# 运行测试
cd src/frontend
node test-aimedia.cjs all       # 基础 22 项
node test-deep.cjs             # 深度 10 项
```

### Git 提交规范

```
feat:     新功能
fix:      修复 bug
docs:     文档更新
refactor: 重构
test:     测试
chore:    杂项（截图更新、依赖等）
```

### 分支策略

```bash
git checkout -b feature/xxx     # 新功能
git checkout -b fix/xxx         # 修复
git checkout -b docs/xxx       # 文档
# 完成后 PR 合并到 main
```

---

## 部署说明

### Docker Compose（推荐）

```bash
# 克隆后直接启动
docker compose up -d

# 查看日志
docker compose logs -f backend

# 重启
docker compose restart
```

### 环境变量说明

| 变量 | 必填 | 说明 |
|------|------|------|
| `MOONSHOT_API_KEY` | ✅ | Moonshot Kimi API Key |
| `KLING_API_KEY` | ✅ | 可灵视频 API Key |
| `MINIMAX_API_KEY` | ✅ | MiniMax API Key |
| `PROXY_URL` | ⚠️ | Docker 内访问国外 API 代理 |
| `VITE_API_BASE_URL` | ✅ | 前端构建时 API 地址 |

---

## 常见问题

**Q: 视频生成失败，提示 Kling API Key 未配置？**
A: 确保 `config/.env` 中 `KLING_API_KEY` 已正确填写，且代理可访问可灵服务器。

**Q: AI 生成超时？**
A: 检查代理是否正常工作，或适当增加 `workflow.py` 中的 timeout 配置。

**Q: Docker 内前端无法访问后端？**
A: 确保 `VITE_API_BASE_URL=http://localhost:4000`（开发）或 `VITE_API_BASE_URL=http://backend:4000`（Docker）。

---

## License

MIT License — 欢迎 Fork 和 Star

---

*最后更新：2026-04-11*
*项目地址：https://github.com/FREDPang2/aimedia*
