"""
Statistics Routes — provides aggregated data for the Statistics Dashboard.

Endpoint:
  GET /api/stats/summary — returns all aggregated statistics
"""
from fastapi import APIRouter

from app.services.stats_service import get_full_stats


# NOTE: prefix is /stats (NOT /api/stats) because main.py
# already adds prefix="/api" when registering this router.
router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("/summary")
async def stats_summary():
    """
    Returns aggregated statistics across all feature histories:

      - overview: high-level counts (reviews, chats, quizzes, etc.)
      - decisions: Include/Exclude/Maybe distribution
      - papers_by_year: bar chart data
      - quiz_scores: average + score history
      - activity: 30-day session activity timeline
      - top_keywords: most searched topics
    """
    return get_full_stats()