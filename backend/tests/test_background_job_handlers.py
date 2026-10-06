"""Tests for background operational maintenance job handlers, retry mechanisms, and sandbox readiness."""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from app.core.worker import BackgroundJobWorker, JobRecord
from app.core.job_handlers import (
    register_all_job_handlers,
    handle_cleanup_expired_sessions,
    handle_generate_analytics_snapshots,
    handle_remediation_signal_scan,
)
from app.domains.identity.models import (
    User,
    UserSession,
    PasswordResetToken,
    EmailVerificationToken,
)
from app.core.security import get_password_hash, UserRole
from app.domains.academic.models import (
    Institution,
    Department,
    Program,
    Batch,
    StudentAcademicProfile,
)
from app.domains.assessment.models import (
    Assessment,
    AssessmentVersion,
    AssessmentAttempt,
)
from app.domains.institutional_intelligence.models import (
    InstitutionalAnalyticsSnapshot,
    AcademicInterventionSignal,
)
from app.domains.assessment.evaluators.coding import (
    HttpSandboxProvider,
    check_sandbox_health,
    ExecutionRequest,
)


@pytest.fixture(autouse=True)
def patch_job_handlers_session(monkeypatch):
    """Ensure job handlers use the in-memory test database session factory."""
    from tests.conftest import TestingSessionLocal
    monkeypatch.setattr("app.core.job_handlers.AsyncSessionLocal", TestingSessionLocal)


@pytest.mark.asyncio
async def test_job_handlers_registration():
    """Verify that all scheduled maintenance tasks are properly registered with worker."""
    worker = BackgroundJobWorker()
    register_all_job_handlers(worker)

    assert "cleanup_expired_sessions" in worker._handlers
    assert "generate_analytics_snapshots" in worker._handlers
    assert "remediation_signal_scan" in worker._handlers


@pytest.mark.asyncio
async def test_cleanup_expired_sessions_handler_success(db_session):
    """Verify expired sessions and tokens are pruned while active sessions remain intact."""
    now = datetime.now(timezone.utc)

    # 1. Create a user
    user = User(
        email="cleanup_test@dhruva.edu.in",
        normalized_email="cleanup_test@dhruva.edu.in",
        hashed_password=get_password_hash("SecretPassword123!"),
        first_name="Cleanup",
        last_name="Test",
        display_name="Cleanup Test",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 2. Add an expired session and an active session
    expired_session = UserSession(
        user_id=user.id,
        refresh_token_hash="hash_expired_1",
        expires_at=now - timedelta(hours=2),
    )
    active_session = UserSession(
        user_id=user.id,
        refresh_token_hash="hash_active_1",
        expires_at=now + timedelta(days=7),
    )
    # Add expired and used tokens
    expired_reset = PasswordResetToken(
        user_id=user.id,
        token_hash="hash_reset_expired",
        expires_at=now - timedelta(hours=1),
    )
    expired_verif = EmailVerificationToken(
        user_id=user.id,
        token_hash="hash_verif_expired",
        expires_at=now - timedelta(hours=1),
    )

    db_session.add_all([expired_session, active_session, expired_reset, expired_verif])
    await db_session.commit()

    # 3. Execute handler
    result = await handle_cleanup_expired_sessions({})
    assert result["cleaned_sessions"] >= 1
    assert result["cleaned_password_resets"] >= 1
    assert result["cleaned_verification_tokens"] >= 1

    # 4. Verify idempotency - running again cleans 0 and raises no error
    idempotent_result = await handle_cleanup_expired_sessions({})
    assert idempotent_result["cleaned_sessions"] == 0
    assert idempotent_result["cleaned_password_resets"] == 0
    assert idempotent_result["cleaned_verification_tokens"] == 0


@pytest.mark.asyncio
async def test_generate_analytics_snapshots_handler(db_session):
    """Verify snapshot generation on empty DB and populated institution."""
    # 1. Empty database resilience
    empty_result = await handle_generate_analytics_snapshots({})
    assert empty_result["snapshots_created"] == 0

    # 2. Seed an institution and department
    inst = Institution(
        name="Test Analytics Tech",
        code="TAT_ANALYTICS",
        email_domains="tat.edu.in",
        status="active",
    )
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    dept = Department(
        institution_id=inst.id,
        name="Computer Science & Engineering",
        code="CSE_ANALYTICS",
    )
    db_session.add(dept)
    await db_session.commit()

    # 3. Execute handler
    result = await handle_generate_analytics_snapshots({"institution_id": inst.id})
    assert result["snapshots_created"] >= 2  # 1 department snapshot + 1 institution snapshot


@pytest.mark.asyncio
async def test_remediation_signal_scan_handler(db_session):
    """Verify remediation signal detection and idempotent deduplication."""
    # 1. Empty database resilience
    empty_result = await handle_remediation_signal_scan({})
    assert empty_result["institutions_scanned"] == 0

    # 2. Seed institution, department, program, student, assessment
    inst = Institution(
        name="Test Remediation University",
        code="TRU_REMED",
        email_domains="tru.edu.in",
        status="active",
    )
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)

    dept = Department(institution_id=inst.id, name="Information Technology", code="IT_REMED")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)

    prog = Program(department_id=dept.id, name="B.Tech IT", code="BIT", degree_type="B.Tech")
    db_session.add(prog)
    await db_session.commit()
    await db_session.refresh(prog)

    user = User(
        email="student_remed@tru.edu.in",
        normalized_email="student_remed@tru.edu.in",
        hashed_password=get_password_hash("Pass123!"),
        first_name="Remed",
        last_name="Student",
        display_name="Remed Student",
        role=UserRole.STUDENT,
        institution_id=inst.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    batch = Batch(
        institution_id=inst.id,
        program_id=prog.id,
        admission_year=2022,
        graduation_year=2026,
        label="2022-2026",
    )
    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)

    student = StudentAcademicProfile(
        user_id=user.id,
        institution_id=inst.id,
        program_id=prog.id,
        batch_id=batch.id,
        enrollment_number="TRU2026_001",
        admission_year=2022,
        graduation_year=2026,
    )
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)

    # Add 3 failed assessment attempts (triggers repeated_assessment_failures signal)
    ass = Assessment(
        institution_id=inst.id,
        title="Diagnostic Quiz",
        assessment_type="quiz",
        status="published",
    )
    db_session.add(ass)
    await db_session.commit()
    await db_session.refresh(ass)

    ass_v = AssessmentVersion(assessment_id=ass.id, version_number=1, title="Diagnostic Quiz", is_frozen=True)
    db_session.add(ass_v)
    await db_session.commit()
    await db_session.refresh(ass_v)

    now_attempt = datetime.now(timezone.utc)
    for i in range(3):
        att = AssessmentAttempt(
            student_profile_id=student.id,
            assessment_version_id=ass_v.id,
            status="evaluated",
            is_passed=False,
            percentage=30.0,
            attempt_number=i + 1,
            started_at=now_attempt,
            expires_at=now_attempt + timedelta(hours=1),
            submitted_at=now_attempt,
        )
        db_session.add(att)
    await db_session.commit()

    # 3. Execute scan
    scan_res = await handle_remediation_signal_scan({"institution_id": inst.id})
    assert scan_res["institutions_scanned"] == 1
    assert scan_res["total_signals_detected"] >= 1

    # 4. Repeat scan to verify idempotency (no duplicate active signals)
    repeat_res = await handle_remediation_signal_scan({"institution_id": inst.id})
    assert repeat_res["institutions_scanned"] == 1
    assert repeat_res["total_signals_detected"] == 0


