# routes/mindmap_routes.py
# API endpoint trả về mindmap JSON

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.routes.pdf_routes import get_text_by_id, get_filename_by_id
from app.services.preprocess_service import preprocess_text
from app.services.keyword_service import extract_keywords
from app.services.ranking_service import rank_sentences
from app.services.layout_service import detect_headings
from app.services.hierarchy_service import build_hierarchy
from app.services.export_service import export_to_json

router = APIRouter()


@router.get("/mindmap/{file_id}")
def get_mindmap(
    file_id: str,
    max_keywords: int = Query(default=15, ge=5,  le=30),
    top_sentences: int = Query(default=5,  ge=3,  le=15),
    num_topics:    int = Query(default=4,  ge=2,  le=10),
):
    """
    Chạy toàn bộ pipeline NLP và trả về mindmap JSON.

    Response: {
        "title": "...",
        "nodes": [...],
        "edges": [...],
        "stats": {...}
    }
    """
    # 1. Lấy text từ file đã upload
    text = get_text_by_id(file_id)
    title = get_filename_by_id(file_id)

    if not text or len(text.strip()) < 50:
        raise HTTPException(status_code=422, detail="Text quá ngắn để phân tích")

    try:
        # 2. Preprocess
        tokens, sentences, paragraphs = preprocess_text(text)

        # 3. TF-IDF keywords
        keywords = extract_keywords(text, top_n=max_keywords)

        # 4. TextRank sentence ranking
        top_sents = rank_sentences(text, top_n=top_sentences)

        # 5. Layout analysis (detect headings từ structure)
        headings = detect_headings(text)

        # 6. Build hierarchy tree
        hierarchy = build_hierarchy(
            text=text,
            headings=headings,
            keywords=keywords,
            summaries=top_sents,
            n_topics=num_topics,
        )

        # 7. Export sang JSON cho React Flow
        result = export_to_json(hierarchy, title=title, keywords=keywords)

        return JSONResponse(result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý: {str(e)}")


@router.get("/mindmap/{file_id}/keywords")
def get_keywords(file_id: str, top_n: int = Query(default=20, ge=5, le=50)):
    """Trả về chỉ keywords — dùng để preview nhanh."""
    text = get_text_by_id(file_id)
    keywords = extract_keywords(text, top_n=top_n)
    return {"keywords": keywords}


@router.get("/mindmap/{file_id}/summary")
def get_summary(file_id: str, top_n: int = Query(default=5, ge=3, le=15)):
    """Trả về chỉ top sentences."""
    text = get_text_by_id(file_id)
    sentences = rank_sentences(text, top_n=top_n)
    return {"sentences": sentences}
