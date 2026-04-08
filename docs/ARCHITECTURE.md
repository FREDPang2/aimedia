# AIMedia 系统架构

## 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        OpenClaw (WSL2)                          │
│  - 零 (main agent): 需求分析、任务分解、进度把控                  │
│  - 代码小一 (xiaoyi): 负责 AIMedia 开发                         │
│  - 通过 ACP 控制 Claude Code 执行开发                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼ (API / CLI)
┌─────────────────────────────────────────────────────────────────┐
│                    AIMedia 核心服务 (Docker/本地)                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   FastAPI   │  │  Celery     │  │   Redis     │           │
│  │   后端服务   │  │  任务队列   │  │  消息队列   │           │
│  │   :4000     │  │             │  │             │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│         │                      │                      │        │
│         ▼                      ▼                      ▼        │
│  ┌───────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │  SQLite   │      │   FFmpeg/    │      │  AI 服务     │  │
│  │  数据库    │      │   MoviePy    │      │  (可灵/Kimi) │  │
│  │  持久化    │      │   视频合成   │      │              │  │
│  └───────────┘      └──────────────┘      └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 模块职责

### 1. API 层 (`routers/`)

| 模块 | 职责 |
|------|------|
| `projects.py` | 项目 CRUD |
| `series.py` | 系列 CRUD + 大纲生成 |
| `episodes.py` | 分集 CRUD + 脚本生成 |
| `openclaw.py` | OpenClaw 控制接口 |

### 2. 服务层 (`services/`)

| 模块 | 职责 | 状态 |
|------|------|------|
| `workflow.py` | AI 工作流编排 | ⭐ 待开发 |
| `kling.py` | 可灵视频生成 API | ⭐ 待开发 |
| `video.py` | 视频合成 | 参考 MPT |
| `voice.py` | 配音生成 | 参考 MPT |
| `subtitle.py` | 字幕生成 | 参考 MPT |

### 3. 数据模型

```
Project (项目)
  └── Series (系列)
        └── Episode (分集)
              └── VideoTask (视频任务)
```

## AI 工作流详解

### 工作流步骤

```python
# 1. 创建项目
POST /api/v1/projects/
  → {"title": "黑洞科普系列", "episode_count": 5}

# 2. 生成系列大纲
POST /api/v1/series/{series_id}/generate-outline
  → 调用 Kimi 生成系列大纲
  → 更新 Series.outline

# 3. 生成分集提纲
POST /api/v1/episodes/{episode_id}/generate-outline
  → 调用 Kimi 生成单集提纲
  → 更新 Episode.outline

# 4. 生成脚本和分镜
POST /api/v1/episodes/{episode_id}/generate-script
  → 调用 Kimi 生成完整脚本
  → 更新 Episode.script, Episode.storyboard

# 5. 生成视频
POST /api/v1/episodes/{episode_id}/generate-video
  → 调用可灵 API 生成视频片段
  → 更新 VideoTask.result_url

# 6. 生成配音
POST /api/v1/episodes/{episode_id}/generate-voice
  → 调用 MiniMax TTS
  → 更新 VideoTask.voice_url

# 7. 合成成片
POST /api/v1/episodes/{episode_id}/compose
  → FFmpeg 合成 视频+配音+字幕
  → 更新 VideoTask.final_url
```

## OpenClaw 控制接口

```bash
# 创建项目
POST /api/v1/openclaw/projects
{"title": "...", "episode_count": 5}

# 查询状态
GET /api/v1/openclaw/projects/{id}/status

# 查看队列
GET /api/v1/openclaw/queue

# 暂停/恢复/重试
POST /api/v1/openclaw/tasks/{id}/pause
POST /api/v1/openclaw/tasks/{id}/resume
POST /api/v1/openclaw/tasks/{id}/retry
```

## 扩展性设计

1. **视频源可切换**：kling ↔ jimeng ↔ 本地素材
2. **TTS 可切换**：MiniMax ↔ Edge-TTS ↔ Azure
3. **LLM 可切换**：Kimi ↔ MiniMax ↔ DeepSeek

---
*最后更新: 2026-04-08*
