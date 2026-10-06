"""Execution handlers for background operational maintenance tasks.

CRITICAL INVARIANTS:
1. Safe to retry: handlers must not corrupt state if executed multiple times.
2. Idempotent: repetitive execution yields identical consistent state.
3. Tenant-isolated: operations are strictly bound by institution boundaries.
4. Resilient: failure in one institution must not abort other institutions.
5. Observable: all outcomes and pruning metrics are logged.
"""

from typing import Dict, Any, Optional
from app.core.logging import logger
from app.core.database import AsyncSessionLocal
from app.domains.identity.service import identity_service
from app.domains.institutional_intelligence.service import InstitutionalIntelligenceService
from app.core.worker import job_worker, BackgroundJobWorker


async def handle_cleanup_expired_sessions(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Prunes expired authentication sessions, password resets, and verification tokens.
    
    Safe to retry, strictly idempotent, and tenant-aware.
    """
    logger.info(f"Executing background job 'cleanup_expired_sessions' [payload={payload}]")
    institution_id = payload.get("institution_id") if isinstance(payload, dict) else None

    async with AsyncSessionLocal() as session:
        try:
            result = await identity_service.cleanup_expired_sessions(
                db=session,
                institution_id=institution_id,
            )
            logger.info(f"Successfully finished 'cleanup_expired_sessions': {result}")
            return result
        except Exception as exc:
            logger.error(f"Error executing 'cleanup_expired_sessions': {exc}")
            raise


async def handle_generate_analytics_snapshots(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generates point-in-time cached aggregate analytics snapshots for institutions and departments.
    
    Safe to retry, strictly idempotent, and tenant-aware.
    """
    logger.info(f"Executing background job 'generate_analytics_snapshots' [payload={payload}]")
    institution_id = payload.get("institution_id") if isinstance(payload, dict) else None

    async with AsyncSessionLocal() as session:
        try:
            snapshots = await InstitutionalIntelligenceService.generate_analytics_snapshots(
                db=session,
                institution_id=institution_id,
            )
            result = {
                "snapshots_created": len(snapshots),
            }
            logger.info(f"Successfully finished 'generate_analytics_snapshots': {result}")
            return result
        except Exception as exc:
            logger.error(f"Error executing 'generate_analytics_snapshots': {exc}")
            raise


async def handle_remediation_signal_scan(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Scans student population for academic deficiency signals and creates intervention alerts.
    
    Safe to retry, strictly idempotent through signal deduplication, and tenant-isolated.
    """
    logger.info(f"Executing background job 'remediation_signal_scan' [payload={payload}]")
    institution_id = payload.get("institution_id") if isinstance(payload, dict) else None

    async with AsyncSessionLocal() as session:
        try:
            results = await InstitutionalIntelligenceService.scan_all_institutions_for_signals(
                db=session,
                institution_id=institution_id,
            )
            total_signals = sum(results.values())
            result = {
                "institutions_scanned": len(results),
                "total_signals_detected": total_signals,
                "signals_by_institution": results,
            }
            logger.info(f"Successfully finished 'remediation_signal_scan': {result}")
            return result
        except Exception as exc:
            logger.error(f"Error executing 'remediation_signal_scan': {exc}")
            raise


def register_all_job_handlers(worker: Optional[BackgroundJobWorker] = None) -> None:
    """Registers all operational maintenance handlers with the target background job worker."""
    target_worker = worker or job_worker
    target_worker.register_handler("cleanup_expired_sessions", handle_cleanup_expired_sessions)
    target_worker.register_handler("generate_analytics_snapshots", handle_generate_analytics_snapshots)
    target_worker.register_handler("remediation_signal_scan", handle_remediation_signal_scan)
    logger.info("All background maintenance job handlers successfully registered.")
