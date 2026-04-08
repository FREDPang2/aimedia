# MoneyPrinterTurbo 代码分析

> 分析版本：harry0703/MoneyPrinterTurbo (main branch)
> 分析时间：2026-04-08
> 分析人：零 (OpenClaw)

---

## 项目概述

**MoneyPrinterTurbo** 是一个成熟的 AI 视频生成工具，只需提供主题或关键词，即可全自动生成视频文案、视频素材、视频字幕、视频背景音乐，然后合成高清短视频。

- **GitHub**: https://github.com/harry0703/MoneyPrinterTurbo
- **Star**: 55k+
- **语言**: Python
- **框架**: FastAPI + Streamlit (Web UI)

---

## 技术架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      main.py                                │
│                   (Uvicorn 启动)                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    app/router.py                            │
│              (FastAPI API 路由汇总)                         │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│   app/controllers/v1/   │     │    app/controllers/     │
│   - video.py (视频)      │     │    manager/ (管理)     │
│   - llm.py (大模型)      │     │                        │
└─────────────────────────┘     └─────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                    app/services/                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│  │  llm    │ │  voice  │ │ subtitle│ │  video  │        │
│  │ (文案)  │ │ (配音)  │ │ (字幕)  │ │ (合成)  │        │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                     │
│  │material │ │  task   │ │  state  │                     │
│  │(素材)  │ │ (任务)  │ │ (状态)  │                     │
│  └─────────┘ └─────────┘ └─────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

### 核心模块

| 模块 | 文件 | 作用 |
|------|------|------|
| **LLM** | `services/llm.py` | AI 文案生成 |
| **Voice** | `services/voice.py` | 语音合成 (TTS) |
| **Subtitle** | `services/subtitle.py` | 字幕生成 |
| **Video** | `services/video.py` | 视频合成 (MoviePy) |
| **Material** | `services/material.py` | 素材获取 (Pexels/Pixabay) |
| **Task** | `services/task.py` | 任务管理 |
| **State** | `services/state.py` | 状态管理 |

### 数据流

```
用户输入主题
    │
    ▼
LLM 生成文案 (services/llm.py)
    │
    ├──► Voice 生成配音 (services/voice.py)
    ├──► Subtitle 生成字幕 (services/subtitle.py)
    └──► Material 获取素材 (services/material.py)
              │
              ▼
         Video 合成视频 (services/video.py)
              │
              ▼
           成片输出
```

---

## 技术栈

| 技术 | 用途 |
|------|------|
| **FastAPI** | API 服务 |
| **Uvicorn** | ASGI 服务器 |
| **Streamlit** | Web UI |
| **MoviePy** | 视频合成 |
| **Pillow** | 图片处理 |
| **Edge-TTS / Google-TTS** | 语音合成 |
| **Loguru** | 日志 |

---

## API 接口

基于 FastAPI，核心接口在 `app/controllers/v1/`：

### 视频接口 (`video.py`)

```python
POST /api/v1/video/generate
  - params: VideoParams (主题、文案、设置)
  - return: task_id

GET /api/v1/video/tasks/{task_id}/status
  - return: TaskStatus

GET /api/v1/video/tasks/{task_id}/download
  - return: video file
```

### LLM 接口 (`llm.py`)

```python
POST /api/v1/llm/chat
  - params: messages, model
  - return: response
```

---

## AI 服务集成

### 支持的 LLM 提供商

| 提供商 | 配置 Key | 默认模型 |
|--------|----------|----------|
| OpenAI | `openai_api_key` | gpt-4o-mini |
| Moonshot | `moonshot_api_key` | moonshot-v1-8k |
| DeepSeek | `deepseek_api_key` | deepseek-chat |
| Azure | `azure_api_key` | - |
| 通义千问 | `qwen_api_key` | qwen-turbo |
| MiniMax | `minimax_api_key` | - |
| 文心一言 | `ernie_api_key` | - |
| Ollama | `ollama_base_url` | 本地模型 |
| Pollinations | `pollinations_api_key` | openai-fast |

### 支持的 TTS 提供商

- Edge-TTS (微软，免费)
- Google-TTS
- OpenAI TTS
- MiniMax TTS (我们的目标)

### 视频素材来源

- Pexels (高清、无版权)
- Pixabay (高清、无版权)
- 本地素材

---

## 二次开发评估

### 优点（可复用）

1. **架构清晰** - MVC 模式，模块解耦
2. **API 设计合理** - FastAPI，接口规范
3. **视频合成成熟** - MoviePy + ffmpeg，稳定可靠
4. **多 AI 提供商支持** - 扩展性强
5. **Web UI 完善** - Streamlit，开箱即用

### 需要改造的地方

| 改造项 | 原因 | 难度 |
|--------|------|------|
| **系列/分集管理** | 现有只有单一视频生成 | ⭐⭐⭐ 中等 |
| **OpenClaw 控制接口** | 现有只有 REST API | ⭐⭐ 简单 |
| **长视频分镜** | 现有只支持短视频片段拼接 | ⭐⭐⭐⭐ 复杂 |
| **MiniMax TTS 集成** | 现有 TTS 不支持我们需要的 | ⭐ 简单 |
| **可灵视频生成** | 现有用 Pexels 素材，需要替换 | ⭐⭐⭐⭐ 复杂 |

### 核心改动计划

#### Phase 1: 数据模型扩展
```
现有: VideoParams → 生成单一视频
改造: Project → Series → Episode → VideoSegment
```

#### Phase 2: 工作流引擎
```
现有: 单一视频生成流程
改造: 多阶段工作流 (大纲→提纲→脚本→视频)
```

#### Phase 3: OpenClaw 集成
```
新增: /api/v1/openclaw/* 接口
功能: 任务创建、状态查询、暂停/恢复
```

---

## 文件结构参考

```
MoneyPrinterTurbo/
├── main.py                 # 入口
├── app/
│   ├── router.py           # API 路由汇总
│   ├── config/             # 配置管理
│   ├── controllers/        # 控制器
│   │   └── v1/
│   │       ├── video.py    # 视频接口
│   │       └── llm.py     # LLM 接口
│   ├── models/             # 数据模型
│   │   └── schema.py       # Pydantic 模型
│   └── services/           # 业务逻辑
│       ├── llm.py          # AI 文案生成
│       ├── voice.py        # 语音合成
│       ├── subtitle.py     # 字幕生成
│       ├── video.py        # 视频合成
│       ├── material.py     # 素材管理
│       ├── task.py         # 任务管理
│       └── state.py        # 状态管理
├── webui/                  # Streamlit Web UI
├── resource/               # 静态资源
│   ├── fonts/             # 字体
│   └── songs/              # 背景音乐
├── docs/                   # 文档
├── test/                   # 测试
├── config.example.toml     # 配置示例
├── Dockerfile
└── docker-compose.yml
```

---

## 结论

MoneyPrinterTurbo 是一个**高度成熟**的项目，架构清晰，代码质量高，适合作为二次开发的基础。

**推荐策略**：
1. **复用** services/ 层的业务逻辑（llm, voice, subtitle, video）
2. **扩展** 数据模型支持系列/分集
3. **新增** OpenClaw 控制接口
4. **替换** 视频素材来源（接入可灵 API）

---

*分析完成*
