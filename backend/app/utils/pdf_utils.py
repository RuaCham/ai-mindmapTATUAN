# utils/pdf_utils.py
import fitz


def get_page_count(pdf_bytes: bytes) -> int:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    n = len(doc)
    doc.close()
    return n


def is_scanned(pdf_bytes: bytes) -> bool:
    """Kiểm tra PDF có phải scan (không có text layer) không."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        if page.get_text("text").strip():
            doc.close()
            return False
    doc.close()
    return True
