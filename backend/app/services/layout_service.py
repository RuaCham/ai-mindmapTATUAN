# services/layout_service.py
import re
import unicodedata


def detect_headings(text: str, blocks: list[dict] = None) -> list[dict]:
    headings = _detect_from_patterns(text)
    if blocks and len(headings) < 3:
        font_h = _detect_from_font(blocks)
        existing = {h["text"] for h in headings}
        for h in font_h:
            if h["text"] not in existing:
                headings.append(h)
        headings.sort(key=lambda x: x["index"])
    return headings


def _detect_from_font(blocks):
    if not blocks:
        return []
    valid = [b for b in blocks if b.get("text","").strip() and len(b["text"].strip()) > 2]
    if not valid:
        return []
    sizes = [b["size"] for b in valid]
    avg   = sum(sizes) / len(sizes)
    mx    = max(sizes)
    headings = []
    for i, b in enumerate(valid):
        text = b.get("text","").strip()
        size = b.get("size", 12)
        bold = b.get("bold", False)
        if not text or len(text) < 3 or len(text) > 100:
            continue
        if size >= avg * 1.6 or size == mx:
            level = 1
        elif size >= avg * 1.25 or (bold and size >= avg * 1.1):
            level = 2
        elif bold or size >= avg * 1.05:
            level = 3
        else:
            continue
        headings.append({"level": level, "text": text, "index": i})
    return headings


def _detect_from_patterns(text: str) -> list[dict]:
    """
    Detect heading với bộ lọc chặt hơn — tránh nhận nhầm body text.

    Chỉ nhận heading khi CHẮC CHẮN là heading:
    - Level 1: I. / II. / III. / Chương X / Phần X
    - Level 2: 1. / 2. / A. / B. / Bài X. / Câu X.
    - Level 3: 1.1 / a) / - tiêu đề rõ ràng

    KHÔNG nhận:
    - Dòng có dấu phẩy/chấm phẩy ở giữa (body text)
    - Số đứng một mình (điểm số)
    - Dòng quá dài > 100 ký tự
    - Dòng là header bảng: "Điểm", "Ghi chú", "TT"
    """
    lines = text.split('\n')
    headings = []

    # Blacklist — những từ dù match pattern vẫn bỏ
    BLACKLIST = {
        "điểm", "ghi chú", "tt", "nội dung", "ghi chú",
        "tổng", "tổng cộng", "lưu ý", "chọn một hoặc một số chủ đề trong các chủ đề sau",
    }

    # Level 1: La Mã + dấu chấm + nội dung: "I. MÔN TOÁN"
    # Hoặc: Chương/Phần/Phụ lục + số
    P1 = [
        r'^(I{1,3}|IV|V?I{0,3}|IX|X{1,3})\.\s+\S.{2,}',   # I. II. III. IV...
        r'^(chương|phần|phụ\s*lục)\s+[\divxIVX]+',
    ]

    # Level 2: Số Ả Rập + dấu chấm + chữ hoa/nội dung rõ: "1. Hình thức"
    # Hoặc: "Bài 1.", "Câu 1.", "A.", "B."
    P2 = [
        r'^\d+\.\s+[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ].{2,}',
        r'^(bài|câu)\s+\d+[\.\:]\s*\S.{1,}',
        r'^[A-Z]\.\s+[A-ZÁÀẢÃẠ].{3,}',
    ]

    # Level 3: "1.1 ...", "a) ...", "+ Bước..."
    P3 = [
        r'^\d+\.\d+[\.\s]+[A-ZÁÀẢÃẠ].{2,}',
        r'^[a-z]\)\s+[A-ZÁÀẢÃẠ].{3,}',
        r'^\+\s*(bước|ý|trường hợp)\s+\d+',
    ]

    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue

        # Bỏ qua dòng quá ngắn hoặc quá dài
        if len(s) < 3 or len(s) > 120:
            continue

        # Bỏ qua nếu là số thuần hoặc số thập phân đứng một mình
        if re.fullmatch(r'[\d\.,\s]+', s):
            continue

        # Bỏ qua nếu trong blacklist
        if s.lower().strip('.') in BLACKLIST:
            continue

        # Bỏ qua nếu dòng chứa nhiều dấu phẩy (body text dạng liệt kê)
        if s.count(',') >= 2:
            continue

        # Bỏ qua dòng bắt đầu bằng dấu bullet/gạch đầu dòng
        if re.match(r'^[•\-–]\s', s):
            continue

        s_norm = unicodedata.normalize("NFC", s)
        level  = None

        for p in P1:
            if re.match(p, s_norm, re.IGNORECASE | re.UNICODE):
                level = 1
                break

        if level is None:
            for p in P2:
                if re.match(p, s_norm, re.IGNORECASE | re.UNICODE):
                    level = 2
                    break

        if level is None:
            for p in P3:
                if re.match(p, s_norm, re.IGNORECASE | re.UNICODE):
                    level = 3
                    break

        if level is not None:
            headings.append({"level": level, "text": s_norm, "index": i})

    return headings
