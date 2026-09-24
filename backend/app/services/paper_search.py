"""
Paper Search — multi-source fallback chain.

Priority (fastest + most reliable first):
  1. arXiv       (no rate limit, always works, ~3s)
  2. Crossref    (generous limit, polite pool, ~2s)
  3. OpenAlex    (bonus — skip-on-429, no wait)
  4. Semantic Scholar (bonus — skip-on-429, no wait)

Design:
  - Fast sources first (arXiv + Crossref usually return 15-20 papers total)
  - If we already have enough papers, skip slower sources entirely
  - Any source failure → skip, never block the pipeline
  - Query expansion (ML → machine learning) preserved
  - Dedup by DOI or title
"""
import json
import os

from app.services.arxiv_client import search_arxiv
from app.services.crossref_client import search_crossref


# ─────────────────────────────────────────────────────────────
# Abbreviation expansion
# ─────────────────────────────────────────────────────────────

_ABBREV_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "abbreviations.json",
)

_abbrev_cache = None


def _load_abbreviations():
    global _abbrev_cache
    if _abbrev_cache is not None:
        return _abbrev_cache
    try:
        with open(_ABBREV_FILE, "r", encoding="utf-8") as f:
            _abbrev_cache = json.load(f)
            return _abbrev_cache
    except (OSError, json.JSONDecodeError) as e:
        print(f"[search] Could not load abbreviations: {e}")
        _abbrev_cache = {}
        return _abbrev_cache


def _expand_query(keyword: str) -> str:
    """Expand common abbreviations (ML → ML machine learning)."""
    if not keyword:
        return keyword

    abbrevs = _load_abbreviations()
    if not abbrevs:
        return keyword

    skip_words = {
        "in", "on", "of", "for", "and", "or", "the", "a", "an",
        "to", "with", "by", "at", "from", "as", "is", "are",
    }

    words = keyword.split()
    expanded = []
    expansions_added = []

    for word in words:
        cleaned = word.lower().strip(".,;:!?\"'()[]{}")
        expanded.append(word)
        if cleaned in skip_words or len(cleaned) < 2:
            continue
        if cleaned in abbrevs and cleaned != "_comment":
            for expansion in abbrevs[cleaned]:
                if expansion not in expansions_added:
                    expansions_added.append(expansion)

    if expansions_added:
        expanded.extend(expansions_added)

    return " ".join(expanded)


# ─────────────────────────────────────────────────────────────
# Dedup helper — cross-source key
# ─────────────────────────────────────────────────────────────

def _dedup_key(paper):
    """Stable dedup key across sources."""
    doi = (paper.get("doi") or "").strip().lower()
    if doi:
        return f"doi:{doi}"
    title = (paper.get("title") or "").strip().lower()[:60]
    return f"title:{title}"


# ─────────────────────────────────────────────────────────────
# Main search — multi-source fallback chain
# ─────────────────────────────────────────────────────────────

def search_papers(keyword, year_min=2000, year_max=2030, limit=10):
    """
    Multi-source search: arXiv → Crossref → OpenAlex → Semantic Scholar.

    Fast sources first. If we already have enough unique papers, skip
    slower ones. Any source failure is skipped (never blocks the pipeline).
    """
    expanded_keyword = _expand_query(keyword)
    if expanded_keyword != keyword:
        print(f"[search] Query expanded: '{keyword}' → '{expanded_keyword}'")
    else:
        print(f"[search] Query: '{keyword}'")

    seen_keys = set()
    all_papers = []

    def _add_papers(new_papers):
        """Add new papers, dedup by DOI/title. Returns count added."""
        added = 0
        for p in new_papers or []:
            key = _dedup_key(p)
            if key and key not in seen_keys:
                seen_keys.add(key)
                all_papers.append(p)
                added += 1
        return added

    # ═══════════════════════════════════════════════════════
    # SOURCE 1: arXiv (fast, no rate limit)
    # ═══════════════════════════════════════════════════════
    try:
        arxiv_papers = search_arxiv(
            expanded_keyword, year_min, year_max, limit
        )
        added = _add_papers(arxiv_papers)
        print(f"[search] arXiv: {added} unique papers added")
    except Exception as e:
        print(f"[search] arXiv failed: {str(e)[:120]}")

    # Early exit if we already have enough
    if len(all_papers) >= limit:
        print(f"[search] ✅ Have enough papers ({len(all_papers)}) — skipping other sources")
        return all_papers[:limit]

    # ═══════════════════════════════════════════════════════
    # SOURCE 2: Crossref (fast, generous limit)
    # ═══════════════════════════════════════════════════════
    try:
        remaining = limit - len(all_papers)
        crossref_papers = search_crossref(
            expanded_keyword, year_min, year_max, remaining
        )
        added = _add_papers(crossref_papers)
        print(f"[search] Crossref: {added} unique papers added")
    except Exception as e:
        print(f"[search] Crossref failed: {str(e)[:120]}")

    if len(all_papers) >= limit:
        print(f"[search] ✅ Have enough papers ({len(all_papers)}) — skipping other sources")
        return all_papers[:limit]

    # ═══════════════════════════════════════════════════════
    # SOURCE 3: OpenAlex (bonus — skip-on-429, no wait)
    # ═══════════════════════════════════════════════════════
    try:
        from app.services.openalex_client import search_openalex
        remaining = limit - len(all_papers)
        openalex_papers = search_openalex(
            expanded_keyword, year_min, year_max, remaining
        )
        added = _add_papers(openalex_papers)
        print(f"[search] OpenAlex: {added} unique papers added")
    except Exception as e:
        print(f"[search] OpenAlex failed: {str(e)[:120]}")

    if len(all_papers) >= limit:
        print(f"[search] ✅ Have enough papers ({len(all_papers)}) — skipping Semantic Scholar")
        return all_papers[:limit]

    # ═══════════════════════════════════════════════════════
    # SOURCE 4: Semantic Scholar (last bonus — skip-on-429)
    # ═══════════════════════════════════════════════════════
    try:
        from app.services.semantic_scholar import search_semantic_scholar
        remaining = limit - len(all_papers)
        s2_papers = search_semantic_scholar(
            expanded_keyword, year_min, year_max, remaining
        )
        added = _add_papers(s2_papers)
        print(f"[search] Semantic Scholar: {added} unique papers added")
    except Exception as e:
        print(f"[search] Semantic Scholar failed: {str(e)[:120]}")

    print(f"[search] ✅ Total: {len(all_papers)} unique papers from all sources")
    return all_papers[:limit]