from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from app.services.coordinator_agent import run_pipeline
from app.services.pipeline_tracker import (
    create_job, get_job, update_job, finish_job, fail_job,
)

router = APIRouter()


class PipelineRequest(BaseModel):
    keyword: str
    criteria: str
    lang: str = "en"
    year_min: int = 2000
    year_max: int = 2030


@router.post("/pipeline")
async def run_full_pipeline(req: PipelineRequest, background: BackgroundTasks):
    """Start the pipeline in the background and return a job_id."""
    job_id = create_job()
    background.add_task(_run_pipeline_task, job_id, req)
    return {"status": "started", "job_id": job_id}


@router.get("/pipeline/status/{job_id}")
async def pipeline_status(job_id: str):
    """Frontend polls this endpoint for live progress."""
    return get_job(job_id)


def _run_pipeline_task(job_id: str, req: PipelineRequest):
    """Runs the pipeline; updates tracker at each stage."""
    try:
        def on_progress(stage, label, current=0, total=0, item=""):
            update_job(
                job_id,
                status="running",
                stage=stage,
                stage_label=label,
                progress_current=current,
                progress_total=total,
                current_item=item or "",  # No character limit
            )

        result = run_pipeline(
            keyword=req.keyword,
            criteria=req.criteria,
            lang=req.lang,
            year_min=req.year_min,
            year_max=req.year_max,
            on_progress=on_progress,
        )
        finish_job(job_id, result)
    except Exception as e:
        import traceback
        print(f"[pipeline] Error: {e}")
        traceback.print_exc()
        fail_job(job_id, str(e))