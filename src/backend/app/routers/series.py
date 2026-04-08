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


class SeriesResponse(BaseModel):
    id: int
    project_id: int
    title: str
    outline: str = ""
    status: str

    class Config:
        from_attributes = True


@router.post("/", response_model=SeriesResponse)
def create_series(series: SeriesCreate, db: Session = Depends(get_db)):
    """创建新系列"""
    db_series = Series(
        project_id=series.project_id,
        title=series.title,
        status=SeriesStatus.DRAFT.value
    )
    db.add(db_series)
    db.commit()
    db.refresh(db_series)
    return db_series


@router.get("/", response_model=List[SeriesResponse])
def list_series(project_id: int = None, db: Session = Depends(get_db)):
    """获取所有系列"""
    query = db.query(Series)
    if project_id:
        query = query.filter(Series.project_id == project_id)
    return query.all()


@router.get("/{series_id}", response_model=SeriesResponse)
def get_series(series_id: int, db: Session = Depends(get_db)):
    """获取单个系列"""
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series
