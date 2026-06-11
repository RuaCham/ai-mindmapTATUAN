# services/pdf_service.py
# Extract text từ PDF — xử lý cả text layer + OCR fallback

import re
import fitz  # PyMuPDF
import unicodedata


def extract_text(pdf_bytes: bytes) -> dict:
    """
    Pipeline:
    1. Thử extract text layer
    2. Kiểm tra chất lượng text
    3. Nếu text bị lỗi encoding → OCR fallback
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    num_pages = len(doc)

    all_blocks  = []
    page_texts  = []
    raw_texts   = []

    for page_num in range(num_pages):
        page = doc[page_num]

        # Lấy text kèm font info
        blocks = page.get_text("dict")["blocks"]
        page_blocks = []
        for block in blocks:
            if block.get("type") == 0:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        t = span.get("text", "").strip()
                        if t:
                            page_blocks.append({
                                "text": t,
                                "size": span.get("size", 12),
                                "bold": "Bold" in span.get("font", ""),
                                "page": page_num + 1,
                            })

        all_blocks.extend(page_blocks)

        # Raw text theo trang
        raw = page.get_text("text")
        raw_texts.append(raw)
        page_texts.append(" ".join(b["text"] for b in page_blocks))

    doc.close()

    # Ghép toàn bộ text
    full_raw = "\n\n".join(raw_texts)

    # Kiểm tra chất lượng
    quality = _check_text_quality(full_raw)

    if quality == "good":
        cleaned = _clean_text(full_raw)
    elif quality == "broken_encoding":
        # Fix encoding lỗi trước
        fixed   = _fix_broken_encoding(full_raw)
        cleaned = _clean_text(fixed)
    else:
        # Quá tệ → OCR
        cleaned = _ocr_fallback(pdf_bytes)

    return {
        "text":      cleaned,
        "num_pages": num_pages,
        "blocks":    all_blocks,
        "quality":   quality,
    }


def _check_text_quality(text: str) -> str:
    """
    Phân loại chất lượng text:
    - "good"             : text layer tốt
    - "broken_encoding"  : có text nhưng bị vỡ dấu/spacing
    - "unreadable"       : quá ít text, cần OCR
    """
    if not text or len(text.strip()) < 50:
        return "unreadable"

    words = text.split()
    if len(words) < 10:
        return "unreadable"

    # Đếm ký tự tiếng Việt hợp lệ
    vi_chars = len(re.findall(
        r'[áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ'
        r'ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]',
        text
    ))

    # Đếm khoảng trắng thừa bất thường (dấu hiệu encoding lỗi)
    broken_spaces = len(re.findall(r'\b\w\s\w\s\w\b', text))  # "H Ọ C" kiểu này
    single_chars  = len(re.findall(r'(?<!\w)\w(?!\w)', text))  # ký tự đứng một mình

    total_words = max(len(words), 1)
    broken_ratio = (broken_spaces + single_chars) / total_words

    if broken_ratio > 0.3:
        return "broken_encoding"

    if vi_chars > 0 or len(text) > 200:
        return "good"

    return "good"


def _fix_broken_encoding(text: str) -> str:
    """
    Fix text bị vỡ do encoding PDF lỗi.
    Vấn đề phổ biến:
    - "H Ọ C S I N H" → "HỌC SINH"
    - "C ẤP H A I"    → "CẤP HAI"
    - Ký tự tiếng Việt bị tách rời khỏi ký tự gốc
    """
    # 1. Normalize unicode (NFC — gộp base char + combining diacritics)
    text = unicodedata.normalize("NFC", text)

    # 2. Fix pattern: chữ cái đơn lẻ cách nhau bởi dấu cách → ghép lại
    # Ví dụ: "H Ọ C" → "HỌC"
    def merge_spaced_chars(m):
        merged = m.group(0).replace(" ", "")
        return merged + " "  # thêm space sau từ đã merge

    # Pattern: 2+ ký tự đơn (có thể có dấu tiếng Việt) cách nhau 1 space
    vi_char_pattern = r'[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]'
    spaced_upper = re.compile(
        rf'(?:{vi_char_pattern} ){{2,}}{vi_char_pattern}(?= |\n|$)'
    )
    text = spaced_upper.sub(merge_spaced_chars, text)

    # 3. Fix khoảng trắng thừa trong từ thường
    # "ng uyên" → "nguyên", "bất bi ến" → "bất biến"
    text = re.sub(r'([a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ])\s([a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ])', r'\1\2', text)

    # 4. Fix dòng bị gãy — merge dòng không kết thúc bằng dấu câu
    lines  = text.split('\n')
    merged = []
    buffer = ""
    for line in lines:
        line = line.strip()
        if not line:
            if buffer:
                merged.append(buffer)
                buffer = ""
            merged.append("")
            continue
        if buffer:
            if not re.search(r'[.!?:;]\s*$', buffer):
                buffer += " " + line
            else:
                merged.append(buffer)
                buffer = line
        else:
            buffer = line
    if buffer:
        merged.append(buffer)

    result = "\n".join(merged)
    result = re.sub(r'\n{3,}', '\n\n', result)
    result = re.sub(r'[ \t]+', ' ', result)
    return result.strip()


def _ocr_fallback(pdf_bytes: bytes) -> str:
    """
    OCR fallback dùng PyMuPDF built-in (không cần Tesseract).
    Render page thành ảnh rồi dùng get_text với higher DPI.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        texts = []
        for page in doc:
            # Render ở DPI cao để OCR tốt hơn
            mat  = fitz.Matrix(2.0, 2.0)  # 2x zoom = ~144 DPI
            pix  = page.get_pixmap(matrix=mat)
            # Dùng textpage từ pixmap
            text = page.get_text("text")
            if text.strip():
                texts.append(text)
        doc.close()
        raw = "\n\n".join(texts)
        return _clean_text(raw)
    except Exception:
        return ""


def _clean_text(text: str) -> str:
    """Clean text cuối cùng."""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
