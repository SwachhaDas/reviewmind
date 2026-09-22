from fastapi import APIRouter
from pydantic import BaseModel

from app.services.gemini_client import quality_check_decision, screen_paper

router = APIRouter()


class ScreenRequest(BaseModel):
    abstract: str
    criteria: str
    lang: str = "en"


class ScreenBatchRequest(BaseModel):
    papers: list[dict]  # each dict needs at least an "abstract" key
    criteria: str
    lang: str = "en"


@router.post("/screen")
async def screen_single(req: ScreenRequest):
    first_pass = screen_paper(req.abstract, req.criteria, req.lang)
    return quality_check_decision(req.abstract, req.criteria, first_pass, req.lang)


@router.post("/screen-batch")
async def screen_batch(req: ScreenBatchRequest):
    """Screens multiple papers at once (Screening Agent + Quality-Check Agent)."""
    results = []
    for paper in req.papers:
        abstract = paper.get("abstract", "")
        first_pass = screen_paper(abstract, req.criteria, req.lang)
        decision = quality_check_decision(abstract, req.criteria, first_pass, req.lang)
        results.append({**paper, **decision})
    return {"status": "success", "count": len(results), "papers": results}
