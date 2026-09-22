"""
PDF parser — uses PyMuPDF (pymupdf) for fast text extraction.
Extracts Abstract + Introduction + Conclusion/Results sections only
to keep text small for AI processing.

Supports multiple extraction libraries with automatic fallback:
  1. PyMuPDF (fast, primary)
  2. pdfminer (fallback)
"""
import io
import re

# ─── Primary: PyMuPDF (fast) ───
try:
    import pymupdf  # PyMuPDF >= 1.24 modern import
    _HAVE_PYMUPDF = True
except ImportError:
    try:
        import fitz  # older PyMuPDF versions
        _HAVE_PYMUPDF = True
        pymupdf = fitz
    except ImportError:
        _HAVE_PYMUPDF = False

# ─── Fallback: pdfminer ───
try:
    from pdfminer.high_level import extract_text as _pdfminer_extract
    _HAVE_PDFMINER = True
except ImportError:
    _HAVE_PDFMINER = False


# Section headers we care about
_SECTION_PATTERNS = {
    "abstract": [
        r"^\s*abstract\b",
        r"^\s*summary\b",
    ],
    "introduction": [
        r"^\s*(?:\d+\.?\s*)?introduction\b",
        r"^\s*(?:\d+\.?\s*)?background\b",
    ],
    "conclusion": [
        r"^\s*(?:\d+\.?\s*)?conclusions?\b",
        r"^\s*(?:\d+\.?\s*)?results?\s+and\s+discussion\b",
        r"^\s*(?:\d+\.?\s*)?discussion\b",
        r"^\s*(?:\d+\.?\s*)?results?\b",
        r"^\s*(?:\d+\.?\s*)?findings\b",
    ],
}

# Section headers that mark END of a section
_END_PATTERNS = [
    r"^\s*(?:\d+\.?\s*)?(?:methods?|methodology)\b",
    r"^\s*(?:\d+\.?\s*)?related\s+work\b",
    r"^\s*(?:\d+\.?\s*)?references?\b",
    r"^\s*(?:\d+\.?\s*)?bibliography\b",
    r"^\s*(?:\d+\.?\s*)?acknowledg",
    r"^\s*(?:\d+\.?\s*)?appendix",
]


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF bytes.
    Tries PyMuPDF first (fast), falls back to pdfminer.
    """
    # ── Try PyMuPDF (fast) ──
    if _HAVE_PYMUPDF:
        try:
            with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
                parts = []
                for page in doc:
                    parts.append(page.get_text("text"))
                text = "\n".join(parts)
                if text and len(text.strip()) > 200:
                    return text
        except Exception as e:
            print(f"[pdf] PyMuPDF failed: {str(e)[:100]}")

    # ── Fallback to pdfminer ──
    if _HAVE_PDFMINER:
        try:
            text = _pdfminer_extract(io.BytesIO(file_bytes))
            return text or ""
        except Exception as e:
            print(f"[pdf] pdfminer failed: {str(e)[:100]}")

    return ""


def extract_relevant_sections(full_text: str) -> str:
    """
    Extract only Abstract + Introduction + Conclusion/Results from full text.
    Keeps text small for AI processing.

    If sections can't be found (unstructured PDF), returns first ~6000 chars.
    """
    if not full_text or not full_text.strip():
        return ""

    lines = full_text.split("\n")
    sections = {"abstract": [], "introduction": [], "conclusion": []}
    current = None
    lines_in_section = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                sections[current].append("")
            continue

        # Check if this line starts a target section
        matched_section = None
        for section, patterns in _SECTION_PATTERNS.items():
            for pat in patterns:
                if re.match(pat, stripped, re.IGNORECASE):
                    matched_section = section
                    break
            if matched_section:
                break

        if matched_section:
            current = matched_section
            lines_in_section = 0
            continue

        # Check if this line ENDS the current section
        if current:
            for pat in _END_PATTERNS:
                if re.match(pat, stripped, re.IGNORECASE):
                    current = None
                    break

        if current:
            sections[current].append(stripped)
            lines_in_section += 1
            if lines_in_section > 200:
                current = None

    # Build result
    parts = []
    if sections["abstract"]:
        parts.append("ABSTRACT:\n" + " ".join(sections["abstract"])[:2500])
    if sections["introduction"]:
        parts.append("INTRODUCTION:\n" + " ".join(sections["introduction"])[:2500])
    if sections["conclusion"]:
        parts.append("CONCLUSION:\n" + " ".join(sections["conclusion"])[:2000])

    combined = "\n\n".join(parts)

    # Fallback: unstructured PDF → use first 6000 chars
    if len(combined.strip()) < 300:
        return full_text[:6000]

    return combined


def extract_abstract(text: str) -> str:
    """Extract abstract only (legacy helper)."""
    if not text:
        return ""
    m = re.search(
        r"abstract\b[\s:]*\n?(.*?)(?:\n\s*(?:\d+\.?\s*)?(?:keywords?|introduction|1\.))",
        text, re.IGNORECASE | re.DOTALL,
    )
    if m:
        return m.group(1).strip()[:2000]
    return text[:1000]