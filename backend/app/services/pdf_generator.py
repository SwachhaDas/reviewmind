"""
PDF Generator — Creates PDF presentations from slide data.
Uses reportlab with the same blue theme as the PPTX output.
"""
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT
import os


# ─── Theme colors (matching ReviewMind website) ───
BLUE_PRIMARY = HexColor('#2563EB')
BLUE_DARK = HexColor('#1E40AF')
BLUE_BG = HexColor('#EFF6FF')
GRAY_DARK = HexColor('#1F2937')
GRAY_TEXT = HexColor('#4B5563')


def _wrap_text(text, style, width):
    """Wrap text using a ReportLab Paragraph and return its height."""
    p = Paragraph(text, style)
    _, h = p.wrap(width, 10000)
    return p, h


def generate_pdf(slides_data, output_path):
    """
    Generate a PDF file from slide data.

    Args:
        slides_data (dict): Same structure as pptx generator.
        output_path (str): Where to save the .pdf file.

    Returns:
        str: Path to the generated file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Landscape A4 (11.69 x 8.27 inches)
    page_size = landscape(A4)
    width, height = page_size

    c = canvas.Canvas(output_path, pagesize=page_size)
    c.setTitle(slides_data.get('title', 'Presentation'))

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=32,
        textColor=BLUE_DARK,
        leading=38,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=GRAY_TEXT,
        leading=22,
        fontName='Helvetica',
    )
    slide_title_style = ParagraphStyle(
        'SlideTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=BLUE_DARK,
        leading=28,
        fontName='Helvetica-Bold',
    )
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=13,
        textColor=GRAY_DARK,
        leading=20,
        fontName='Helvetica',
        leftIndent=20,
    )

    # ─── Title slide ───
    c.setFillColor(BLUE_BG)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    # Left accent bar
    c.setFillColor(BLUE_PRIMARY)
    c.rect(0, 0, 0.3 * inch, height, fill=1, stroke=0)
    # Top bar
    c.rect(0, height - 0.15 * inch, width, 0.15 * inch, fill=1, stroke=0)

    # Title
    title_p, th = _wrap_text(
        slides_data.get('title', 'Untitled'),
        title_style,
        width - 2 * inch
    )
    title_p.drawOn(c, 1 * inch, height - 3 * inch - th)

    # Subtitle
    if slides_data.get('subtitle'):
        sub_p, sh = _wrap_text(
            slides_data['subtitle'], subtitle_style, width - 2 * inch
        )
        sub_p.drawOn(c, 1 * inch, height - 4 * inch - sh)

    c.showPage()

    # ─── Content slides ───
    for slide_data in slides_data.get('slides', []):
        # White background
        c.setFillColor(white)
        c.rect(0, 0, width, height, fill=1, stroke=0)
        # Top bar
        c.setFillColor(BLUE_PRIMARY)
        c.rect(0, height - 0.15 * inch, width, 0.15 * inch, fill=1, stroke=0)

        # Slide title — draw first, then anchor the accent underline
        # directly beneath the title's real bottom edge. Using a fixed
        # y-position caused the underline to overlap multi-line titles
        # and appear like a strikethrough line across the text.
        title_p, th = _wrap_text(
            slide_data.get('title', ''), slide_title_style, width - 2 * inch
        )
        title_top = height - 1.2 * inch
        title_bottom = title_top - th
        title_p.drawOn(c, 0.6 * inch, title_bottom)

        # Accent underline — placed below the title's actual bottom,
        # with a small gap so it never touches descenders (g, y, p).
        underline_y = title_bottom - 0.12 * inch
        c.setFillColor(BLUE_PRIMARY)
        c.rect(0.6 * inch, underline_y, 1.5 * inch, 0.05 * inch,
               fill=1, stroke=0)

        # Bullets
        bullets = slide_data.get('bullets', [])
        if not bullets:
            bullets = [slide_data.get('content', '')]

        # Start bullets below the underline (dynamic, not fixed), so
        # multi-line titles push content down instead of overlapping.
        y_pos = underline_y - 0.4 * inch
        for bullet in bullets:
            bullet_text = f"• {bullet}"
            bp, bh = _wrap_text(bullet_text, bullet_style, width - 1.5 * inch)
            if y_pos - bh < 0.5 * inch:
                # Not enough space; stop adding bullets to this page
                break
            bp.drawOn(c, 0.6 * inch, y_pos - bh)
            y_pos -= (bh + 0.1 * inch)

        # Footer
        c.setFillColor(GRAY_TEXT)
        c.setFont('Helvetica', 9)
        c.drawRightString(width - 0.5 * inch, 0.35 * inch, 'ReviewMind')

        c.showPage()

    c.save()
    return output_path