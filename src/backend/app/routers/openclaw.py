"""
OpenClaw 控制接口
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

import json

from database import get_db
from models import Project, Series, Episode, VideoTask, TaskStatus, EpisodeStatus

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


# ─── Phase 2: 列表 + 触发接口 ───────────────────────────────────────


@router.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    """列出所有项目（简要信息）"""
    projects = db.query(Project).order_by(Project.id.desc()).all()
    return [
        {"id": p.id, "title": p.title, "status": p.status, "episode_count": p.episode_count}
        for p in projects
    ]


@router.get("/projects/{project_id}/series")
def list_series(project_id: int, db: Session = Depends(get_db)):
    """列出项目下的所有系列"""
    series_list = db.query(Series).filter(Series.project_id == project_id).order_by(Series.id.desc()).all()
    return [
        {"id": s.id, "title": s.title, "status": s.status, "outline": s.outline or ""}
        for s in series_list
    ]


@router.get("/series/{series_id}/episodes")
def list_episodes(series_id: int, db: Session = Depends(get_db)):
    """列出系列下的所有分集"""
    episodes = db.query(Episode).filter(Episode.series_id == series_id).order_by(Episode.episode_number).all()
    return [
        {
            "id": e.id,
            "title": e.title or f"第{e.episode_number}集",
            "status": e.status,
            "script": e.script or "",
            "video_path": e.video_path or "",
            "episode_number": e.episode_number,
        }
        for e in episodes
    ]


@router.post("/episodes/{episode_id}/generate-video")
def trigger_episode_video(episode_id: int, db: Session = Depends(get_db)):
    """触发指定分集的视频生成（异步）"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    if episode.status not in [EpisodeStatus.SCRIPT_GENERATED.value, EpisodeStatus.VIDEO_COMPLETED.value]:
        raise HTTPException(status_code=400, detail="Script must be generated before video generation")

    episode.status = EpisodeStatus.VIDEO_GENERATING.value
    db.commit()

    def generate():
        try:
            from database import get_db as _get_db
            from app.services.video_pipeline import run_pipeline
            import tempfile

            db2 = next(_get_db())
            ep = db2.query(Episode).filter(Episode.id == episode_id).first()
            if not ep or not ep.script:
                raise ValueError("Episode or script not found")

            output_dir = tempfile.gettempdir()
            ok, msg, video_path = run_pipeline(
                episode_id=episode_id,
                script_json=ep.script,
                output_dir=output_dir,
            )

            db3 = next(_get_db())
            ep2 = db3.query(Episode).filter(Episode.id == episode_id).first()
            if ep2:
                if ok:
                    ep2.video_path = video_path
                    ep2.status = EpisodeStatus.VIDEO_COMPLETED.value
                    print(f"[OPENCLAW] Video pipeline complete: {video_path}")
                else:
                    ep2.status = EpisodeStatus.VIDEO_FAILED.value
                    print(f"[OPENCLAW] Video pipeline failed: {msg}")
                db3.commit()
            db3.close()
        except Exception as e:
            print(f"[OPENCLAW] Video pipeline error: {e}")
            try:
                from database import get_db as _get_db
                db_err = next(_get_db())
                ep_err = db_err.query(Episode).filter(Episode.id == episode_id).first()
                if ep_err:
                    ep_err.status = EpisodeStatus.VIDEO_FAILED.value
                    db_err.commit()
                db_err.close()
            except Exception:
                pass

    import threading
    threading.Thread(target=generate, daemon=True).start()
    return {"episode_id": episode_id, "status": "triggered", "message": "视频生成任务已加入队列"}


@router.get("/episodes/{episode_id}")
def get_episode(episode_id: int, db: Session = Depends(get_db)):
    """获取分集详情，包括 video_path"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return {
        "id": episode.id,
        "title": episode.title or f"第{episode.episode_number}集",
        "status": episode.status,
        "script": episode.script or "",
        "video_path": episode.video_path or "",
        "episode_number": episode.episode_number,
        "description": episode.description or "",
    }
