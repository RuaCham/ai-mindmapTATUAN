# db/database.py
# SQLite (local) — dễ swap sang PostgreSQL chỉ bằng 1 dòng .env

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Đọc từ .env — nếu không có thì dùng SQLite local
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./storage/mindmap.db")

# SQLite cần check_same_thread=False
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency cho FastAPI — tự đóng session sau mỗi request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Tạo tất cả bảng nếu chưa có."""
    # Import models để SQLAlchemy biết cần tạo bảng gì
    from app.db import models  # noqa
    Base.metadata.create_all(bind=engine)
