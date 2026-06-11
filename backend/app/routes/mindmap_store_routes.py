# routes/mindmap_store_routes.py
# CRUD endpoints cho mindmaps đã lưu

import json
import os
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db
from app.db.models import Mindmap, MindmapVersion

router = APIRouter()


# ── Lấy danh sách mindmaps đã lưu ─────────────────────────────────────────────
@router.get("/mindmaps")
def list_mindmaps(
    skip:  int = Query(default=0,  ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Trả về danh sách tất cả mindmap đã lưu.
    Dùng cho trang "Mindmaps cũ".
    """
    mindmaps = (
        db.query(Mindmap)
        .order_by(Mindmap.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    total = db.query(Mindmap).count()

    return {
        "total": total,
        "items": [m.to_dict(include_json=False) for m in mindmaps],
    }


# ── Lấy 1 mindmap cụ thể (kèm JSON để render) ─────────────────────────────────
@router.get("/mindmaps/{mindmap_id}")
def get_mindmap_by_id(mindmap_id: str, db: Session = Depends(get_db)):
    m = db.query(Mindmap).filter(Mindmap.id == mindmap_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Không tìm thấy mindmap")
    return m.to_dict(include_json=True)


# ── Lưu mindmap mới (gọi sau khi generate xong) ───────────────────────────────
@router.post("/mindmaps/save")
def save_mindmap(payload: dict, db: Session = Depends(get_db)):
    """
    Body: {
        "title":           str,
        "source_pdf_name": str,
        "source_pdf_path": str (optional),
        "mindmap_data":    dict,   ← full JSON từ export_service
        "keywords":        dict,
        "num_pages":       int,
    }
    """
    required = ["title", "source_pdf_name", "mindmap_data"]
    for field in required:
        if field not in payload:
            raise HTTPException(status_code=422, detail=f"Thiếu field: {field}")

    mindmap_data = payload["mindmap_data"]
    num_nodes    = mindmap_data.get("stats", {}).get("total_nodes", 0)

    # Tạo summary từ top keywords
    keywords = payload.get("keywords", {})
    summary  = ", ".join(list(keywords.keys())[:5]) if keywords else ""

    m = Mindmap(
        title             = payload["title"][:255],
        source_pdf_name   = payload["source_pdf_name"][:255],
        source_pdf_path   = payload.get("source_pdf_path"),
        mindmap_json      = json.dumps(mindmap_data, ensure_ascii=False),
        keywords_json     = json.dumps(keywords,     ensure_ascii=False),
        summary           = summary,
        num_nodes         = num_nodes,
        num_pages         = payload.get("num_pages", 0),
    )
    db.add(m)
    db.flush()  # lấy id trước khi commit

    # Tạo version đầu tiên
    v = MindmapVersion(
        mindmap_id   = m.id,
        version      = 1,
        mindmap_json = m.mindmap_json,
    )
    db.add(v)

    # Tạo preview PNG
    try:
        from app.services.storage_service import generate_preview
        preview_path = generate_preview(mindmap_data, m.id)
        if preview_path:
            m.preview_image_path = preview_path
    except Exception:
        pass

    db.commit()
    db.refresh(m)

    return {"id": m.id, "message": "Đã lưu mindmap", "mindmap": m.to_dict()}


# ── Xoá mindmap ────────────────────────────────────────────────────────────────
@router.delete("/mindmaps/{mindmap_id}")
def delete_mindmap(mindmap_id: str, db: Session = Depends(get_db)):
    m = db.query(Mindmap).filter(Mindmap.id == mindmap_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Không tìm thấy mindmap")

    # Xoá file preview
    try:
        from app.services.storage_service import delete_preview
        delete_preview(mindmap_id)
    except Exception:
        pass

    db.delete(m)
    db.commit()
    return {"message": "Đã xoá"}


# ── Lấy ảnh preview ────────────────────────────────────────────────────────────
@router.get("/mindmaps/{mindmap_id}/preview")
def get_preview(mindmap_id: str, db: Session = Depends(get_db)):
    m = db.query(Mindmap).filter(Mindmap.id == mindmap_id).first()
    if not m or not m.preview_image_path:
        raise HTTPException(status_code=404, detail="Không có preview")
    if not os.path.exists(m.preview_image_path):
        raise HTTPException(status_code=404, detail="File preview không tồn tại")
    return FileResponse(m.preview_image_path, media_type="image/png")


# ── Download mindmap JSON ──────────────────────────────────────────────────────
@router.get("/mindmaps/{mindmap_id}/download")
def download_mindmap(mindmap_id: str, db: Session = Depends(get_db)):
    m = db.query(Mindmap).filter(Mindmap.id == mindmap_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Không tìm thấy mindmap")

    data = json.loads(m.mindmap_json)
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f'attachment; filename="{m.title}.json"'
        }
    )


# ── Lịch sử versions ──────────────────────────────────────────────────────────
@router.get("/mindmaps/{mindmap_id}/versions")
def get_versions(mindmap_id: str, db: Session = Depends(get_db)):
    versions = (
        db.query(MindmapVersion)
        .filter(MindmapVersion.mindmap_id == mindmap_id)
        .order_by(MindmapVersion.version.desc())
        .all()
    )
    return {"versions": [v.to_dict() for v in versions]}


# ── Restore version cũ ────────────────────────────────────────────────────────
@router.post("/mindmaps/{mindmap_id}/restore/{version_id}")
def restore_version(mindmap_id: str, version_id: str, db: Session = Depends(get_db)):
    m = db.query(Mindmap).filter(Mindmap.id == mindmap_id).first()
    v = db.query(MindmapVersion).filter(MindmapVersion.id == version_id).first()

    if not m or not v:
        raise HTTPException(status_code=404, detail="Không tìm thấy")

    # Lưu state hiện tại thành version mới trước khi restore
    latest_version = max((ver.version for ver in m.versions), default=0)
    new_v = MindmapVersion(
        mindmap_id   = m.id,
        version      = latest_version + 1,
        mindmap_json = m.mindmap_json,
    )
    db.add(new_v)

    # Restore
    m.mindmap_json = v.mindmap_json
    m.updated_at   = datetime.utcnow()
    db.commit()
    db.refresh(m)

    return {"message": f"Đã restore về version {v.version}", "mindmap": m.to_dict(include_json=True)}
