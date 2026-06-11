# db/models.py
# SQLAlchemy models — tương đương schema database

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Mindmap(Base):
    """Bảng chính lưu mỗi mindmap đã tạo."""
    __tablename__ = "mindmaps"

    id                = Column(String, primary_key=True, default=generate_uuid)
    title             = Column(String(255), nullable=False)
    source_pdf_name   = Column(String(255), nullable=False)
    source_pdf_path   = Column(String(500), nullable=True)   # path file PDF gốc
    mindmap_json      = Column(Text,        nullable=False)   # full JSON để render lại
    keywords_json     = Column(Text,        nullable=True)    # keywords dạng JSON string
    summary           = Column(Text,        nullable=True)    # tóm tắt ngắn
    preview_image_path= Column(String(500), nullable=True)    # path ảnh preview PNG
    num_nodes         = Column(Integer,     default=0)
    num_pages         = Column(Integer,     default=0)
    created_at        = Column(DateTime,    default=datetime.utcnow)
    updated_at        = Column(DateTime,    default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship với versions
    versions = relationship("MindmapVersion", back_populates="mindmap",
                            cascade="all, delete-orphan", order_by="MindmapVersion.version")

    def to_dict(self, include_json: bool = False) -> dict:
        d = {
            "id":               self.id,
            "title":            self.title,
            "source_pdf_name":  self.source_pdf_name,
            "num_nodes":        self.num_nodes,
            "num_pages":        self.num_pages,
            "summary":          self.summary or "",
            "preview_url":      f"/api/mindmaps/{self.id}/preview" if self.preview_image_path else None,
            "created_at":       self.created_at.isoformat() if self.created_at else None,
            "updated_at":       self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_json:
            import json
            d["mindmap_data"]  = json.loads(self.mindmap_json)
            d["keywords"]      = json.loads(self.keywords_json) if self.keywords_json else {}
        return d


class MindmapVersion(Base):
    """Lưu lịch sử các phiên bản — mỗi lần re-generate là 1 version mới."""
    __tablename__ = "mindmap_versions"

    id           = Column(String,   primary_key=True, default=generate_uuid)
    mindmap_id   = Column(String,   ForeignKey("mindmaps.id"), nullable=False)
    version      = Column(Integer,  nullable=False, default=1)
    mindmap_json = Column(Text,     nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

    mindmap = relationship("Mindmap", back_populates="versions")

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "mindmap_id": self.mindmap_id,
            "version":    self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
