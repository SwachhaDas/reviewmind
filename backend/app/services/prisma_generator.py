"""
PRISMA Flow Diagram Generator.

Builds a professional PRISMA flow diagram (PNG) showing:
    - Records identified
    - Duplicates removed
    - Records screened
    - Records excluded
    - Records marked as Maybe
    - Records with errors
    - Studies included

Supports English and Bengali labels.
"""
import os
import uuid

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated")
os.makedirs(OUTPUT_DIR, exist_ok=True)


LABELS = {
    "en": {
        "identification": "Identification",
        "screening": "Screening",
        "included_section": "Included",
        "identified": "Records identified",
        "duplicates_removed": "Duplicates removed",
        "screened": "Records screened",
        "excluded": "Records excluded",
        "maybe": "Records marked 'Maybe'",
        "error": "Screening errors",
        "full_text": "Full-text assessed",
        "included": "Studies included",
    },
    "bn": {
        "identification": "শনাক্তকরণ",
        "screening": "স্ক্রিনিং",
        "included_section": "অন্তর্ভুক্ত",
        "identified": "শনাক্তকৃত রেকর্ড",
        "duplicates_removed": "ডুপ্লিকেট সরানো",
        "screened": "স্ক্রিন করা রেকর্ড",
        "excluded": "বাদ পড়া রেকর্ড",
        "maybe": "'সম্ভব' হিসেবে চিহ্নিত",
        "error": "স্ক্রিনিং ত্রুটি",
        "full_text": "পূর্ণ-টেক্সট মূল্যায়ন",
        "included": "অন্তর্ভুক্ত গবেষণা",
    },
}


def _draw_box(ax, x, y, width, height, text, color, fontsize=10):
    box = FancyBboxPatch(
        (x - width / 2, y - height / 2), width, height,
        boxstyle="round,pad=0.1", facecolor=color,
        edgecolor="#444444", linewidth=1.2,
    )
    ax.add_patch(box)
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize, fontweight="bold")


def _draw_arrow(ax, x, y_from, y_to, color="#666666"):
    arrow_style = dict(arrowstyle="->,head_width=0.3", color=color, lw=1.2)
    ax.annotate("", xy=(x, y_to), xytext=(x, y_from), arrowprops=arrow_style)


def generate_prisma(
    identified: int = 0,
    duplicates_removed: int = 0,
    screened: int = 0,
    excluded: int = 0,
    maybe: int = 0,
    error: int = 0,
    full_text: int = 0,
    included: int = 0,
    lang: str = "en",
) -> str:
    L = LABELS.get(lang, LABELS["en"])
    fig, ax = plt.subplots(figsize=(10, 12))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 14)
    ax.axis("off")

    center_x = 5
    box_w = 7
    box_h = 1.1
    side_x = 10.2

    c_ident = "#cfe8ff"
    c_screen = "#d6f5d6"
    c_excl = "#ffd6d6"
    c_maybe = "#fff6cf"
    c_error = "#ffd9cc"
    c_incl = "#b8e6b8"

    ax.text(center_x - 4.5, 13.4, L["identification"], fontsize=12, fontweight="bold", color="#1F3F7A")
    ax.text(center_x - 4.5, 8.9, L["screening"], fontsize=12, fontweight="bold", color="#1F3F7A")
    ax.text(center_x - 4.5, 2.4, L["included_section"], fontsize=12, fontweight="bold", color="#1F3F7A")

    _draw_box(ax, center_x, 12.5, box_w, box_h, f"{L['identified']}\n(n = {identified})", c_ident)
    _draw_box(ax, side_x, 12.5, 3.5, box_h, f"{L['duplicates_removed']}\n(n = {duplicates_removed})", c_excl, fontsize=9)
    _draw_box(ax, center_x, 10.5, box_w, box_h, f"{L['screened']}\n(n = {screened})", c_screen)
    _draw_box(ax, side_x, 10.5, 3.5, box_h, f"{L['excluded']}\n(n = {excluded})", c_excl, fontsize=9)
    _draw_box(ax, side_x, 8.7, 3.5, box_h, f"{L['maybe']}\n(n = {maybe})", c_maybe, fontsize=9)
    _draw_box(ax, side_x, 6.9, 3.5, box_h, f"{L['error']}\n(n = {error})", c_error, fontsize=9)
    _draw_box(ax, center_x, 8.5, box_w, box_h, f"{L['full_text']}\n(n = {full_text})", c_maybe)
    _draw_box(ax, center_x, 5.5, box_w, box_h, f"{L['included']}\n(n = {included})", c_incl)

    _draw_arrow(ax, center_x, 12.0, 11.0)
    _draw_arrow(ax, center_x, 10.0, 9.0)
    _draw_arrow(ax, center_x, 8.0, 6.0)

    arrow_side = dict(arrowstyle="->,head_width=0.3", color="#888888", lw=1.0)
    ax.annotate("", xy=(side_x - 1.8, 12.5), xytext=(center_x + box_w / 2, 12.5), arrowprops=arrow_side)
    ax.annotate("", xy=(side_x - 1.8, 10.5), xytext=(center_x + box_w / 2, 10.5), arrowprops=arrow_side)
    ax.annotate("", xy=(side_x - 1.8, 8.7), xytext=(center_x + box_w / 2, 8.7), arrowprops=arrow_side)
    ax.annotate("", xy=(side_x - 1.8, 6.9), xytext=(center_x + box_w / 2, 6.9), arrowprops=arrow_side)

    filename = f"prisma_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    return filepath