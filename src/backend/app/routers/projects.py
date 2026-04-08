"""
项目路由
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Project, ProjectStatus

router = APIRouter()


class ProjectCreate(BaseModel):
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

    class Config:
        from_attributes = True


@router.post("/", response_model=ProjectResponse)
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
    return db_project


@router.get("/", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    """获取所有项目"""
    return db.query(Project).all()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """获取单个项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """删除项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}
