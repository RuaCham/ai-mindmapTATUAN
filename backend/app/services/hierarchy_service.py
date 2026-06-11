# services/hierarchy_service.py
import re
import unicodedata
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.preprocess_service import _tokenize, _split_paragraphs
from app.services.section_analyzer import analyze_section
from app.services.keyword_service import extract_keywords_for_section


class Node:
    def __init__(self, id: str, title: str, level: int = 0):
        self.id         = id
        self.title      = title
        self.level      = level
        self.keywords:  list[str] = []
        self.summary:   str = ""
        self.main_idea: str = ""
        self.children:  list["Node"] = []

    def to_dict(self) -> dict:
        return {
            "id":        self.id,
            "title":     self.title,
            "level":     self.level,
            "keywords":  self.keywords,
            "summary":   self.summary,
            "main_idea": self.main_idea,
            "children":  [c.to_dict() for c in self.children],
        }


def build_hierarchy(text, headings, keywords, summaries, n_topics=4) -> Node:
    title = _detect_doc_title(text)
    root  = Node(id="root", title=title, level=0)

    if headings and len(headings) >= 2:
        _build_from_headings(root, text, headings)
        if _count_nodes(root) < 4:
            root = Node(id="root", title=title, level=0)
            _build_from_topics(root, text, n_topics)
    else:
        _build_from_topics(root, text, n_topics)

    return root


def _build_from_headings(root, text, headings):
    lines = text.split('\n')
    stack: list[Node] = [root]

    for i, h in enumerate(headings):
        level = h["level"]
        raw   = h["text"]
        if len(raw.strip()) < 3:
            continue

        title = _clean_title(raw)
        if not title or title.lower() == root.title.lower():
            continue

        # Lấy text của section này
        start   = h["index"]
        end     = headings[i+1]["index"] if i+1 < len(headings) else len(lines)
        section = "\n".join(lines[start:end])

        # Phân tích nội dung CHỈ trong section này — không dùng keyword toàn doc
        analysis    = analyze_section(section)
        section_kws = extract_keywords_for_section(section, top_n=5)

        node            = Node(id=f"h_{i}", title=title, level=level)
        node.keywords   = list(section_kws.keys())  # keyword của RIÊNG section này
        node.summary    = analysis["summary"]
        node.main_idea  = analysis["main_idea"]

        # Build children — ưu tiên bullet items
        bullet_items = analysis["bullet_items"]
        if bullet_items:
            for j, item in enumerate(bullet_items[:6]):
                child = Node(id=f"bullet_{i}_{j}", title=item, level=level+1)
                # Keyword của leaf cũng chỉ từ section cha
                child.keywords = list(section_kws.keys())[:2]
                node.children.append(child)
        else:
            # Fallback: dùng câu từ summary
            if analysis["summary"]:
                for j, sent in enumerate(analysis["summary"].split('. ')[:3]):
                    sent = sent.strip()
                    if len(sent) > 10:
                        child = Node(id=f"sent_{i}_{j}", title=sent, level=level+1)
                        node.children.append(child)
            # Cuối cùng mới dùng keyword — và chỉ keyword của section này
            if not node.children and section_kws:
                for j, kw in enumerate(list(section_kws.keys())[:4]):
                    child = Node(id=f"kw_{i}_{j}", title=kw.replace("_", " ").title(), level=level+1)
                    node.children.append(child)

        # Đặt đúng vị trí trong stack
        while len(stack) > 1 and stack[-1].level >= level:
            stack.pop()
        stack[-1].children.append(node)
        stack.append(node)


