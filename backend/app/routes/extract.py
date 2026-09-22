from fastapi import APIRouter
from pydantic import BaseModel

from app.services.extract_data import extract_paper_data

router = APIRouter()


class ExtractRequest(BaseModel):
    full_text: str
    lang: str = "en"


@router.post("/extract")
async def extract_single(req: ExtractRequest):
    return extract_paper_data(req.full_text, req.lang)
