"""
项目路由
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Project, ProjectStatus, Series, Episode

router = APIRouter()


class ProjectCreate(BaseModel):
    title: str
    description: str = ""
    target_audience: str = ""
    style: str = ""
    episode_count: int = 5


class ProjectUpdate(BaseModel):
    title: str
    description: str = ""
    target_audience: str = ""
    style: str = ""
    episode_count: int = 5


class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str
    target_audience: str
    style: str
    episode_count: int
    status: str
    created_at: str = ""

    class Config:
        from_attributes = True


def _project_to_response(project: Project, db: Session) -> dict:
    series_count = db.query(Series).filter(Series.project_id == project.id).count()
    episode_count = (
        db.query(Episode)
        .join(Series)
        .filter(Series.project_id == project.id)
        .count()
    )
    return {
        "id": project.id,
        "title": project.title,
        "description": project.description or "",
        "target_audience": project.target_audience or "",
        "style": project.style or "",
        "episode_count": project.episode_count or 5,
        "status": project.status,
        "created_at": str(project.created_at) if project.created_at else "",
        "series_count": series_count,
        "episode_count_total": episode_count
    }


@router.post("")
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """创建新项目"""
    db_project = Project(
        title=project.title,
        description=project.description,
        target_audience=project.target_audience,
        style=project.style,
        episode_count=project.episode_count,
        status=ProjectStatus.DRAFT.value
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return _project_to_response(db_project, db)


@router.get("")
def list_projects(db: Session = Depends(get_db)):
    """获取所有项目"""
    projects = db.query(Project).all()
    return [_project_to_response(p, db) for p in projects]


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    """获取单个项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_to_response(project, db)


@router.put("/{project_id}")
def update_project(project_id: int, update: ProjectUpdate, db: Session = Depends(get_db)):
    """更新项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.title = update.title
    project.description = update.description
    project.target_audience = update.target_audience
    project.style = update.style
    project.episode_count = update.episode_count
    db.commit()
    db.refresh(project)
    return _project_to_response(project, db)


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """删除项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}
