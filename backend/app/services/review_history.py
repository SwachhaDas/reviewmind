"""
Review History — per-user isolated JSON storage for systematic review sessions.

Uses the shared HistoryStore class (from history_store.py) which:
  - Requires user_id on every write.
  - Filters list/get/delete by user_id — no cross-user visibility.

Stores FULL pipeline output so a review can be reloaded exactly:
  - keyword, criteria, language
  - all papers (with screening decisions + confidence + verification)
  - duplicates_removed count
  - pipeline counts (total_found, included, excluded, etc.)
  - report filename (if a report was generated)
  - created_at / updated_at timestamps
"""
import time

from app.services.history_store import review_history_store as _store


def create_session(user_id, keyword, criteria, lang, papers,
                   duplicates_removed=0, counts=None, report_filename=None):
    """
    Save a completed review pipeline as a session.

    Args:
        user_id (str): Required. Owner of this session.
        keyword (str): Search keyword used.
        criteria (str): Screening criteria used.
        lang (str): Language code ('en' or 'bn').
        papers (list): Full list of papers with all metadata + decisions.
        duplicates_removed (int): Number of duplicates removed.
        counts (dict): Pipeline counts.
        report_filename (str, optional): Generated Word report filename.

    Returns:
        dict: Full session record (with session_id, user_id, created_at).
    """
    title = (keyword or 'Untitled Review').strip()[:80]

    data = {
        'title': title,
        'keyword': keyword,
        'criteria': criteria,
        'language': lang,
        'papers': papers,
        'duplicates_removed': duplicates_removed,
        'counts': counts or {},
        'report_filename': report_filename,
    }

    record = _store.save_session(user_id, data)

    # Add ISO-style timestamp on top of the numeric created_at
    record['created_at_str'] = time.strftime('%Y-%m-%d %H:%M:%S')
    return record


def get_session(user_id, session_id):
    """Retrieve one full session by id (must belong to user_id)."""
    return _store.get_session(user_id, session_id)


def list_sessions(user_id):
    """
    Return a lightweight list for the sidebar (no papers array).
    Only returns sessions belonging to user_id.
    """
    items = []
    for s in _store.list_sessions(user_id):
        counts = s.get('counts', {}) or {}
        items.append({
            'id': s.get('session_id'),
            'title': s.get('title', 'Untitled'),
            'keyword': s.get('keyword', ''),
            'language': s.get('language', 'en'),
            'paper_count': len(s.get('papers', [])),
            'included_count': counts.get('total_included', 0),
            'excluded_count': counts.get('irrelevant_excluded', 0),
            'created_at': s.get('created_at_str') or s.get('created_at'),
            'updated_at': s.get('created_at_str') or s.get('created_at'),
            'has_report': bool(s.get('report_filename')),
        })
    # newest first
    items.sort(key=lambda s: s.get('created_at') or 0, reverse=True)
    return items


def update_title(user_id, session_id, new_title):
    """Update the title of a session (user edit)."""
    ok = _store.rename_session(user_id, session_id, (new_title or '').strip())
    if not ok:
        return None
    return _store.get_session(user_id, session_id)


def attach_report(user_id, session_id, report_filename):
    """Attach a generated report filename to a session."""
    session = _store.get_session(user_id, session_id)
    if not session:
        return False
    session['report_filename'] = report_filename
    _store.save_session(user_id, session)
    return True


def delete_session(user_id, session_id):
    """Delete a session from history."""
    return _store.delete_session(user_id, session_id)