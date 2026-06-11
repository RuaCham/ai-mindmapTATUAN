# services/storage_service.py
# Quản lý file lưu trữ (PDF, PNG preview)
# Dễ swap sang Supabase/S3 sau này — chỉ cần đổi các hàm bên dưới

import os
import uuid
import json

STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join(os.path.dirname(__file__), "../../../storage"))
PDF_DIR     = os.path.join(STORAGE_DIR, "pdfs")
PREVIEW_DIR = os.path.join(STORAGE_DIR, "previews")


def ensure_dirs():
    """Tạo thư mục storage nếu chưa có."""
    os.makedirs(PDF_DIR,     exist_ok=True)
    os.makedirs(PREVIEW_DIR, exist_ok=True)


def save_pdf(pdf_bytes: bytes, filename: str) -> str:
    """
    Lưu file PDF vào storage/pdfs/
    Trả về đường dẫn tương đối.
    """
    ensure_dirs()
    safe_name = f"{uuid.uuid4()}_{_safe_filename(filename)}"
    path      = os.path.join(PDF_DIR, safe_name)
    with open(path, "wb") as f:
        f.write(pdf_bytes)
    return path


def delete_pdf(path: str):
    """Xoá file PDF."""
    if path and os.path.exists(path):
        os.remove(path)


def save_preview(png_bytes: bytes, mindmap_id: str) -> str:
    """
    Lưu ảnh preview PNG vào storage/previews/
    Trả về đường dẫn tương đối.
    """
    ensure_dirs()
    path = os.path.join(PREVIEW_DIR, f"{mindmap_id}.png")
    with open(path, "wb") as f:
        f.write(png_bytes)
    return path


def get_preview_path(mindmap_id: str) -> str | None:
    """Trả về path preview nếu tồn tại."""
    path = os.path.join(PREVIEW_DIR, f"{mindmap_id}.png")
    return path if os.path.exists(path) else None


def delete_preview(mindmap_id: str):
    """Xoá file preview."""
    path = get_preview_path(mindmap_id)
    if path:
        os.remove(path)


def generate_preview(mindmap_data: dict, mindmap_id: str) -> str | None:
    """
    Tạo ảnh preview PNG từ mindmap JSON.
    Dùng thư viện Pillow — vẽ cây đơn giản.
    Trả về path nếu thành công, None nếu lỗi.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import math

        nodes = mindmap_data.get("nodes", [])
        edges = mindmap_data.get("edges", [])
        title = mindmap_data.get("title", "Mindmap")

        if not nodes:
            return None

        # Canvas size
        W, H   = 1200, 800
        img    = Image.new("RGB", (W, H), color=(15, 17, 23))  # dark background
        draw   = ImageDraw.Draw(img)

        # Màu theo depth
        COLORS = {
            0: (79, 110, 247),   # blue — root
            1: (75, 85, 99),     # gray — branch
            2: (55, 65, 81),     # darker gray — leaf
        }

        # Build position map từ node data
        # Dùng layout đơn giản: root ở giữa trái, nhánh ra phải theo depth
        node_map = {n["id"]: n for n in nodes}
        pos_map  = {}

        def _assign_positions(node_id, x, y_start, y_end):
            pos_map[node_id] = (x, (y_start + y_end) // 2)
            children_ids = [
                e["target"] for e in edges if e["source"] == node_id
            ]
            if not children_ids:
                return
            slot = (y_end - y_start) // max(len(children_ids), 1)
            for i, child_id in enumerate(children_ids):
                cy_start = y_start + i * slot
                cy_end   = cy_start + slot
                _assign_positions(child_id, x + 200, cy_start, cy_end)

        # Root node
        root_nodes = [n for n in nodes if n.get("type") == "root"]
        if root_nodes:
            _assign_positions(root_nodes[0]["id"], 60, 50, H - 50)

        # Vẽ edges
        for edge in edges:
            src = pos_map.get(edge["source"])
            tgt = pos_map.get(edge["target"])
            if src and tgt:
                draw.line([src, tgt], fill=(55, 65, 81), width=1)

        # Vẽ nodes
        for node in nodes:
            pos   = pos_map.get(node["id"])
            if not pos:
                continue
            depth = node["data"].get("depth", 1)
            color = COLORS.get(min(depth, 2), COLORS[2])
            label = node["data"].get("label", "")[:25]

            # Box
            x, y = pos
            bw   = max(80, len(label) * 7 + 16)
            bh   = 28
            draw.rounded_rectangle(
                [x - bw//2, y - bh//2, x + bw//2, y + bh//2],
                radius=6, fill=color
            )
            # Text
            draw.text((x, y), label, fill=(226, 232, 240), anchor="mm")

        # Title
        draw.text((W//2, 20), title[:60], fill=(148, 163, 184), anchor="mm")

        # Lưu
        path = os.path.join(PREVIEW_DIR, f"{mindmap_id}.png")
        ensure_dirs()
        img.save(path, "PNG")
        return path

    except Exception as e:
        print(f"[preview] Error generating preview: {e}")
        return None


def _safe_filename(name: str) -> str:
    """Làm sạch tên file."""
    import re
    name = os.path.basename(name)
    name = re.sub(r'[^\w\-_\. ]', '_', name)
    return name[:100]
