"""
Quiz routes — generate quizzes + persist history to JSON.

Endpoints:
  POST   /api/quiz                     Generate quiz from content
  GET    /api/quiz/history             List all quiz sessions
  GET    /api/quiz/history/{id}        Get one session (with questions & answers)
  POST   /api/quiz/history/{id}/answers  Save answers progress
  POST   /api/quiz/history/{id}/score    Mark completed & save score
  PATCH  /api/quiz/history/{id}/title    Update session title
  DELETE /api/quiz/history/{id}        Delete one session
  DELETE /api/quiz/history             Clear all sessions
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.services.gemini_client import generate_quiz, _generate_session_title
from app.services import quiz_history

router = APIRouter()


# ─────────────────────────────────────────────────────────────
# Request models
# ─────────────────────────────────────────────────────────────

class QuizRequest(BaseModel):
    context_text: str
    num_questions: int = 5
    lang: str = "en"
    source: str = "pasted"  # 'pasted' | 'uploaded'


class SaveAnswersRequest(BaseModel):
    answers: List[Optional[int]]


class SaveScoreRequest(BaseModel):
    correct: int
    total: int


class UpdateTitleRequest(BaseModel):
    title: str


# ─────────────────────────────────────────────────────────────
# Main quiz generation
# ─────────────────────────────────────────────────────────────

@router.post("/quiz")
async def quiz(req: QuizRequest):
    """Generate a quiz from content and save to history."""
    # Validate question count
    num_q = max(1, min(50, req.num_questions))

    # Generate quiz via Gemini
    result = generate_quiz(req.context_text, num_q, req.lang)

    if not result.get("questions"):
        return {
            "error": result.get("error", "Failed to generate quiz"),
            "questions": [],
        }

    # Generate title from content
    title = _generate_session_title(req.context_text[:1500], req.lang)

    # Save to history
    session = quiz_history.create_session(
        title=title,
        content=req.context_text,
        source=req.source,
        num_questions=num_q,
        questions=result["questions"],
    )

    return {
        "status": "success",
        "session_id": session["id"],
        "title": session["title"],
        "questions": result["questions"],
    }


# ─────────────────────────────────────────────────────────────
# History endpoints
# ─────────────────────────────────────────────────────────────

@router.get("/quiz/history")
async def get_quiz_history():
    """List all quiz sessions (summary only)."""
    return {"sessions": quiz_history.list_sessions()}


@router.get("/quiz/history/{session_id}")
async def get_quiz_session(session_id: str):
    """Get full session with questions and answers."""
    session = quiz_history.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    return session


@router.post("/quiz/history/{session_id}/answers")
async def save_quiz_answers(session_id: str, req: SaveAnswersRequest):
    """Save user's answers progress."""
    session = quiz_history.save_answers(session_id, req.answers)
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    return {"status": "success", "session_id": session_id}


@router.post("/quiz/history/{session_id}/score")
async def save_quiz_score(session_id: str, req: SaveScoreRequest):
    """Mark quiz completed and save score."""
    session = quiz_history.save_score(session_id, req.correct, req.total)
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    return {"status": "success", "score": session["score"]}


@router.patch("/quiz/history/{session_id}/title")
async def update_quiz_title(session_id: str, req: UpdateTitleRequest):
    """Update quiz session title."""
    if not req.title or not req.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    ok = quiz_history.update_title(session_id, req.title.strip())
    if not ok:
        raise HTTPException(status_code=404, detail="Quiz session not found")

    return {"status": "success", "session_id": session_id, "title": req.title.strip()}


@router.delete("/quiz/history/{session_id}")
async def delete_quiz_session(session_id: str):
    """Delete one quiz session."""
    ok = quiz_history.delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    return {"status": "success", "deleted": session_id}


@router.delete("/quiz/history")
async def clear_quiz_history():
    """Delete all quiz sessions."""
    count = quiz_history.clear_all()
    return {"status": "success", "deleted_count": count}