"""
Chat routes — supports two chat modes + persistent history.

Modes:
  - 'paper' : answer questions using ONLY the loaded paper content
  - 'free'  : answer any question using the AI's general knowledge

Endpoints:
  POST   /api/chat                     Send a message, get AI response
  GET    /api/chat/history             List all chat sessions
  GET    /api/chat/history/{id}        Get one session with full messages
  POST   /api/chat/history             Create a new empty session
  PATCH  /api/chat/history/{id}/title  Update session title
  DELETE /api/chat/history/{id}        Delete one session
  DELETE /api/chat/history             Clear all sessions
"""
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.gemini_client import chat_about_paper, _api_key, _MODEL_NAME
from app.services import chat_history
import google.generativeai as genai


router = APIRouter()


# ─────────────────────────────────────────────────────────────
# Request models
# ─────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    context_text: str = ""
    question: str
    lang: str = "en"
    mode: str = "paper"
    session_id: str = ""
    paper_title: str = ""

    # Paper data — saved with the session for later reload
    paper_full_text: str = ""
    paper_abstract: str = ""
    paper_introduction: str = ""
    paper_methodology: str = ""
    paper_findings: str = ""
    paper_limitations: str = ""
    paper_conclusion: str = ""
    paper_key_points: list = []
    paper_content_type: str = ""


class CreateSessionRequest(BaseModel):
    title: str = "New Chat"
    paper_title: str = ""
    source: str = "free"


class UpdateTitleRequest(BaseModel):
    title: str


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _generate_session_title(text: str, lang: str = "en") -> str:
    """
    Generate a short ChatGPT-style session title from the given text.
    """
    if not text or not text.strip():
        return "New Chat"

    if _api_key:
        try:
            model = genai.GenerativeModel(_MODEL_NAME)

            lang_note = (
                "Generate the title in Bengali (বাংলা)."
                if lang == "bn"
                else "Generate the title in English."
            )

            prompt = f"""Generate a SHORT title (3-6 words, max 40 characters) for this chat session based on the content below.

The title should be descriptive, like a ChatGPT chat title. Do NOT include quotes, punctuation at the end, or the words "Chat about" or "Discussion of".

Examples:
- React useEffect Guide
- Machine Learning Basics
- Transformer Architecture
- Python Data Analysis
- ChatGPT in Healthcare

CONTENT (first 1000 chars):
{text[:1000]}

{lang_note}

Respond with ONLY the title text, nothing else."""

            response = model.generate_content(prompt)
            title = response.text.strip().strip('"').strip("'")
            title = re.sub(r"[^\w\s\-\u0980-\u09FF]", "", title)[:50].strip()
            if title and len(title) >= 3:
                return title
        except Exception as e:
            print(f"[title] AI failed: {e}")

    words = text.strip().split()[:6]
    title = " ".join(words)[:50]
    return title if title else "New Chat"


def _chat_free(question: str, lang: str = "en") -> dict:
    """Answer using general AI knowledge (no paper context)."""
    if not _api_key:
        return {"answer": "GEMINI_API_KEY is not set."}

    try:
        model = genai.GenerativeModel(_MODEL_NAME)

        lang_note = (
            "Respond in Bengali (বাংলা)."
            if lang == "bn"
            else "Respond in English."
        )

        prompt = f"""You are an academic research assistant helping students and researchers.

Answer the following question accurately and clearly. Use your general knowledge.
Keep answers focused, well-structured, and academic in tone.

QUESTION:
{question}

{lang_note}
"""

        response = model.generate_content(prompt)
        return {"answer": response.text.strip()}

    except Exception as e:
        return {"answer": f"Error: {e}"}


# ─────────────────────────────────────────────────────────────
# Main chat endpoint
# ─────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(req: ChatRequest):
    """
    Send a question. Two modes:
      - 'paper': uses context_text as the sole source
      - 'free' : uses AI's general knowledge
    Saves both messages to history and stores the paper data
    so it can be reloaded from history later.
    """
    try:
        session_id = req.session_id

        # Auto-create session if none provided
        if not session_id:
            if req.paper_title:
                auto_title = req.paper_title
            elif req.context_text:
                auto_title = _generate_session_title(req.context_text, req.lang)
            else:
                auto_title = _generate_session_title(req.question, req.lang)

            # Build paper_data dict from request
            has_paper = bool(
                req.paper_full_text or req.paper_abstract or req.paper_title
            )
            paper_data = None
            if has_paper:
                paper_data = {
                    "title": req.paper_title,
                    "full_text": req.paper_full_text,
                    "abstract": req.paper_abstract,
                    "introduction": req.paper_introduction,
                    "methodology": req.paper_methodology,
                    "findings": req.paper_findings,
                    "limitations": req.paper_limitations,
                    "conclusion": req.paper_conclusion,
                    "key_points": req.paper_key_points,
                    "content_type": req.paper_content_type,
                }

            session = chat_history.create_session(
                title=auto_title,
                paper_title=req.paper_title,
                source="paper" if (req.mode == "paper" or req.context_text) else "free",
                paper_data=paper_data,
            )
            session_id = session["id"]

        # Save user message
        chat_history.append_message(session_id, "user", req.question)

        # Generate answer based on mode
        if req.mode == "paper":
            if not req.context_text or not req.context_text.strip():
                answer = "No paper loaded. Please upload or paste a paper first."
            else:
                result = chat_about_paper(req.context_text, req.question, req.lang)
                answer = result.get("answer", "No answer.")
        else:
            result = _chat_free(req.question, req.lang)
            answer = result.get("answer", "No answer.")

        # Save assistant message
        chat_history.append_message(session_id, "assistant", answer)

        return {
            "status": "success",
            "answer": answer,
            "session_id": session_id,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# History endpoints
# ─────────────────────────────────────────────────────────────

@router.get("/chat/history")
async def get_history_list():
    """Return summary of all chat sessions."""
    return {"sessions": chat_history.list_sessions()}


@router.get("/chat/history/{session_id}")
async def get_history_detail(session_id: str):
    """Return full session data."""
    session = chat_history.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/chat/history")
async def create_history_session(req: CreateSessionRequest):
    """Create a new empty session manually."""
    session = chat_history.create_session(
        title=req.title,
        paper_title=req.paper_title,
        source=req.source,
    )
    return session


@router.patch("/chat/history/{session_id}/title")
async def update_history_title(session_id: str, req: UpdateTitleRequest):
    """Update a session's title."""
    if not req.title or not req.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    success = chat_history.update_session_title(session_id, req.title.strip())
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "status": "success",
        "session_id": session_id,
        "title": req.title.strip(),
    }


@router.delete("/chat/history/{session_id}")
async def delete_history_session(session_id: str):
    """Delete one session."""
    ok = chat_history.delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success", "deleted": session_id}


@router.delete("/chat/history")
async def clear_history():
    """Delete all sessions."""
    count = chat_history.clear_all()
    return {"status": "success", "deleted_count": count}