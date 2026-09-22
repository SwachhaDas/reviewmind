"""
Data Extraction Agent — extracts structured fields from each included paper.

Uses full paper text (when available) instead of just the abstract.
Expanded prompt for detailed methodology and findings.

Fields extracted (7 total):
  1. methodology          — research design, methods, tools
  2. sample_size          — number of participants/datasets/cases
  3. key_findings         — main results and conclusions
  4. limitations          — acknowledged limitations
  5. research_questions   — questions or objectives addressed
  6. dataset              — dataset or corpus used
  7. evaluation_metrics   — metrics or measures used

Includes:
  - Retry logic with exponential backoff (survives 429 quota errors)
  - Throttle integration (respects Gemini free-tier rate limits)
  - Graceful fallbacks so the report never breaks
  - Text cleanup (removes LaTeX/markdown artifacts)
  - Title hint so the AI focuses on the correct paper
"""
import json
import re
import time

import google.generativeai as genai

from app.services.gemini_client import (
    _MODEL_NAME,
    _api_key,
    _clean_json_response,
    _lang_instruction,
    _throttle,
)


# Fallback values returned when extraction is impossible
_FALLBACK = {
    "methodology": "Not specified in the paper",
    "sample_size": "Not specified in the paper",
    "key_findings": "Not specified in the paper",
    "limitations": "Not specified in the paper",
    "research_questions": "Not specified in the paper",
    "dataset": "Not specified in the paper",
    "evaluation_metrics": "Not specified in the paper",
}


def _clean_extracted_text(text):
    """
    Clean LaTeX and markdown artifacts from a single extracted field.
    Handles: \\( \\) \\[ \\] \\% \\_ \\# \\& and markdown ##, **, etc.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)

    # Remove LaTeX math delimiters
    text = text.replace("\\(", "(").replace("\\)", ")")
    text = text.replace("\\[", "[").replace("\\]", "]")

    # Remove LaTeX escape backslashes before common symbols
    text = re.sub(r"\\([%_#&$])", r"\1", text)

    # Remove markdown headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Remove markdown bold/italic
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^\*\n]+?)\*(?!\*)", r"\1", text)

    # Remove code fences
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Remove markdown links [text](url) → keep text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    return text


def extract_paper_data(
    full_text: str,
    lang: str = "en",
    original_title: str = "",
) -> dict:
    """
    Extraction Agent — pulls structured data out of a paper using Gemini.

    Uses FULL paper text when available (up to 50,000 characters) for
    much more detailed methodology, findings, and metadata extraction.

    Args:
        full_text: The paper's full text or abstract.
        lang: Language code for output fields ('en' or 'bn').
        original_title: The paper's original title (used as a hint so the AI
                        focuses on the correct paper).

    Returns:
        dict with 7 fields: methodology, sample_size, key_findings,
        limitations, research_questions, dataset, evaluation_metrics.
    """
    # Guard: API key missing
    if not _api_key:
        return {
            **{k: "Error" for k in _FALLBACK},
            "key_findings": "GEMINI_API_KEY is not set",
        }

    # Guard: no text to extract from
    if not full_text or not full_text.strip():
        return {k: "No text available" for k in _FALLBACK}

    model = genai.GenerativeModel(_MODEL_NAME)

    # Include title as a hint so AI focuses on the correct paper
    title_hint = ""
    if original_title:
        title_hint = (
            f"PAPER TITLE (extract from THIS paper only):\n"
            f"{original_title}\n\n"
        )

    # ─── Send up to 50,000 chars instead of 4,000 ───
    # This gives Gemini access to the full methodology section
    MAX_TEXT_CHARS = 50000
    text_excerpt = full_text[:MAX_TEXT_CHARS]

    prompt = f"""{title_hint}You are extracting structured data from a research
paper for a systematic literature review.

Extract the following fields with DETAIL. Each field must be a complete,
self-contained explanation. Minimum 2-3 sentences per field. No length limit.

FIELDS TO EXTRACT:

1. **methodology** — How was the research conducted? Include:
   - Research design (experimental, survey, case study, review, etc.)
   - Data collection methods
   - Analysis techniques
   - Tools, frameworks, or algorithms used
   Write at least 3-4 detailed sentences. If the text describes multiple
   methods, list them all. Extract from the methodology / methods section.

2. **sample_size** — How many participants, samples, datasets, or cases
   were studied? Give the exact number if mentioned.

3. **key_findings** — What were the main results and conclusions?
   List 2-4 key findings in detail with any reported numbers.

4. **limitations** — What limitations did the authors acknowledge?
   If not mentioned, write "The authors did not explicitly mention limitations."

5. **research_questions** — What research questions or objectives did the
   paper address? Extract from the introduction if stated.

6. **dataset** — What dataset, corpus, or data source was used? Include
   the name and size if available.

7. **evaluation_metrics** — What evaluation metrics or measures were used?
   (Examples: accuracy, F1, precision, recall, RMSE, AUC, etc.)

PAPER TEXT:
{text_excerpt}

{_lang_instruction(lang)}

IMPORTANT:
- Extract ONLY from the paper text above.
- Do NOT include LaTeX symbols or markdown formatting in output.
- Use plain text only.
- If a field is genuinely not mentioned, write "Not specified in the paper".
- Prioritize DETAIL over brevity for methodology and key_findings.

Respond with JSON ONLY, no markdown fences, no extra text:
{{"methodology": "...", "sample_size": "...", "key_findings": "...", "limitations": "...", "research_questions": "...", "dataset": "...", "evaluation_metrics": "..."}}
"""

    # Retry loop — up to 5 attempts with exponential backoff for 429s
    max_retries = 5
    for attempt in range(max_retries):
        try:
            _throttle()
            response = model.generate_content(prompt)
            result = _clean_json_response(response.text)

            # Clean each field's text (remove LaTeX/markdown)
            for key in _FALLBACK:
                if key not in result or not result[key]:
                    result[key] = "Not specified in the paper"
                else:
                    result[key] = _clean_extracted_text(result[key])

            # Log if methodology is unusually short (possible extraction issue)
            method_len = len(result.get("methodology", ""))
            if method_len < 50:
                print(
                    f"   ⚠️ Short methodology ({method_len} chars) "
                    f"for: {original_title[:60]}"
                )

            return result

        except json.JSONDecodeError as e:
            print(f"   ⚠️ Extraction JSON parse error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return _FALLBACK
            time.sleep(3)

        except Exception as e:
            error_msg = str(e)

            # Rate limit (429 / quota) → wait and retry with backoff
            if "429" in error_msg or "quota" in error_msg.lower():
                wait = 15 * (attempt + 1)  # 15s, 30s, 45s, 60s, 75s
                print(
                    f"   ⏳ Extraction quota hit. Waiting {wait}s "
                    f"(try {attempt + 1}/{max_retries})"
                )
                time.sleep(wait)
                continue

            # Other errors → log and retry once more, else fallback
            print(f"   ❌ Extraction error: {error_msg[:150]}")
            if attempt == max_retries - 1:
                return {
                    **{k: "Error" for k in _FALLBACK},
                    "key_findings": error_msg[:200],
                }
            time.sleep(5)

    # All retries exhausted
    return _FALLBACK