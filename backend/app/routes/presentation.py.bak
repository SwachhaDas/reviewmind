"""
Presentation Routes — Generate PPTX + PDF slide decks from user content.
Full history system: save / reload / delete / title edit / download.
"""
import os
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services import presentation_history as history
from app.services.ppt_generator import generate_pptx
from app.services.pdf_generator import generate_pdf


# NOTE: prefix is /presentation (NOT /api/presentation) because main.py
# already adds prefix="/api" when registering the router.
router = APIRouter(prefix="/presentation", tags=["presentation"])


# ─── Output directory for generated files ───
GENERATED_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'generated',
    'presentations'
)
os.makedirs(GENERATED_DIR, exist_ok=True)


# ─── Pydantic models ───
class PresentationRequest(BaseModel):
    content: str
    title: Optional[str] = None
    lang: Optional[str] = 'en'


class TitleUpdateRequest(BaseModel):
    title: str


# ─── Helper ───
def _generate_files(session_id, slides_data):
    """Generate both PPTX and PDF for a session and return filenames."""
    pptx_filename = f"{session_id}.pptx"
    pdf_filename = f"{session_id}.pdf"

    pptx_path = os.path.join(GENERATED_DIR, pptx_filename)
    pdf_path = os.path.join(GENERATED_DIR, pdf_filename)

    generate_pptx(slides_data, pptx_path)
    generate_pdf(slides_data, pdf_path)

    return pptx_filename, pdf_filename


# ═══════════════════════════════════════════════
# ROUTE 1: Generate from pasted content
# ═══════════════════════════════════════════════
@router.post("/generate")
async def generate_presentation(req: PresentationRequest):
    """
    Generate a presentation from pasted content.
    Returns: session data + slides + download URLs.
    """
    if not req.content or not req.content.strip():
        raise HTTPException(status_code=400, detail="Content is required")

    # 1. Create session (calls Gemini, saves to JSON)
    session = history.create_session(
        content=req.content,
        title_hint=req.title,
        lang=req.lang or 'en',
    )

    # 2. Build slides_data structure for the generators
    slides_data = {
        'title': session['title'],
        'subtitle': session.get('subtitle', ''),
        'slides': session.get('slides', []),
    }

    # 3. Generate PPTX + PDF
    try:
        pptx_file, pdf_file = _generate_files(session['id'], slides_data)
        history.update_files(session['id'], pptx_file=pptx_file, pdf_file=pdf_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File generation failed: {e}")

    return {
        'status': 'success',
        'session_id': session['id'],
        'title': session['title'],
        'subtitle': session.get('subtitle', ''),
        'slides': session.get('slides', []),
        'pptx_url': f"/api/presentation/download/{session['id']}/pptx",
        'pdf_url': f"/api/presentation/download/{session['id']}/pdf",
        'created_at': session['created_at'],
    }


# ═══════════════════════════════════════════════
# ROUTE 2: Upload a file (txt / md) and generate
# ═══════════════════════════════════════════════
@router.post("/upload")
async def upload_and_generate(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    lang: Optional[str] = 'en',
):
    """
    Upload a text file and generate a presentation from it.
    Only supports .txt / .md (PDF upload should go through /api/upload first).
    """
    filename = (file.filename or '').lower()
    if not (filename.endswith('.txt') or filename.endswith('.md')):
        raise HTTPException(
            status_code=400,
            detail="Only .txt or .md files are supported here. Use /api/upload for PDFs."
        )

    raw = await file.read()
    try:
        content = raw.decode('utf-8', errors='ignore')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {e}")

    if not content.strip():
        raise HTTPException(status_code=400, detail="File is empty")

    # Reuse the same generation flow
    return await generate_presentation(
        PresentationRequest(content=content, title=title or file.filename, lang=lang)
    )


# ═══════════════════════════════════════════════
# ROUTE 3: List history
# ═══════════════════════════════════════════════
@router.get("/history")
async def list_history():
    """Return lightweight history list for the sidebar."""
    items = history.list_sessions()
    return {'status': 'success', 'items': items}


# ═══════════════════════════════════════════════
# ROUTE 4: Load a specific session
# ═══════════════════════════════════════════════
@router.get("/history/{session_id}")
async def get_history_session(session_id: str):
    """Reload a saved presentation session."""
    session = history.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        'status': 'success',
        'session_id': session['id'],
        'title': session['title'],
        'subtitle': session.get('subtitle', ''),
        'slides': session.get('slides', []),
        'raw_content': session.get('raw_content', ''),
        'language': session.get('language', 'en'),
        'created_at': session.get('created_at'),
        'updated_at': session.get('updated_at'),
        'pptx_url': (
            f"/api/presentation/download/{session['id']}/pptx"
            if session.get('pptx_file') else None
        ),
        'pdf_url': (
            f"/api/presentation/download/{session['id']}/pdf"
            if session.get('pdf_file') else None
        ),
    }


# ═══════════════════════════════════════════════
# ROUTE 5: Edit title
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
# ROUTE 6: Delete session
# ═══════════════════════════════════════════════
@router.delete("/history/{session_id}")
async def delete_history_session(session_id: str):
    """Delete a session and its generated files."""
    session = history.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Remove associated files first
    removed_files = history.delete_session(session_id)
    for fname in removed_files:
        fpath = os.path.join(GENERATED_DIR, fname)
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except OSError as e:
                print(f'[presentation] File delete failed: {fpath} — {e}')

    return {'status': 'success', 'deleted': session_id}


# ═══════════════════════════════════════════════
# ROUTE 7: Download generated file
# ═══════════════════════════════════════════════
@router.get("/download/{session_id}/{fmt}")
async def download_file(session_id: str, fmt: str):
    """
    Download the PPTX or PDF for a session.
    fmt must be 'pptx' or 'pdf'.
    """
    if fmt not in ('pptx', 'pdf'):
        raise HTTPException(status_code=400, detail="Format must be pptx or pdf")

    session = history.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Prefer the stored filename; fall back to session_id-based name
    stored = session.get('pptx_file') if fmt == 'pptx' else session.get('pdf_file')
    filename = stored or f"{session_id}.{fmt}"
    file_path = os.path.join(GENERATED_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    media_type = (
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        if fmt == 'pptx'
        else 'application/pdf'
    )

    # Build a friendly download name from the session title
    safe_title = ''.join(
        c for c in session.get('title', 'Presentation')
        if c.isalnum() or c in ' -_'
    ).strip() or 'Presentation'

    return FileResponse(
        file_path,
        media_type=media_type,
        filename=f"{safe_title}.{fmt}",
    )