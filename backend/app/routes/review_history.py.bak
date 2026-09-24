"""
Review History Routes — CRUD endpoints for systematic review sessions.

Endpoints:
  POST   /api/review/history              — Save a completed pipeline
  GET    /api/review/history              — List all sessions (sidebar)
  GET    /api/review/history/{id}         — Reload a full session
  PATCH  /api/review/history/{id}/title   — Edit session title
  DELETE /api/review/history/{id}         — Delete a session
  POST   /api/review/history/{id}/report  — Attach a report filename
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import review_history as history


# NOTE: prefix is /review (NOT /api/review) because main.py
# already adds prefix="/api" when registering this router.
router = APIRouter(prefix="/review", tags=["review-history"])


# ─── Pydantic models ───
class SaveReviewRequest(BaseModel):
    keyword: str
    criteria: str
    lang: str = "en"
    papers: list[dict]
    duplicates_removed: int = 0
    counts: Optional[dict] = None
    report_filename: Optional[str] = None


class TitleUpdateRequest(BaseModel):
    title: str


class AttachReportRequest(BaseModel):
    report_filename: str


# ═══════════════════════════════════════════════
# ROUTE 1: Save a completed review
# ═══════════════════════════════════════════════
@router.post("/history")
async def save_review(req: SaveReviewRequest):
    """
    Save a completed review pipeline to history.
    Called automatically by the frontend after the pipeline finishes.
    """
    if not req.papers:
        raise HTTPException(status_code=400, detail="No papers to save")

    session = history.create_session(
        keyword=req.keyword,
        criteria=req.criteria,
        lang=req.lang,
        papers=req.papers,
        duplicates_removed=req.duplicates_removed,
        counts=req.counts or {},
        report_filename=req.report_filename,
    )

    return {
        'status': 'success',
        'session_id': session['id'],
        'title': session['title'],
        'created_at': session['created_at'],
    }


# ═══════════════════════════════════════════════
# ROUTE 2: List all sessions (lightweight)
# ═══════════════════════════════════════════════
@router.get("/history")
async def list_reviews():
    """Return a lightweight list for the sidebar."""
    items = history.list_sessions()
    return {'status': 'success', 'items': items}


# ═══════════════════════════════════════════════
# ROUTE 3: Reload a full session
# ═══════════════════════════════════════════════
@router.get("/history/{session_id}")
async def get_review(session_id: str):
    """Reload a full saved review session (papers + counts + report)."""
    session = history.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        'status': 'success',
        'session_id': session['id'],
        'title': session['title'],
        'keyword': session.get('keyword', ''),
        'criteria': session.get('criteria', ''),
        'language': session.get('language', 'en'),
        'papers': session.get('papers', []),
        'duplicates_removed': session.get('duplicates_removed', 0),
        'counts': session.get('counts', {}),
        'report_filename': session.get('report_filename'),
        'created_at': session.get('created_at'),
        'updated_at': session.get('updated_at'),
    }


# ═══════════════════════════════════════════════
# ROUTE 4: Edit title
# ═══════════════════════════════════════════════
@router.patch("/history/{session_id}/title")
async def edit_title(session_id: str, req: TitleUpdateRequest):
    """Update the title of a saved session."""
    session = history.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    updated = history.update_title(session_id, req.title)
    return {'status': 'success', 'title': updated['title']}


# ═══════════════════════════════════════════════
# ROUTE 5: Attach a report filename to a session
# ═══════════════════════════════════════════════
@router.post("/history/{session_id}/report")
async def attach_report(session_id: str, req: AttachReportRequest):
    """
    Attach a generated Word report filename to a session.
    Called by the frontend after /api/report succeeds.
    """
    session = history.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    history.attach_report(session_id, req.report_filename)
    return {'status': 'success', 'report_filename': req.report_filename}


# ═══════════════════════════════════════════════
# ROUTE 6: Delete a session
# ═══════════════════════════════════════════════
@router.delete("/history/{session_id}")
async def delete_review(session_id: str):
    """Delete a saved review session."""
    session = history.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    history.delete_session(session_id)
    return {'status': 'success', 'deleted': session_id}