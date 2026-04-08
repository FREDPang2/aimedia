"""
OpenClaw 控制接口
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Project, Series, Episode, VideoTask, TaskStatus

router = APIRouter()


class CreateProjectRequest(BaseModel):
    title: str
    description: str = ""
    target_audience: str = ""
    style: str = ""
    episode_count: int = 5


class QueueStatusResponse(BaseModel):
    pending: int
    active: int
    completed: int
    failed: int


@router.post("/projects")
def create_project(req: CreateProjectRequest, db: Session = Depends(get_db)):
    """通过 OpenClaw 创建项目"""
    project = Project(
        title=req.title,
        description=req.description,
        target_audience=req.target_audience,
        style=req.style,
        episode_count=req.episode_count
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"project_id": project.id, "status": "created"}


@router.get("/projects/{project_id}/status")
def get_project_status(project_id: int, db: Session = Depends(get_db)):
    """获取项目状态"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    series_list = db.query(Series).filter(Series.project_id == project_id).all()
    total_episodes = 0
    completed_episodes = 0

    for s in series_list:
        episodes = db.query(Episode).filter(Episode.series_id == s.id).all()
        total_episodes += len(episodes)
        completed_episodes += len([e for e in episodes if e.status == "completed"])

    return {
        "project_id": project_id,
        "status": project.status,
        "total_episodes": total_episodes,
        "completed_episodes": completed_episodes,
        "progress": (completed_episodes / total_episodes * 100) if total_episodes > 0 else 0
    }


@router.get("/queue")
def get_queue_status(db: Session = Depends(get_db)):
    """获取任务队列状态"""
    pending = db.query(VideoTask).filter(VideoTask.status == TaskStatus.PENDING.value).count()
    active = db.query(VideoTask).filter(VideoTask.status == TaskStatus.IN_PROGRESS.value).count()
    completed = db.query(VideoTask).filter(VideoTask.status == TaskStatus.COMPLETED.value).count()
    failed = db.query(VideoTask).filter(VideoTask.status == TaskStatus.FAILED.value).count()

    return QueueStatusResponse(
        pending=pending,
        active=active,
        completed=completed,
        failed=failed
    )


@router.post("/tasks/{task_id}/pause")
def pause_task(task_id: int, db: Session = Depends(get_db)):
    """暂停任务"""
    task = db.query(VideoTask).filter(VideoTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # 实现暂停逻辑
    return {"task_id": task_id, "status": "paused"}


@router.post("/tasks/{task_id}/resume")
def resume_task(task_id: int, db: Session = Depends(get_db)):
    """恢复任务"""
    task = db.query(VideoTask).filter(VideoTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "status": "resumed"}


@router.post("/tasks/{task_id}/retry")
def retry_task(task_id: int, db: Session = Depends(get_db)):
    """重试失败任务"""
    task = db.query(VideoTask).filter(VideoTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = TaskStatus.PENDING.value
    db.commit()
    return {"task_id": task_id, "status": "queued"}
