# services/preprocess_service.py
import re
import unicodedata

STOPWORDS_VI = {
    "là","và","của","có","trong","được","cho","với","các","một",
    "này","đó","thì","mà","khi","để","từ","theo","về","trên",
    "tại","bởi","hay","hoặc","nếu","vì","do","như","vậy","cũng",
    "đã","sẽ","đang","rất","nhiều","hơn","nhất","còn","nên","cần",
    "không","chưa","chỉ","đều","lại","đến","ra","vào","qua","lên",
    "xuống","sau","trước","giữa","dưới","ngoài","bên","đây","kia",
    "tôi","bạn","họ","chúng","ta","mình","người","những","mỗi",
    "tất","cả","toàn","phần","loại","dạng","kiểu","cách","việc",
    "điều","vấn","đề","thông","đồng","thời","nói","làm","thể",
    "nào","gì","sao","đâu","bao","thế","hỏi","hãy","rằng","thực",
    "hiện","theo","trên","dưới","trái","phải","giải","toán","bài",
}


def preprocess_text(text: str) -> tuple[list[str], list[str], list[str]]:
    normalized = _normalize(text)
    tokens     = _tokenize(normalized)
    sentences  = _split_sentences(normalized)
    paragraphs = _split_paragraphs(normalized)
    return tokens, sentences, paragraphs


def _normalize(text: str) -> str:
    # NFC normalize — fix dấu tiếng Việt bị tách
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    # Fix khoảng trắng thừa giữa các ký tự tiếng Việt
    text = re.sub(
        r'([a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ])'
        r'\s'
        r'([a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ])',
        r'\1\2', text
    )
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def _tokenize(text: str) -> list[str]:
    # Thử underthesea, fallback về split đơn giản
    try:
        from underthesea import word_tokenize
        tokens = word_tokenize(text, format="text").split()
    except Exception:
        tokens = text.lower().split()

    cleaned = []
    for t in tokens:
        t = t.lower().strip()
        if len(t) < 2:
            continue
        if re.fullmatch(r'[\d\W_]+', t):
            continue
        if t in STOPWORDS_VI:
            continue
        cleaned.append(t)
    return cleaned


def _split_sentences(text: str) -> list[str]:
    # Tách câu — xử lý cả dấu chấm trong số (1.2, 3.14...)
    pattern = r'(?<![0-9])(?<=[.!?])\s+(?=[A-ZÁÀẢÃẠ])'
    parts = re.split(pattern, text.strip())
    result = []
    for s in parts:
        s = s.strip()
        if len(s.split()) >= 5:
            result.append(s)
    return result


def _split_paragraphs(text: str) -> list[str]:
    # Tách đoạn theo dòng trống HOẶC heading pattern
    raw_paras = re.split(r'\n{2,}', text.strip())
    result = []
    for p in raw_paras:
        p = p.strip().replace('\n', ' ')
        p = re.sub(r'[ \t]+', ' ', p)
        if len(p.split()) >= 8:
            result.append(p)
    return result
