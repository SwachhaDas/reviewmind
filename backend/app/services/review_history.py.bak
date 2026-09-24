"""
Review History — JSON-based storage for systematic review sessions.

Mirrors the pattern used by chat_history.py, quiz_history.py, and
presentation_history.py.

Stores the FULL pipeline output so a review can be reloaded exactly:
  - keyword, criteria, language
  - all papers (with screening decisions + confidence + verification)
  - duplicates_removed count
  - pipeline counts (total_found, included, excluded, etc.)
  - report filename (if a report was generated)
  - created_at / updated_at timestamps
"""
import json
import os
import time
import uuid


# ─── Storage path ───
_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data'
)
os.makedirs(_DATA_DIR, exist_ok=True)
_HISTORY_FILE = os.path.join(_DATA_DIR, 'review_history.json')


def _load_all():
    """Load all review sessions from JSON file."""
    if not os.path.exists(_HISTORY_FILE):
        return []
    try:
        with open(_HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        print(f'[review_history] Load failed: {e}')
        return []


def _save_all(sessions):
    """Persist all review sessions to JSON file."""
    try:
        with open(_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f'[review_history] Save failed: {e}')


def create_session(keyword, criteria, lang, papers, duplicates_removed=0,
                   counts=None, report_filename=None):
    """
    Save a completed review pipeline as a session.

    Args:
        keyword (str): Search keyword used.
        criteria (str): Screening criteria used.
        lang (str): Language code ('en' or 'bn').
        papers (list): Full list of papers with all metadata + decisions.
        duplicates_removed (int): Number of duplicates the dedup agent removed.
        counts (dict): Pipeline counts (total_found, included, excluded, etc.).
        report_filename (str, optional): Generated Word report filename.

    Returns:
        dict: Full session record.
    """
    session_id = f"review_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    now = time.strftime('%Y-%m-%d %H:%M:%S')

    # Auto-generate a friendly title from keyword
    title = (keyword or 'Untitled Review').strip()[:80]

    session = {
        'id': session_id,
        'title': title,
        'keyword': keyword,
        'criteria': criteria,
        'language': lang,
        'papers': papers,                       # FULL content, no truncation
        'duplicates_removed': duplicates_removed,
        'counts': counts or {},
        'report_filename': report_filename,     # may be None
        'created_at': now,
        'updated_at': now,
    }

    sessions = _load_all()
    sessions.insert(0, session)                 # newest first
    _save_all(sessions)
    return session


def get_session(session_id):
    """Retrieve one full session by id."""
    for s in _load_all():
        if s['id'] == session_id:
            return s
    return None


def list_sessions():
    """
    Return a lightweight list for the sidebar (no papers array).
    Includes summary counts so the sidebar can show useful info.
    """
    items = []
    for s in _load_all():
        counts = s.get('counts', {}) or {}
        items.append({
            'id': s['id'],
            'title': s['title'],
            'keyword': s.get('keyword', ''),
            'language': s.get('language', 'en'),
            'paper_count': len(s.get('papers', [])),
            'included_count': counts.get('total_included', 0),
            'excluded_count': counts.get('irrelevant_excluded', 0),
            'created_at': s.get('created_at'),
            'updated_at': s.get('updated_at'),
            'has_report': bool(s.get('report_filename')),
        })
    return items


def update_title(session_id, new_title):
    """Update the title of a session (user edit)."""
    sessions = _load_all()
    for s in sessions:
        if s['id'] == session_id:
            s['title'] = (new_title or '').strip() or s['title']
            s['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            break
    _save_all(sessions)
    return get_session(session_id)


def attach_report(session_id, report_filename):
    """Attach a generated report filename to a session."""
    sessions = _load_all()
    for s in sessions:
        if s['id'] == session_id:
            s['report_filename'] = report_filename
            s['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            break
    _save_all(sessions)


def delete_session(session_id):
    """Delete a session from history."""
    sessions = _load_all()
    new_sessions = [s for s in sessions if s['id'] != session_id]
    _save_all(new_sessions)
    return len(sessions) - len(new_sessions)