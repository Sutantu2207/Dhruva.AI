"""Periodic job scheduler for automated academic maintenance routines.

SCHEDULED CADENCE (Timezone: Asia/Kolkata):
1. Expired Token & Session Pruning: Periodic (hourly)
2. Retention Decay & SM-2 Review Prioritization: Daily
3. Adaptive Remediation Deficit Ingestion: Daily
4. Institutional Analytics Snapshots: Nightly

CRITICAL INVARIANT: The scheduler only triggers deterministic workflows.
It NEVER alters academic truth arbitrarily.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.core.logging import logger
from app.core.config import settings
from app.core.worker import job_worker


class MaintenanceScheduler:
    """Lightweight in-process cron scheduler for automated operational maintenance."""

    def __init__(self):
        self._is_running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._last_run_map: Dict[str, datetime] = {}

    async def _scheduler_loop(self) -> None:
        """Periodic heartbeat checking intervals."""
        logger.info("Maintenance scheduler heartbeat started.")
        while self._is_running:
            try:
                now = datetime.now(timezone.utc)

                # 1. Periodic cleanup task (every hour)
                last_cleanup = self._last_run_map.get("cleanup")
                if not last_cleanup or (now - last_cleanup).total_seconds() > 3600:
                    await job_worker.enqueue("cleanup_expired_sessions", {"triggered_by": "scheduler"})
                    self._last_run_map["cleanup"] = now

                # 2. Daily analytics snapshot check (every 24 hours)
                last_analytics = self._last_run_map.get("analytics_snapshot")
                if not last_analytics or (now - last_analytics).total_seconds() > 86400:
                    await job_worker.enqueue("generate_analytics_snapshots", {"triggered_by": "scheduler"})
                    self._last_run_map["analytics_snapshot"] = now

                # 3. Daily adaptive remediation check (every 24 hours)
                last_remediation = self._last_run_map.get("remediation_scan")
                if not last_remediation or (now - last_remediation).total_seconds() > 86400:
                    await job_worker.enqueue("remediation_signal_scan", {"triggered_by": "scheduler"})
                    self._last_run_map["remediation_scan"] = now

                # Sleep 60 seconds before next interval check
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in maintenance scheduler loop: {e}")
                await asyncio.sleep(60)

    def start(self) -> None:
        """Starts scheduler if worker feature enabled."""
        if not settings.FEATURE_BACKGROUND_WORKERS_ENABLED:
            logger.info("Maintenance scheduler disabled by feature flag.")
            return

        if not self._is_running:
            self._is_running = True
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())

    async def stop(self) -> None:
        """Gracefully halts scheduler."""
        self._is_running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

    def get_status(self) -> dict:
        """Returns scheduler observability status."""
        return {
            "is_running": self._is_running,
            "timezone": "Asia/Kolkata (stored UTC)",
            "scheduled_tasks": [
                {
                    "name": "cleanup_expired_sessions",
                    "interval": "hourly",
                    "last_run": self._last_run_map.get("cleanup", None),
                },
                {
                    "name": "generate_analytics_snapshots",
                    "interval": "daily",
                    "last_run": self._last_run_map.get("analytics_snapshot", None),
                },
                {
                    "name": "remediation_signal_scan",
                    "interval": "daily",
                    "last_run": self._last_run_map.get("remediation_scan", None),
                },
            ],
        }


scheduler = MaintenanceScheduler()
