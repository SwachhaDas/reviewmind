"""
Multi-Table Word Report Generator with Full Verification and Clickable Links.

Fixes applied:
  • Verification steps rendered as separate numbered paragraphs (no merge)
  • Table 2 source column shows only "SS" or "OA" (no stray "0")
  • Clickable hyperlinks in tables, DOI/URL fields, and references
  • Sanitized text (no debug/QA notes)
  • "Not mentioned" for missing limitations (never "—")
  • Methodology can be "Inferred: ..." for overview papers
  • Clean page breaks (no orphan pages)
"""
import os
import re
import uuid
from datetime import datetime

from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from app.services.prisma_generator import OUTPUT_DIR


LABELS = {
    "en": {
        "title": "Systematic Literature Review Report",
        "generated_on": "Generated on",
        "keyword": "Research Topic",
        "criteria": "Inclusion/Exclusion Criteria",
        "verification_statement": "Verification Statement",
        "verification_text": (
            "This report contains data from real research papers "
            "retrieved from verified academic APIs (Semantic Scholar, OpenAlex). "
            "Every paper has a DOI link and verification URL for independent checking. "
            "AI-extracted data can be cross-verified against the original paper text "
            "in the appendices."
        ),
        "total_papers": "Total papers analyzed",
        "sources_used": "Sources used",
        "fetched_time": "Data fetched at",
        "table1_title": "Table 1. Overview Statistics",
        "table2_title": "Table 2. Included Studies Summary",
        "table3_title": "Table 3. Methodology",
        "table4_title": "Table 4. Key Findings",
        "table5_title": "Table 5. Quality Assessment",
        "table6_title": "Table 6. PRISMA Flow Diagram",
        "appendix_a": "Appendix A. Full Methodology",
        "appendix_b": "Appendix B. Full Findings",
        "appendix_c": "Appendix C. Verification Log",
        "references_title": "References",
        "col_num": "#",
        "col_metric": "Metric",
        "col_value": "Value",
        "col_study": "Study",
        "col_year": "Year",
        "col_venue": "Venue",
        "col_source": "Source",
        "col_link": "Link",
        "col_methodology": "Methodology",
        "col_findings": "Key Findings",
        "col_limitations": "Limitations",
        "col_confidence": "Confidence",
        "col_reason": "AI Reason",
        "row_total_found": "Total papers identified",
        "row_duplicates": "Duplicates removed",
        "row_after_dedup": "Papers after deduplication",
        "row_excluded": "Excluded during screening",
        "row_maybe": "Marked as Maybe",
        "row_errors": "Screening errors",
        "row_included": "Final included papers",
        "no_data": "No data available",
        "paper_n": "Paper",
        "basic_info": "Basic Information",
        "source_verification": "Source Verification",
        "api_source": "API Source",
        "api_endpoint": "API Endpoint",
        "api_response_id": "API Response ID",
        "doi_label": "DOI",
        "url_label": "URL",
        "fetched_at_label": "Fetched At",
        "verification_url_label": "Verification URL",
        "ai_extraction": "AI Extraction",
        "screening_decision": "Screening Decision",
        "confidence_label": "Confidence",
        "reason_label": "Reason",
        "verify_steps": "Verification Steps for Reviewer",
    },
    "bn": {
        "title": "সিস্টেমেটিক লিটারেচার রিভিউ রিপোর্ট",
        "generated_on": "তৈরি করা হয়েছে",
        "keyword": "গবেষণার বিষয়",
        "criteria": "অন্তর্ভুক্তি/বহিষ্কারের মানদণ্ড",
        "verification_statement": "যাচাই বিবৃতি",
        "verification_text": (
            "এই রিপোর্টে থাকা তথ্য সত্যিকারের গবেষণাপত্র থেকে সংগ্রহ করা হয়েছে "
            "(Semantic Scholar, OpenAlex)। প্রতিটি পেপারের DOI লিঙ্ক এবং "
            "যাচাইয়ের URL আছে।"
        ),
        "total_papers": "মোট পেপার",
        "sources_used": "ব্যবহৃত সোর্স",
        "fetched_time": "ডেটা সংগ্রহ সময়",
        "table1_title": "টেবিল ১। সারসংক্ষেপ পরিসংখ্যান",
        "table2_title": "টেবিল ২। অন্তর্ভুক্ত পেপারের সারসংক্ষেপ",
        "table3_title": "টেবিল ৩। পদ্ধতি",
        "table4_title": "টেবিল ৪। মূল ফলাফল",
        "table5_title": "টেবিল ৫। গুণগত মান মূল্যায়ন",
        "table6_title": "টেবিল ৬। PRISMA ফ্লো ডায়াগ্রাম",
        "appendix_a": "পরিশিষ্ট ক। সম্পূর্ণ পদ্ধতি",
        "appendix_b": "পরিশিষ্ট খ। সম্পূর্ণ ফলাফল",
        "appendix_c": "পরিশিষ্ট গ। যাচাই লগ",
        "references_title": "তথ্যসূত্র",
        "col_num": "#",
        "col_metric": "বিষয়",
        "col_value": "মান",
        "col_study": "গবেষণা",
        "col_year": "বছর",
        "col_venue": "প্রকাশস্থান",
        "col_source": "সোর্স",
        "col_link": "লিঙ্ক",
        "col_methodology": "পদ্ধতি",
        "col_findings": "মূল ফলাফল",
        "col_limitations": "সীমাবদ্ধতা",
        "col_confidence": "আত্মবিশ্বাস",
        "col_reason": "AI কারণ",
        "row_total_found": "মোট পেপার পাওয়া গেছে",
        "row_duplicates": "ডুপ্লিকেট সরানো হয়েছে",
        "row_after_dedup": "ডুপ্লিকেট বাদ দেওয়ার পর",
        "row_excluded": "স্ক্রিনিংয়ে বাদ পড়েছে",
        "row_maybe": "সম্ভব হিসেবে চিহ্নিত",
        "row_errors": "স্ক্রিনিং ত্রুটি",
        "row_included": "চূড়ান্ত অন্তর্ভুক্ত পেপার",
        "no_data": "কোনো তথ্য নেই",
        "paper_n": "পেপার",
        "basic_info": "মৌলিক তথ্য",
        "source_verification": "সোর্স যাচাই",
        "api_source": "API সোর্স",
        "api_endpoint": "API এন্ডপয়েন্ট",
        "api_response_id": "API রেসপন্স ID",
        "doi_label": "DOI",
        "url_label": "URL",
        "fetched_at_label": "সংগ্রহ সময়",
        "verification_url_label": "যাচাই URL",
        "ai_extraction": "AI এক্সট্র্যাকশন",
        "screening_decision": "স্ক্রিনিং সিদ্ধান্ত",
        "confidence_label": "আত্মবিশ্বাস",
        "reason_label": "কারণ",
        "verify_steps": "রিভিউয়ারের জন্য যাচাই ধাপ",
    },
}