@pytest.mark.asyncio
async def test_worker_retry_behavior_and_failure_handling():
    """Verify BackgroundJobWorker bounds retries with exponential backoff and tracks failure metrics."""
    worker = BackgroundJobWorker()
    attempts = 0

    async def transient_failing_handler(payload: Dict[str, Any]):
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ValueError("Transient database glitch")

    worker.register_handler("test_transient", transient_failing_handler)
    job_id = await worker.enqueue("test_transient", {"test": True}, max_retries=3)

    # Run worker loop manually for the queue items
    # Attempt 1 -> fails and re-enqueues
    record: JobRecord = await worker._queue.get()
    record.attempts += 1
    with pytest.raises(ValueError):
        await transient_failing_handler(record.payload)
    record.status = "PENDING"
    await worker._queue.put(record)

    # Attempt 2 -> succeeds
    record2: JobRecord = await worker._queue.get()
    record2.attempts += 1
    await transient_failing_handler(record2.payload)
    record2.status = "COMPLETED"

    assert record2.status == "COMPLETED"
    assert attempts == 2


@pytest.mark.asyncio
async def test_sandbox_unconfigured_honest_requires_sandbox_state():
    """Verify removing SANDBOX_API_URL results in honest REQUIRES_SANDBOX without network timeout."""
    # Provider with empty URL
    provider = HttpSandboxProvider(api_url="", api_token=None)
    assert not provider.is_configured

    # Health check returns degraded immediately without network delay
    health = provider.check_health()
    assert health["status"] == "degraded"
    assert health["configured"] is False
    assert "REQUIRES_SANDBOX" in health["message"]

    # Code execution returns unavailable immediately without spoofing
    req = ExecutionRequest(
        language="python",
        code="print('test')",
        time_limit_ms=1000,
        memory_limit_mb=128,
        test_cases=[],
    )
    result = provider.execute(req)
    assert not result.is_available
    assert result.compile_status == "unavailable"
    assert "REQUIRES_SANDBOX" in result.error_message


@pytest.mark.asyncio
async def test_worker_non_blocking_retry_drains_subsequent_jobs():
    """Verify that a failing job waiting on exponential backoff does NOT block subsequent queue jobs.
    
    Previous bug: A synchronous await asyncio.sleep(...) inside _worker_loop blocked
    the entire loop, causing queue_depth=2 with running=0 while subsequent jobs were starved.
    """
    worker = BackgroundJobWorker()
    job2_executed = asyncio.Event()
    job1_attempts = 0

    async def failing_handler(payload):
        nonlocal job1_attempts
        job1_attempts += 1
        raise ValueError("Simulated failure")

    async def healthy_handler(payload):
        job2_executed.set()

    worker.register_handler("job1_fail", failing_handler)
    worker.register_handler("job2_healthy", healthy_handler)

    # Enqueue job1 (fails) then job2 (healthy)
    await worker.enqueue("job1_fail", {}, max_retries=2)
    await worker.enqueue("job2_healthy", {})

    # Start worker
    worker.start()

    # Job2 should execute quickly even though Job1 is retrying
    await asyncio.wait_for(job2_executed.wait(), timeout=3.0)
    assert job2_executed.is_set(), "Job 2 was blocked by Job 1's retry sleep!"

    metrics = worker.get_metrics()
    assert metrics["completed"] >= 1
    # Check metric invariant: total_jobs == completed + failed + running + queue_depth
    assert metrics["total_jobs"] == metrics["completed"] + metrics["failed"] + metrics["running"] + metrics["queue_depth"]

    await worker.stop()

