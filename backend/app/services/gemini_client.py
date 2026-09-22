"""
Gemini API client — merged screening+extraction, sanitize, batch calls.
"""
import json
import os
import re
import time

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv("GEMINI_API_KEY")
if _api_key:
    genai.configure(api_key=_api_key)

_MODEL_NAME = "gemini-3.5-flash-lite"
_LANG_NAMES = {"en": "English", "bn": "Bengali"}

_last_call_time = 0.0
_MIN_SECONDS_BETWEEN_CALLS = 0.2


def _throttle():
    global _last_call_time
    elapsed = time.time() - _last_call_time
    if elapsed < _MIN_SECONDS_BETWEEN_CALLS:
        time.sleep(_MIN_SECONDS_BETWEEN_CALLS - elapsed)
    _last_call_time = time.time()


def _lang_instruction(lang: str) -> str:
    name = _LANG_NAMES.get(lang, "English")
    return f"Respond in {name}."


def _clean_json_response(raw_text: str) -> dict:
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text.strip())


def _normalize_decision(result: dict) -> dict:
    valid = {"include": "Include", "exclude": "Exclude", "maybe": "Maybe"}
    raw = str(result.get("decision", "")).strip().lower()
    result["decision"] = valid.get(raw, "Maybe")
    return result


# ═════════════════════════════════════════════════════════════
# SESSION TITLE
# ═════════════════════════════════════════════════════════════

def _generate_session_title(text: str, lang: str = "en") -> str:
    if not text or not text.strip():
        return "New Quiz"
    if _api_key:
        try:
            model = genai.GenerativeModel(_MODEL_NAME)
            lang_note = (
                "Generate the title in Bengali (বাংলা)."
                if lang == "bn"
                else "Generate the title in English."
            )
            prompt = f"""Generate a SHORT title (3-6 words, max 40 characters) for this quiz based on the content below.

Do NOT include quotes, punctuation at the end, or the words "Quiz about".

CONTENT (first 1000 chars):
{text[:1000]}

{lang_note}

Respond with ONLY the title text, nothing else."""
            response = model.generate_content(prompt)
            title = response.text.strip().strip('"').strip("'")
            title = re.sub(r"[^\w\s\-\u0980-\u09FF]", "", title)[:50].strip()
            if title and len(title) >= 3:
                return title
        except Exception as e:
            print(f"[title] AI failed: {e}")
    words = text.strip().split()[:6]
    title = " ".join(words)[:50]
    return title if title else "New Quiz"


# ═════════════════════════════════════════════════════════════
# SANITIZE
# ═════════════════════════════════════════════════════════════

_DEBUG_PATTERNS = [
    r"⚠️\s*\(Note:[^)]*\)",
    r"\(Note:[^)]*\)",
    r"\(Debug:[^)]*\)",
    r"\(QA:[^)]*\)",
    r"\(Internal:[^)]*\)",
    r"\(Auto-generated[^)]*\)",
    r"\[DEBUG[^\]]*\]",
    r"\[QA[^\]]*\]",
]


def sanitize_ai_text(text: str) -> str:
    if not text or not isinstance(text, str):
        return text or ""
    cleaned = text
    for pattern in _DEBUG_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    if not cleaned:
        return "Not specified in the paper."
    return cleaned


# ═════════════════════════════════════════════════════════════
# MERGED SCREEN + EXTRACT
# ═════════════════════════════════════════════════════════════

_FALLBACK_EXTRACT = {
    "abstract": "Not specified in the paper.",
    "keywords": "Not specified in the paper.",
    "methodology": "Not specified in the paper.",
    "findings": "Not specified in the paper.",
    "limitations": "Not mentioned in the paper.",
}