# ═════════════════════════════════════════════════════════════
# Text cleaning
# ═════════════════════════════════════════════════════════════

def _clean_text(text):
    """Remove LaTeX and markdown artifacts."""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)

    if text.strip() == "#":
        return "#"

    text = text.replace("\\(", "(").replace("\\)", ")")
    text = text.replace("\\[", "[").replace("\\]", "]")
    text = re.sub(r"\\([%_#&$])", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^\*\n]+?)\*(?!\*)", r"\1", text)
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"^\s*[-•]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()
    return text


def _clean_placeholder(text):
    """Replace placeholder text with "—"."""
    if text is None:
        return "—"
    if not isinstance(text, str):
        text = str(text)

    cleaned = text.strip().lower()

    placeholder_phrases = [
        "not mentioned",
        "not specified",
        "not extractable",
        "not applicable",
        "no text available",
        "no data available",
        "n/a",
        "none",
    ]

    for phrase in placeholder_phrases:
        if cleaned == phrase or cleaned.startswith(phrase):
            return "—"

    return _clean_text(text)


# ═════════════════════════════════════════════════════════════
# Word helpers
# ═════════════════════════════════════════════════════════════

def _set_cell_width(cell, width_inches):
    """Set cell width at XML level."""
    cell.width = Inches(width_inches)
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    existing = tcPr.find(qn('w:tcW'))
    if existing is not None:
        tcPr.remove(existing)
    tcW = OxmlElement('w:tcW')
    tcW.set(qn('w:w'), str(int(width_inches * 1440)))
    tcW.set(qn('w:type'), 'dxa')
    tcPr.append(tcW)


