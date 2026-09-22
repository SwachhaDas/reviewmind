"""
Semantic Scholar API client.

Returns paper data enriched with verification fields:
  - source_api: 'semantic_scholar'
  - api_endpoint: full request URL
  - semantic_scholar_id: paper ID
  - doi, url, verification_url
  - fetched_at: ISO timestamp
"""
import os
import time
import requests
from datetime import datetime


def search_semantic_scholar(keyword, year_min=2000, year_max=2030, limit=10):
    """
    Search papers via Semantic Scholar API.
    Returns list of paper dicts with full verification metadata.
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": keyword,
        "limit": limit,
        "year": f"{year_min}-{year_max}",
        "fields": "title,authors,publicationDate,abstract,externalIds,url,venue",
    }

    headers = {}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key

    max_retries = 4
    data = {"data": []}
    fetch_time = datetime.utcnow().isoformat() + "Z"

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=20)

            if response.status_code == 200:
                data = response.json()
                break

            if response.status_code == 429:
                wait = 10 * (attempt + 1)
                print(f"[semantic-scholar] Rate limit. Waiting {wait}s...")
                time.sleep(wait)
                continue

            print(f"[semantic-scholar] Error: {response.status_code}")
            break
        except Exception as e:
            print(f"[semantic-scholar] Exception: {e}")
            time.sleep(5)

    # Build full API endpoint URL for verification
    full_endpoint = f"{url}?query={keyword}&limit={limit}&year={year_min}-{year_max}"

    results = []
    for paper in data.get("data", []):
        authors = [a.get("name", "") for a in paper.get("authors", []) or []]
        pub_date = paper.get("publicationDate") or ""
        paper_id = paper.get("paperId", "")
        doi = (paper.get("externalIds") or {}).get("DOI", "")
        paper_url = paper.get("url", "") or ""

        # Build verification URL
        if paper_id:
            verification_url = f"https://www.semanticscholar.org/paper/{paper_id}"
        elif doi:
            verification_url = f"https://doi.org/{doi}"
        else:
            verification_url = paper_url

        results.append({
            # ─── Core data ───
            "id": paper_id,
            "title": paper.get("title", "") or "",
            "authors": ", ".join(authors),
            "year": pub_date[:4] if pub_date else "",
            "abstract": paper.get("abstract", "") or "",
            "doi": doi,
            "url": paper_url,
            "venue": paper.get("venue", "") or "",

            # ─── Verification metadata ───
            "source_api": "semantic_scholar",
            "api_endpoint": full_endpoint,
            "api_response_id": paper_id,
            "semantic_scholar_id": paper_id,
            "verification_url": verification_url,
            "fetched_at": fetch_time,
        })

    print(f"[semantic-scholar] Found {len(results)} papers")
    return results