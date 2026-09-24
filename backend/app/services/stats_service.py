"""
Statistics Service — aggregates data from all JSON history files
to power the Statistics Dashboard.

Reads from:
  - review_history.json
  - chat_history.json
  - quiz_history.json
  - presentation_history.json

Handles both JSON formats:
  - Direct list:    [ {...}, {...} ]
  - Dict with list: { "sessions": [ {...}, {...} ] }
"""
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta


# ─── Paths to history files ───
_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data'
)

_REVIEW_FILE = os.path.join(_DATA_DIR, 'review_history.json')
_CHAT_FILE = os.path.join(_DATA_DIR, 'chat_history.json')
_QUIZ_FILE = os.path.join(_DATA_DIR, 'quiz_history.json')
_PRESENTATION_FILE = os.path.join(_DATA_DIR, 'presentation_history.json')


# ═════════════════════════════════════════════════════════════
# Safe JSON loader — handles both list and dict-with-list
# ═════════════════════════════════════════════════════════════

def _load_json(path):
    """
    Safely load a JSON file and return a list of records.

    Handles BOTH formats:
      1. Direct list:    [ {...}, {...} ]
      2. Dict with list: { "sessions": [ {...}, {...} ] }

    Returns an empty list on any error.
    """
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Case 1: Direct list
        if isinstance(data, list):
            return data

        # Case 2: Dict — look for known wrapper keys
        if isinstance(data, dict):
            for key in ('sessions', 'items', 'data', 'records', 'chats', 'quizzes'):
                value = data.get(key)
                if isinstance(value, list):
                    return value

            # Fallback: return first list value found
            for value in data.values():
                if isinstance(value, list):
                    return value

        # Anything else: empty list
        return []

    except (json.JSONDecodeError, OSError):
        return []


def _parse_date(date_str):
    """Parse 'YYYY-MM-DD HH:MM:SS' to date object, return None on error."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return None


# ═════════════════════════════════════════════════════════════
# Aggregation functions
# ═════════════════════════════════════════════════════════════

def get_overview_stats() -> dict:
    """High-level overview counts from all histories."""
    reviews = _load_json(_REVIEW_FILE)
    chats = _load_json(_CHAT_FILE)
    quizzes = _load_json(_QUIZ_FILE)
    presentations = _load_json(_PRESENTATION_FILE)

    # Count papers across all reviews
    total_papers = 0
    total_included = 0
    for r in reviews:
        papers = r.get('papers', [])
        total_papers += len(papers)
        counts = r.get('counts', {})
        total_included += counts.get('total_included', 0)

    return {
        'reviews': len(reviews),
        'chats': len(chats),
        'quizzes': len(quizzes),
        'presentations': len(presentations),
        'total_papers': total_papers,
        'total_included': total_included,
    }


def get_decision_distribution() -> dict:
    """Aggregate Include/Exclude/Maybe counts across all reviews."""
    reviews = _load_json(_REVIEW_FILE)
    dist = {'Include': 0, 'Exclude': 0, 'Maybe': 0}

    for r in reviews:
        counts = r.get('counts', {})
        dist['Include'] += counts.get('total_included', 0)
        dist['Exclude'] += counts.get('irrelevant_excluded', 0)
        dist['Maybe'] += counts.get('maybe', 0)

    return dist


def get_papers_by_year() -> list:
    """Bar chart data: papers per year across all reviews."""
    reviews = _load_json(_REVIEW_FILE)
    year_counts = Counter()

    for r in reviews:
        for p in r.get('papers', []):
            year = p.get('year')
            if year:
                try:
                    year_counts[int(year)] += 1
                except (ValueError, TypeError):
                    continue

    # Sort by year
    sorted_years = sorted(year_counts.items())
    return [{'year': str(y), 'count': c} for y, c in sorted_years]


def get_quiz_scores() -> dict:
    """Line chart data: quiz scores over time."""
    quizzes = _load_json(_QUIZ_FILE)
    scores = []

    for q in quizzes:
        score = q.get('score')
        if not score:
            continue
        try:
            total = int(score.get('total', 0))
            correct = int(score.get('correct', 0))
            if total > 0:
                percentage = round((correct / total) * 100)
                scores.append({
                    'date': (q.get('created_at', '') or '')[:10],
                    'title': q.get('title', 'Quiz'),
                    'percentage': percentage,
                })
        except (ValueError, TypeError):
            continue

    avg_score = 0
    if scores:
        avg_score = round(sum(s['percentage'] for s in scores) / len(scores), 1)

    return {
        'history': scores[-20:],   # Last 20 quizzes
        'average': avg_score,
        'total': len(scores),
    }


def get_activity_timeline(days: int = 30) -> list:
    """
    Activity timeline: sessions per day for last N days.
    Combines all features (reviews, chats, quizzes, presentations).
    """
    today = datetime.now().date()
    start = today - timedelta(days=days - 1)

    # Initialize all days to 0
    daily_counts = defaultdict(int)
    for i in range(days):
        day = start + timedelta(days=i)
        daily_counts[day.isoformat()] = 0

    # Aggregate all histories
    all_sessions = (
        _load_json(_REVIEW_FILE) +
        _load_json(_CHAT_FILE) +
        _load_json(_QUIZ_FILE) +
        _load_json(_PRESENTATION_FILE)
    )

    for s in all_sessions:
        dt = _parse_date(s.get('created_at', ''))
        if dt and dt.date() >= start:
            key = dt.date().isoformat()
            if key in daily_counts:
                daily_counts[key] += 1

    # Convert to list
    result = []
    for i in range(days):
        day = start + timedelta(days=i)
        result.append({
            'date': day.isoformat(),
            'count': daily_counts[day.isoformat()],
        })
    return result


def get_top_keywords(limit: int = 10) -> list:
    """Top keywords from review searches."""
    reviews = _load_json(_REVIEW_FILE)
    keywords = Counter()

    for r in reviews:
        kw = (r.get('keyword') or '').strip().lower()
        if kw:
            keywords[kw] += 1

    return [
        {'keyword': k, 'count': c}
        for k, c in keywords.most_common(limit)
    ]


# ═════════════════════════════════════════════════════════════
# Main entry point
# ═════════════════════════════════════════════════════════════

def get_full_stats() -> dict:
    """Aggregate everything for the dashboard."""
    return {
        'overview': get_overview_stats(),
        'decisions': get_decision_distribution(),
        'papers_by_year': get_papers_by_year(),
        'quiz_scores': get_quiz_scores(),
        'activity': get_activity_timeline(days=30),
        'top_keywords': get_top_keywords(limit=10),
    }