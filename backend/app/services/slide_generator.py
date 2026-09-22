"""
Slide Generator — Uses Gemini to convert raw content into structured slide data.

Follows the same pattern as gemini_client.py (genai.GenerativeModel + _throttle).
Falls back to simple heuristics if Gemini fails.
"""
import json
import re
import time
import os

import google.generativeai as genai
from dotenv import load_dotenv

from app.services.gemini_client import _throttle, _clean_json_response, _MODEL_NAME


load_dotenv()

_api_key = os.getenv("GEMINI_API_KEY")


SLIDE_SYSTEM_PROMPT = """You are an expert presentation designer.

Given raw content (a research report, notes, article, or any text), create a
professional slide deck structure.

Return ONLY valid JSON in this exact format:
{
  "title": "Presentation title (max 10 words)",
  "subtitle": "Short subtitle or author line (optional, can be empty)",
  "slides": [
    {
      "title": "Slide title (max 8 words)",
      "bullets": [
        "Concise bullet 1 (max 25 words)",
        "Concise bullet 2",
        "Concise bullet 3"
      ]
    }
  ]
}

Rules:
- Create 8 to 15 slides depending on content depth.
- Each slide should have 3 to 6 bullets.
- First slide: introduction/overview.
- Last slide: conclusion or key takeaways.
- Keep language simple and clear.
- No markdown, no code fences — pure JSON only.
- Match the language of the source content (if source is Bengali, output Bengali; if English, output English).
"""


def _fallback_slides(content, title_hint=None):
    """Simple fallback if Gemini fails — split content into slides by paragraphs."""
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    slides = []
    chunk_size = 5
    for i in range(0, len(lines), chunk_size):
        chunk = lines[i:i + chunk_size]
        slides.append({
            'title': f'Section {len(slides) + 1}',
            'bullets': chunk[:6]
        })

    if not slides:
        slides = [{'title': 'Content', 'bullets': ['No content provided.']}]

    return {
        'title': title_hint or 'Presentation',
        'subtitle': '',
        'slides': slides[:15],
    }


def generate_slide_data(content, title_hint=None, lang='en'):
    """
    Convert raw content into structured slide data using Gemini.

    Args:
        content (str): Raw text provided by the user.
        title_hint (str): Optional title override.
        lang (str): Language hint for output ('en' or 'bn').

    Returns:
        dict: {'title': str, 'subtitle': str, 'slides': [ {...}, ... ]}
    """
    if not content or not content.strip():
        return _fallback_slides('No content provided.', title_hint)

    # If no API key, skip Gemini and use fallback
    if not _api_key:
        print('[slide_generator] GEMINI_API_KEY not set — using fallback')
        return _fallback_slides(content, title_hint)

    # Keep a generous prompt cap to avoid token overflow.
    # Full content is still preserved in the saved JSON for traceability.
    MAX_PROMPT_CHARS = 30000
    prompt_content = content[:MAX_PROMPT_CHARS]

    lang_note = (
        "Respond in Bengali (বাংলা)."
        if lang == 'bn'
        else "Respond in English."
    )

    title_line = f"Preferred title: {title_hint}\n" if title_hint else ""

    full_prompt = f"""{SLIDE_SYSTEM_PROMPT}

{lang_note}
{title_line}
--- RAW CONTENT START ---
{prompt_content}
--- RAW CONTENT END ---

Generate the slide deck JSON now."""

    try:
        model = genai.GenerativeModel(_MODEL_NAME)
        _throttle()
        response = model.generate_content(full_prompt)
        data = _clean_json_response(response.text)

        if data and isinstance(data, dict) and data.get('slides'):
            data.setdefault('title', title_hint or 'Presentation')
            data.setdefault('subtitle', '')
            return data

    except json.JSONDecodeError as e:
        print(f'[slide_generator] JSON parse failed: {e}')
    except Exception as e:
        print(f'[slide_generator] Gemini error: {e}')

    return _fallback_slides(content, title_hint)