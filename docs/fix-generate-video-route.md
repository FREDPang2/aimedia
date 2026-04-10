# Fix: generate-video 路由修复文档

## 问题描述

`POST /api/v1/episodes/{id}/generate-video` 当前只修改了数据库状态（`VIDEO_GENERATING`），但**从未调用** `video_pipeline.run_pipeline()` 执行真正的视频生成。

管线代码（`video_pipeline.py`）完全就绪，但路由层没有连接它。

---

## 根因

参考 `generate_script` 路由的实现，它通过 `threading.Thread` + `asyncio.run()` 在后台线程中异步执行 AI 生成，完成后更新数据库状态。

`generate_video` 路由模仿了 `generate_script` 的状态设置，但**遗漏了最关键的线程启动代码**。

---

## 参考文件

| 文件 | 路径 |
|------|------|
| 路由文件 | `src/backend/app/routers/episodes.py` |
| 管线入口 | `src/backend/app/services/video_pipeline.py` |
| 数据模型 | `src/backend/models.py` |
| 异步模式参考 | `generate_script` 路由（同一文件内） |

---

## 修复步骤

### Step 1: 确认 EpisodeStatus 枚举值

确保 `models.py` 中包含 `VIDEO_GENERATING`、`VIDEO_COMPLETED`、`VIDEO_FAILED` 三个状态值。如果不存在，需要添加。

### Step 2: 修改 `generate_video` 路由

在 `threading.Thread` 中调用 `video_pipeline.run_pipeline()`，完整流程：

1. **获取 episode 信息**（在主线程做完，因为有 db session）
2. **更新状态**为 `VIDEO_GENERATING`
3. **启动后台线程**，在线程中：
   - 重新获取数据库 session
   - 调用 `run_pipeline(episode_id, script_json, output_dir)`
   - 成功 → 更新状态为 `VIDEO_COMPLETED`，保存最终视频路径
   - 失败 → 更新状态为 `VIDEO_FAILED`

### Step 3: run_pipeline 调用参数

```python
# output_dir 建议使用 /tmp/aimedia/videos 或项目配置的存储路径
# script_json 从 episode.script 字段获取（JSON 字符串）
# 其他参数使用默认值
```

---

## 完整代码（可直接替换）

### 替换 `src/backend/app/routers/episodes.py` 中的 `generate_video` 路由

```python
@router.post("/{episode_id}/generate-video")
def generate_video(episode_id: int, db: Session = Depends(get_db)):
    """
    触发视频生成任务
    完整流程：解析脚本 → MiniMax TTS 配音 → Kling 文生视频 → FFmpeg 合成最终成片
    """
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # 前置条件检查：必须有脚本才能生成视频
    if not episode.script or not episode.script.strip():
        raise HTTPException(status_code=400, detail="Episode must have a script before video generation")

    # 当前状态必须是已完成脚本生成，或者正在生成的（允许重试）
    allowed_statuses = [
        EpisodeStatus.SCRIPT_GENERATED.value,
        EpisodeStatus.VIDEO_GENERATING.value,  # 允许重试
    ]
    if episode.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Episode status must be 'script_generated' or 'video_generating', got '{episode.status}'"
        )

    # 记录脚本内容（用于线程中传递）
    script_content = episode.script

    # 更新状态为生成中
    episode.status = EpisodeStatus.VIDEO_GENERATING.value
    db.commit()

    # 后台异步执行视频生成管线
    try:
        from app.services import video_pipeline

        def run_video_generation():
            """在后台线程中执行完整的视频生成管线"""
            try:
                # Step 1: 解析脚本获取场景
                scenes = video_pipeline.parse_script(script_content)
                print(f"[generate-video] episode={episode_id}, scenes={len(scenes)}")

                # Step 2: 设置输出目录
                output_dir = "/tmp/aimedia/videos"
                import os
                os.makedirs(output_dir, exist_ok=True)

                # Step 3: 调用管线（阻塞直到完成或失败）
                ok, msg, output_path = video_pipeline.run_pipeline(
                    episode_id=episode_id,
                    script_json=script_content,
                    output_dir=output_dir,
                    voice="longxiao",
                    aspect_ratio="16:9",
                    kling_model="c1",
                )

                # Step 4: 更新数据库
                from database import get_db as _get_db
                db2 = next(_get_db())
                ep = db2.query(Episode).filter(Episode.id == episode_id).first()
                if ep:
                    if ok:
                        ep.status = EpisodeStatus.VIDEO_COMPLETED.value
                        ep.video_path = output_path or ""
                        print(f"[generate-video] SUCCESS episode={episode_id}, output={output_path}")
                    else:
                        ep.status = EpisodeStatus.VIDEO_FAILED.value
                        ep.error_message = msg
                        print(f"[generate-video] FAILED episode={episode_id}, error={msg}")
                    db2.commit()

            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"[generate-video] EXCEPTION episode={episode_id}: {e}")
                from database import get_db as _get_db
                db2 = next(_get_db())
                ep = db2.query(Episode).filter(Episode.id == episode_id).first()
                if ep:
                    ep.status = EpisodeStatus.VIDEO_FAILED.value
                    ep.error_message = str(e)
                    db2.commit()

        thread = threading.Thread(target=run_video_generation)
        thread.start()

    except Exception as e:
        print(f"[WARN] Failed to start video generation thread: {e}")
        episode.status = EpisodeStatus.VIDEO_FAILED.value
        episode.error_message = f"Failed to start generation: {str(e)}"
        db.commit()

    return {
        "message": "Video generation started",
        "episode_id": episode_id,
        "status": EpisodeStatus.VIDEO_GENERATING.value
    }
```

