# routes/pdf_routes.py
# API endpoint nhận file PDF upload

import uuid
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.services.pdf_service import extract_text
from app.utils.file_utils import save_upload, delete_file

router = APIRouter()

# Lưu tạm thời các file đã upload: {id: {"path": str, "filename": str}}
_uploads: dict = {}


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Nhận file PDF, extract text, trả về id để dùng cho /mindmap/{id}

    Request : multipart/form-data  → file PDF
    Response: {"id": "...", "filename": "...", "num_pages": int, "preview": "..."}
    """
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file PDF")

    # Đọc bytes
    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="File rỗng")

    # Lưu file tạm
    file_id = str(uuid.uuid4())
    file_path = save_upload(file_id, pdf_bytes)

    # Extract text ngay khi upload
    try:
        result = extract_text(pdf_bytes)
    except Exception as e:
        delete_file(file_path)
        raise HTTPException(status_code=500, detail=f"Lỗi đọc PDF: {str(e)}")

    # Lưu thông tin vào memory
    _uploads[file_id] = {
        "path":      file_path,
        "filename":  file.filename,
        "text":      result["text"],
        "num_pages": result["num_pages"],
    }

    return JSONResponse({
        "id":        file_id,
        "filename":  file.filename,
        "num_pages": result["num_pages"],
        "num_chars": len(result["text"]),
        "preview":   result["text"][:300] + "..." if len(result["text"]) > 300 else result["text"],
    })


@router.get("/upload/{file_id}")
def get_upload_info(file_id: str):
    """Lấy thông tin file đã upload."""
    if file_id not in _uploads:
        raise HTTPException(status_code=404, detail="Không tìm thấy file")

    info = _uploads[file_id]
    return {
        "id":        file_id,
        "filename":  info["filename"],
        "num_pages": info["num_pages"],
        "num_chars": len(info["text"]),
    }


def get_text_by_id(file_id: str) -> str:
    """Helper: lấy text từ file_id — dùng nội bộ cho mindmap_routes."""
    if file_id not in _uploads:
        raise HTTPException(status_code=404, detail="Không tìm thấy file")
    return _uploads[file_id]["text"]


def get_filename_by_id(file_id: str) -> str:
    """Helper: lấy tên file từ file_id."""
    if file_id not in _uploads:
        return "Document"
    name = _uploads[file_id]["filename"]
    return name.replace(".pdf", "").replace("_", " ").replace("-", " ").title()
