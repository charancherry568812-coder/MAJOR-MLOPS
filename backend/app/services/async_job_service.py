"""Asynchronous Background Job Engine for Long-Running MLOps & Banking Tasks."""

from __future__ import annotations

import concurrent.futures
import json
import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.async_job import AsyncJob

logger = logging.getLogger("AsyncJobManager")


class AsyncJobManager:
    """Thread-pool based background worker with progress tracking and database persistence."""

    def __init__(self, max_workers: int = 8):
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self._running_jobs: Dict[str, concurrent.futures.Future] = {}

    def submit_job(
        self,
        job_type: str,
        title: str,
        task_fn: Callable[..., Any],
        *args,
        created_by: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Create a new AsyncJob record and dispatch to thread pool worker."""
        db = SessionLocal()
        try:
            job = AsyncJob(
                job_type=job_type,
                title=title,
                status="QUEUED",
                progress_percent=0.0,
                current_step="Task submitted to worker queue",
                created_by=created_by,
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            job_id = job.id
        finally:
            db.close()

        def _worker_wrapper(jid: str):
            worker_db = SessionLocal()
            try:
                j = worker_db.query(AsyncJob).filter(AsyncJob.id == jid).first()
                if j:
                    j.status = "RUNNING"
                    j.started_at = datetime.now(timezone.utc)
                    j.current_step = "Executing task"
                    worker_db.commit()

                # Execute target function
                def update_progress(pct: float, step_msg: str):
                    w_db = SessionLocal()
                    try:
                        w_j = w_db.query(AsyncJob).filter(AsyncJob.id == jid).first()
                        if w_j:
                            w_j.progress_percent = pct
                            w_j.current_step = step_msg
                            w_db.commit()
                    finally:
                        w_db.close()

                result = task_fn(progress_cb=update_progress, *args, **kwargs)

                # Mark Completed
                j = worker_db.query(AsyncJob).filter(AsyncJob.id == jid).first()
                if j:
                    j.status = "COMPLETED"
                    j.progress_percent = 100.0
                    j.current_step = "Completed successfully"
                    j.completed_at = datetime.now(timezone.utc)
                    j.result_json = json.dumps(result) if result else "{}"
                    worker_db.commit()

            except Exception as e:
                logger.error(f"Async Job {jid} failed: {e}")
                j = worker_db.query(AsyncJob).filter(AsyncJob.id == jid).first()
                if j:
                    j.status = "FAILED"
                    j.current_step = f"Error: {str(e)[:200]}"
                    j.error_message = str(e)
                    j.completed_at = datetime.now(timezone.utc)
                    worker_db.commit()
            finally:
                worker_db.close()
                self._running_jobs.pop(jid, None)

        future = self._executor.submit(_worker_wrapper, job_id)
        self._running_jobs[job_id] = future
        return job_id


async_job_manager = AsyncJobManager()
