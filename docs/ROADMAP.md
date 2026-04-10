# AIMedia 开发 Roadmap

> 制定时间：2026-04-10  
> 负责人：零（协调） + 代码小一（执行）+ Claude Code（开发）

---

## 项目目标

基于 AI 的系列视频自动化生产管线：
```
选题 → 系列大纲 → 分集提纲 → 脚本+分镜 → 视频片段 → 配音合成 → 成片
```

---

## 一、当前状态

### 已完成 ✅
| 模块 | 状态 | 说明 |
|------|------|------|
| 数据模型 | ✅ | Project / Series / Episode / VideoTask |
| 后端基础 | ✅ | FastAPI，23个路由，SQLite |
| 前端骨架 | ✅ | Vue3 + Element Plus，4个页面 |
| Playwright 测试 | ✅ | 22项基础 + 10项深度，全通 |
| workflow 服务 | ✅ | Moonshot API 集成（大纲/提纲/脚本/分镜）|
| kling 服务 | ✅ | 可灵视频 API |
| voice_tts 服务 | ✅ | MiniMax TTS |
| video_compose 服务 | ✅ | FFmpeg 视频合成 |
| video_pipeline 管 线 | ✅ | 完整管线编排 |

### 待完成 ⬜
| 优先级 | 功能 | 状态 |
|--------|------|------|
| P0 | **Pending changes 提交** | 有未 commit 的修改 |
| P0 | **完整视频管线联调** | pipeline 各环节串通 |
| P1 | **OpenClaw 控制接口** | openclaw router 完善 |
| P1 | **前端 AI 生成按钮绑定** | 调用后端 AI 管线 |
| P1 | **前端视频播放** | video_path 回显 + 播放 |
| P2 | **E2E 完整流程测试** | 从创建项目到生成视频 |
| P2 | **错误处理完善** | 各环节超时/重试/降级 |
| P2 | **配置文件管理** | API Keys / 代理配置页面 |
| P3 | **Docker 部署** | docker-compose.yml |
| P3 | **文档完善** | API 文档 / 用户指南 |

---

## 二、P0 紧急任务（必须先完成）

### Task 0: 提交 Pending Changes
```bash
# 当前有未提交的修改：
# - episodes.py (新增 generate-video 路由)
# - kling.py (增强)
# - video_compose.py (增强)
# - voice_tts.py (增强)
# - models.py (新增状态枚举)
# - video_pipeline.py (新文件)
# - 多张截图更新

# 需要：
1. git add 所有修改
2. 写清楚 commit message
3. 验证后端仍可正常启动
```

### Task 1: 视频管线联调
```python
# run_pipeline() 需要完整串通：
run_pipeline(episode_id, script_json, output_dir)
  → parse_script(script_json)        ✅ 已有
  → voice_tts.generate_voice()       ✅ 已有
  → kling.generate_video()            ✅ 已有
  → kling.wait_for_completion()       ✅ 已有
  → video_compose.compose_video()    ✅ 已有
  → 更新 episode.video_path           🔄 待验证

# 验证方式：
1. 创建 episode，填入测试脚本 JSON
2. 调用 /api/v1/episodes/{id}/generate-video
3. 检查 episode.video_path 是否写入
4. 检查文件是否真实存在
```

### Task 2: 前后端 AI 管线串联
```
前端：
  [生成大纲] → POST /api/v1/series/{id}/generate-outline
  [生成脚本] → POST /api/v1/episodes/{id}/generate-script
  [生成视频] → POST /api/v1/episodes/{id}/generate-video

后端：
  generate-outline → workflow.create_series_outline() → 更新 series.outline
  generate-script → workflow.create_script_storyboard() → 更新 episode.script
  generate-video → video_pipeline.run_pipeline() → 更新 episode.video_path

需要：
1. 检查 series router 是否有 generate-outline 路由
2. 检查前端按钮是否正确调用上述 API
3. 前端状态轮询展示 AI 生成进度
```

---

## 三、P1 功能完善

### Task 3: OpenClaw 控制接口
```
路由：/api/v1/openclaw/
功能：
  - 列出当前所有 Project/Series/Episode
  - 触发指定 episode 的视频生成
  - 查询任务状态
  - 获取生成结果（video_path）
```

### Task 4: 前端视频播放
```
1. Episode 页面显示 video_path
2. 如果 video_path 存在，显示 <video> 播放器
3. 支持 MP4/WebM 格式
```

### Task 5: 前端状态轮询
```
AI 生成过程中：
1. 前端显示 loading 状态
2. 每 3 秒轮询 GET /api/v1/episodes/{id}
3. status 变化后刷新页面（outline_generated / script_generated / video_completed 等）
```

---

## 四、P2 测试与稳健性

### Task 6: E2E 完整流程测试
```python
# 使用 Playwright 或 httpx：
1. 创建 Project("测试项目")
2. 创建 Series（关联 Project）
3. 调用 generate-outline，验证 outline 生成
4. 创建 Episode（关联 Series）
5. 调用 generate-script，验证 script 生成
6. 调用 generate-video，验证视频文件生成
7. 验证 episode.video_path 指向真实文件
```

### Task 7: 错误处理
```
- kling API 超时 → 重试 3 次
- TTS 失败 → 降级为静音或默认语音
- FFmpeg 合成失败 → 记录日志，返回友好错误
- API Key 缺失 → 启动时检查，缺少则提示
```

---

## 五、执行顺序

```
Phase 1（现在）:
  [Task 0] 提交 pending changes
  [Task 1] 视频管线联调 + E2E 验证
  [Task 2] 前后端 AI 串联

Phase 2:
  [Task 3] OpenClaw 控制接口完善
  [Task 4] 前端视频播放
  [Task 5] 状态轮询

Phase 3:
  [Task 6] E2E 完整测试
  [Task 7] 错误处理

Phase 4:
  [Task 8] Docker 部署
  [Task 9] 文档
```

---

## 六、当前_pending 的未完成事项

请按上述顺序执行。每完成一个 task 更新状态。
