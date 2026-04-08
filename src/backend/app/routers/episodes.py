"""
分集路由
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Episode, EpisodeStatus

router = APIRouter()


class EpisodeCreate(BaseModel):
    series_id: int
    episode_number: int
    title: str


class EpisodeResponse(BaseModel):
    id: int
    series_id: int
    episode_number: int
    title: str
    outline: str = ""
    script: str = ""
    storyboard: str = ""
    status: str

    class Config:
        from_attributes = True


@router.post("/", response_model=EpisodeResponse)
def create_episode(episode: EpisodeCreate, db: Session = Depends(get_db)):
    """创建新分集"""
    db_episode = Episode(
        series_id=episode.series_id,
        episode_number=episode.episode_number,
        title=episode.title,
        status=EpisodeStatus.DRAFT.value
    )
    db.add(db_episode)
    db.commit()
    db.refresh(db_episode)
    return db_episode


@router.get("/", response_model=List[EpisodeResponse])
def list_episodes(series_id: int = None, db: Session = Depends(get_db)):
    """获取所有分集"""
    query = db.query(Episode)
    if series_id:
        query = query.filter(Episode.series_id == series_id)
    return query.order_by(Episode.episode_number).all()


@router.get("/{episode_id}", response_model=EpisodeResponse)
def get_episode(episode_id: int, db: Session = Depends(get_db)):
    """获取单个分集"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode


@router.patch("/{episode_id}/script")
def update_script(episode_id: int, script: str, db: Session = Depends(get_db)):
    """更新分集脚本"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    episode.script = script
    episode.status = EpisodeStatus.SCRIPT_GENERATED.value
    db.commit()
    return {"message": "Script updated"}
