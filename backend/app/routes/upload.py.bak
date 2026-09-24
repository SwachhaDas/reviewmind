"""
PDF Upload & Text Paste Handler.

Simplified detection:
  - research_paper → point-wise sections (Abstract, Introduction, etc.)
  - everything else → full text only

Endpoints:
  POST /upload          — Upload a PDF
  POST /upload/paste    — Paste raw text
"""
import io
import os
import re
import json

import fitz  # PyMuPDF
import pdfplumber
import google.generativeai as genai
from pypdf import PdfReader
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

from app.services.gemini_client import _api_key, _MODEL_NAME

# ─────────────────────────────────────────────────────────────
# Tesseract OCR setup
# ─────────────────────────────────────────────────────────────
try:
    import pytesseract
    from pdf2image import convert_from_bytes

    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

    OCR_AVAILABLE = True
    print("[upload] OCR enabled")
except Exception as e:
    print(f"[upload] OCR not available: {e}")
    OCR_AVAILABLE = False


router = APIRouter()


# ═════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═════════════════════════════════════════════════════════════

class PasteRequest(BaseModel):
    text: str


# ═════════════════════════════════════════════════════════════
# TEXT CLEANING
# ═════════════════════════════════════════════════════════════

def clean_text(text: str) -> str:
    """Clean PDF extraction artifacts WITHOUT losing content."""
    if not text:
        return text
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_text_good(text: str) -> bool:
    if not text or len(text) < 100:
        return False
    words = re.findall(r"\b[a-zA-Z\u0980-\u09FF]{2,}\b", text)
    if not words:
        return False
    avg_len = sum(len(w) for w in words) / len(words)
    if avg_len > 12:
        return False
    long_words = [w for w in words if len(w) > 15]
    if len(long_words) / len(words) > 0.15:
        return False
    return True


def clean_title(raw_title: str) -> str:
    if not raw_title:
        return ""
    title = raw_title.strip()
    title = re.sub(r"\S+@\S+\.\S+", "", title)
    for sym in ["∗", "*", "†", "‡", "§", "¶"]:
        title = title.replace(sym, "")
    stop_patterns = [
        r"\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s+(Google|Microsoft|University|Institute|Research)",
        r"\s+(Google Brain|Google Research|Microsoft Research|OpenAI)",
        r"\s+(University of|Institute of|Department of)",
    ]
    for pat in stop_patterns:
        match = re.search(pat, title)
        if match:
            title = title[:match.start()].strip()
            break
    title = title.rstrip(".,;:").strip()
    title = re.sub(r"\s+", " ", title)
    return title[:200]


# ═════════════════════════════════════════════════════════════
# EXTRACTION ENGINES
# ═════════════════════════════════════════════════════════════

def extract_with_pymupdf(contents: bytes) -> str:
    try:
        doc = fitz.open(stream=contents, filetype="pdf")
        parts = [page.get_text("text") for page in doc if page.get_text("text")]
        doc.close()
        return "\n".join(parts)
    except Exception as e:
        print(f"[extract] pymupdf failed: {e}")
        return ""


def extract_with_pypdf(contents: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(contents))
        parts = [(page.extract_text() or "") for page in reader.pages]
        return "\n".join(p for p in parts if p)
    except Exception as e:
        print(f"[extract] pypdf failed: {e}")
        return ""


def extract_with_pdfplumber(contents: bytes, layout: bool = False) -> str:
    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            parts = []
            for page in pdf.pages:
                text = page.extract_text(layout=layout) if layout else page.extract_text()
                if text:
                    parts.append(text)
            return "\n".join(parts)
    except Exception as e:
        print(f"[extract] pdfplumber failed: {e}")
        return ""


def extract_with_ocr(contents: bytes) -> str:
    if not OCR_AVAILABLE:
        return ""
    try:
        print("[extract] OCR on all pages...")
        images = convert_from_bytes(contents, dpi=150)
        parts = []
        total = len(images)
        for i, img in enumerate(images, start=1):
            try:
                parts.append(pytesseract.image_to_string(img, lang="eng"))
                if i % 5 == 0 or i == total:
                    print(f"[extract] OCR page {i}/{total}")
            except Exception as e:
                print(f"[extract] OCR page {i} failed: {e}")
        return "\n".join(parts)
    except Exception as e:
        print(f"[extract] OCR failed: {e}")
        return ""