def _build_from_topics(root, text, n_topics):
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        words = text.split()
        chunk = max(40, len(words) // n_topics)
        paragraphs = [" ".join(words[i:i+chunk]) for i in range(0, len(words), chunk)]

    if len(paragraphs) <= n_topics:
        for i, p in enumerate(paragraphs):
            node = _make_topic_node(i, p, level=1)
            root.children.append(node)
        return

    tokenized = [" ".join(_tokenize(p)) or p.lower() for p in paragraphs]
    try:
        vec    = TfidfVectorizer(sublinear_tf=True, min_df=1)
        matrix = vec.fit_transform(tokenized)
    except Exception:
        for i, p in enumerate(paragraphs[:n_topics]):
            root.children.append(_make_topic_node(i, p, 1))
        return

    sims = [
        float(cosine_similarity(matrix[i], matrix[i+1])[0][0])
        for i in range(len(paragraphs) - 1)
    ]

    n_bound    = min(n_topics - 1, len(sims))
    boundaries = sorted([i for i, _ in sorted(enumerate(sims), key=lambda x: x[1])[:n_bound]])

    segs, start = [], 0
    for b in boundaries:
        segs.append(paragraphs[start:b+1])
        start = b + 1
    segs.append(paragraphs[start:])

    for i, seg in enumerate([s for s in segs if s]):
        combined = " ".join(seg)
        node     = _make_topic_node(i, combined, level=1)

        # Children chỉ từ nội dung segment này
        analysis = analyze_section(combined)
        if analysis["bullet_items"]:
            for j, item in enumerate(analysis["bullet_items"][:5]):
                child = Node(id=f"sub_{i}_{j}", title=item, level=2)
                node.children.append(child)
        elif len(seg) > 1:
            for j, sub in enumerate(seg[:3]):
                a         = analyze_section(sub)
                sub_title = a["main_idea"] or sub.split('.')[0].strip()[:60]
                if sub_title and len(sub_title) > 5:
                    child = Node(id=f"sub_{i}_{j}", title=_clean_title(sub_title), level=2)
                    node.children.append(child)

        root.children.append(node)


def _make_topic_node(idx, text, level=1, prefix="t") -> Node:
    analysis    = analyze_section(text)
    section_kws = extract_keywords_for_section(text, top_n=5)

    title = analysis["main_idea"]
    if not title or len(title) < 5:
        first = text.strip().split('.')[0].strip()
        title = first if 5 <= len(first) <= 60 else (
            list(section_kws.keys())[0].replace("_", " ").title()
            if section_kws else f"Chủ đề {idx+1}"
        )

    node            = Node(id=f"{prefix}_{idx}", title=_clean_title(title), level=level)
    node.keywords   = list(section_kws.keys())  # chỉ keyword của section này
    node.summary    = analysis["summary"]
    node.main_idea  = analysis["main_idea"]

    # Children từ bullet — chỉ trong section này
    for j, item in enumerate(analysis["bullet_items"][:5]):
        child = Node(id=f"leaf_{prefix}_{idx}_{j}", title=item, level=level+1)
        node.children.append(child)

    if not node.children and section_kws:
        for j, kw in enumerate(list(section_kws.keys())[:4]):
            child = Node(id=f"kw_{prefix}_{idx}_{j}", title=kw.replace("_", " ").title(), level=level+1)
            node.children.append(child)

    return node


def _detect_doc_title(text) -> str:
    lines = [l.strip() for l in text.split('\n') if l.strip()][:8]
    for line in lines:
        line = unicodedata.normalize("NFC", line)
        if 5 <= len(line) <= 80 and not re.search(r'[,;]\s*$', line):
            return _clean_title(line)
    return "Tài liệu"


def _clean_title(title) -> str:
    title = unicodedata.normalize("NFC", title)
    title = re.sub(r'^[\d]+\.\s*', '', title)
    title = re.sub(r'^[A-Z]\.\s*', '', title)
    title = title.replace("_", " ").strip()
    title = re.sub(r'\s+', ' ', title)
    if len(title) > 55:
        title = title[:52] + "..."
    return title.strip() or "Node"


def _count_nodes(node) -> int:
    return 1 + sum(_count_nodes(c) for c in node.children)
