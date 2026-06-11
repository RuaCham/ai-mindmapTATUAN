# services/section_analyzer.py
# Lớp "section understanding" — hiểu nội dung từng section
# Không dùng AI — chỉ dùng thuật toán NLP nhẹ

import re
import unicodedata
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.preprocess_service import _tokenize


def analyze_section(section_text: str) -> dict:
    """
    Input : text thô của 1 section (nội dung dưới 1 heading)
    Output: {
        "summary":      str,         ← 1-2 câu quan trọng nhất
        "bullet_items": list[str],   ← các mục con có nội dung thật
        "key_phrases":  list[str],   ← cụm từ quan trọng (2-4 từ)
        "main_idea":    str,         ← 1 câu ngắn mô tả ý chính
    }
    """
    if not section_text or len(section_text.strip()) < 20:
        return {"summary": "", "bullet_items": [], "key_phrases": [], "main_idea": ""}

    sentences   = _split_sentences(section_text)
    bullets     = _extract_bullets(section_text)
    key_phrases = _extract_key_phrases(section_text)
    summary     = _summarize(sentences, top_n=2)
    main_idea   = _get_main_idea(sentences, bullets, key_phrases)

    return {
        "summary":      summary,
        "bullet_items": bullets,
        "key_phrases":  key_phrases,
        "main_idea":    main_idea,
    }


def _split_sentences(text: str) -> list[str]:
    """Tách câu — tránh nhầm dấu chấm trong số."""
    # Bỏ dòng chỉ là số/ký hiệu
    text = re.sub(r'\n\s*[\d\.]+\s*\n', '\n', text)
    # Tách câu
    pattern = r'(?<![0-9])(?<=[.!?])\s+(?=[A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬ])'
    parts   = re.split(pattern, text.strip())
    result  = []
    for s in parts:
        s = s.strip().replace('\n', ' ')
        s = re.sub(r'\s+', ' ', s)
        # Chỉ lấy câu có ít nhất 6 từ và không phải header bảng
        words = s.split()
        if len(words) >= 6 and not _is_table_row(s):
            result.append(s)
    return result


def _is_table_row(text: str) -> bool:
    """Kiểm tra dòng có phải row của bảng không."""
    # Dấu hiệu: nhiều tab, chứa số điểm, quá ngắn
    if re.search(r'\t{2,}', text):
        return True
    if re.fullmatch(r'[\d\s\.,\(\)điểm]+', text, re.IGNORECASE):
        return True
    return False


def _extract_bullets(text: str) -> list[str]:
    """
    Lấy bullet items — ưu tiên nội dung đầy đủ thay vì keyword lẻ.
    Nhận diện nhiều dạng bullet:
    - • / - / – / + ở đầu dòng
    - Dạng "Chủ đề tên (điểm số)"
    - Dạng "PART A: ..." / "Câu 1: ..."
    - Dạng "Tên rõ ràng không có dấu câu cuối"
    """
    lines  = text.split('\n')
    items  = []
    seen   = set()

    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue

        item = None

        # Dạng bullet ký hiệu: •, -, –, +
        m = re.match(r'^[•\-–\+]\s+(.+)', line)
        if m:
            item = m.group(1).strip()

        # Dạng "Số thứ tự) nội dung": "1) Khái niệm..."
        if item is None:
            m = re.match(r'^\d+\)\s+(.+)', line)
            if m:
                item = m.group(1).strip()

        # Dạng "PART A: LISTENING" / "Câu 1. Nghị luận..."
        if item is None:
            m = re.match(
                r'^(PART\s+[A-Z]|câu\s+\d+|bài\s+\d+)[\.:]\s*(.+)',
                line, re.IGNORECASE
            )
            if m:
                item = f"{m.group(1).upper()}: {m.group(2).strip()}"

        # Dạng "Tên chủ đề (X điểm)" — phổ biến trong tài liệu giáo dục
        if item is None:
            m = re.match(r'^([A-ZÁÀẢÃẠ].{5,60})\(\d[\d,\.]*\s*điểm\)', line)
            if m:
                item = m.group(1).strip()

        # Heuristic: dòng ngắn (5-80 ký tự), bắt đầu chữ hoa,
        # không kết thúc dấu phẩy, không phải số thuần
        if item is None and 8 <= len(line) <= 80:
            if (line[0].isupper() and
                not re.search(r'[,;]\s*$', line) and
                not re.fullmatch(r'[\d\s\.,]+', line) and
                not _is_table_row(line)):
                item = line

        if item:
            item = _clean_bullet(item)
            if item and len(item) >= 5 and item not in seen:
                seen.add(item)
                items.append(item)

    # Bỏ item trùng lặp hoặc quá giống nhau
    return _deduplicate(items)[:8]


