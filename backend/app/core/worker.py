"""Production-grade asynchronous background job and scheduler system for Dhruva.AI.

CRITICAL INVARIANTS:
1. Long-running or heavy operations (analytics recalculation, retention updates, email dispatch)
   must NOT block the FastAPI HTTP event loop.
2. Background jobs must be IDEMPOTENT. Repeated execution must never corrupt academic truth.
3. Failures must be tracked and bounded with exponential backoff and dead-letter monitoring.
"""

import asyncio
from datetime import datetime, timezone
from typing import Callable, Dict, Any, List, Optional
from dataclasses import dataclass, field
import uuid
from app.core.logging import logger
from app.core.config import settings


@dataclass
class JobRecord:
    id: str
    name: str
    payload: Dict[str, Any]
    status: str  # PENDING, RUNNING, COMPLETED, FAILED
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempts: int = 0
    max_retries: int = 3
    error: Optional[str] = None


class BackgroundJobWorker:
    """In-process and queue-capable background job worker for Dhruva.AI."""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._handlers: Dict[str, Callable] = {}
        self._job_history: List[JobRecord] = []
        self._worker_task: Optional[asyncio.Task] = None
        self._retry_tasks: set[asyncio.Task] = set()
        self._is_running = False

    def register_handler(self, job_name: str, handler: Callable) -> None:
        """Registers an asynchronous job processing function."""
        self._handlers[job_name] = handler
        logger.info(f"Registered background job handler for '{job_name}'")

    async def enqueue(self, job_name: str, payload: Dict[str, Any], max_retries: int = 3) -> str:
        """Enqueues an idempotent background task for asynchronous execution."""
        job_id = str(uuid.uuid4())
        record = JobRecord(
            id=job_id,
            name=job_name,
            payload=payload,
            status="PENDING",
            created_at=datetime.now(timezone.utc),
            max_retries=max_retries,
        )
        self._job_history.append(record)
        if len(self._job_history) > 500:
            self._job_history.pop(0)  # Bound memory history

        await self._queue.put(record)
        logger.info(f"Enqueued background job '{job_name}' [id={job_id}]")
        return job_id

    async def _worker_loop(self) -> None:
        """Continuously pulls and executes jobs from the FIFO queue."""
        logger.info("Background job worker loop started.")
        while self._is_running:
            try:
                record: JobRecord = await self._queue.get()
                record.started_at = datetime.now(timezone.utc)
                record.status = "RUNNING"
                record.attempts += 1

                handler = self._handlers.get(record.name)
                if not handler:
                    record.status = "FAILED"
                    record.error = f"No handler registered for job type '{record.name}'"
                    record.completed_at = datetime.now(timezone.utc)
                    self._queue.task_done()
                    continue

                try:
                    await handler(record.payload)
                    record.status = "COMPLETED"
                    record.completed_at = datetime.now(timezone.utc)
                    logger.info(f"Successfully processed job '{record.name}' [id={record.id}]")
                except Exception as exc:
                    logger.error(f"Job '{record.name}' [id={record.id}] failed (attempt {record.attempts}): {exc}")
                    if record.attempts < record.max_retries:
                        # Re-enqueue for retry asynchronously without blocking the consumer loop
                        record.status = "PENDING"
                        backoff_delay = 2 ** record.attempts

                        async def _delayed_retry(rec: JobRecord, delay: float) -> None:
                            try:
                                await asyncio.sleep(delay)
                                if self._is_running:
                                    await self._queue.put(rec)
                            except asyncio.CancelledError:
                                pass

                        task = asyncio.create_task(_delayed_retry(record, backoff_delay))
                        self._retry_tasks.add(task)
                        task.add_done_callback(self._retry_tasks.discard)
                    else:
                        record.status = "FAILED"
                        record.error = str(exc)
                        record.completed_at = datetime.now(timezone.utc)

                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in background job worker: {e}")

    def start(self) -> None:
        """Starts background worker if feature enabled."""
        if not settings.FEATURE_BACKGROUND_WORKERS_ENABLED:
            logger.info("Background job worker disabled by feature flag.")
            return

        if not self._is_running:
            if not self._handlers:
                try:
                    from app.core.job_handlers import register_all_job_handlers
                    register_all_job_handlers(self)
                except Exception as reg_err:
                    logger.warning(f"Failed to auto-register background job handlers: {reg_err}")

            self._is_running = True
            self._worker_task = asyncio.create_task(self._worker_loop())

    async def stop(self) -> None:
        """Gracefully halts worker."""
        self._is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        for task in list(self._retry_tasks):
            task.cancel()
        if self._retry_tasks:
            await asyncio.gather(*self._retry_tasks, return_exceptions=True)
            self._retry_tasks.clear()

    def get_metrics(self) -> dict:
        """Returns observability metrics for job executions."""
        total = len(self._job_history)
        completed = sum(1 for j in self._job_history if j.status == "COMPLETED")
        failed = sum(1 for j in self._job_history if j.status == "FAILED")
        running = sum(1 for j in self._job_history if j.status == "RUNNING")
        pending = sum(1 for j in self._job_history if j.status == "PENDING")

        return {
            "is_running": self._is_running,
            "total_jobs": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "queue_depth": pending,
        }

    def get_recent_jobs(self, limit: int = 20) -> List[dict]:
        """Returns recent execution summaries."""
        return [
            {
                "id": j.id,
                "name": j.name,
                "status": j.status,
                "attempts": j.attempts,
                "created_at": j.created_at.isoformat(),
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                "error": j.error,
            }
            for j in reversed(self._job_history[-limit:])
        ]


job_worker = BackgroundJobWorker()