# ═════════════════════════════════════════════════════════════
# CONTENT TYPE — SIMPLIFIED (research paper vs not)
# ═════════════════════════════════════════════════════════════

def detect_content_type(text: str) -> str:
    """
    Simplified detection:
      - 'research_paper' if paper-like keywords present
      - 'other' otherwise
    """
    if not text or len(text.strip()) < 100:
        return "other"

    # Sample first 8000 chars for detection
    sample = text[:8000].lower()

    # Research paper keywords — strong indicators
    paper_keywords = [
        "abstract",
        "introduction",
        "methodology",
        "method",
        "results",
        "findings",
        "discussion",
        "conclusion",
        "references",
        "et al",
        "doi",
        "this paper",
        "this study",
        "we propose",
        "we present",
        "our approach",
        "our method",
    ]

    count = sum(1 for kw in paper_keywords if kw in sample)

    # 2 or more paper keywords → research paper
    if count >= 2:
        print(f"[content-type] research_paper (keywords found: {count})")
        return "research_paper"

    print(f"[content-type] other (keywords found: {count})")
    return "other"


# ═════════════════════════════════════════════════════════════
# REGEX-BASED SECTION DETECTION
# ═════════════════════════════════════════════════════════════

SECTION_PATTERNS = {
    "abstract": [r"^\s*abstract\s*$", r"^\s*abstract[:\.]\s*"],
    "introduction": [
        r"^\s*1\.?\s*introduction\s*$",
        r"^\s*introduction\s*$",
        r"^\s*background\s*$",
    ],
    "methodology": [
        r"^\s*\d*\.?\s*method(?:s|ology)?\s*$",
        r"^\s*\d*\.?\s*materials?\s+and\s+methods?\s*$",
        r"^\s*\d*\.?\s*approach\s*$",
    ],
    "findings": [
        r"^\s*\d*\.?\s*results?\s*$",
        r"^\s*\d*\.?\s*findings?\s*$",
        r"^\s*\d*\.?\s*evaluation\s*$",
    ],
    "conclusion": [
        r"^\s*\d*\.?\s*conclusions?\s*$",
        r"^\s*\d*\.?\s*discussion\s*$",
    ],
}


def detect_sections_regex(text: str) -> dict:
    lines = text.split("\n")
    sections = {"title": "", "full_text": text}
    for key in ["abstract", "introduction", "methodology",
                "findings", "limitations", "conclusion"]:
        sections[key] = ""

    positions = {}
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or len(s) > 80:
            continue
        for name, patterns in SECTION_PATTERNS.items():
            if name in positions:
                continue
            for pat in patterns:
                if re.match(pat, s, re.IGNORECASE):
                    positions[name] = i
                    break

    title_end = min(positions.values()) if positions else min(50, len(lines))
    for ln in lines[:title_end]:
        s = ln.strip()
        if 15 < len(s) < 200 and "@" not in s and not s.startswith("http"):
            sections["title"] = s
            break

    ordered = sorted(positions.items(), key=lambda x: x[1])
    for idx, (name, start) in enumerate(ordered):
        end = ordered[idx + 1][1] if idx + 1 < len(ordered) else len(lines)
        content = "\n".join(lines[start + 1:end]).strip()
        if content:
            sections[name] = content

    return sections


# ═════════════════════════════════════════════════════════════
# AI-BASED SECTION DETECTION
# ═════════════════════════════════════════════════════════════

