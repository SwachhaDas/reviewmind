"""
Chat History Manager — persists chat sessions to a JSON file.

Each session has:
  - id: unique session id
  - title: derived from paper title or AI-generated
  - paper_title: title of the loaded paper (if any)
  - source: 'uploaded' | 'pasted' | 'free'
  - created_at: ISO timestamp
  - updated_at: ISO timestamp
  - messages: [{role: 'user'|'assistant', text, time}]
  - paper_data: {full_text, abstract, introduction, ...} for reload

The file is stored at: backend/app/data/chat_history.json
"""
import json
import os
import uuid
import threading
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────────────────────
# Storage location
# ─────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data"
)
os.makedirs(DATA_DIR, exist_ok=True)
HISTORY_FILE = os.path.join(DATA_DIR, "chat_history.json")

_lock = threading.Lock()


# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _load_all() -> dict:
    if not os.path.exists(HISTORY_FILE):
        return {"sessions": []}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "sessions" not in data:
                data["sessions"] = []
            return data
    except Exception as e:
        print(f"[history] Load failed: {e}")
        return {"sessions": []}


def _save_all(data: dict) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def list_sessions() -> list:
    """Return a lightweight list of all sessions (no full messages)."""
    with _lock:
        data = _load_all()
        summary = []
        for s in data["sessions"]:
            summary.append({
                "id": s.get("id"),
                "title": s.get("title", "Untitled"),
                "paper_title": s.get("paper_title", ""),
                "source": s.get("source", "free"),
                "created_at": s.get("created_at"),
                "updated_at": s.get("updated_at"),
                "message_count": len(s.get("messages", [])),
            })
        summary.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return summary


def get_session(session_id: str) -> Optional[dict]:
    """Return one full session or None."""
    with _lock:
        data = _load_all()
        for s in data["sessions"]:
            if s.get("id") == session_id:
                return s
        return None


def create_session(
    title: str = "New Chat",
    paper_title: str = "",
    source: str = "free",
    paper_data: dict = None,
) -> dict:
    """
    Create a new session.

    Args:
        title: Display title for the session.
        paper_title: Title of the loaded paper (if any).
        source: 'paper' or 'free'.
        paper_data: Optional full paper content for later reload.
    """
    with _lock:
        data = _load_all()
        session = {
            "id": uuid.uuid4().hex[:12],
            "title": title[:80],
            "paper_title": paper_title[:200],
            "source": source,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "messages": [],
            "paper_data": paper_data or {},
        }
        data["sessions"].append(session)
        _save_all(data)
        print(f"[history] Created session: {session['id']} — {title}")
        return session


def append_message(session_id: str, role: str, text: str) -> Optional[dict]:
    """Append a message to a session."""
    with _lock:
        data = _load_all()
        for s in data["sessions"]:
            if s.get("id") == session_id:
                s.setdefault("messages", []).append({
                    "role": role,
                    "text": text,
                    "time": datetime.utcnow().isoformat() + "Z",
                })
                s["updated_at"] = datetime.utcnow().isoformat() + "Z"
                _save_all(data)
                return s
        return None


def update_session_title(session_id: str, new_title: str) -> bool:
    """Update a session's title. Returns True if updated."""
    with _lock:
        data = _load_all()
        for s in data["sessions"]:
            if s.get("id") == session_id:
                s["title"] = new_title[:80]
                s["updated_at"] = datetime.utcnow().isoformat() + "Z"
                _save_all(data)
                print(f"[history] Updated title for {session_id}: {new_title}")
                return True
        return False


def update_session_paper_data(session_id: str, paper_data: dict) -> bool:
    """Attach paper_data to a session that was created without it."""
    with _lock:
        data = _load_all()
        for s in data["sessions"]:
            if s.get("id") == session_id:
                s["paper_data"] = paper_data
                s["updated_at"] = datetime.utcnow().isoformat() + "Z"
                _save_all(data)
                return True
        return False


def delete_session(session_id: str) -> bool:
    """Delete one session. Returns True if removed."""
    with _lock:
        data = _load_all()
        before = len(data["sessions"])
        data["sessions"] = [
            s for s in data["sessions"] if s.get("id") != session_id
        ]
        if len(data["sessions"]) < before:
            _save_all(data)
            print(f"[history] Deleted session: {session_id}")
            return True
        return False


def clear_all() -> int:
    """Delete all sessions. Returns count deleted."""
    with _lock:
        data = _load_all()
        count = len(data["sessions"])
        data["sessions"] = []
        _save_all(data)
        print(f"[history] Cleared {count} sessions")
        return count