### Step 4: 修改 models.py

**⚠️ 重要发现**：`src/backend/models.py`（注意不是 `app/models.py`）中：

- ✅ `EpisodeStatus.VIDEO_GENERATING` 已存在
- ✅ `Episode.error_message` 字段已存在
- ❌ `EpisodeStatus.VIDEO_COMPLETED` 和 `VIDEO_FAILED` **缺失，需要添加**
- ❌ `Episode.video_path` 字段 **缺失，需要添加**

在 `src/backend/models.py` 中进行以下修改：

**1. EpisodeStatus 枚举新增两个值：**

```python
class EpisodeStatus(str, Enum):
    DRAFT = "draft"
    OUTLINE_GENERATED = "outline_generated"
    SCRIPT_GENERATING = "script_generating"
    SCRIPT_GENERATED = "script_generated"
    VIDEO_GENERATING = "video_generating"
    VIDEO_COMPLETED = "video_completed"   # ← 新增
    VIDEO_FAILED = "video_failed"          # ← 新增
    FAILED = "failed"
```

**2. Episode 模型新增 video_path 字段：**

在 `Episode` 类中（`error_message` 字段附近）添加：

```python
video_path = Column(String, default="")    # 最终视频文件路径（管线完成后写入）
```

---

## 验证方法

### 1. 手动测试（无真实 API）

```bash
# 启动后端
cd /home/fredrog/Aiproject/AIMedia/src/backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 4000

# 创建测试项目/系列/分集，并确保分集有脚本
curl -X POST http://localhost:4000/api/v1/episodes/1/generate-video

# 检查状态
curl http://localhost:4000/api/v1/episodes/1
```

### 2. 使用 Playwright 端到端测试

确保前端 "生成视频" 按钮能触发管线。

---

## 注意事项

1. **数据库 session 限制**：SQLAlchemy 的 session 不能跨线程共享，必须在线程中用 `next(get_db())` 重新获取
2. **asyncio 限制**：`run_pipeline` 内部是同步函数（调用 httpx 的 `AsyncClient` 用了 `async/await`，但入口 `run_pipeline` 是同步的），不需要 `asyncio.run()`
3. **Kling/MiniMax API Key**：真实环境需要设置 `KLING_API_KEY`、`MINIMAX_API_KEY` 环境变量
4. **FFmpeg**：确保已安装（`sudo apt install ffmpeg`）

---

## 修改文件清单

| 文件 | 操作 |
|------|------|
| `src/backend/models.py` | 新增 `VIDEO_COMPLETED`、`VIDEO_FAILED` 枚举值；新增 `video_path` 字段 |
| `src/backend/app/routers/episodes.py` | 替换 `generate_video` 路由（加入线程调用 `run_pipeline`） |
