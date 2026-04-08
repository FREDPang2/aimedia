# AIMedia API 规范

## 基础信息

- **Base URL**: `http://localhost:4000/api/v1`
- **Content-Type**: `application/json`
- **认证**: 暂不启用（V1 内网部署）

---

## 项目管理接口

### 创建选题

```http
POST /topics
```

**请求体**:
```json
{
  "title": "黑洞科普系列",
  "description": "用通俗语言解释黑洞的形成、结构和影响",
  "target_audience": "普通大众",
  "style": "科普/动画",
  "episode_count": 5
}
```

**响应**:
```json
{
  "id": "topic_abc123",
  "title": "黑洞科普系列",
  "status": "created",
  "created_at": "2026-04-08T15:44:00Z"
}
```

### 生成系列大纲

```http
POST /topics/{topic_id}/generate-outline
```

**请求体**:
```json
{
  "model": "kimi/kimi-code",
  "temperature": 0.7
}
```

**响应**:
```json
{
  "series_id": "series_xyz789",
  "outline": {
    "title": "黑洞探秘",
    "episodes": [
      {
        "episode_number": 1,
        "title": "什么是黑洞",
        "duration": "3-5分钟",
        "key_points": ["..."]
      }
    ]
  },
  "status": "outline_generated"
}
```

### 获取系列详情

```http
GET /series/{series_id}
```

**响应**:
```json
{
  "id": "series_xyz789",
  "topic_id": "topic_abc123",
  "title": "黑洞探秘",
  "status": "outline_generated",
  "episodes": [...],
  "progress": {
    "total": 5,
    "completed": 0,
    "in_progress": 0
  }
}
```

---

## 分集管理接口

### 生成单集脚本

```http
POST /episodes/{episode_id}/generate-script
```

**请求体**:
```json
{
  "model": "kimi/kimi-code",
  "tone": "通俗有趣",
  "word_count": 800
}
```

**响应**:
```json
{
  "episode_id": "ep_def456",
  "script": {
    "scenes": [
      {
        "scene_number": 1,
        "visual": "宇宙星空背景，镜头推进",
        "narration": "在浩瀚的宇宙中，有一种神秘的天体...",
        "duration": 15
      }
    ],
    "total_duration": 240
  },
  "storyboard": [...]
}
```

### 开始视频生成

```http
POST /episodes/{episode_id}/generate-video
```

**请求体**:
```json
{
  "video_provider": "kling",
  "voice_provider": "minimax",
  "bgm_style": "epic"
}
```

**响应**:
```json
{
  "task_id": "task_ghi789",
  "episode_id": "ep_def456",
  "status": "queued",
  "estimated_time": 600
}
```

---

## OpenClaw 控制接口

### 获取项目列表

```http
GET /openclaw/projects
```

### 获取任务状态

```http
GET /openclaw/tasks/{task_id}/status
```

**响应**:
```json
{
  "task_id": "task_ghi789",
  "status": "in_progress",
  "current_step": "generate_video_segments",
  "progress": 45,
  "logs": [...]
}
```

### 暂停任务

```http
POST /openclaw/tasks/{task_id}/pause
```

### 恢复任务

```http
POST /openclaw/tasks/{task_id}/resume
```

### 重试失败步骤

```http
POST /openclaw/tasks/{task_id}/retry
```

### 获取队列状态

```http
GET /openclaw/queue
```

**响应**:
```json
{
  "pending": 3,
  "active": 1,
  "completed": 10,
  "failed": 0
}
```

---

## WebSocket 实时推送

**连接**: `ws://localhost:4000/ws/tasks/{task_id}`

**消息格式**:
```json
{
  "type": "progress_update",
  "task_id": "task_ghi789",
  "step": "generate_voiceover",
  "progress": 60,
  "message": "正在合成配音 (2/3)..."
}
```

---

## 错误处理

**统一错误格式**:
```json
{
  "error": {
    "code": "VIDEO_GENERATION_FAILED",
    "message": "可灵 API 返回错误",
    "details": {
      "provider": "kling",
      "raw_error": "..."
    }
  }
}
```

**常见错误码**:
- `400` - 请求参数错误
- `404` - 资源不存在
- `429` - API 限流
- `500` - 内部错误
- `502` - 外部 AI 服务错误

---

## 模型别名

| 别名 | 实际模型 |
|------|----------|
| `kimi` | kimi/kimi-code |
| `minimax` | minimax/MiniMax-M2.7-highspeed |
| `kling` | 可灵 API |
| `jimeng` | 即梦 API |

---
*最后更新: 2026-04-08*
