"""
Dedup Agent — builds sentence embeddings and removes near-duplicate
papers using cosine similarity (lightweight ML, no API calls needed).
"""
import numpy as np

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")  # small, fast, free model
    return _model


def deduplicate_papers(papers: list[dict], threshold: float = 0.92) -> tuple[list[dict], int]:
    """
    Removes duplicate papers based on abstract embedding similarity.
    Returns: (unique_papers, duplicates_removed_count)
    """
    if len(papers) <= 1:
        return papers, 0

    texts = [p.get("abstract") or p.get("title", "") for p in papers]
    non_empty_idx = [i for i, t in enumerate(texts) if t.strip()]
    if len(non_empty_idx) <= 1:
        return papers, 0

    model = _get_model()
    embeddings = model.encode([texts[i] for i in non_empty_idx], normalize_embeddings=True)

    keep = set(range(len(papers)))
    removed = 0
    n = len(non_empty_idx)
    for a in range(n):
        idx_a = non_empty_idx[a]
        if idx_a not in keep:
            continue
        for b in range(a + 1, n):
            idx_b = non_empty_idx[b]
            if idx_b not in keep:
                continue
            similarity = float(np.dot(embeddings[a], embeddings[b]))
            if similarity >= threshold:
                keep.discard(idx_b)  # treat the later one as the duplicate
                removed += 1

    unique_papers = [p for i, p in enumerate(papers) if i in keep]
    return unique_papers, removed
