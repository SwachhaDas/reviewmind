"""
Paper Search — sync version with OpenAlex retry + S2 rate-limit tracking.

Fixes:
  - OpenAlex gets retry with exponential backoff (2s/4s/8s) on 504/timeout.
  - Semantic Scholar rate limit is tracked in-memory. Once blocked, we skip
    the call entirely instead of wasting 10+20+30+40 = 100s waiting.
  - Query expansion (ML → machine learning) preserved.
"""
import json
import os
import time

from app.services.semantic_scholar import search_semantic_scholar


# ─────────────────────────────────────────────────────────────
# Abbreviation expansion (unchanged)
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
# Semantic Scholar rate-limit tracking (in-memory)
# ─────────────────────────────────────────────────────────────

# Track when S2 becomes rate-limited. Once set, skip S2 calls until
# this timestamp passes — no more 100s wait cycles.
_S2_BLOCKED_UNTIL = 0.0
_S2_BLOCK_DURATION = 300  # 5 minutes


# ─────────────────────────────────────────────────────────────
# Main search
# ─────────────────────────────────────────────────────────────

def search_papers(keyword, year_min=2000, year_max=2030, limit=10):
    """
    OpenAlex-first search with retry. Falls back to Semantic Scholar
    only if OpenAlex fails, and only if S2 is not rate-limited.

    No more 100s waits — S2 rate-limit state is remembered.
    """
    global _S2_BLOCKED_UNTIL

    expanded_keyword = _expand_query(keyword)
    if expanded_keyword != keyword:
        print(f"[search] Query expanded: '{keyword}' → '{expanded_keyword}'")
    else:
        print(f"[search] Query: '{keyword}'")

    # ═══════════════════════════════════════════════
    # PRIMARY: OpenAlex with retry
    # ═══════════════════════════════════════════════
    try:
        from app.services.openalex_client import search_openalex
    except ImportError as e:
        print(f"[search] Cannot import openalex_client: {e}")
        return _try_semantic_scholar(expanded_keyword, year_min, year_max, limit)

    # Retry with delays: 0s (first try), 2s, 4s, 8s
    delays = [0, 2, 4, 8]
    for attempt, delay in enumerate(delays):
        if delay > 0:
            print(f"[search] OpenAlex retry in {delay}s "
                  f"(attempt {attempt + 1}/{len(delays)})...")
            time.sleep(delay)

        try:
            papers = search_openalex(
                expanded_keyword, year_min, year_max, limit
            )
            if papers and len(papers) > 0:
                print(f"[search] OpenAlex: {len(papers)} papers found")
                return papers
            print(f"[search] OpenAlex returned 0 papers "
                  f"(attempt {attempt + 1}/{len(delays)})")

        except Exception as e:
            err = str(e)[:120]
            print(f"[search] OpenAlex error (attempt {attempt + 1}): {err}")

    # ═══════════════════════════════════════════════
    # FALLBACK: Semantic Scholar (skip if rate-limited)
    # ═══════════════════════════════════════════════
    return _try_semantic_scholar(
        expanded_keyword, year_min, year_max, limit
    )


def _try_semantic_scholar(keyword, year_min, year_max, limit):
    """Semantic Scholar fallback — skips if we're already rate-limited."""
    global _S2_BLOCKED_UNTIL

    now = time.time()
    if now < _S2_BLOCKED_UNTIL:
        remaining = int(_S2_BLOCKED_UNTIL - now)
        print(f"[search] Semantic Scholar known rate-limited — "
              f"skipping call, unblocks in {remaining}s")
        return []

    try:
        papers = search_semantic_scholar(
            keyword, year_min, year_max, limit
        )
        if papers and len(papers) > 0:
            print(f"[search] Semantic Scholar: {len(papers)} papers found")
            return papers
        print("[search] Semantic Scholar returned 0 papers")
    except Exception as e:
        err = str(e)
        if "429" in err or "rate" in err.lower():
            _S2_BLOCKED_UNTIL = time.time() + _S2_BLOCK_DURATION
            print(f"[search] Semantic Scholar rate-limited (429). "
                  f"Blocking for {_S2_BLOCK_DURATION}s — no wait, "
                  f"future calls skipped.")
        else:
            print(f"[search] Semantic Scholar failed: {err[:120]}")

    print("[search] Both APIs failed — returning empty list")
    return []