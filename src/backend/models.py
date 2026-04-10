"""
AIMedia 数据模型
基于 SQLAlchemy
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class SeriesStatus(str, Enum):
    DRAFT = "draft"
    OUTLINE_GENERATED = "outline_generated"
    EPISODES_GENERATING = "episodes_generating"
    COMPLETED = "completed"


class EpisodeStatus(str, Enum):
    DRAFT = "draft"
    OUTLINE_GENERATED = "outline_generated"
    SCRIPT_GENERATING = "script_generating"
    SCRIPT_GENERATED = "script_generated"
    VIDEO_GENERATING = "video_generating"
    VIDEO_COMPLETED = "video_completed"
    VIDEO_FAILED = "video_failed"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_audience = Column(String(255), nullable=True)
    style = Column(String(100), nullable=True)
    episode_count = Column(Integer, default=1)
    status = Column(String(50), default=ProjectStatus.DRAFT.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    series = relationship("Series", back_populates="project", cascade="all, delete-orphan")


class Series(Base):
    __tablename__ = "series"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    outline = Column(Text, nullable=True)  # JSON 格式的大纲
    status = Column(String(50), default=SeriesStatus.DRAFT.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    project = relationship("Project", back_populates="series")
    episodes = relationship("Episode", back_populates="series", cascade="all, delete-orphan")


class Episode(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    series_id = Column(Integer, ForeignKey("series.id"), nullable=False)
    episode_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    outline = Column(Text, nullable=True)  # 单集详细提纲
    script = Column(Text, nullable=True)  # 完整脚本 (JSON)
    storyboard = Column(Text, nullable=True)  # 分镜描述 (JSON)
    video_path = Column(String(500), nullable=True)  # 最终视频文件路径
    status = Column(String(50), default=EpisodeStatus.DRAFT.value)
    duration_estimate = Column(Integer, nullable=True)  # 预估时长(秒)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    series = relationship("Series", back_populates="episodes")
    tasks = relationship("VideoTask", back_populates="episode", cascade="all, delete-orphan")


class VideoTask(Base):
    __tablename__ = "video_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=False)
    task_type = Column(String(50), nullable=False)  # video, voice, subtitle, compose
    status = Column(String(50), default=TaskStatus.PENDING.value)
    progress = Column(Integer, default=0)  # 0-100
    result_url = Column(String(500), nullable=True)  # 任务结果URL
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 关系
    episode = relationship("Episode", back_populates="tasks")


# 数据库初始化
DATABASE_URL = "sqlite:///./aimedia.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("✅ 数据库初始化完成: aimedia.db")
