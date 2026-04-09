"""
AIMedia FastAPI 应用入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_database
from app.routers import projects, series, episodes, openclaw, tasks

# 初始化数据库
init_database()

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
