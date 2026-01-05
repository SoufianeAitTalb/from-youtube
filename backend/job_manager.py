import asyncio
import uuid
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import sys
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

@dataclass
class Job:
    id: str
    status: JobStatus = JobStatus.IDLE
    progress: int = 0
    logs: List[str] = field(default_factory=list)
    result: Optional[Any] = None
    error: Optional[str] = None
    _task: Optional[asyncio.Task] = None

    def add_log(self, message: str):
        self.logs.append(message)
        # Keep logs manageable, maybe limit to last 1000 lines if needed
        if len(self.logs) > 5000:
             self.logs = self.logs[-5000:]

class JobManager:
    def __init__(self):
        self.jobs: Dict[str, Job] = {}

    def create_job(self) -> str:
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = Job(id=job_id)
        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        return self.jobs.get(job_id)

    def update_job_status(self, job_id: str, status: JobStatus):
        if job := self.jobs.get(job_id):
            job.status = status

    def update_job_progress(self, job_id: str, progress: int):
        if job := self.jobs.get(job_id):
            job.progress = max(0, min(100, progress))

    def add_job_log(self, job_id: str, message: str):
        if job := self.jobs.get(job_id):
            job.add_log(message)

    def fail_job(self, job_id: str, error: str):
        if job := self.jobs.get(job_id):
            job.status = JobStatus.FAILED
            job.error = error
            job.add_log(f"ERROR: {error}")

    def complete_job(self, job_id: str, result: Any):
        if job := self.jobs.get(job_id):
            job.status = JobStatus.SUCCESS
            job.progress = 100
            job.result = result
            job.add_log("Job completed successfully.")

    async def run_task(self, job_id: str, func, *args, **kwargs):
        """
        Runs a function in a separate thread (for blocking IO) or directly if async.
        Captures stdout/stderr to job logs.
        """
        job = self.jobs.get(job_id)
        if not job:
            return

        job.status = JobStatus.RUNNING
        job.progress = 0
        job.add_log(f"Starting job {job_id}...")

        try:
            # We need to capture stdout/stderr from the executed function
            # Since existing scripts use 'print', we can redirect stdout/stderr
            # BUT, redirecting global stdout/stderr is risky in async app.
            # Instead, we will rely on the called function to be wrapped or
            # we accept that we might miss some prints unless we modify the scripts to accept a logger.
            # For this PoC, we will try to just run it and catch errors. 
            
            # To capture prints, we'd ideally run in a subprocess, but that's complex to manage state.
            # We will patch 'builtins.print' context manager slightly risky or just wrap execution.
            # Let's just run it for now.
            
            if asyncio.iscoroutinefunction(func):
                result = await func(self, job_id, *args, **kwargs)
            else:
                # Run sync function in thread pool
                 result = await asyncio.to_thread(func, self, job_id, *args, **kwargs)

            self.complete_job(job_id, result)
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            self.fail_job(job_id, str(e))

# Global instance
job_manager = JobManager()
