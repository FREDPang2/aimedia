"""
AIMedia FastAPI 应用入口
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_database
from app.routers import projects, series, episodes, openclaw, tasks


def _check_api_keys():
    """启动时检查关键 API Key，未配置时打印警告（不影响启动）"""
    warnings = []
    if not os.environ.get("MOONSHOT_API_KEY"):
        warnings.append("⚠️  MOONSHOT_API_KEY 未设置 — AI 大纲/脚本生成将失败")
    if not os.environ.get("KLING_API_KEY"):
        warnings.append("⚠️  KLING_API_KEY 未设置 — 视频生成将失败")
    if not os.environ.get("MINIMAX_API_KEY"):
        warnings.append("⚠️  MINIMAX_API_KEY 未设置 — TTS 配音生成将失败")
    for w in warnings:
        print(w)
    return warnings


# 初始化数据库
init_database()

# 启动时检查配置
_check_api_keys()

# 创建 FastAPI 应用
app = FastAPI(
    title="AIMedia API",
    description="AI 视频生产管线 API",
    version="0.1.0",
    redirect_slashes=True  # 允许尾部斜杠重定向，兼容 /series 和 /series/ 两种调用
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(series.router, prefix="/api/v1/series", tags=["series"])
app.include_router(episodes.router, prefix="/api/v1/episodes", tags=["episodes"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(openclaw.router, prefix="/api/v1/openclaw", tags=["openclaw"])


@app.get("/")
async def root():
    return {"message": "AIMedia API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
