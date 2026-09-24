"""
OpenAlex API client.

Returns paper data enriched with verification fields:
  - source_api: 'openalex'
  - api_endpoint: full request URL
  - openalex_id: paper ID
  - doi, url, verification_url
  - fetched_at: ISO timestamp
  - venue: journal/conference name (with multiple fallbacks)
"""
import os
import time
import requests
from datetime import datetime


def search_openalex(keyword, year_min=2000, year_max=2030, limit=10):
    """
    Search papers via OpenAlex API.
    Returns list of paper dicts with verification metadata.
    """
    url = "https://api.openalex.org/works"
    contact_email = os.getenv("OPENALEX_CONTACT_EMAIL", "research@example.com")

    params = {
        "search": keyword,
        "filter": f"from_publication_date:{year_min}-01-01,"
                  f"to_publication_date:{year_max}-12-31",
        "per-page": limit,
        "mailto": contact_email,
    }

    max_retries = 4
    data = {"results": []}
    fetch_time = datetime.utcnow().isoformat() + "Z"

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=20)

            if response.status_code == 200:
                data = response.json()
                break

            if response.status_code == 429:
                wait = 5 * (attempt + 1)
                print(f"[openalex] Rate limit. Waiting {wait}s...")
                time.sleep(wait)
                continue

            print(f"[openalex] Error: {response.status_code}")
            break
        except Exception as e:
            print(f"[openalex] Exception: {e}")
            time.sleep(3)

    # Build full API endpoint URL
    full_endpoint = (
        f"{url}?search={keyword}&per-page={limit}"
        f"&filter=year:{year_min}-{year_max}"
    )

    results = []
    for work in data.get("results", []):
        authors = [
            a.get("author", {}).get("display_name", "")
            for a in work.get("authorships", [])
        ]
        pub_date = work.get("publication_date") or ""
        work_id = work.get("id", "")
        doi = (work.get("doi") or "").replace("https://doi.org/", "")
        abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))

        # Build verification URL with multiple fallbacks
        if doi:
            verification_url = f"https://doi.org/{doi}"
        elif work_id:
            verification_url = work_id
        else:
            verification_url = ""

        # Get venue with multiple fallbacks
        venue = _get_venue(work)

        # Get link with fallbacks
        link = _get_link(work, doi, work_id)

        results.append({
            # ─── Core data ───
            "id": work_id,
            "title": work.get("title", "") or "",
            "authors": ", ".join(authors),
            "year": pub_date[:4] if pub_date else "",
            "abstract": abstract,
            "doi": doi,
            "url": link,
            "venue": venue,

            # ─── Verification metadata ───
            "source_api": "openalex",
            "api_endpoint": full_endpoint,
            "api_response_id": work_id,
            "openalex_id": work_id,
            "verification_url": verification_url,
            "fetched_at": fetch_time,
        })

    print(f"[openalex] Found {len(results)} papers")
    return results


# ─────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────

def _reconstruct_abstract(inverted_index):
    """
    OpenAlex returns abstract as inverted index — convert to text.
    Example: {"The": [0], "cat": [1], "sat": [2]} → "The cat sat"
    """
    if not inverted_index:
        return ""

    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))

    word_positions.sort()
    return " ".join(word for _, word in word_positions)


def _get_venue(work):
    """
    Extract venue name from OpenAlex work with multiple fallbacks.

    Tries in order:
      1. primary_location.source.display_name
      2. best_oa_location.source.display_name
      3. host_venue.display_name
      4. locations[0].source.display_name
    """
    # Fallback 1: primary_location
    loc = work.get("primary_location") or {}
    source = loc.get("source") or {}
    name = source.get("display_name", "")
    if name:
        return name

    # Fallback 2: best_oa_location
    best_loc = work.get("best_oa_location") or {}
    best_source = best_loc.get("source") or {}
    name = best_source.get("display_name", "")
    if name:
        return name

    # Fallback 3: host_venue (older OpenAlex API)
    host_venue = work.get("host_venue") or {}
    name = host_venue.get("display_name", "")
    if name:
        return name

    # Fallback 4: first location in locations list
    locations = work.get("locations") or []
    for location in locations:
        loc_source = location.get("source") or {}
        name = loc_source.get("display_name", "")
        if name:
            return name

    # Final fallback
    return "—"


def _get_link(work, doi, work_id):
    """
    Get the best available link for the paper.

    Priority:
      1. DOI link (most stable)
      2. OpenAlex URL
      3. Landing page URL
      4. PDF URL
    """
    # Priority 1: DOI
    if doi:
        return f"https://doi.org/{doi}"

    # Priority 2: OpenAlex ID
    if work_id:
        return work_id

    # Priority 3: Primary location landing page
    loc = work.get("primary_location") or {}
    landing = loc.get("landing_page_url", "")
    if landing:
        return landing

    # Priority 4: Best OA location
    best_loc = work.get("best_oa_location") or {}
    best_url = best_loc.get("landing_page_url", "") or best_loc.get("pdf_url", "")
    if best_url:
        return best_url

    return "—"