def merged_screen_and_extract(paper: dict, criteria: str, lang: str = "en") -> dict:
    fallback_decision = {
        "decision": "Maybe",
        "reason": "AI call failed — needs manual verification.",
        "confidence": 0,
        **_FALLBACK_EXTRACT,
    }
    if not _api_key:
        return {**fallback_decision, "reason": "GEMINI_API_KEY is not set"}

    title = paper.get("title", "") or "Unknown"
    year = paper.get("year", "") or "Unknown"
    venue = paper.get("venue", "") or "Unknown"
    authors = paper.get("authors", "") or "Unknown"
    doi = paper.get("doi", "") or "N/A"

    full_text = paper.get("full_text") or paper.get("abstract", "") or ""
    full_text = full_text[:8000]

    model = genai.GenerativeModel(_MODEL_NAME)

    prompt = f"""You are analyzing a research paper for a Systematic Literature Review.

═══════════════════════════════════════════════════════════
CRITERIA (must be strictly enforced):
{criteria}
═══════════════════════════════════════════════════════════

VERIFIED METADATA (from API — use as GROUND TRUTH):
- Title: {title}
- Publication Year: {year}
- Venue: {venue}
- Authors: {authors}
- DOI: {doi}

PAPER TEXT:
{full_text}

═══════════════════════════════════════════════════════════
TASK 1 — SCREENING DECISION:

Rules:
1. Compare VERIFIED Publication Year against year threshold in CRITERIA.
2. If year satisfies criteria → proceed to other criteria.
3. If year fails → decision = "Exclude".
4. If year unknown AND criteria depends on year → "Maybe".

TASK 2 — DATA EXTRACTION:

- abstract: The paper's abstract (1 paragraph, no truncation)
- keywords: Comma-separated keywords or topics (3-8 items)
- methodology: How was the research conducted? 2-4 sentences.
  * If a methodology section is present, extract from there.
  * If only abstract/overview, INFER the methodology TYPE from
    title + venue + framing (e.g., "systematic literature review",
    "survey", "experimental study", "case study").
    Start such fields with "Inferred: ".
  * Only write "Not specified in the paper." if truly impossible.
  * Do NOT fabricate numbers.

- findings: Main results and conclusions (2-4 sentences).
  If the paper is a review/survey, summarize main themes.

- limitations: Limitations, challenges, or constraints of the study.
  IMPORTANT — try in this order:
  1. Look for an explicit "Limitations" section → extract from there.
  2. Look for phrases like "However", "but", "constraint", "challenge",
     "future work", "further research is needed", "remains unclear"
     → these often express limitations implicitly.
  3. If the paper is a review/survey, note common challenges mentioned.
  4. If the paper is a conceptual/theoretical work, note the lack of
     empirical validation as an implicit limitation.
  Start INFERRED limitations with "Inferred: ".
  Only write "Not mentioned in the paper." if you truly cannot find or
  infer anything after checking all of the above.
  Do NOT fabricate specific numbers or claims.

═══════════════════════════════════════════════════════════
OUTPUT RULES:
- Respond with JSON ONLY. No markdown fences. No extra text.
- Do NOT include debug notes, ⚠️ warnings, or "(Note: ...)" text.
- Do NOT include LaTeX or markdown syntax.

{_lang_instruction(lang)}

Respond with this exact JSON structure:
{{
  "decision": "Include",
  "reason": "Year 2023 satisfies criteria '2020+'.",
  "confidence": 92,
  "abstract": "...",
  "keywords": "keyword1, keyword2, keyword3",
  "methodology": "...",
  "findings": "...",
  "limitations": "..."
}}
"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            _throttle()
            response = model.generate_content(prompt)
            result = _clean_json_response(response.text)
            result = _normalize_decision(result)

            for key in ("reason", "abstract", "keywords",
                        "methodology", "findings", "limitations"):
                if key in result:
                    result[key] = sanitize_ai_text(result[key])

            for key in _FALLBACK_EXTRACT:
                if not result.get(key):
                    result[key] = _FALLBACK_EXTRACT[key]

            if not result.get("confidence"):
                result["confidence"] = 0

            result = _enforce_year_rule(result, year, criteria)
            return result

        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return fallback_decision
            time.sleep(2)
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                wait = 10 * (attempt + 1)
                print(f"   ⏳ Rate limit. Waiting {wait}s...")
                time.sleep(wait)
                continue
            print(f"   ❌ Error: {err[:200]}")
            if attempt == max_retries - 1:
                return fallback_decision
            time.sleep(3)

    return fallback_decision


def _enforce_year_rule(result: dict, year, criteria: str) -> dict:
    threshold = _extract_year_threshold(criteria)
    if not threshold:
        return result
    try:
        year_int = int(year)
    except (ValueError, TypeError):
        if result.get("decision") == "Include":
            result["decision"] = "Maybe"
            result["reason"] = (
                "Overridden: year could not be verified. "
                "Original reason: " + (result.get("reason", "")[:200])
            )
        return result
    if year_int < threshold and result.get("decision") == "Include":
        result["decision"] = "Exclude"
        result["reason"] = (
            f"Overridden: verified year {year_int} fails threshold "
            f"{threshold}+."
        )
        result["confidence"] = 100
    return result


def _extract_year_threshold(criteria: str):
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
    for pattern in patterns:
        m = re.search(pattern, criteria, re.IGNORECASE)
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


# ═════════════════════════════════════════════════════════════
# BATCH screen-and-extract
# ═════════════════════════════════════════════════════════════

def batch_screen_and_extract(papers: list, criteria: str, lang: str = "en") -> list:
    if not papers:
        return []
    if not _api_key:
        return [
            {"decision": "Maybe", "reason": "GEMINI_API_KEY not set",
             "confidence": 0, **_FALLBACK_EXTRACT}
            for _ in papers
        ]

    model = genai.GenerativeModel(_MODEL_NAME)

    papers_text = ""
    for i, p in enumerate(papers, 1):
        title = (p.get("title", "") or "Unknown")[:200]
        year = p.get("year", "") or "Unknown"
        venue = (p.get("venue", "") or "Unknown")[:100]
        authors = (p.get("authors", "") or "Unknown")[:200]
        text = (p.get("full_text") or p.get("abstract") or "")[:3500]

        papers_text += f"""
