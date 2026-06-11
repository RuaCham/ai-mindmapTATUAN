# services/ranking_service.py
import numpy as np
import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from app.services.preprocess_service import _tokenize, _split_sentences


def rank_sentences(text: str, top_n: int = 5) -> list[str]:
    """TextRank — trả về top câu quan trọng nhất."""
    sentences = _split_sentences(text)
    if not sentences:
        return []
    if len(sentences) <= top_n:
        return sentences

    tokenized = [" ".join(_tokenize(s)) or s.lower() for s in sentences]

    vectorizer = TfidfVectorizer(sublinear_tf=True)
    try:
        matrix = vectorizer.fit_transform(tokenized)
    except ValueError:
        return sentences[:top_n]

    sim_matrix = cosine_similarity(matrix)

    graph = nx.Graph()
    n = len(sentences)
    for i in range(n):
        for j in range(i + 1, n):
            score = float(sim_matrix[i][j])
            if score > 0.1:
                graph.add_edge(i, j, weight=score)
    for i in range(n):
        if i not in graph:
            graph.add_node(i)

    try:
        scores = nx.pagerank(graph, weight="weight", alpha=0.85, max_iter=200)
    except Exception:
        scores = {i: 1.0 / n for i in range(n)}

    top_indices = sorted(
        sorted(scores, key=scores.get, reverse=True)[:top_n]
    )
    return [sentences[i] for i in top_indices]
