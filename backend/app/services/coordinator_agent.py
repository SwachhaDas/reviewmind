"""
Coordinator Agent — pipeline with:
  • Parallel PDF fetch (ThreadPoolExecutor)
  • Multi-source PDF lookup (6 sources for maximum success rate)
  • Merged screen+extract (batch AI call)
  • Pre-report validation (count consistency)
  • Screening-error logging
"""
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from app.services.dedup_agent import deduplicate_papers
from app.services.gemini_client import batch_screen_and_extract
from app.services.paper_search import search_papers


# ═════════════════════════════════════════════════════════════
# CONFIG
# ═════════════════════════════════════════════════════════════
_UNPAYWALL_EMAIL = "swachhadas@gmail.com"   # ← YOUR real email

_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

_PDF_TIMEOUT = 3.0
_MAX_PDF_BYTES = 8 * 1024 * 1024


def _extract_year_threshold(criteria: str):
    """Extract a year threshold from a criteria string."""
    if not criteria:
        return None
    patterns = [
        r"(\d{4})\s*\+",
        r"(\d{4})\s*or\s+(?:later|newer)",
        r"after\s+(\d{4})",
        r"since\s+(\d{4})",
        r"from\s+(\d{4})",
        r"(\d{4})\s*[-–]\s*\d{4}",
    ]
    for pat in patterns:
        m = re.search(pat, criteria, re.IGNORECASE)
        if m:
            try:
                y = int(m.group(1))
                if 1900 <= y <= 2100:
                    return y
            except (ValueError, IndexError):
                continue
    m = re.search(r"\b(19\d{2}|20\d{2})\b", criteria)
    if m:
        try:
            y = int(m.group(1))
            if 1900 <= y <= 2100:
                return y
        except (ValueError, IndexError):
            pass
    return None


def _paper_year(p):
    """Safely extract integer year."""
    y = p.get("year")
    if y is None:
        return None
    try:
        return int(y)
    except (ValueError, TypeError):
        return None


def _paper_id(paper):
    """Get stable ID for a paper."""
    return (
        paper.get("id")
        or paper.get("doi")
        or paper.get("title", "")[:60]
        or "unknown"
    )


def _bare_doi(doi: str) -> str:
    """Strip URL prefix from DOI."""
    if not doi:
        return ""
    return (
        doi.replace("https://doi.org/", "")
           .replace("http://doi.org/", "")
           .strip()
    )


# ═════════════════════════════════════════════════════════════
# SOURCE 1: Unpaywall
# ═════════════════════════════════════════════════════════════

def _get_unpaywall_pdf_url(doi: str) -> str:
    """Query Unpaywall for open-access PDF URL."""
    if not doi:
        return ""
    try:
        bare = _bare_doi(doi)
        resp = requests.get(
            f"https://api.unpaywall.org/v2/{bare}",
            params={"email": _UNPAYWALL_EMAIL},
            timeout=3,
            headers={"User-Agent": "ReviewMind/1.0 (SLR tool)"},
        )
        if resp.status_code == 200:
            data = resp.json()
            best = data.get("best_oa_location") or {}
            url = best.get("url_for_pdf") or best.get("url")
            if url:
                return url
        return ""
    except Exception:
        return ""


# ═════════════════════════════════════════════════════════════
# SOURCE 2: Semantic Scholar openAccessPdf
# ═════════════════════════════════════════════════════════════

def _get_semantic_scholar_pdf_url(doi: str) -> str:
    """Query Semantic Scholar API for openAccessPdf URL."""
    if not doi:
        return ""
    try:
        bare = _bare_doi(doi)
        # Semantic Scholar Graph API — paper endpoint by DOI
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{bare}"
        resp = requests.get(
            url,
            params={"fields": "openAccessPdf,externalIds"},
            timeout=3,
            headers={"User-Agent": "ReviewMind/1.0"},
        )
        if resp.status_code == 200:
            data = resp.json()
            oa = data.get("openAccessPdf") or {}
            pdf_url = oa.get("url")
            if pdf_url:
                return pdf_url
        return ""
    except Exception:
        return ""


# ═════════════════════════════════════════════════════════════
# SOURCE 3: CORE API (aggregator of 200M+ open-access papers)
# ═════════════════════════════════════════════════════════════

def _get_core_pdf_url(doi: str) -> str:
    """
    Query CORE.ac.uk for open-access PDF URL.
    CORE provides free API access (no key for basic search).
    """
    if not doi:
        return ""
    try:
        bare = _bare_doi(doi)
        # CORE search by DOI
        resp = requests.get(
            "https://api.core.ac.uk/v3/search/works",
            params={"q": f'doi:"{bare}"', "limit": 1},
            timeout=3,
            headers={"User-Agent": "ReviewMind/1.0"},
        )
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                first = results[0]
                # Try downloadUrl
                pdf_url = first.get("downloadUrl") or first.get("fullTextIdentifier")
                if pdf_url:
                    return pdf_url
        return ""
    except Exception:
        return ""