def detect_sections_ai(text: str) -> dict:
    if not _api_key:
        return {}
    raw = ""
    try:
        model = genai.GenerativeModel(_MODEL_NAME)
        sample = text[:20000]

        prompt = f"""You are analyzing a research paper to extract its sections.

Map section names to the closest standard category:

1. **title** — The paper's main title only
2. **abstract** — Summary paragraph
3. **introduction** — Background, motivation
4. **methodology** — Methods, approach, model architecture
5. **findings** — Results, evaluation, experiments
6. **limitations** — Challenges, constraints
7. **conclusion** — Conclusion, summary, discussion

For EACH section, provide the EXACT first 15 words as an anchor.
For sections that DON'T exist, return empty string "".

IMPORTANT: Respond with valid JSON only.

Respond with JSON ONLY:
{{
  "title": "first 15 words of title only",
  "abstract": "first 15 words of abstract",
  "introduction": "first 15 words of introduction",
  "methodology": "first 15 words of methodology",
  "findings": "first 15 words of findings",
  "limitations": "first 15 words of limitations",
  "conclusion": "first 15 words of conclusion"
}}

PAPER SAMPLE:
{sample}
"""

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
        return result

    except json.JSONDecodeError as e:
        print(f"[ai-detect] JSON parse failed: {e}")
        try:
            salvaged = {}
            for key in ["title", "abstract", "introduction", "methodology",
                        "findings", "limitations", "conclusion"]:
                m = re.search(rf'"{key}"\s*:\s*"([^"]*)"', raw)
                if m:
                    salvaged[key] = m.group(1)
            return salvaged
        except Exception:
            pass
        return {}
    except Exception as e:
        print(f"[ai-detect] Failed: {e}")
        return {}


def extract_section_from_anchor(full_text: str, anchor: str,
                                 max_length: int = 25000) -> str:
    if not anchor or len(anchor.strip()) < 10:
        return ""
    anchor_clean = re.sub(r"\s+", " ", anchor.strip())
    full_clean = re.sub(r"\s+", " ", full_text)

    pos = full_clean.lower().find(anchor_clean.lower())
    if pos < 0:
        pos = full_clean.lower().find(" ".join(anchor_clean.split()[:10]).lower())
    if pos < 0:
        pos = full_clean.lower().find(" ".join(anchor_clean.split()[:6]).lower())
    if pos < 0:
        pos = full_clean.lower().find(" ".join(anchor_clean.split()[:4]).lower())

    if pos < 0:
        return ""
    return full_clean[pos:pos + max_length]


# ═════════════════════════════════════════════════════════════
# AI TITLE GENERATION
# ═════════════════════════════════════════════════════════════

