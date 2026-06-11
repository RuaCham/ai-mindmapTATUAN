# services/keyword_service.py
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from app.services.preprocess_service import _tokenize, _split_paragraphs

KEYWORD_BLACKLIST = {
    "câu", "lớp", "năm", "điểm", "ghi", "chú", "tổng", "cộng",
    "hình", "thức", "cấu", "trúc", "nội", "dung", "bài", "số",
    "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín",
    "phần", "mục", "thí", "sinh", "lưu", "ý", "gồm", "theo",
    "0_điểm", "1_câu", "câu_lớp", "năm_năm",
}


def extract_keywords(text: str, top_n: int = 20) -> dict[str, float]:
    """TF-IDF trên toàn document — trả về keyword tổng."""
    paragraphs = _split_paragraphs(text)
    if len(paragraphs) < 3:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.split()) >= 5]
        paragraphs = sentences if sentences else [text]

    tokenized = []
    for para in paragraphs:
        tokens = _tokenize(para)
        if tokens:
            tokenized.append(" ".join(tokens))

    if not tokenized:
        return {}

    vectorizer = TfidfVectorizer(
        max_features=1000,
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
    )

    try:
        matrix = vectorizer.fit_transform(tokenized)
    except ValueError:
        return {}

    feature_names = vectorizer.get_feature_names_out()
    mean_scores   = np.asarray(matrix.mean(axis=0)).flatten()

    keyword_scores = {}
    for k, v in zip(feature_names, mean_scores):
        if v <= 0:
            continue
        if re.fullmatch(r'[\d\s_\.,]+', k):
            continue
        if len(k) < 3:
            continue
        if k.lower() in KEYWORD_BLACKLIST:
            continue
        if re.search(r'\d', k):
            continue
        keyword_scores[k] = float(v)

    return dict(
        sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    )


def extract_keywords_for_section(section_text: str, top_n: int = 6) -> dict[str, float]:
    """
    TF-IDF chỉ trên nội dung của 1 section cụ thể.
    KHÔNG fallback ra keyword toàn document.
    Nếu section không có keyword có nghĩa → trả về {} rỗng.
    """
    if not section_text or len(section_text.strip()) < 30:
        return {}

    tokens = _tokenize(section_text)
    if len(tokens) < 3:
        return {}

    # Đếm tần suất từ trong section
    freq: dict[str, int] = {}
    for t in tokens:
        if t in KEYWORD_BLACKLIST:
            continue
        if re.search(r'\d', t):
            continue
        if len(t) < 3:
            continue
        freq[t] = freq.get(t, 0) + 1

    if not freq:
        return {}

    total = sum(freq.values())
    tf_scores = {k: v / total for k, v in freq.items()}

    # Ưu tiên từ xuất hiện nhiều lần (có nghĩa trong section đó)
    meaningful = {k: v for k, v in tf_scores.items() if freq[k] >= 1}

    return dict(
        sorted(meaningful.items(), key=lambda x: x[1], reverse=True)[:top_n]
    )