[PAPER {i}]
Title: {title}
Year: {year}
Venue: {venue}
Authors: {authors}
Text: {text}
"""

    prompt = f"""You are processing {len(papers)} papers for a Systematic Literature Review.

CRITERIA (strictly enforced):
{criteria}

PAPERS:
{papers_text}

For EACH paper:

1) SCREENING: Decide Include / Exclude / Maybe.
   - If Year fails year threshold in criteria → "Exclude"
   - If year unknown AND criteria depends on year → "Maybe"
   - Never "Include" if year cannot be verified

2) EXTRACTION:
   - abstract: summary of the paper's abstract
   - keywords: 3-8 comma-separated keywords
   - methodology: 2-4 sentences.
     * If methods section present → extract from there.
     * If only abstract/overview → INFER the methodology TYPE from
       title + venue + framing. Start inferred fields with "Inferred: ".
     * Do NOT fabricate specific numbers.
   - findings: 2-4 sentences summarizing results/themes.
   - limitations: Limitations, challenges, or constraints.
     IMPORTANT — try in this order:
     1. Explicit "Limitations" section.
     2. Phrases like "However", "but", "constraint", "challenge",
        "future work", "further research needed", "remains unclear".
     3. Common challenges in reviews/surveys.
     4. Lack of empirical validation for conceptual papers.
     Start inferred limitations with "Inferred: ".
     Only write "Not mentioned in the paper." if truly nothing found
     after checking all of the above.
     Do NOT fabricate specific numbers or claims.

RULES:
- Output JSON ONLY. No markdown fences. No extra text.
- Do NOT include debug notes or "(Note: ...)" text.
- Do NOT include LaTeX/markdown.

{_lang_instruction(lang)}

Respond with this exact JSON structure:
{{"papers": [
  {{"index": 1, "decision": "Include", "reason": "...", "confidence": 90,
    "abstract": "...", "keywords": "...", "methodology": "...",
    "findings": "...", "limitations": "..."}},
  {{"index": 2, "decision": "Exclude", "reason": "...", "confidence": 95,
    "abstract": "...", "keywords": "...", "methodology": "...",
    "findings": "...", "limitations": "..."}}
]}}
"""

    try:
        _throttle()
        response = model.generate_content(prompt)
        result = _clean_json_response(response.text)
        raw = result.get("papers", [])

        by_index = {}
        for item in raw:
            try:
                idx = int(item.get("index", 0))
                item = _normalize_decision(item)
                for key in ("reason", "abstract", "keywords",
                            "methodology", "findings", "limitations"):
                    if key in item:
                        item[key] = sanitize_ai_text(item[key])
                for key in _FALLBACK_EXTRACT:
                    if not item.get(key):
                        item[key] = _FALLBACK_EXTRACT[key]
                if not item.get("confidence"):
                    item["confidence"] = 0
                paper_year = None
                if 0 < idx <= len(papers):
                    paper_year = papers[idx - 1].get("year")
                item = _enforce_year_rule(item, paper_year, criteria)
                by_index[idx] = item
            except (ValueError, TypeError, IndexError):
                continue

        final = []
        for i in range(1, len(papers) + 1):
            if i in by_index:
                final.append(by_index[i])
            else:
                final.append({
                    "decision": "Maybe",
                    "reason": "Not classified by batch model",
                    "confidence": 0,
                    **_FALLBACK_EXTRACT,
                })
        return final

    except Exception as e:
        print(f"[batch_screen_and_extract] Error: {str(e)[:200]}")
        return [
            {"decision": "Error", "reason": str(e)[:100], "confidence": 0,
             **_FALLBACK_EXTRACT}
            for _ in papers
        ]


# ═════════════════════════════════════════════════════════════
# LEGACY functions
# ═════════════════════════════════════════════════════════════

def screen_paper(abstract: str, criteria: str, lang: str = "en",
                 paper_metadata: dict = None) -> dict:
    fake_paper = {
        "title": (paper_metadata or {}).get("title", ""),
        "year": (paper_metadata or {}).get("year", ""),
        "venue": (paper_metadata or {}).get("venue", ""),
        "authors": (paper_metadata or {}).get("authors", ""),
        "abstract": abstract,
    }
    result = merged_screen_and_extract(fake_paper, criteria, lang)
    return {
        "decision": result.get("decision", "Maybe"),
        "reason": result.get("reason", ""),
        "confidence": result.get("confidence", 0),
    }


def quality_check_decision(abstract, criteria, decision, lang="en",
                            paper_metadata=None):
    return decision


def chat_about_paper(context_text: str, question: str, lang: str = "en") -> dict:
    if not _api_key:
        return {"answer": "GEMINI_API_KEY is not set."}
    model = genai.GenerativeModel(_MODEL_NAME)
    prompt = f"""Answer a question about a research paper, based only on the text provided.

