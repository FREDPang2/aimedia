"""
系列路由
"""

import asyncio
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Series, SeriesStatus, Project

router = APIRouter()


class SeriesCreate(BaseModel):
    project_id: int
    title: str
    description: str = ""


class SeriesUpdate(BaseModel):
    title: str
    description: str = ""
    outline: str = ""


def _series_to_response(s: Series, episode_count: int) -> dict:
    return {
        "id": s.id,
        "project_id": s.project_id,
        "title": s.title,
        "description": s.description or "",
        "outline": s.outline or "",
        "status": s.status,
        "episode_count": episode_count,
        "created_at": str(s.created_at) if s.created_at else ""
    }


@router.post("/")
def create_series(series: SeriesCreate, db: Session = Depends(get_db)):
    """创建新系列"""
    db_series = Series(
        project_id=series.project_id,
        title=series.title,
        description=series.description or "",
        status=SeriesStatus.DRAFT.value
    )
    db.add(db_series)
    db.commit()
    db.refresh(db_series)
    return _series_to_response(db_series, 0)


@router.get("/")
def list_series(project_id: int = None, db: Session = Depends(get_db)):
    """获取所有系列"""
    query = db.query(Series)
    if project_id:
        query = query.filter(Series.project_id == project_id)
    series_list = query.all()
    from models import Episode
    result = []
    for s in series_list:
        episode_count = db.query(Episode).filter(Episode.series_id == s.id).count()
        result.append(_series_to_response(s, episode_count))
    return result


@router.get("/{series_id}")
def get_series(series_id: int, db: Session = Depends(get_db)):
    """获取单个系列"""
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    from models import Episode
    episode_count = db.query(Episode).filter(Episode.series_id == series.id).count()
    return _series_to_response(series, episode_count)


@router.put("/{series_id}")
def update_series(series_id: int, update: SeriesUpdate, db: Session = Depends(get_db)):
    """更新系列"""
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    series.title = update.title
    series.description = update.description
    if update.outline is not None:
        series.outline = update.outline
    db.commit()
    db.refresh(series)
    from models import Episode
    episode_count = db.query(Episode).filter(Episode.series_id == series.id).count()
    return _series_to_response(series, episode_count)


@router.post("/{series_id}/generate-outline")
def generate_outline(series_id: int, db: Session = Depends(get_db)):
    """使用 AI 生成大纲"""
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    # 获取项目信息
    project = db.query(Project).filter(Project.id == series.project_id).first()
    project_title = project.title if project else "未命名项目"
    project_desc = project.description if project else ""
    episode_count = project.episode_count if project else 5

    # 同步调用异步 AI 生成（后台进行）
    series.status = SeriesStatus.OUTLINE_GENERATED.value
    db.commit()

    # 后台异步执行 AI 生成
    try:
        from app.services.workflow import create_series_outline
        import threading

        def generate():
            try:
                result = asyncio.run(create_series_outline(
                    project_id=series.project_id,
                    project_title=project_title,
                    project_description=project_desc,
                    episode_count=episode_count
                ))
                # 更新大纲内容
                db2 = next(get_db())
                s = db2.query(Series).filter(Series.id == series_id).first()
                if s:
                    s.outline = result.get("outline", "")
                    db2.commit()
            except Exception as e:
                print(f"[ERROR] Outline generation failed: {e}")

        thread = threading.Thread(target=generate)
        thread.start()
    except Exception as e:
        print(f"[WARN] Failed to start outline generation thread: {e}")

    return {"message": "Outline generation started", "series_id": series_id, "status": series.status}
