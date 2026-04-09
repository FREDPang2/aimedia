"""
任务路由
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import VideoTask, TaskStatus

router = APIRouter()


class TaskResponse(BaseModel):
    id: int
    episode_id: int
    task_type: str
    status: str
    progress: int
    result_url: str = ""
    error_message: str = ""
    created_at: str = ""
    completed_at: str = ""

    class Config:
        from_attributes = True


@router.get("/", response_model=List[TaskResponse])
def list_tasks(
    episode_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取任务列表"""
    query = db.query(VideoTask)
    if episode_id is not None:
        query = query.filter(VideoTask.episode_id == episode_id)
    if status is not None:
        query = query.filter(VideoTask.status == status)
    tasks = query.order_by(VideoTask.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "episode_id": t.episode_id,
            "task_type": t.task_type,
            "status": t.status,
            "progress": t.progress,
            "result_url": t.result_url or "",
            "error_message": t.error_message or "",
            "created_at": str(t.created_at) if t.created_at else "",
            "completed_at": str(t.completed_at) if t.completed_at else ""
        }
        for t in tasks
    ]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """获取单个任务"""
    task = db.query(VideoTask).filter(VideoTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": task.id,
        "episode_id": task.episode_id,
        "task_type": task.task_type,
        "status": task.status,
        "progress": task.progress,
        "result_url": task.result_url or "",
        "error_message": task.error_message or "",
        "created_at": str(task.created_at) if task.created_at else "",
        "completed_at": str(task.completed_at) if task.completed_at else ""
    }
