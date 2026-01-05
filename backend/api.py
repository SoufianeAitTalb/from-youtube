from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio

from backend.job_manager import job_manager, JobStatus
from backend.tasks import (
    task_download_video, 
    task_cut_video, 
    task_crop_video, 
    task_subtitle_video
)

router = APIRouter()

# --- Request Models ---

class DownloadRequest(BaseModel):
    videoId: str
    outputDir: str 

class CutRequest(BaseModel):
    videoId: str
    videoFilePath: str
    replayedParts: List[dict]
    outputDir: str

class CropRequest(BaseModel):
    inputDir: str
    outputDir: str

class SubtitleRequest(BaseModel):
    inputDir: str
    outputDir: str
    modelSize: str = "medium"

# --- Endpoints ---

@router.post("/download")
async def start_download(req: DownloadRequest, background_tasks: BackgroundTasks):
    job_id = job_manager.create_job()
    background_tasks.add_task(job_manager.run_task, job_id, task_download_video, req.videoId, req.outputDir)
    return {"jobId": job_id}

@router.post("/cut")
async def start_cut(req: CutRequest, background_tasks: BackgroundTasks):
    job_id = job_manager.create_job()
    background_tasks.add_task(job_manager.run_task, job_id, task_cut_video, req.videoId, req.videoFilePath, req.replayedParts, req.outputDir)
    return {"jobId": job_id}

@router.post("/crop")
async def start_crop(req: CropRequest, background_tasks: BackgroundTasks):
    job_id = job_manager.create_job()
    background_tasks.add_task(job_manager.run_task, job_id, task_crop_video, req.inputDir, req.outputDir)
    return {"jobId": job_id}

@router.post("/subtitles")
async def start_subtitles(req: SubtitleRequest, background_tasks: BackgroundTasks):
    job_id = job_manager.create_job()
    background_tasks.add_task(job_manager.run_task, job_id, task_subtitle_video, req.inputDir, req.outputDir, req.modelSize)
    return {"jobId": job_id}

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "status": job.status,
        "progress": job.progress,
        "logs": job.logs,
        "result": job.result,
        "error": job.error
    }

async def log_stream_generator(job_id: str):
    """
    Streams Server-Sent Events (SSE) for job logs and status.
    """
    job = job_manager.get_job(job_id)
    if not job:
        yield f"event: error\ndata: Job not found\n\n"
        return

    last_log_idx = 0
    
    # Loop until job is done
    while True:
        # Send new logs
        current_logs = job.logs
        if len(current_logs) > last_log_idx:
            new_lines = current_logs[last_log_idx:]
            for line in new_lines:
                yield f"data: {line}\n\n"
            last_log_idx = len(current_logs)
            
        # Check completion
        if job.status in [JobStatus.SUCCESS, JobStatus.FAILED]:
            yield f"event: status\ndata: {job.status}\n\n"
            if job.status == JobStatus.FAILED:
                 yield f"event: error\ndata: {job.error}\n\n"
            await asyncio.sleep(1)
            break
            
        await asyncio.sleep(0.5)

@router.get("/jobs/{job_id}/stream")
async def stream_job_logs(job_id: str):
    return StreamingResponse(log_stream_generator(job_id), media_type="text/event-stream")
