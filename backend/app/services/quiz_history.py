"""
Quiz History Manager — persists quiz sessions to JSON file.

Each session has:
  - id: unique session id
  - title: AI-generated title from content
  - content: full paper text (for reloading)
  - content_preview: first 200 chars
  - source: 'pasted' | 'uploaded'
  - num_questions: number of questions generated
  - created_at, updated_at
  - questions: [{question, options, correct_index, explanation}]
  - answers: user's selected answers (null if not answered)
  - score: {correct, total, percentage} after completion

Storage: backend/app/data/quiz_history.json
"""
import json
import os
import uuid
import threading
from datetime import datetime
from typing import Optional


DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data"
)
os.makedirs(DATA_DIR, exist_ok=True)
HISTORY_FILE = os.path.join(DATA_DIR, "quiz_history.json")

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
        print(f"[quiz-history] Load failed: {e}")
        return {"sessions": []}


def _save_all(data: dict) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def list_sessions() -> list:
    """Lightweight list — no full content or questions."""
    with _lock:
        data = _load_all()
        summary = []
        for s in data["sessions"]:
            summary.append({
                "id": s.get("id"),
                "title": s.get("title", "Untitled Quiz"),
                "content_preview": s.get("content_preview", ""),
                "source": s.get("source", "pasted"),
                "num_questions": s.get("num_questions", 0),
                "created_at": s.get("created_at"),
                "updated_at": s.get("updated_at"),
                "score": s.get("score"),  # null if not completed
                "completed": s.get("completed", False),
            })
        summary.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return summary


def get_session(session_id: str) -> Optional[dict]:
    """Return full session including questions & answers."""
    with _lock:
        data = _load_all()
        for s in data["sessions"]:
            if s.get("id") == session_id:
                return s
        return None


def create_session(
    title: str = "New Quiz",
    content: str = "",
    source: str = "pasted",
    num_questions: int = 5,
    questions: list = None,
) -> dict:
    """Create a new quiz session with generated questions."""
    with _lock:
        data = _load_all()
        content_preview = content[:200].replace("\n", " ").strip()
        session = {
            "id": uuid.uuid4().hex[:12],
            "title": title[:80],
            "content": content,
            "content_preview": content_preview,
            "source": source,
            "num_questions": num_questions,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "questions": questions or [],
            "answers": [None] * (num_questions if not questions else len(questions)),
            "score": None,
            "completed": False,
        }
        data["sessions"].append(session)
        _save_all(data)
        print(f"[quiz-history] Created session: {session['id']} — {title}")
        return session


def save_answers(session_id: str, answers: list) -> Optional[dict]:
    """Save user's answers as they progress through the quiz."""
    with _lock:
        data = _load_all()
        for s in data["sessions"]:
            if s.get("id") == session_id:
                s["answers"] = answers
                s["updated_at"] = datetime.utcnow().isoformat() + "Z"
                _save_all(data)
                return s
        return None


def save_score(session_id: str, correct: int, total: int) -> Optional[dict]:
    """Mark quiz as completed and store score."""
    with _lock:
        data = _load_all()
        for s in data["sessions"]:
            if s.get("id") == session_id:
                percentage = round((correct / total) * 100) if total > 0 else 0
                s["score"] = {
                    "correct": correct,
                    "total": total,
                    "percentage": percentage,
                }
                s["completed"] = True
                s["updated_at"] = datetime.utcnow().isoformat() + "Z"
                _save_all(data)
                print(f"[quiz-history] Score saved: {correct}/{total} ({percentage}%)")
                return s
        return None


def update_title(session_id: str, new_title: str) -> bool:
    """Update quiz session title."""
    with _lock:
        data = _load_all()
        for s in data["sessions"]:
            if s.get("id") == session_id:
                s["title"] = new_title[:80]
                s["updated_at"] = datetime.utcnow().isoformat() + "Z"
                _save_all(data)
                return True
        return False


def delete_session(session_id: str) -> bool:
    """Delete one quiz session."""
    with _lock:
        data = _load_all()
        before = len(data["sessions"])
        data["sessions"] = [
            s for s in data["sessions"] if s.get("id") != session_id
        ]
        if len(data["sessions"]) < before:
            _save_all(data)
            print(f"[quiz-history] Deleted session: {session_id}")
            return True
        return False


def clear_all() -> int:
    """Delete all quiz sessions."""
    with _lock:
        data = _load_all()
        count = len(data["sessions"])
        data["sessions"] = []
        _save_all(data)
        print(f"[quiz-history] Cleared {count} sessions")
        return count