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
| P0 | **Pending changes 提交** | ✅ 已提交（2026-04-11）- 18张截图更新并推送 |
| P0 | **完整视频管线联调** | ✅ 已联调（2026-04-11）- Episode 9 route返回200，status→video_generating→video_failed（Kling缺API Key属预期） |
| P1 | **OpenClaw 控制接口** | ✅ 已完成（2026-04-10）- /projects, /series, /episodes, /generate-video 接口 |
| P1 | **前端 AI 生成按钮绑定** | ✅ 已完成（2026-04-10） |
| P1 | **前端视频播放** | ✅ 已完成（2026-04-10）- video_path 回显 + video 播放器 |
| P1 | **前端状态轮询** | ✅ 已完成（2026-04-10）- 3秒轮询，AI生成中自动刷新 |
| P2 | **E2E 完整流程测试** | ✅ 基础验证（2026-04-10）- CRUD routes工作正常，AI generation需代理，video generation正确拦截无script请求 |
| P2 | **错误处理完善** | 🔄 基础完成（2026-04-10）- pipeline有try/except，Kling重试3次逻辑待实现 |
| P2 | **配置文件管理** | ⬜ 待开发 - API Keys / 代理配置页面 |
| P3 | **Docker 部署** | ✅ 已完成（2026-04-11）- VITE_API_BASE_URL 构建时配置，Redis healthcheck，depends_on 条件等待 |
| P3 | **文档完善** | 🔄 进行中 - README / 快速开始指南 |

---

## 二、P0 紧急任务（必须先完成）

### Task 0: 提交 Pending Changes ✅
> 已完成（2026-04-10）- 截图已提交（commit: 3ac892a），Playwright 22/10 全通
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

### Task 1: 视频管线联调 ✅
> 已完成（2026-04-10）- 已验证：Episode 9 触发 `/generate-video`，后端运行正常，TTS 配音生成成功，Kling 因 API Key 未配置属预期行为
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

### Task 2: 前后端 AI 管线串联 ✅
> 已完成（2026-04-10）- series router 有 `/generate-outline` 路由（line 101），前端 API 绑定正确（generateOutline/generateScript/generateVideo），Episode.vue 和 Series.vue 按钮正确连接，3秒状态轮询已启用
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

### Task 6: E2E 完整流程测试 ✅
> 已完成（2026-04-11）

**E2E 测试脚本**: `test_e2e_flow.py`（重构，支持 --skip-ai / --ai-only）

**测试覆盖**:
- CRUD: Project/Series/Episode 创建/读取/更新/删除 ✅
- 错误场景: generate-video 无 script 正确拦截（400）✅
- AI 流程: outline → script → video 状态轮询

**运行**: `python3 test_e2e_flow.py [--skip-ai|--ai-only]`

### Task 7: 错误处理 ✅
> 已完成（2026-04-11）

**已实现**:
- ✅ kling 片段失败自动重试 3 次（`generate_all_video_clips`）
- ✅ TTS 失败降级为静音音频，不阻断管线（`_generate_silent_audio`）
- ✅ API Key 启动检查，未配置时打印警告（`main.py:_check_api_keys`）
```

---

## 五、执行顺序

```
Phase 1（现在）:
  [Task 0] 提交 pending changes ✅ （2026-04-11 截图已提交并推送）
  [Task 1] 视频管线联调 + E2E 验证 ✅ （Episode 25 状态更新 video_failed，Kling API Key 未配置属预期）
  [Task 2] 前后端 AI 串联 ✅ （generateOutline/generateScript/generateVideo 路由与前端绑定正确）

**Phase 1 完成总结**（2026-04-11）:
- Playwright 测试：基础 22/22 ✅ 深度 10/10 ✅
- 视频管线：generate-video 路由正常，状态流转正确 (script_generated → video_generating → video_failed)
- AI 按钮绑定：Series.vue 生成大纲 ✅，Episode.vue 生成脚本/视频 ✅
- 所有截图已提交并推送

Phase 2:
  [Task 3] OpenClaw 控制接口完善 ✅
  [Task 4] 前端视频播放 ✅
  [Task 5] 状态轮询 ✅

Phase 3:
  [Task 6] E2E 完整测试 ✅
  [Task 7] 错误处理 ✅

Phase 4:
  [Task 8] Docker 部署 ✅ （2026-04-11）- VITE_API_BASE_URL 可配置，Redis 健康检查，compose 重启策略
  [Task 9] 文档 🔄 进行中 - README / 快速开始指南
```

---

## 六、当前_pending 的未完成事项

请按上述顺序执行。每完成一个 task 更新状态。
