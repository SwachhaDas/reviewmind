"""
Report routes — generates PRISMA diagram and Word report.

Endpoints:
  POST /api/prisma         — Generate only PRISMA diagram
  POST /api/report         — Generate full Word report + PRISMA
  GET  /api/download/{file} — Download generated file
"""
import os
import traceback

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.prisma_generator import generate_prisma, OUTPUT_DIR
from app.services.report_generator import generate_word_report

router = APIRouter()


# ─────────────────────────────────────────────────────────────
# Request models
# ─────────────────────────────────────────────────────────────

class PrismaCounts(BaseModel):
    identified: int = 0
    duplicates_removed: int = 0
    screened: int = 0
    excluded: int = 0
    maybe: int = 0
    error: int = 0
    full_text: int = 0
    included: int = 0


class PrismaRequest(BaseModel):
    identified: int = 0
    duplicates_removed: int = 0
    screened: int = 0
    excluded: int = 0
    maybe: int = 0
    error: int = 0
    full_text: int = 0
    included: int = 0
    lang: str = "en"


class ReportRequest(BaseModel):
    papers: list[dict]
    prisma_counts: PrismaCounts = PrismaCounts()
    keyword: str = ""
    criteria: str = ""
    lang: str = "en"


# ─────────────────────────────────────────────────────────────
# PRISMA-only endpoint
# ─────────────────────────────────────────────────────────────

@router.post("/prisma")
async def make_prisma(req: PrismaRequest):
    """Generate only a PRISMA flow diagram."""
    try:
        print(f"\n[prisma] === REQUEST ===")
        path = generate_prisma(
            identified=req.identified,
            duplicates_removed=req.duplicates_removed,
            screened=req.screened,
            excluded=req.excluded,
            maybe=req.maybe,
            error=req.error,
            full_text=req.full_text,
            included=req.included,
            lang=req.lang,
        )
        print(f"[prisma] Generated: {path}")
        return {"status": "success", "filename": os.path.basename(path)}
    except Exception as e:
        print(f"[prisma] ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Full report endpoint
# ─────────────────────────────────────────────────────────────

@router.post("/report")
async def make_report(req: ReportRequest):
    """
    Generate the full Word report + PRISMA diagram.
    With detailed debug logging for troubleshooting.
    """
    try:
        # ─── LOG 1: Request received ───
        print(f"\n[report] ═══════════════════════════════")
        print(f"[report] === REQUEST RECEIVED ===")
        print(f"[report] papers count: {len(req.papers)}")
        print(f"[report] keyword: {req.keyword}")
        print(f"[report] criteria: {req.criteria}")
        print(f"[report] lang: {req.lang}")
        print(f"[report] prisma_counts: {req.prisma_counts.model_dump()}")

        # ─── Validate papers ───
        if not req.papers:
            print(f"[report] ⚠️ No papers in request")
            raise HTTPException(status_code=400, detail="No papers provided")

        # ─── LOG 2: Sample paper check ───
        first_paper = req.papers[0]
        print(f"[report] Sample paper keys: {list(first_paper.keys())[:10]}")
        print(f"[report] Sample decision: {first_paper.get('decision')}")

        # ─── Build counts ───
        counts = req.prisma_counts.model_dump()

        if counts.get("identified", 0) == 0 and len(req.papers) > 0:
            included = [p for p in req.papers if p.get("decision") == "Include"]
            counts = {
                "identified": len(req.papers),
                "duplicates_removed": 0,
                "screened": len(req.papers),
                "excluded": len([p for p in req.papers if p.get("decision") == "Exclude"]),
                "maybe": len([p for p in req.papers if p.get("decision") == "Maybe"]),
                "error": len([p for p in req.papers if p.get("decision") == "Error"]),
                "full_text": len(included),
                "included": len(included),
            }
            print(f"[report] Recomputed counts: {counts}")

        report_counts = {
            "total_found": counts.get("identified", 0),
            "duplicates_removed": counts.get("duplicates_removed", 0),
            "irrelevant_excluded": counts.get("excluded", 0),
            "maybe": counts.get("maybe", 0),
            "error": counts.get("error", 0),
            "total_included": counts.get("included", 0),
        }

        # ─── LOG 3: Generating PRISMA ───
        print(f"[report] → Generating PRISMA diagram...")
        try:
            prisma_path = generate_prisma(
                identified=counts.get("identified", 0),
                duplicates_removed=counts.get("duplicates_removed", 0),
                screened=counts.get("screened", 0),
                excluded=counts.get("excluded", 0),
                maybe=counts.get("maybe", 0),
                error=counts.get("error", 0),
                full_text=counts.get("full_text", 0),
                included=counts.get("included", 0),
                lang=req.lang,
            )
            print(f"[report] ✅ PRISMA generated: {prisma_path}")
        except Exception as pe:
            print(f"[report] ❌ PRISMA FAILED: {pe}")
            traceback.print_exc()
            prisma_path = None

        # ─── LOG 4: Generating Word report ───
        print(f"[report] → Generating Word report...")
        try:
            report_path = generate_word_report(
                papers=req.papers,
                counts=report_counts,
                prisma_image_path=prisma_path,
                keyword=req.keyword,
                criteria=req.criteria,
                lang=req.lang,
            )
            print(f"[report] ✅ Word report generated: {report_path}")
        except Exception as we:
            print(f"[report] ❌ WORD REPORT FAILED: {we}")
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Word report generation failed: {str(we)}"
            )

        # ─── LOG 5: Success ───
        print(f"[report] === SUCCESS ===")
        print(f"[report] ═══════════════════════════════\n")

        return {
            "status": "success",
            "filename": os.path.basename(report_path),
            "prisma_filename": os.path.basename(prisma_path) if prisma_path else "",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"\n[report] ❌ TOP-LEVEL ERROR: {e}")
        traceback.print_exc()
        print()
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Download endpoint
# ─────────────────────────────────────────────────────────────

@router.get("/download/{filename}")
async def download_file(filename: str):
    """Download a generated file (Word report or PRISMA PNG)."""
    try:
        filepath = os.path.join(OUTPUT_DIR, filename)
        print(f"[download] Requested: {filename}")
        print(f"[download] Full path: {filepath}")
        print(f"[download] Exists: {os.path.exists(filepath)}")

        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            filepath,
            filename=filename,
            media_type="application/octet-stream",
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[download] ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))