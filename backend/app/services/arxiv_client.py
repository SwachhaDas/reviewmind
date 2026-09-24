"""
arXiv API client — no API key needed, no aggressive rate limits.

Returns paper data enriched with the same verification fields as
OpenAlex and Semantic Scholar clients so pipeline code stays uniform.

arXiv API docs: http://export.arxiv.org/api/query
"""
import os
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime

import requests


_ARXIV_API = "http://export.arxiv.org/api/query"
_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def search_arxiv(keyword, year_min=2000, year_max=2030, limit=10):
    """
    Search papers via arXiv API.
    Returns list of paper dicts compatible with OpenAlex/S2 schema.
    """
    if not keyword:
        return []

    # arXiv search supports AND/OR and field prefixes
    query = f"all:{keyword}"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": min(max(limit * 2, 20), 100),  # over-fetch for year filter
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    url = f"{_ARXIV_API}?{urllib.parse.urlencode(params)}"

    max_retries = 2
    fetch_time = datetime.utcnow().isoformat() + "Z"
    response_text = ""

    for attempt in range(max_retries):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                response_text = r.text
                break
            if r.status_code == 429:
                print("[arxiv] Rate limited — skipping (no wait)")
                return []
            print(f"[arxiv] HTTP {r.status_code} — skipping")
            return []
        except Exception as e:
            print(f"[arxiv] Exception: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return []

    if not response_text:
        return []

    # Parse Atom XML
    try:
        root = ET.fromstring(response_text)
    except ET.ParseError as e:
        print(f"[arxiv] XML parse error: {e}")
        return []

    results = []
    for entry in root.findall("atom:entry", _NS):
        try:
            # Title (strip extra whitespace)
            title_el = entry.find("atom:title", _NS)
            title = " ".join((title_el.text or "").split()) if title_el is not None else ""

            # Summary/abstract
            summary_el = entry.find("atom:summary", _NS)
            abstract = " ".join((summary_el.text or "").split()) if summary_el is not None else ""

            # Published date → year
            pub_el = entry.find("atom:published", _NS)
            pub_date = pub_el.text if pub_el is not None else ""
            year = pub_date[:4] if pub_date else ""

            # Year filter
            try:
                y_int = int(year) if year else None
            except ValueError:
                y_int = None
            if y_int and (y_int < year_min or y_int > year_max):
                continue

            # arXiv ID and abstract URL
            id_el = entry.find("atom:id", _NS)
            arxiv_url = id_el.text if id_el is not None else ""
            arxiv_id = ""
            if arxiv_url:
                m = re.search(r"abs/([^v]+)", arxiv_url)
                if m:
                    arxiv_id = m.group(1)

            # Authors
            authors = []
            for author in entry.findall("atom:author", _NS):
                name_el = author.find("atom:name", _NS)
                if name_el is not None and name_el.text:
                    authors.append(name_el.text.strip())

            # DOI (if published)
            doi = ""
            doi_el = entry.find("arxiv:doi", _NS)
            if doi_el is not None and doi_el.text:
                doi = doi_el.text.strip()

            # PDF link
            pdf_url = ""
            for link in entry.findall("atom:link", _NS):
                if link.get("title") == "pdf" or link.get("type") == "application/pdf":
                    pdf_url = link.get("href", "")
                    break

            # Venue (journal ref if available)
            journal_el = entry.find("arxiv:journal_ref", _NS)
            venue = journal_el.text.strip() if journal_el is not None and journal_el.text else "arXiv"

            # Verification URL
            verification_url = arxiv_url or (f"https://doi.org/{doi}" if doi else "")

            results.append({
                # Core data
                "id": arxiv_id or arxiv_url,
                "title": title,
                "authors": ", ".join(authors),
                "year": year,
                "abstract": abstract,
                "doi": doi,
                "url": arxiv_url,
                "venue": venue,
                "pdf_url": pdf_url,

                # Verification metadata
                "source_api": "arxiv",
                "api_endpoint": url,
                "api_response_id": arxiv_id,
                "arxiv_id": arxiv_id,
                "verification_url": verification_url,
                "fetched_at": fetch_time,
            })

            if len(results) >= limit:
                break

        except Exception as e:
            print(f"[arxiv] Entry parse error: {e}")
            continue

    print(f"[arxiv] Found {len(results)} papers")
    return results
