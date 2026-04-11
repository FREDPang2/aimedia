"""
分集路由
"""

import asyncio
import threading
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Episode, EpisodeStatus, Series

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
    status: str = ""


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
        "video_path": ep.video_path or "",
        "status": ep.status,
        "created_at": str(ep.created_at) if ep.created_at else "",
        "tasks": []
    }


@router.post("/")
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


@router.get("/")
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
    if update.script:
        episode.script = update.script
    if update.storyboard is not None:
        episode.storyboard = update.storyboard
    if update.status:
        episode.status = update.status
    db.commit()
    db.refresh(episode)
    return _episode_to_response(episode)
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
    """使用 AI 生成视频脚本"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    episode.status = EpisodeStatus.SCRIPT_GENERATING.value
    db.commit()

    # 获取系列信息用于提示词
    series = db.query(Series).filter(Series.id == episode.series_id).first()
    series_theme = series.title if series else "未指定主题"

    # 后台异步执行 AI 生成
    try:
        from app.services.workflow import create_script_storyboard

        def generate():
            try:
                result = asyncio.run(create_script_storyboard(
                    episode_id=episode_id,
                    episode_title=episode.title,
                    episode_number=episode.episode_number,
                    episode_outline=episode.outline or ""
                ))
                # 更新脚本内容
                from database import get_db as _get_db
                db2 = next(_get_db())
                ep = db2.query(Episode).filter(Episode.id == episode_id).first()
                if ep:
                    ep.script = result.get("script", "")
                    ep.status = EpisodeStatus.SCRIPT_GENERATED.value
                    db2.commit()
            except Exception as e:
                print(f"[ERROR] Script generation failed for episode {episode_id}: {e}")
                from database import get_db as _get_db
                db2 = next(_get_db())
                ep = db2.query(Episode).filter(Episode.id == episode_id).first()
                if ep:
                    ep.status = EpisodeStatus.FAILED.value
                    db2.commit()

        thread = threading.Thread(target=generate)
        thread.start()
    except Exception as e:
        print(f"[WARN] Failed to start script generation thread: {e}")

    return {"message": "Script generation started", "episode_id": episode_id, "status": episode.status}


@router.post("/{episode_id}/generate-video")
def generate_video(episode_id: int, db: Session = Depends(get_db)):
    """触发视频生成任务（异步执行完整管线）"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    if episode.status not in [EpisodeStatus.SCRIPT_GENERATED.value, EpisodeStatus.VIDEO_COMPLETED.value, EpisodeStatus.VIDEO_FAILED.value]:
        raise HTTPException(status_code=400, detail="Script must be generated before video generation")
    episode.status = EpisodeStatus.VIDEO_GENERATING.value
    db.commit()

    # 后台异步执行管线
    try:
        from app.services.video_pipeline import run_pipeline
        import tempfile

        def generate():
            try:
                from database import get_db as _get_db
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
                        print(f"[SUCCESS] Video pipeline complete: {video_path}")
                    else:
                        ep2.status = EpisodeStatus.VIDEO_FAILED.value
                        print(f"[ERROR] Video pipeline failed: {msg}")
                    db3.commit()
            except Exception as e:
                import traceback
                traceback.print_exc()
                try:
                    from database import get_db as _get_db
                    db_fail = next(_get_db())
                    ep_fail = db_fail.query(Episode).filter(Episode.id == episode_id).first()
                    if ep_fail:
                        ep_fail.status = EpisodeStatus.VIDEO_FAILED.value
                        db_fail.commit()
                except Exception:
                    pass

        thread = threading.Thread(target=generate)
        thread.start()
    except Exception as e:
        print(f"[WARN] Failed to start video generation thread: {e}")

    return {"message": "Video generation started", "episode_id": episode_id, "status": episode.status}
