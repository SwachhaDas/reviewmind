"""
Presentation History — JSON-based storage for presentation sessions.

Mirrors the pattern used by chat_history.py and quiz_history.py.
Stores:
  - session id
  - title (user-editable)
  - raw content (full, no truncation)
  - slide data
  - pptx / pdf filenames
  - created_at / updated_at timestamps
"""
import json
import os
import time
import uuid

from app.services.slide_generator import generate_slide_data


# ─── Storage path ───
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
os.makedirs(_DATA_DIR, exist_ok=True)
_HISTORY_FILE = os.path.join(_DATA_DIR, 'presentation_history.json')


def _load_all():
    """Load all sessions from JSON file."""
    if not os.path.exists(_HISTORY_FILE):
        return []
    try:
        with open(_HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        print(f'[presentation_history] Load failed: {e}')
        return []


def _save_all(sessions):
    """Persist all sessions to JSON file."""
    try:
        with open(_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f'[presentation_history] Save failed: {e}')


def create_session(content, title_hint=None, lang='en'):
    """
    Create a new presentation session:
      1. Call Gemini to generate slide data.
      2. Save session metadata + slides + raw content.
      3. Return the session dict.

    Args:
        content (str): Full raw content.
        title_hint (str): Optional preferred title.
        lang (str): Language ('en' or 'bn').

    Returns:
        dict: Full session record.
    """
    # Generate slides via Gemini (with fallback inside)
    slide_data = generate_slide_data(content, title_hint, lang)

    session_id = f"pres_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    now = time.strftime('%Y-%m-%d %H:%M:%S')

    session = {
        'id': session_id,
        'title': slide_data.get('title', title_hint or 'Presentation'),
        'subtitle': slide_data.get('subtitle', ''),
        'slides': slide_data.get('slides', []),
        'raw_content': content,             # full content, no truncation
        'language': lang,
        'created_at': now,
        'updated_at': now,
        'pptx_file': None,                  # filled after generation
        'pdf_file': None,                   # filled after generation
    }

    sessions = _load_all()
    sessions.insert(0, session)             # newest first
    _save_all(sessions)
    return session


def update_files(session_id, pptx_file=None, pdf_file=None):
    """Attach generated file names to a session."""
    sessions = _load_all()
    for s in sessions:
        if s['id'] == session_id:
            if pptx_file:
                s['pptx_file'] = pptx_file
            if pdf_file:
                s['pdf_file'] = pdf_file
            s['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            break
    _save_all(sessions)


def get_session(session_id):
    """Retrieve one session by id."""
    for s in _load_all():
        if s['id'] == session_id:
            return s
    return None


def list_sessions():
    """
    Return a lightweight list (no raw content or full slides) for the sidebar.
    """
    items = []
    for s in _load_all():
        items.append({
            'id': s['id'],
            'title': s['title'],
            'subtitle': s.get('subtitle', ''),
            'slide_count': len(s.get('slides', [])),
            'language': s.get('language', 'en'),
            'created_at': s.get('created_at'),
            'updated_at': s.get('updated_at'),
            'has_pptx': bool(s.get('pptx_file')),
            'has_pdf': bool(s.get('pdf_file')),
        })
    return items


def delete_session(session_id):
    """
    Delete a session from history. Also returns the filenames to delete
    so the caller can remove the generated .pptx/.pdf files.
    """
    sessions = _load_all()
    removed_files = []
    new_sessions = []
    for s in sessions:
        if s['id'] == session_id:
            if s.get('pptx_file'):
                removed_files.append(s['pptx_file'])
            if s.get('pdf_file'):
                removed_files.append(s['pdf_file'])
        else:
            new_sessions.append(s)
    _save_all(new_sessions)
    return removed_files


def update_title(session_id, new_title):
    """Update the title of a session (user edit)."""
    sessions = _load_all()
    for s in sessions:
        if s['id'] == session_id:
            s['title'] = new_title.strip() or s['title']
            s['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            break
    _save_all(sessions)
    return get_session(session_id)