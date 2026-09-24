from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routes import chat, extract, pipeline, quiz, report, screen, search, upload
from app.routes import presentation
from app.routes import review_history
from app.routes import stats  # ← NEW

app = FastAPI(title="ReviewMind API")

# ─── CORS setup ───
# Local dev origins are always allowed. In production, the deployed
# frontend URL is supplied via the FRONTEND_URL environment variable
# (set on Render). allow_origin_regex covers Netlify preview URLs.
_local_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
_prod_origin = os.getenv("FRONTEND_URL", "").strip()
_allow_origins = _local_origins + ([_prod_origin] if _prod_origin else [])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    # Matches Netlify deploy-preview subdomains (e.g. *.netlify.app)
    # and any https domain passed in FRONTEND_URL.
    allow_origin_regex=r"https://.*\.netlify\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(screen.router, prefix="/api", tags=["screen"])
app.include_router(extract.router, prefix="/api", tags=["extract"])
app.include_router(report.router, prefix="/api", tags=["report"])
app.include_router(pipeline.router, prefix="/api", tags=["pipeline"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(quiz.router, prefix="/api", tags=["quiz"])
app.include_router(presentation.router, prefix="/api", tags=["presentation"])
app.include_router(review_history.router, prefix="/api", tags=["review-history"])
app.include_router(stats.router, prefix="/api", tags=["statistics"])  # ← NEW


@app.get("/")
async def root():
    return {"status": "ok", "message": "ReviewMind API is running"}