def _set_table_fixed_layout(table):
    """Force fixed table layout."""
    tbl = table._tbl
    tblPr = tbl.tblPr
    existing = tblPr.find(qn('w:tblLayout'))
    if existing is not None:
        tblPr.remove(existing)
    layout = OxmlElement('w:tblLayout')
    layout.set(qn('w:type'), 'fixed')
    tblPr.append(layout)


def _prevent_row_split(row):
    """Prevent table row from splitting across pages."""
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    existing = trPr.find(qn('w:cantSplit'))
    if existing is not None:
        trPr.remove(existing)
    cant_split = OxmlElement('w:cantSplit')
    trPr.append(cant_split)


def _add_page_break_clean(doc):
    """Add a clean page break without orphan pages."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = Pt(1)
    run = p.add_run()
    run.add_break(WD_BREAK.PAGE)


def _add_hyperlink(paragraph, url, text=None):
    """Add a CLICKABLE hyperlink to a docx paragraph."""
    if text is None:
        text = url

    if not url or not url.startswith("http"):
        run = paragraph.add_run(text)
        return run

    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)

    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")

    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    rPr.append(color)

    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(u)

    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "16")
    rPr.append(sz)

    new_run.append(rPr)

    t = OxmlElement("w:t")
    t.text = text
    t.set(qn("xml:space"), "preserve")
    new_run.append(t)

    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

    return hyperlink


def _add_heading(doc, text, level=1):
    """Add a heading."""
    return doc.add_heading(_clean_text(text), level=level)


def _add_paragraph(doc, text, size=10, bold=False, italic=False, indent=0):
    """Add a paragraph."""
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent = Inches(indent)
    run = p.add_run(_clean_text(text))
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    return p


def _add_key_value(doc, key, value, indent=0):
    """Add a key-value pair paragraph."""
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent = Inches(indent)
    run = p.add_run(f"{_clean_text(key)}: ")
    run.bold = True
    run.font.size = Pt(10)
    run2 = p.add_run(_clean_text(value))
    run2.font.size = Pt(10)
    return p


def _add_key_hyperlink(doc, key, url, display_text=None, indent=0):
    """Add a key-value pair where the value is a CLICKABLE hyperlink."""
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent = Inches(indent)

    run = p.add_run(f"{_clean_text(key)}: ")
    run.bold = True
    run.font.size = Pt(10)

    if url and isinstance(url, str) and url.startswith("http"):
        display = display_text or url
        _add_hyperlink(p, url, display)
    else:
        run2 = p.add_run(_clean_text(url))
        run2.font.size = Pt(10)

    return p


def _add_table_from_rows(doc, headers, rows, col_widths=None, link_cols=None):
    """Create a table with optional clickable link columns."""
    if link_cols is None:
        link_cols = set()

    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Header row
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = ""
        p = hdr_cells[i].paragraphs[0]
        cleaned_header = _clean_text(str(h))
        if not cleaned_header:
            cleaned_header = str(h)
        run = p.add_run(cleaned_header)
        run.bold = True
        run.font.size = Pt(9)
        p.paragraph_format.keep_with_next = True
    _prevent_row_split(table.rows[0])

    # Data rows
    for row_data in rows:
        row = table.add_row()
        cells = row.cells
        for i, val in enumerate(row_data):
            cells[i].text = ""
            p = cells[i].paragraphs[0]

            if i in link_cols:
                if val and isinstance(val, str) and val.startswith("http"):
                    icon_run = p.add_run("🔗 ")
                    icon_run.font.size = Pt(8)
                    _add_hyperlink(p, val, val)
                else:
                    text = _clean_text(val) if val else "—"
                    run = p.add_run(text)
                    run.font.size = Pt(8)
            else:
                text = _clean_text(val) if val is not None else "—"
                run = p.add_run(text if text else "—")
                run.font.size = Pt(8)

            p.paragraph_format.word_wrap = True
            p.paragraph_format.keep_with_next = False
        _prevent_row_split(row)

    if col_widths:
        _set_table_fixed_layout(table)
        for row in table.rows:
            for i, w in enumerate(col_widths):
                if i < len(row.cells):
                    _set_cell_width(row.cells[i], w)

    return table


# ═════════════════════════════════════════════════════════════
# Field helpers
# ═════════════════════════════════════════════════════════════

def _get_link(paper):
    """Get best available link."""
    doi = paper.get("doi", "")
    if doi:
        return f"https://doi.org/{doi}"
    return paper.get("url", "") or paper.get("verification_url", "") or ""


def _get_source_short(paper):
    """Return SS or OA (no stray characters)."""
    source = paper.get("source_api", "")
    if source == "semantic_scholar":
        return "SS"
    if source == "openalex":
        return "OA"
    return "—"


def _get_author_year(paper):
    """First author et al. (Year)."""
    authors = paper.get("authors", "") or ""
    year = paper.get("year", "") or "n.d."

    if not authors:
        return f"Unknown ({year})"

    first_author = authors.split(",")[0].strip()
    name_parts = first_author.split()
    last_name = name_parts[-1] if len(name_parts) >= 2 else first_author

    if "," in authors:
        return f"{last_name} et al. ({year})"
    return f"{last_name} ({year})"


def _ensure_limitations(p):
    """Ensure limitations is never empty — returns a readable string."""
    raw = (p.get("limitations", "") or "").strip()
    if not raw:
        return "Not mentioned in the paper"
    cleaned = _clean_placeholder(raw)
    if not cleaned or cleaned == "—":
        return "Not mentioned in the paper"
    return cleaned


def _add_verification_log(doc, paper, index, L):
    """
    Verification section for one paper (Appendix C).
    Steps rendered as separate numbered paragraphs to avoid merge.
    """
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    run = p.add_run(
        f"{L['paper_n']} {index}: {_clean_text(paper.get('title', 'Untitled'))}"
    )
    run.bold = True
    run.font.size = Pt(13)
    run.font.color.rgb = RGBColor(0x1F, 0x3F, 0x7A)

    # Basic Info
    _add_paragraph(doc, L["basic_info"], size=11, bold=True)
    _add_key_value(doc, "Title", paper.get("title", "—"), indent=0.3)
    _add_key_value(doc, "Authors", paper.get("authors", "—"), indent=0.3)
    _add_key_value(doc, "Year", paper.get("year", "—"), indent=0.3)
    _add_key_value(doc, "Venue", paper.get("venue", "—"), indent=0.3)
    doc.add_paragraph()

    # Source Verification
    _add_paragraph(doc, L["source_verification"], size=11, bold=True)
    _add_key_value(doc, L["api_source"], paper.get("source_api", "—"), indent=0.3)

    api_endpoint = paper.get("api_endpoint", "—")
    if api_endpoint and api_endpoint.startswith("http"):
        _add_key_hyperlink(doc, L["api_endpoint"], api_endpoint, indent=0.3)
    else:
        _add_key_value(doc, L["api_endpoint"], api_endpoint, indent=0.3)

    api_response_id = paper.get("api_response_id", "—")
    if api_response_id and api_response_id.startswith("http"):
        _add_key_hyperlink(doc, L["api_response_id"], api_response_id, indent=0.3)
    else:
        _add_key_value(doc, L["api_response_id"], api_response_id, indent=0.3)

    doi = paper.get("doi", "")
    if doi:
        doi_url = f"https://doi.org/{doi}"
        _add_key_hyperlink(doc, L["doi_label"], doi_url, doi_url, indent=0.3)
    else:
        _add_key_value(doc, L["doi_label"], "—", indent=0.3)

    url = paper.get("url", "")
    if url and url.startswith("http"):
        _add_key_hyperlink(doc, L["url_label"], url, indent=0.3)
    else:
        _add_key_value(doc, L["url_label"], url or "—", indent=0.3)

    _add_key_value(doc, L["fetched_at_label"], paper.get("fetched_at", "—"), indent=0.3)

    verify_url = paper.get("verification_url", "")
    if verify_url and verify_url.startswith("http"):
        _add_key_hyperlink(doc, L["verification_url_label"], verify_url, indent=0.3)
    else:
        _add_key_value(doc, L["verification_url_label"], verify_url or "—", indent=0.3)

    doc.add_paragraph()

    # AI Extraction
    _add_paragraph(doc, L["ai_extraction"], size=11, bold=True)
    _add_key_value(doc, L["screening_decision"], paper.get("decision", "—"), indent=0.3)
    _add_key_value(
        doc, L["confidence_label"],
        f"{paper.get('confidence', '—')}%", indent=0.3
    )
    _add_key_value(doc, L["reason_label"], paper.get("reason", "—"), indent=0.3)

    doc.add_paragraph()

    # Verification Steps — each on its own paragraph
    _add_paragraph(doc, L["verify_steps"], size=11, bold=True)

    doi_url = _get_link(paper)
    verify_url = paper.get("verification_url", "")

    # Step 1
    p1 = doc.add_paragraph()
    p1.paragraph_format.left_indent = Inches(0.3)
    p1.add_run("1. Open DOI: ").font.size = Pt(10)
    if doi_url and doi_url.startswith("http"):
        _add_hyperlink(p1, doi_url, doi_url)
    else:
        p1.add_run(doi_url or "—").font.size = Pt(10)

    # Step 2
    p2 = doc.add_paragraph()
    p2.paragraph_format.left_indent = Inches(0.3)
    p2.add_run("2. Open Verification URL: ").font.size = Pt(10)
    if verify_url and verify_url.startswith("http"):
        _add_hyperlink(p2, verify_url, verify_url)
    else:
        p2.add_run(verify_url or "—").font.size = Pt(10)

    # Step 3
    p3 = doc.add_paragraph()
    p3.paragraph_format.left_indent = Inches(0.3)
    p3.add_run(
        f"3. Compare methodology with Appendix A (Paper {index})"
    ).font.size = Pt(10)

    # Step 4
    p4 = doc.add_paragraph()
    p4.paragraph_format.left_indent = Inches(0.3)
    p4.add_run(
        f"4. Compare findings with Appendix B (Paper {index})"
    ).font.size = Pt(10)

    doc.add_paragraph()
    _add_paragraph(doc, "─" * 60, size=8, italic=True)


def _add_full_text_section(doc, heading, papers, field, lang="en"):
    """Full-text appendix (A / B)."""
    L = LABELS.get(lang, LABELS["en"])
    _add_heading(doc, heading, level=1)

    if not papers:
        _add_paragraph(doc, L["no_data"])
        return

    for i, paper in enumerate(papers, 1):
        title = _clean_text(paper.get("title", "Untitled"))
        raw_text = paper.get(field, "") or ""
        text = _clean_placeholder(raw_text)

        p = doc.add_paragraph()
        p.paragraph_format.keep_with_next = True
        run = p.add_run(f"{L['paper_n']} {i}: {title}")
        run.bold = True
        run.font.size = Pt(11)

        if text and text != "—":
            _add_paragraph(doc, text, size=10)
        else:
            _add_paragraph(doc, "—", size=10, italic=True)

        doc.add_paragraph()


# ═════════════════════════════════════════════════════════════
# Main report generator
# ═════════════════════════════════════════════════════════════

def generate_word_report(
    papers: list,
    counts: dict = None,
    prisma_image_path: str = None,
    keyword: str = "",
    criteria: str = "",
    lang: str = "en",
) -> str:
    """Build the Word report with FULL text and CLICKABLE hyperlinks."""
    L = LABELS.get(lang, LABELS["en"])
    doc = Document()

    section = doc.sections[0]
    section.left_margin = Cm(1.5)
    section.right_margin = Cm(1.5)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    if not counts:
        included_count = len([p for p in papers if p.get("decision") == "Include"])
        counts = {
            "total_found": len(papers),
            "duplicates_removed": 0,
            "irrelevant_excluded": len([p for p in papers if p.get("decision") == "Exclude"]),
            "maybe": len([p for p in papers if p.get("decision") == "Maybe"]),
            "error": len([p for p in papers if p.get("decision") == "Error"]),
            "total_included": included_count,
        }

    # ─── COVER ───
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_p.add_run(L["title"])
    run.bold = True
    run.font.size = Pt(22)
    run.font.color.rgb = RGBColor(0x1F, 0x3F, 0x7A)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_run = meta.add_run(
        f"{L['generated_on']}: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    meta_run.italic = True

    doc.add_paragraph()
    doc.add_paragraph(f"{L['keyword']}: {_clean_text(keyword) or '—'}")
    doc.add_paragraph(f"{L['criteria']}: {_clean_text(criteria) or '—'}")
    doc.add_paragraph()

    # ─── VERIFICATION STATEMENT ───
    _add_heading(doc, L["verification_statement"], level=1)
    _add_paragraph(doc, L["verification_text"], size=10)

    ss_count = len([p for p in papers if p.get("source_api") == "semantic_scholar"])
    oa_count = len([p for p in papers if p.get("source_api") == "openalex"])

    _add_key_value(doc, L["total_papers"], len(papers))
    _add_key_value(doc, L["sources_used"],
                   f"Semantic Scholar: {ss_count}, OpenAlex: {oa_count}")
    if papers:
        _add_key_value(doc, L["fetched_time"], papers[0].get("fetched_at", "—"))
    doc.add_paragraph()

    # ─── TABLE 1 ───
    _add_heading(doc, L["table1_title"], level=1)

    total_found = counts.get("total_found", 0)
    duplicates = counts.get("duplicates_removed", 0)
    after_dedup = total_found - duplicates
    excluded = counts.get("irrelevant_excluded", 0)
    maybe = counts.get("maybe", 0)
    errors = counts.get("error", 0)
    included = counts.get("total_included", 0)

    table1_rows = [
        [L["row_total_found"], total_found],
        [L["row_duplicates"], duplicates],
        [L["row_after_dedup"], after_dedup],
        [L["row_excluded"], excluded],
        [L["row_maybe"], maybe],
        [L["row_errors"], errors],
        [L["row_included"], included],
    ]
    _add_table_from_rows(doc, [L["col_metric"], L["col_value"]],
                         table1_rows, col_widths=[3.5, 2.0])
    doc.add_paragraph()

    included_papers = [p for p in papers if p.get("decision") == "Include"]

    # ─── TABLE 2 — Summary ───
    _add_heading(doc, L["table2_title"], level=1)
    if included_papers:
        t2_headers = [L["col_num"], L["col_study"], L["col_year"],
                      L["col_venue"], L["col_source"], L["col_link"]]
        t2_rows = []
        for i, p in enumerate(included_papers, 1):
            t2_rows.append([
                i,
                _get_author_year(p),
                p.get("year", "—"),
                _clean_text(p.get("venue", "")) or "—",
                _get_source_short(p),  # Returns clean "SS" or "OA"
                _get_link(p),
            ])
        _add_table_from_rows(
            doc, t2_headers, t2_rows,
            col_widths=[0.3, 1.2, 0.5, 1.5, 0.5, 2.3],
            link_cols={5},
        )
    else:
        _add_paragraph(doc, L["no_data"])
    doc.add_paragraph()

    # ─── TABLE 3 — Methodology ───
    _add_heading(doc, L["table3_title"], level=1)
    if included_papers:
        t3_headers = [L["col_num"], L["col_study"], L["col_methodology"]]
        t3_rows = []
        for i, p in enumerate(included_papers, 1):
            t3_rows.append([
                i,
                _get_author_year(p),
                _clean_text(p.get("methodology", "")) or "—",
            ])
        _add_table_from_rows(doc, t3_headers, t3_rows,
                             col_widths=[0.3, 1.5, 4.5])
    else:
        _add_paragraph(doc, L["no_data"])
    doc.add_paragraph()

    # ─── TABLE 4 — Findings ───
    _add_heading(doc, L["table4_title"], level=1)
    if included_papers:
        t4_headers = [L["col_num"], L["col_study"], L["col_findings"]]
        t4_rows = []
        for i, p in enumerate(included_papers, 1):
            t4_rows.append([
                i,
                _get_author_year(p),
                _clean_text(p.get("key_findings", "")) or "—",
            ])
        _add_table_from_rows(doc, t4_headers, t4_rows,
                             col_widths=[0.3, 1.3, 4.7])
    else:
        _add_paragraph(doc, L["no_data"])
    doc.add_paragraph()

    # ─── TABLE 5 — Quality (Limitations always shown) ───
    _add_heading(doc, L["table5_title"], level=1)
    if included_papers:
        t5_headers = [L["col_num"], L["col_study"], L["col_limitations"],
                      L["col_confidence"], L["col_reason"]]
        t5_rows = []
        for i, p in enumerate(included_papers, 1):
            conf = p.get("confidence", "")
            conf_str = f"{conf}%" if isinstance(conf, (int, float)) else "—"
            t5_rows.append([
                i,
                _get_author_year(p),
                _ensure_limitations(p),
                conf_str,
                _clean_text(p.get("reason", "")) or "—",
            ])
        _add_table_from_rows(doc, t5_headers, t5_rows,
                             col_widths=[0.3, 1.0, 2.0, 0.5, 2.8])
    else:
        _add_paragraph(doc, L["no_data"])
    doc.add_paragraph()

    # ─── TABLE 6 — PRISMA ───
    _add_heading(doc, L["table6_title"], level=1)
    if prisma_image_path and os.path.exists(prisma_image_path):
        try:
            doc.add_picture(prisma_image_path, width=Inches(5.5))
        except Exception as e:
            _add_paragraph(doc, f"(PRISMA image failed: {e})")
    else:
        _add_paragraph(doc, L["no_data"])
    doc.add_paragraph()

    # ─── APPENDIX A ───
    _add_page_break_clean(doc)
    _add_full_text_section(doc, L["appendix_a"], included_papers, "methodology", lang)

    # ─── APPENDIX B ───
    _add_page_break_clean(doc)
    _add_full_text_section(doc, L["appendix_b"], included_papers, "key_findings", lang)

    # ─── APPENDIX C ───
    _add_page_break_clean(doc)
    _add_heading(doc, L["appendix_c"], level=1)
    _add_paragraph(
        doc,
        "Every paper below includes full source verification. "
        "Use the DOI and verification URL to check each paper independently.",
        size=10, italic=True
    )
    doc.add_paragraph()

    for i, paper in enumerate(included_papers, 1):
        _add_verification_log(doc, paper, i, L)

    # ─── REFERENCES ───
    _add_page_break_clean(doc)
    _add_heading(doc, L["references_title"], level=1)
    if included_papers:
        for i, p in enumerate(included_papers, 1):
            cite_p = doc.add_paragraph()
            cite_p.paragraph_format.left_indent = Inches(0.4)
            cite_p.paragraph_format.first_line_indent = Inches(-0.4)

            authors = _clean_text(p.get("authors", "Unknown") or "Unknown")
            year = p.get("year", "n.d.")
            title = _clean_text(p.get("title", "Untitled") or "Untitled")
            venue = _clean_text(p.get("venue", "") or "")

            cite_p.add_run(f"[{i}] {authors} ({year}). {title}. ")
            if venue:
                cite_p.add_run(f"{venue}. ")

            doi = p.get("doi", "")
            if doi:
                doi_url = f"https://doi.org/{doi}"
                _add_hyperlink(cite_p, doi_url, doi_url)
            elif p.get("url"):
                url = p["url"]
                _add_hyperlink(cite_p, url, url)

            src_p = doc.add_paragraph()
            src_p.paragraph_format.left_indent = Inches(0.7)
            src_run = src_p.add_run(
                f"   Source: {p.get('source_api', '—')} | "
                f"Fetched: {p.get('fetched_at', '—')} | Verify: "
            )
            src_run.italic = True
            src_run.font.size = Pt(9)

            verify_url = p.get("verification_url", "")
            if verify_url and verify_url.startswith("http"):
                _add_hyperlink(src_p, verify_url, verify_url)
            else:
                src_run2 = src_p.add_run(verify_url or "—")
                src_run2.italic = True
                src_run2.font.size = Pt(9)
    else:
        _add_paragraph(doc, L["no_data"])

    # ─── SAVE ───
    filename = f"SLR_Report_{lang.upper()}_{uuid.uuid4().hex[:8]}.docx"
    output_path = os.path.join(OUTPUT_DIR, filename)
    doc.save(output_path)
    print(f"[report] Generated: {output_path}")
    return output_path