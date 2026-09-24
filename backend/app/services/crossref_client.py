"""
Crossref API client — no API key needed, generous rate limits.

Uses polite mailto param (from OPENALEX_CONTACT_EMAIL env var) to get
into Crossref's polite pool, which has higher rate limits.

Crossref API docs: https://api.crossref.org/swagger-ui/index.html
"""
import os
import time
from datetime import datetime

import requests


_CROSSREF_API = "https://api.crossref.org/works"


def search_crossref(keyword, year_min=2000, year_max=2030, limit=10):
    """
    Search papers via Crossref API.
    Returns list of paper dicts compatible with OpenAlex/S2 schema.
    """
    if not keyword:
        return []

    # Polite pool email from env (fallback to generic)
    contact_email = os.getenv("OPENALEX_CONTACT_EMAIL", "research@example.com")

    params = {
        "query": keyword,
        "rows": min(max(limit * 2, 20), 100),
        "filter": f"from-pub-date:{year_min}-01-01,until-pub-date:{year_max}-12-31",
        "select": "DOI,title,author,abstract,published,container-title,URL,type",
        "mailto": contact_email,
    }

    url = _CROSSREF_API
    max_retries = 2
    fetch_time = datetime.utcnow().isoformat() + "Z"
    data = {"message": {"items": []}}

    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                break
            if r.status_code == 429:
                print("[crossref] Rate limited — skipping (no wait)")
                return []
            print(f"[crossref] HTTP {r.status_code} — skipping")
            return []
        except Exception as e:
            print(f"[crossref] Exception: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return []

    items = (data.get("message") or {}).get("items", []) or []
    results = []

    for item in items:
        try:
            # Title (list of strings)
            title_list = item.get("title") or []
            title = title_list[0].strip() if title_list else ""

            # Abstract (strip HTML tags)
            abstract_raw = item.get("abstract") or ""
            abstract = _strip_html(abstract_raw)

            # Year from published date
            pub = item.get("published") or {}
            date_parts = (pub.get("date-parts") or [[]])[0]
            year = str(date_parts[0]) if date_parts else ""

            # Year filter (Crossref filters already, but double-check)
            try:
                y_int = int(year) if year else None
            except ValueError:
                y_int = None
            if y_int and (y_int < year_min or y_int > year_max):
                continue

            # Authors
            authors = []
            for author in item.get("author", []) or []:
                given = author.get("given", "")
                family = author.get("family", "")
                name = f"{given} {family}".strip()
                if name:
                    authors.append(name)

            # DOI
            doi = item.get("DOI", "") or ""

            # Venue
            container = item.get("container-title") or []
            venue = container[0].strip() if container else ""

            # URL (prefer DOI link)
            verification_url = f"https://doi.org/{doi}" if doi else item.get("URL", "")

            results.append({
                # Core data
                "id": doi or item.get("URL", ""),
                "title": title,
                "authors": ", ".join(authors),
                "year": year,
                "abstract": abstract,
                "doi": doi,
                "url": f"https://doi.org/{doi}" if doi else item.get("URL", ""),
                "venue": venue,
                "pdf_url": "",  # Crossref doesn't give direct PDF

                # Verification metadata
                "source_api": "crossref",
                "api_endpoint": url,
                "api_response_id": doi,
                "crossref_doi": doi,
                "verification_url": verification_url,
                "fetched_at": fetch_time,
            })

            if len(results) >= limit:
                break

        except Exception as e:
            print(f"[crossref] Entry parse error: {e}")
            continue

    print(f"[crossref] Found {len(results)} papers")
    return results


def _strip_html(text: str) -> str:
    """Strip HTML tags from Crossref abstracts."""
    import re
    if not text:
        return ""
    # Remove <jats:p>, <jats:title>, etc.
    cleaned = re.sub(r"<[^>]+>", " ", text)
    # Collapse whitespace
    return " ".join(cleaned.split())
