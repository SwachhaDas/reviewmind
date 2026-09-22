"""
Pipeline Tracker — tracks live progress of a running pipeline.
Stores job status in memory, keyed by a unique job ID.
Frontend polls GET /api/pipeline/status/{job_id} to show progress.
"""
import time
from typing import Dict, Any


_jobs: Dict[str, Dict[str, Any]] = {}


def create_job() -> str:
    job_id = f"job_{int(time.time() * 1000)}"
    _jobs[job_id] = {
        "job_id": job_id,
        "status": "starting",
        "stage": "init",
        "stage_label": "Initializing...",
        "progress_current": 0,
        "progress_total": 0,
        "current_item": "",
        "started_at": time.time(),
        "elapsed": 0.0,
        "counts": {},
        "result": None,
        "error": None,
    }
    return job_id


def update_job(job_id: str, **kwargs):
    if job_id not in _jobs:
        return
    _jobs[job_id].update(kwargs)
    _jobs[job_id]["elapsed"] = round(time.time() - _jobs[job_id]["started_at"], 1)


def get_job(job_id: str) -> dict:
    if job_id not in _jobs:
        return {"error": "Job not found", "job_id": job_id}
    return _jobs[job_id]


def finish_job(job_id: str, result: dict):
    if job_id not in _jobs:
        return
    _jobs[job_id]["status"] = "complete"
    _jobs[job_id]["stage"] = "done"
    _jobs[job_id]["stage_label"] = "✅ Pipeline complete!"
    _jobs[job_id]["result"] = result
    _jobs[job_id]["counts"] = result.get("counts", {})
    _jobs[job_id]["elapsed"] = round(time.time() - _jobs[job_id]["started_at"], 1)


def fail_job(job_id: str, error: str):
    if job_id not in _jobs:
        return
    _jobs[job_id]["status"] = "failed"
    _jobs[job_id]["error"] = error
    _jobs[job_id]["elapsed"] = round(time.time() - _jobs[job_id]["started_at"], 1)