# ═════════════════════════════════════════════════════════════
# SOURCE 4: PubMed Central (biomedical open-access)
# ═════════════════════════════════════════════════════════════

def _get_pmc_pdf_url(doi: str) -> str:
    """
    Query NCBI PubMed Central for free full-text PDF.
    Only works for biomedical papers (PMC-indexed).
    """
    if not doi:
        return ""
    try:
        bare = _bare_doi(doi)
        # NCBI eutils ID converter to get PMC ID from DOI
        resp = requests.get(
            "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/",
            params={
                "ids": bare,
                "format": "json",
                "tool": "reviewmind",
                "email": _UNPAYWALL_EMAIL,
            },
            timeout=3,
            headers={"User-Agent": "ReviewMind/1.0"},
        )
        if resp.status_code == 200:
            data = resp.json()
            records = data.get("records", [])
            if records:
                pmcid = records[0].get("pmcid")
                if pmcid:
                    # Direct PMC PDF URL
                    return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
        return ""
    except Exception:
        return ""


# ═════════════════════════════════════════════════════════════
# SOURCE 5: OpenAlex location URLs (multiple per paper)
# ═════════════════════════════════════════════════════════════

def _get_openalex_all_urls(paper: dict) -> list:
    """Extract ALL open-access URLs from OpenAlex metadata."""
    urls = []
    # Direct URL
    oa = paper.get("open_access_url") or paper.get("oa_url")
    if oa:
        urls.append(oa)
    # All locations
    for loc in paper.get("open_access_locations", []) or []:
        if isinstance(loc, dict):
            for key in ("pdf_url", "landing_page_url", "url"):
                u = loc.get(key)
                if u and u not in urls:
                    urls.append(u)
    return urls


# ═════════════════════════════════════════════════════════════
# PDF FETCH — tries multiple sources
# ═════════════════════════════════════════════════════════════

def _download_pdf(url: str, timeout: float) -> bytes:
    """Download a PDF with size cap. Returns bytes or empty."""
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            stream=True,
            headers={
                "User-Agent": _BROWSER_UA,
                "Accept": "application/pdf,*/*",
            },
            allow_redirects=True,
        )
        if resp.status_code != 200:
            return b""
        chunks = []
        total = 0
        try:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    chunks.append(chunk)
                    total += len(chunk)
                    if total > _MAX_PDF_BYTES:
                        break
        except requests.exceptions.ChunkedEncodingError:
            pass
        return b"".join(chunks)
    except Exception:
        return b""


def _fetch_single_pdf(paper: dict, timeout: float = _PDF_TIMEOUT) -> tuple:
    """
    Download a paper's open-access PDF and extract relevant sections.

    Tries 6 sources in order:
      1. OpenAlex direct URL
      2. OpenAlex all location URLs
      3. Unpaywall API
      4. Semantic Scholar openAccessPdf
      5. CORE.ac.uk
      6. PubMed Central
      7. arXiv (if available)
    """
    pid = _paper_id(paper)
    doi = paper.get("doi", "")
    title = paper.get("title", "")[:40]

    # ─── Build candidate URL list from all sources ───
    candidate_urls = []

    # 1. OpenAlex URLs
    for u in _get_openalex_all_urls(paper):
        if u and u not in candidate_urls:
            candidate_urls.append(u)

    # 2. Unpaywall
    if doi:
        uw = _get_unpaywall_pdf_url(doi)
        if uw and uw not in candidate_urls:
            candidate_urls.append(uw)

    # 3. Semantic Scholar PDF
    if doi:
        ss = _get_semantic_scholar_pdf_url(doi)
        if ss and ss not in candidate_urls:
            candidate_urls.append(ss)

    # 4. CORE
    if doi:
        core = _get_core_pdf_url(doi)
        if core and core not in candidate_urls:
            candidate_urls.append(core)

    # 5. PubMed Central (biomedical only)
    if doi:
        pmc = _get_pmc_pdf_url(doi)
        if pmc and pmc not in candidate_urls:
            candidate_urls.append(pmc)

    # 6. arXiv
    arxiv_id = paper.get("arxiv_id") or paper.get("arxiv")
    if arxiv_id:
        arxiv_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        if arxiv_url not in candidate_urls:
            candidate_urls.append(arxiv_url)

    if not candidate_urls:
        return (pid, "", "no_pdf_source")

    # ─── Try each URL ───
    print(f"      🔍 Trying {len(candidate_urls)} source(s) for '{title}'...")

    last_error = "no_pdf_source"

    for i, url in enumerate(candidate_urls, 1):
        pdf_bytes = _download_pdf(url, timeout)

        if not pdf_bytes:
            last_error = f"download_failed_{i}"
            continue
        if len(pdf_bytes) < 1000:
            last_error = f"too_small_{i}"
            continue
        if not pdf_bytes.startswith(b"%PDF-"):
            last_error = f"not_pdf_{i}"
            continue

        # Extract text
        from app.services.pdf_parser import (
            extract_text_from_pdf,
            extract_relevant_sections,
        )
        try:
            raw = extract_text_from_pdf(pdf_bytes)
            if not raw or len(raw.strip()) < 500:
                last_error = f"empty_text_{i}"
                continue

            text = extract_relevant_sections(raw)
            if not text or len(text.strip()) < 200:
                last_error = f"no_sections_{i}"
                continue

            print(f"      ✅ {title}: {len(text)} chars from source {i}")
            return (pid, text, None)
        except Exception as e:
            last_error = f"parse_error_{i}"
            continue

    return (pid, "", last_error)


