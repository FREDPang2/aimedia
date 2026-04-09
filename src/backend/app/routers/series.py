"""
系列路由
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Series, SeriesStatus

router = APIRouter()


class SeriesCreate(BaseModel):
    project_id: int
    title: str
    description: str = ""


class SeriesUpdate(BaseModel):
    title: str
    description: str = ""
    outline: str = ""


class SeriesResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: str = ""
    outline: str = ""
    status: str
    episode_count: int = 0
    created_at: str = ""

    class Config:
        from_attributes = True


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


@router.post("")
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


@router.get("")
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
    """触发 AI 大纲生成"""
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    series.status = SeriesStatus.OUTLINE_GENERATED.value
    db.commit()
    # TODO: 调用 workflow service 生成大纲
    # from app.services.workflow import create_series_outline
    # asyncio.create_task(create_series_outline(series_id))
    return {"message": "Outline generation started", "series_id": series_id, "status": series.status}