def generate_content_title(text: str, lang: str = "en") -> str:
    if not text or not text.strip():
        return "Untitled Text"

    if _api_key:
        try:
            model = genai.GenerativeModel(_MODEL_NAME)
            lang_note = (
                "Generate the title in Bengali (বাংলা)."
                if lang == "bn"
                else "Generate the title in English."
            )
            prompt = f"""Generate a SHORT title (3-6 words, max 40 characters) for the content below.

The title should be descriptive. Do NOT include quotes.

Examples:
- React useEffect Guide
- Machine Learning Basics
- Transformer Architecture

CONTENT (first 1500 chars):
{text[:1500]}

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
    return title if title else "Untitled Text"


# ═════════════════════════════════════════════════════════════
# SECTION EXTRACTION — Research Paper only
# ═════════════════════════════════════════════════════════════

def detect_all_sections(text: str, content_type: str = "other") -> dict:
    """
    If research_paper: extract 6 academic sections.
    Otherwise: return full_text only.
    """
    final = {
        "full_text": text,
        "content_type": content_type,
        "title": "",
        "abstract": "",
        "introduction": "",
        "methodology": "",
        "findings": "",
        "limitations": "",
        "conclusion": "",
        "key_points": [],
    }

    # ─── Not a research paper: just full text ───
    if content_type != "research_paper":
        print(f"[sections] Content '{content_type}' — full text only")
        final["title"] = generate_content_title(text)
        final["abstract"] = text[:1500]  # short preview only
        return final

    # ─── Research paper: extract point-wise sections ───
    print("[sections] Research paper — extracting sections")

    regex_sections = detect_sections_regex(text)
    ai_anchors = detect_sections_ai(text)

    for section in ["title", "abstract", "introduction",
                    "methodology", "findings", "limitations", "conclusion"]:
        if ai_anchors.get(section):
            if section == "title":
                final["title"] = clean_title(ai_anchors[section])
            else:
                extracted = extract_section_from_anchor(text, ai_anchors[section])
                if extracted and len(extracted) > 100:
                    final[section] = extracted

        if not final[section] and regex_sections.get(section):
            if section == "title":
                final["title"] = clean_title(regex_sections[section])
            else:
                final[section] = regex_sections[section]

    # Fallbacks
    if not final["conclusion"]:
        for keyword in ["conclusion", "conclusions", "discussion", "summary"]:
            match = re.search(rf"\b{keyword}\b", text, re.IGNORECASE)
            if match:
                final["conclusion"] = text[match.start():match.start() + 15000]
                break

    if not final["limitations"]:
        for keyword in ["limitation", "limitations", "constraint"]:
            match = re.search(rf"\b{keyword}\b", text, re.IGNORECASE)
            if match:
                final["limitations"] = text[match.start():match.start() + 5000]
                break

    if not final["title"]:
        final["title"] = generate_content_title(text)

    if not final["abstract"]:
        final["abstract"] = text[:1500]

    return final


# ═════════════════════════════════════════════════════════════
# ENDPOINTS
# ═════════════════════════════════════════════════════════════

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload PDF and extract content."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return {"status": "error", "message": "Only PDF files are supported"}

    try:
        contents = await file.read()
        print(f"\n[upload] === Received: {file.filename} "
              f"({len(contents) / 1024:.1f} KB) ===")

        candidates = []
        for name, extractor in [
            ("pymupdf", extract_with_pymupdf),
            ("pypdf", extract_with_pypdf),
            ("pdfplumber-layout", lambda c: extract_with_pdfplumber(c, True)),
            ("pdfplumber", lambda c: extract_with_pdfplumber(c, False)),
        ]:
            text = extractor(contents)
            if text:
                candidates.append((name, text))

        best_name, best_text, best_score = "", "", -1
        for name, txt in candidates:
            words = re.findall(r"\b[a-zA-Z\u0980-\u09FF]{2,}\b", txt)
            if not words:
                continue
            short = len([w for w in words if 2 <= len(w) <= 12])
            long = len([w for w in words if len(w) > 15])
            score = short - long * 3
            if score > best_score:
                best_score = score
                best_name = name
                best_text = txt

        if not is_text_good(best_text) and OCR_AVAILABLE:
            ocr_text = extract_with_ocr(contents)
            if is_text_good(ocr_text):
                best_name, best_text = "ocr", ocr_text

        if not best_text:
            return {"status": "error", "message": "No text could be extracted."}

        cleaned = clean_text(best_text)
        print(f"[upload] Final: {len(cleaned)} chars, using '{best_name}'")

        content_type = detect_content_type(cleaned)
        print(f"[upload] Content type: {content_type}")

        sections = detect_all_sections(cleaned, content_type)

        return {
            "status": "success",
            "method": best_name,
            "filename": file.filename,
            "content_type": content_type,
            "title": sections["title"] or "Untitled",
            "abstract": sections["abstract"],
            "introduction": sections["introduction"],
            "methodology": sections["methodology"],
            "findings": sections["findings"],
            "limitations": sections["limitations"],
            "conclusion": sections["conclusion"],
            "key_points": sections.get("key_points", []),
            "full_text": sections["full_text"],
            "char_count": len(cleaned),
            "word_count": len(cleaned.split()),
        }

    except Exception as e:
        print(f"[upload] Error: {e}")
        return {"status": "error", "message": f"Error: {str(e)}"}


@router.post("/upload/paste")
async def paste_text(req: PasteRequest):
    """Process pasted text."""
    text = (req.text or "").strip()
    if not text:
        return {"status": "error", "message": "Empty text"}

    print(f"\n[paste] === Received {len(text)} chars ===")

    cleaned = clean_text(text)
    content_type = detect_content_type(cleaned)
    print(f"[paste] Content type: {content_type}")

    sections = detect_all_sections(cleaned, content_type)

    if not sections.get("title") or len(sections["title"]) < 5:
        sections["title"] = generate_content_title(cleaned)

    return {
        "status": "success",
        "content_type": content_type,
        "title": sections.get("title", "Untitled Text"),
        "abstract": sections.get("abstract", cleaned[:1500]),
        "introduction": sections.get("introduction", ""),
        "methodology": sections.get("methodology", ""),
        "findings": sections.get("findings", ""),
        "limitations": sections.get("limitations", ""),
        "conclusion": sections.get("conclusion", ""),
        "key_points": sections.get("key_points", []),
        "full_text": cleaned,
        "char_count": len(cleaned),
        "word_count": len(cleaned.split()),
    }