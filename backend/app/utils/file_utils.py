# utils/file_utils.py
import os

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../data")


def save_upload(file_id: str, pdf_bytes: bytes) -> str:
    """Lưu file PDF tạm vào thư mục data/. Trả về đường dẫn file."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
    with open(path, "wb") as f:
        f.write(pdf_bytes)
    return path


def delete_file(path: str):
    """Xoá file nếu tồn tại."""
    if path and os.path.exists(path):
        os.remove(path)