PAPER TEXT:
{context_text}

QUESTION:
{question}

Answer concisely based only on the paper text. If the answer isn't in the text, say so.
{_lang_instruction(lang)}
"""
    try:
        _throttle()
        response = model.generate_content(prompt)
        return {"answer": sanitize_ai_text(response.text.strip())}
    except Exception as e:
        return {"answer": f"Error: {e}"}


def generate_quiz(context_text: str, num_questions: int = 5, lang: str = "en") -> dict:
    if not _api_key:
        return {"questions": [], "error": "GEMINI_API_KEY is not set"}
    num_questions = max(1, min(50, num_questions))
    model = genai.GenerativeModel(_MODEL_NAME)

    prompt = f"""Create exactly {num_questions} multiple-choice quiz questions from this text.

REQUIREMENTS:
- Each question has exactly 4 options
- One correct answer per question
- Include explanation for correct answer

TEXT:
{context_text}

{_lang_instruction(lang)}

Respond with JSON ONLY:
{{"questions": [
  {{"question": "...", "options": ["A", "B", "C", "D"], "correct_index": 0, "explanation": "..."}}
]}}
"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            _throttle()
            response = model.generate_content(prompt)
            raw = response.text.strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            raw = re.sub(r"[\x00-\x1f\x7f]", " ", raw)
            raw = re.sub(r"\s+", " ", raw)
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                raw = match.group(0)
            result = json.loads(raw)
            if "questions" in result and isinstance(result["questions"], list):
                for q in result["questions"]:
                    if "correct_index" in q:
                        try:
                            q["correct_index"] = int(q["correct_index"])
                        except (ValueError, TypeError):
                            q["correct_index"] = 0
                    if not q.get("options") or len(q["options"]) != 4:
                        continue
                    if "explanation" in q:
                        q["explanation"] = sanitize_ai_text(q["explanation"])
                return result
            return {"questions": [], "error": "Invalid response format"}
        except json.JSONDecodeError as e:
            print(f"[quiz] JSON parse failed (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return {"questions": [], "error": "Failed to parse AI response"}
            time.sleep(2)
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                wait = 10 * (attempt + 1)
                print(f"[quiz] Rate limit. Waiting {wait}s...")
                time.sleep(wait)
                continue
            return {"questions": [], "error": str(err)}
    return {"questions": [], "error": "Max retries exceeded"}


def extract_papers_batch(papers: list, lang: str = "en") -> list:
    if not papers:
        return []
    results = []
    for p in papers:
        r = merged_screen_and_extract(p, "", lang)
        results.append({
            "methodology": r.get("methodology", "Not specified in the paper."),
            "sample_size": "Not specified in the paper.",
            "key_findings": r.get("findings", "Not specified in the paper."),
            "limitations": r.get("limitations", "Not mentioned in the paper."),
            "abstract": r.get("abstract", ""),
            "keywords": r.get("keywords", ""),
        })
    return results


def screen_papers_batch(papers: list, criteria: str, lang: str = "en") -> list:
    results = batch_screen_and_extract(papers, criteria, lang)
    return [
        {
            "decision": r.get("decision", "Maybe"),
            "reason": r.get("reason", ""),
            "confidence": r.get("confidence", 0),
        }
        for r in results
    ]