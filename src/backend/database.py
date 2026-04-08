"""
AIMedia 数据库配置
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base

DATABASE_URL = "sqlite:///./aimedia.db"


def get_engine():
    return create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite 特定
        echo=False
    )


def get_session_maker():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def init_database():
    """初始化所有表"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    return engine


def get_db():
    """依赖注入用的数据库会话获取器"""
    SessionLocal = get_session_maker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
