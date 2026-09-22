from fastapi import APIRouter, HTTPException, Query

from app.services.semantic_scholar import search_semantic_scholar

router = APIRouter()


@router.get("/search")
async def search_papers(
    keyword: str = Query(..., min_length=2),
    year_min: int = Query(2000, ge=1900),
    year_max: int = Query(2030, le=2100),
):
    """Searches Semantic Scholar for papers matching a keyword."""
    try:
        papers = search_semantic_scholar(keyword, year_min, year_max)
        return {"status": "success", "count": len(papers), "papers": papers}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Semantic Scholar lookup failed: {e}")
