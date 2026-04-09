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
    description: str = ""


class EpisodeUpdate(BaseModel):
    title: str
    description: str = ""
    outline: str = ""
    script: str = ""
    storyboard: str = ""


def _episode_to_response(ep: Episode) -> dict:
    return {
        "id": ep.id,
        "series_id": ep.series_id,
        "episode_number": ep.episode_number,
        "title": ep.title,
        "description": ep.description or "",
        "outline": ep.outline or "",
        "script": ep.script or "",
        "storyboard": ep.storyboard or "",
        "status": ep.status,
        "created_at": str(ep.created_at) if ep.created_at else "",
        "tasks": []
    }


@router.post("")
def create_episode(episode: EpisodeCreate, db: Session = Depends(get_db)):
    """创建新分集"""
    db_episode = Episode(
        series_id=episode.series_id,
        episode_number=episode.episode_number,
        title=episode.title,
        description=episode.description or "",
        status=EpisodeStatus.DRAFT.value
    )
    db.add(db_episode)
    db.commit()
    db.refresh(db_episode)
    return _episode_to_response(db_episode)


@router.get("")
def list_episodes(series_id: int = None, db: Session = Depends(get_db)):
    """获取所有分集"""
    query = db.query(Episode)
    if series_id:
        query = query.filter(Episode.series_id == series_id)
    episodes = query.order_by(Episode.episode_number).all()
    return [_episode_to_response(ep) for ep in episodes]


@router.get("/{episode_id}")
def get_episode(episode_id: int, db: Session = Depends(get_db)):
    """获取单个分集"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return _episode_to_response(episode)


@router.put("/{episode_id}")
def update_episode(episode_id: int, update: EpisodeUpdate, db: Session = Depends(get_db)):
    """更新分集"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    episode.title = update.title
    episode.description = update.description
    if update.outline is not None:
        episode.outline = update.outline
    if update.script is not None:
        episode.script = update.script
    if update.storyboard is not None:
        episode.storyboard = update.storyboard
    db.commit()
    db.refresh(episode)
    return _episode_to_response(episode)


@router.patch("/{episode_id}/script")
def patch_episode_script(episode_id: int, body: dict, db: Session = Depends(get_db)):
    """更新分集脚本"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    script = body.get("script")
    if script is not None:
        episode.script = script
        episode.status = EpisodeStatus.SCRIPT_GENERATED.value
    db.commit()
    return {"message": "Script updated"}


@router.post("/{episode_id}/generate-script")
def generate_script(episode_id: int, db: Session = Depends(get_db)):
    """触发 AI 脚本生成任务"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    episode.status = EpisodeStatus.SCRIPT_GENERATING.value
    db.commit()
    return {"message": "Script generation started", "episode_id": episode_id, "status": episode.status}


@router.post("/{episode_id}/generate-video")
def generate_video(episode_id: int, db: Session = Depends(get_db)):
    """触发视频生成任务"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    if episode.status not in [EpisodeStatus.SCRIPT_GENERATED.value, EpisodeStatus.VIDEO_GENERATING.value]:
        raise HTTPException(status_code=400, detail="Script must be generated before video generation")
    episode.status = EpisodeStatus.VIDEO_GENERATING.value
    db.commit()
    return {"message": "Video generation started", "episode_id": episode_id, "status": episode.status}