def _parallel_fetch_full_text(
    papers: list,
    per_paper_timeout: float = _PDF_TIMEOUT,
    max_workers: int = 10,
) -> dict:
    """Concurrently download PDFs for all papers."""
    results = {}
    if not papers:
        return results

    with ThreadPoolExecutor(max_workers=min(max_workers, len(papers))) as ex:
        futures = {
            ex.submit(_fetch_single_pdf, p, per_paper_timeout): p
            for p in papers
        }
        for fut in as_completed(futures):
            try:
                pid, text, err = fut.result()
                results[pid] = {"text": text, "error": err}
            except Exception as e:
                p = futures[fut]
                pid = _paper_id(p)
                results[pid] = {
                    "text": "",
                    "error": f"thread_error:{str(e)[:50]}",
                }
    return results


# ═════════════════════════════════════════════════════════════
# VALIDATION
# ═════════════════════════════════════════════════════════════

def validate_counts(counts: dict, included_count: int) -> list:
    """Validate pipeline count consistency."""
    errors = []
    identified = counts.get("total_found", 0)
    duplicates = counts.get("duplicates_removed", 0)
    excluded = counts.get("irrelevant_excluded", 0)
    maybe = counts.get("maybe", 0)
    error_count = counts.get("error", 0)
    total_included = counts.get("total_included", 0)

    after_dedup = identified - duplicates
    sum_decisions = excluded + maybe + error_count + total_included

    if after_dedup != sum_decisions:
        errors.append(
            f"Count mismatch: after_dedup={after_dedup} but "
            f"excluded+maybe+errors+included={sum_decisions}"
        )

    if total_included != included_count:
        errors.append(
            f"Table-2 row count ({included_count}) != "
            f"total_included count ({total_included})"
        )

    return errors


# ═════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═════════════════════════════════════════════════════════════