def _clean_bullet(text: str) -> str:
    """Làm sạch bullet item."""
    text = unicodedata.normalize("NFC", text)
    # Bỏ ký tự đặc biệt đầu dòng
    text = re.sub(r'^[•\-–\+\*]\s*', '', text)
    # Bỏ số thứ tự đầu: "1. " / "a) "
    text = re.sub(r'^\d+[\.\)]\s*', '', text)
    text = re.sub(r'^[a-z]\)\s*', '', text)
    # Truncate nếu quá dài
    if len(text) > 70:
        text = text[:67] + "..."
    return text.strip()


def _deduplicate(items: list[str]) -> list[str]:
    """Bỏ item quá giống nhau (substring hoặc overlap > 80%)."""
    result = []
    for item in items:
        is_dup = False
        for existing in result:
            # Nếu item là substring của existing hoặc ngược lại
            if item.lower() in existing.lower() or existing.lower() in item.lower():
                is_dup = True
                break
        if not is_dup:
            result.append(item)
    return result


def _extract_key_phrases(text: str) -> list[str]:
    """
    Lấy cụm từ quan trọng (2-4 từ) bằng TF-IDF bigram/trigram.
    Đây là 'tag phụ' — không dùng làm leaf node chính.
    """
    tokens = _tokenize(text)
    if len(tokens) < 4:
        return []

    token_str = " ".join(tokens)
    try:
        vec = TfidfVectorizer(ngram_range=(2, 3), max_features=20, sublinear_tf=True)
        vec.fit_transform([token_str])
        phrases = vec.get_feature_names_out().tolist()
        # Lọc phrase có nghĩa (không chứa stopword lẻ)
        return [p.replace("_", " ") for p in phrases if len(p) > 5][:6]
    except Exception:
        return []


def _summarize(sentences: list[str], top_n: int = 2) -> str:
    """
    TextRank nhẹ — lấy 1-2 câu quan trọng nhất làm summary.
    Dùng TF-IDF + cosine similarity đơn giản.
    """
    if not sentences:
        return ""
    if len(sentences) <= top_n:
        return " ".join(sentences)

    tokenized = [" ".join(_tokenize(s)) or s.lower() for s in sentences]

    try:
        vec    = TfidfVectorizer(sublinear_tf=True)
        matrix = vec.fit_transform(tokenized)
        sim    = cosine_similarity(matrix)

        # Score mỗi câu = tổng similarity với tất cả câu khác
        scores = sim.sum(axis=1) - 1  # trừ similarity với chính nó
        top_idx = sorted(
            np.argsort(scores)[::-1][:top_n]
        )  # giữ thứ tự gốc
        return " ".join(sentences[i] for i in top_idx)
    except Exception:
        return sentences[0] if sentences else ""


def _get_main_idea(sentences: list[str], bullets: list[str], key_phrases: list[str]) -> str:
    """
    Tạo 1 câu ngắn mô tả ý chính của section.
    Ưu tiên: câu đầu tiên ngắn gọn > bullet đầu > key phrase
    """
    # Thử lấy câu đầu tiên nếu ngắn gọn
    for sent in sentences[:3]:
        words = sent.split()
        if 8 <= len(words) <= 25:
            return sent

    # Thử bullet đầu tiên
    if bullets:
        return bullets[0]

    # Thử key phrase
    if key_phrases:
        return key_phrases[0].title()

    return ""