def run_pipeline(
    keyword: str,
    criteria: str,
    lang: str = "en",
    year_min: int = 2000,
    year_max: int = 2030,
    limit: int = 10,
    on_progress=None,
) -> dict:
    """Runs the full pipeline with parallel fetch + merged AI."""

    def report(stage, label, current=0, total=0, item=""):
        if on_progress:
            try:
                on_progress(stage, label, current, total, item)
            except Exception as e:
                print(f"[pipeline] progress error: {e}")
        print(f"[pipeline] {label} {current}/{total}" if total else f"[pipeline] {label}")

    # ─── STEP 1: Search ───
    report("search", "🔍 Searching papers...")
    identified = search_papers(keyword, year_min, year_max, limit=limit)
    identified_count = len(identified)
    report("search_done", f"✅ Found {identified_count} papers",
           identified_count, identified_count)

    if not identified:
        return _empty_result()

    # ─── STEP 2: Dedup ───
    if identified_count > 20:
        report("dedup", "🧹 Removing duplicates...")
        deduped, duplicates_removed = deduplicate_papers(identified)
        screened_count = len(deduped)
        report("dedup_done",
               f"✅ {duplicates_removed} duplicates removed — {screened_count} left",
               screened_count, screened_count)
    else:
        deduped = identified
        duplicates_removed = 0
        screened_count = identified_count
        print(f"[pipeline] Skipping dedup (only {identified_count} papers)")

    # ─── STEP 3: Year Pre-filter ───
    year_threshold = _extract_year_threshold(criteria)
    if year_threshold:
        print(f"[pipeline] Year threshold: {year_threshold}+")

    to_process = []
    pre_excluded = []

    for p in deduped:
        py = _paper_year(p)
        if year_threshold and py is not None and py < year_threshold:
            p["decision"] = "Exclude"
            p["reason"] = (
                f"Year {py} fails threshold {year_threshold}+ "
                f"(deterministic filter)."
            )
            p["confidence"] = 100
            p["auto_filtered"] = True
            pre_excluded.append(p)
        else:
            to_process.append(p)

    print(f"[pipeline] Pre-filter: {len(pre_excluded)} excluded, "
          f"{len(to_process)} to AI")

    # ─── STEP 4: Parallel PDF Fetch ───
    fetch_results = {}
    if to_process:
        report(
            "fetch",
            f"📥 Fetching full text for {len(to_process)} papers "
            f"(multi-source)...",
            0,
            len(to_process),
        )
        fetch_results = _parallel_fetch_full_text(
            to_process, per_paper_timeout=_PDF_TIMEOUT
        )

        success_count = 0
        for p in to_process:
            pid = _paper_id(p)
            res = fetch_results.get(pid, {"text": "", "error": "unknown"})
            if res.get("text"):
                p["full_text"] = res["text"]
                success_count += 1
            else:
                p["full_text"] = ""
                print(f"      ⚠️ {p.get('title', '')[:40]}: "
                      f"{res.get('error', 'unknown')} (abstract only)")

        print(f"[pipeline] ✅ Full text fetched: "
              f"{success_count}/{len(to_process)} papers")

    # ─── STEP 5: Batch AI ───
    ai_results = []
    if to_process:
        report(
            "ai",
            f"🤖 Screening + extracting {len(to_process)} papers...",
            len(to_process),
            len(to_process),
        )
        ai_results = batch_screen_and_extract(to_process, criteria, lang)

    # ─── STEP 6: Merge results ───
    results = list(pre_excluded)
    excluded_count = len(pre_excluded)
    maybe_count = 0
    error_count = 0
    screening_errors = []

    for paper, ai_out in zip(to_process, ai_results):
        merged = {**paper, **ai_out}
        merged["methodology"] = ai_out.get("methodology",
                                           "Not specified in the paper.")
        merged["key_findings"] = ai_out.get("findings",
                                            "Not specified in the paper.")
        merged["limitations"] = ai_out.get("limitations",
                                           "Not mentioned in the paper.")
        merged["abstract"] = ai_out.get("abstract", "")
        merged["keywords"] = ai_out.get("keywords", "")

        results.append(merged)

        d = ai_out.get("decision")
        if d == "Exclude":
            excluded_count += 1
        elif d == "Maybe":
            maybe_count += 1
        elif d == "Error":
            error_count += 1
            screening_errors.append({
                "title": paper.get("title", ""),
                "doi": paper.get("doi", ""),
                "reason": ai_out.get("reason", ""),
            })

    included = [p for p in results if p.get("decision") == "Include"]

    # ─── STEP 7: Validation ───
    counts = {
        "total_found": identified_count,
        "duplicates_removed": duplicates_removed,
        "irrelevant_excluded": excluded_count,
        "maybe": maybe_count,
        "error": error_count,
        "total_included": len(included),
    }

    validation_errors = validate_counts(counts, len(included))
    if validation_errors:
        print("[pipeline] ❌ VALIDATION FAILED:")
        for e in validation_errors:
            print(f"   - {e}")
    else:
        print("[pipeline] ✅ Validation passed")

    report("done", "✅ Pipeline complete!")

    print(f"[pipeline] Summary: {identified_count} found | "
          f"{duplicates_removed} dup | {excluded_count} excluded | "
          f"{len(included)} included")

    return {
        "papers": results,
        "included_papers": included,
        "duplicates_removed": duplicates_removed,
        "counts": counts,
        "prisma_counts": {
            "identified": identified_count,
            "duplicates_removed": duplicates_removed,
            "screened": screened_count,
            "excluded": excluded_count,
            "maybe": maybe_count,
            "error": error_count,
            "full_text": len(included),
            "included": len(included),
        },
        "screening_errors": screening_errors,
        "validation_errors": validation_errors,
    }


def _empty_result() -> dict:
    return {
        "papers": [],
        "included_papers": [],
        "duplicates_removed": 0,
        "counts": {
            "total_found": 0, "duplicates_removed": 0,
            "irrelevant_excluded": 0, "maybe": 0, "error": 0,
            "total_included": 0,
        },
        "prisma_counts": {
            "identified": 0, "duplicates_removed": 0,
            "screened": 0, "excluded": 0, "maybe": 0,
            "error": 0, "full_text": 0, "included": 0,
        },
        "screening_errors": [],
        "validation_errors": [],
    }