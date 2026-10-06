"""Coding assessment evaluation and sandbox execution abstraction.

CRITICAL SECURITY RULE:
Arbitrary untrusted student code is NEVER executed directly inside the FastAPI/Uvicorn process.
Evaluation is delegated through a secure CodeExecutionProvider abstraction.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.domains.assessment.evaluators.base import EvaluationInput, EvaluationResult


class ExecutionTestCase(BaseModel):
    input_data: str
    expected_output: str
    is_hidden: bool = False
    points_weight: Decimal = Decimal("1.00")


class ExecutionRequest(BaseModel):
    language: str
    code: str
    time_limit_ms: int = 2000
    memory_limit_mb: int = 256
    test_cases: List[ExecutionTestCase]


class ExecutionTestResult(BaseModel):
    test_index: int
    is_passed: bool
    status: str  # "passed", "wrong_answer", "time_limit_exceeded", "runtime_error", "memory_limit_exceeded"
    execution_time_ms: Optional[int] = None
    memory_used_kb: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    is_hidden: bool = False


class ExecutionResponse(BaseModel):
    is_available: bool
    compile_status: str  # "ok", "compile_error", "unavailable"
    error_message: Optional[str] = None
    test_results: List[ExecutionTestResult] = []
    tests_passed: int = 0
    total_tests: int = 0


class CodeExecutionProvider(ABC):
    """Abstract interface for isolated sandbox execution backends (Docker, gVisor, Firecracker, Lambda)."""

    @abstractmethod
    def execute(self, req: ExecutionRequest) -> ExecutionResponse:
        """Executes code against test cases in an isolated sandbox environment."""
        pass


class UnavailableCodeExecutionProvider(CodeExecutionProvider):
    """Default production-safe provider when no isolated sandbox worker is configured."""

    def execute(self, req: ExecutionRequest) -> ExecutionResponse:
        return ExecutionResponse(
            is_available=False,
            compile_status="unavailable",
            error_message="Sandbox execution cluster is not configured in this environment.",
            test_results=[],
            tests_passed=0,
            total_tests=len(req.test_cases),
        )


class MockSandboxProvider(CodeExecutionProvider):
    """Safe deterministic test sandbox provider that simulates test matching for verification without code execution."""

    def __init__(self, simulate_pass_rate: float = 1.0):
        self.simulate_pass_rate = simulate_pass_rate

    def execute(self, req: ExecutionRequest) -> ExecutionResponse:
        if not req.code or not req.code.strip():
            return ExecutionResponse(
                is_available=True,
                compile_status="compile_error",
                error_message="Empty code submission",
                test_results=[],
                tests_passed=0,
                total_tests=len(req.test_cases),
            )

        results: List[ExecutionTestResult] = []
        passed_count = 0
        total = len(req.test_cases)
        threshold = int(total * self.simulate_pass_rate)

        for i, tc in enumerate(req.test_cases):
            passed = (i < threshold)
            if passed:
                passed_count += 1
            results.append(
                ExecutionTestResult(
                    test_index=i,
                    is_passed=passed,
                    status="passed" if passed else "wrong_answer",
                    execution_time_ms=45,
                    memory_used_kb=10240,
                    is_hidden=tc.is_hidden,
                )
            )

        return ExecutionResponse(
            is_available=True,
            compile_status="ok",
            test_results=results,
            tests_passed=passed_count,
            total_tests=total,
        )


import httpx
from app.core.config import settings
from app.core.logging import logger


class HttpSandboxProvider(CodeExecutionProvider):
    """Production REST client for isolated sandbox execution cluster (e.g., Docker/gVisor/Firecracker).

    Invariants:
    - Never executes untrusted code inside the FastAPI process.
    - If SANDBOX_API_URL is missing or unavailable, returns compile_status="unavailable"
      and error_message="REQUIRES_SANDBOX", never faking execution or test results.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_token: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ):
        self.api_url = (api_url or settings.SANDBOX_API_URL or "").rstrip("/")
        self.api_token = api_token or settings.SANDBOX_API_TOKEN
        self.timeout_seconds = timeout_seconds or settings.SANDBOX_TIMEOUT_SECONDS

    @property
    def is_configured(self) -> bool:
        return bool(self.api_url)

    def execute(self, req: ExecutionRequest) -> ExecutionResponse:
        if not self.is_configured:
            return ExecutionResponse(
                is_available=False,
                compile_status="unavailable",
                error_message="Sandbox cluster not configured (REQUIRES_SANDBOX).",
                test_results=[],
                tests_passed=0,
                total_tests=len(req.test_cases),
            )

        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        payload = {
            "language": req.language,
            "code": req.code,
            "time_limit_ms": min(req.time_limit_ms, self.timeout_seconds * 1000),
            "memory_limit_mb": min(req.memory_limit_mb, settings.SANDBOX_MAX_MEMORY_MB),
            "test_cases": [
                {
                    "input_data": tc.input_data,
                    "expected_output": tc.expected_output,
                    "is_hidden": tc.is_hidden,
                    "points_weight": float(tc.points_weight),
                }
                for tc in req.test_cases
            ],
        }

        try:
            with httpx.Client(timeout=float(self.timeout_seconds)) as client:
                resp = client.post(f"{self.api_url}/execute", json=payload, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"Sandbox runner HTTP error {resp.status_code}: {resp.text}")
                    return ExecutionResponse(
                        is_available=False,
                        compile_status="unavailable",
                        error_message=f"Sandbox runner HTTP {resp.status_code} (REQUIRES_SANDBOX)",
                        test_results=[],
                        tests_passed=0,
                        total_tests=len(req.test_cases),
                    )

                data = resp.json()
                results = [
                    ExecutionTestResult(**tr)
                    for tr in data.get("test_results", [])
                ]
                return ExecutionResponse(
                    is_available=data.get("is_available", True),
                    compile_status=data.get("compile_status", "ok"),
                    error_message=data.get("error_message"),
                    test_results=results,
                    tests_passed=data.get("tests_passed", 0),
                    total_tests=data.get("total_tests", len(req.test_cases)),
                )
        except Exception as exc:
            logger.warning(f"Sandbox runner connection failed: {exc}")
            return ExecutionResponse(
                is_available=False,
                compile_status="unavailable",
                error_message=f"Sandbox runner unreachable: {exc} (REQUIRES_SANDBOX)",
                test_results=[],
                tests_passed=0,
                total_tests=len(req.test_cases),
            )

    def check_health(self) -> Dict[str, Any]:
        """Probes the sandbox service for platform readiness."""
        if not self.is_configured:
            return {
                "status": "degraded",
                "configured": False,
                "message": "SANDBOX_API_URL not configured; coding execution marked offline (REQUIRES_SANDBOX)",
            }
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.api_url}/health", headers=headers)
                if res.status_code == 200:
                    return {"status": "healthy", "configured": True, "details": res.json()}
                return {"status": "degraded", "configured": True, "http_status": res.status_code}
        except Exception as exc:
            return {"status": "degraded", "configured": True, "error": str(exc)}


# Global active provider (defaults to UnavailableCodeExecutionProvider for strict security)
_active_provider: CodeExecutionProvider = UnavailableCodeExecutionProvider()


def set_code_execution_provider(provider: CodeExecutionProvider) -> None:
    """Configures the active code execution provider."""
    global _active_provider
    _active_provider = provider


def get_code_execution_provider() -> CodeExecutionProvider:
    """Returns the configured code execution provider."""
    global _active_provider
    if isinstance(_active_provider, UnavailableCodeExecutionProvider) and settings.SANDBOX_API_URL:
        return HttpSandboxProvider()
    return _active_provider


def check_sandbox_health() -> Dict[str, Any]:
    """Probes sandbox execution readiness."""
    provider = get_code_execution_provider()
    if isinstance(provider, HttpSandboxProvider):
        return provider.check_health()
    elif isinstance(provider, MockSandboxProvider):
        return {"status": "healthy", "configured": True, "provider": "mock"}
    return {
        "status": "degraded",
        "configured": False,
        "message": "No active sandbox provider configured (REQUIRES_SANDBOX)",
    }


class CodingEvaluator:
    """Evaluates student code submissions using the configured CodeExecutionProvider."""

    def evaluate(self, inp: EvaluationInput) -> EvaluationResult:
        student_code = str(inp.response_payload.get("code", "")).strip()
        if not student_code:
            return EvaluationResult(
                awarded_marks=Decimal("0.00"),
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=False,
                evaluation_type="coding_sandbox",
                feedback="Unanswered: No code submitted",
            )

        coding_meta = inp.truth_metadata.get("coding_config", {})
        language = coding_meta.get("language", "python")
        test_cases_data = coding_meta.get("test_cases", [])

        test_cases = [
            ExecutionTestCase(
                input_data=tc.get("input_data", ""),
                expected_output=tc.get("expected_output", ""),
                is_hidden=tc.get("is_hidden", False),
                points_weight=Decimal(str(tc.get("points_weight", "1.00"))),
            )
            for tc in test_cases_data
        ]

        provider = get_code_execution_provider()
        req = ExecutionRequest(
            language=language,
            code=student_code,
            time_limit_ms=coding_meta.get("time_limit_ms", 2000),
            memory_limit_mb=coding_meta.get("memory_limit_mb", 256),
            test_cases=test_cases,
        )

        resp = provider.execute(req)
        if not resp.is_available:
            return EvaluationResult(
                awarded_marks=Decimal("0.00"),
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=False,
                evaluation_type="coding_sandbox",
                feedback="Execution sandbox unavailable. Submission queued for offline evaluation.",
                details={"status": "unavailable", "message": resp.error_message},
            )

        if resp.compile_status != "ok":
            return EvaluationResult(
                awarded_marks=Decimal("0.00"),
                penalty_marks=inp.negative_marks,
                max_marks=inp.points,
                is_correct=False,
                evaluation_type="coding_sandbox",
                feedback=f"Compilation/Syntax Error: {resp.error_message}",
                details={"status": resp.compile_status},
            )

        total_weight = sum(tc.points_weight for tc in test_cases) or Decimal("1.00")
        earned_weight = Decimal("0.00")
        for i, res in enumerate(resp.test_results):
            if res.is_passed and i < len(test_cases):
                earned_weight += test_cases[i].points_weight

        fraction = max(Decimal("0.00"), min(Decimal("1.00"), earned_weight / total_weight))
        awarded_marks = round(inp.points * fraction, 2)
        is_all_passed = (resp.tests_passed == resp.total_tests and resp.total_tests > 0)

        # Build student-safe test summary: NEVER expose hidden test case inputs/outputs
        safe_tests = []
        for res in resp.test_results:
            safe_tests.append({
                "test_index": res.test_index + 1,
                "is_passed": res.is_passed,
                "status": res.status,
                "is_hidden": res.is_hidden,
                "execution_time_ms": res.execution_time_ms,
            })

        return EvaluationResult(
            awarded_marks=awarded_marks,
            penalty_marks=Decimal("0.00"),
            max_marks=inp.points,
            is_correct=is_all_passed,
            evaluation_type="coding_sandbox",
            feedback=f"Passed {resp.tests_passed} of {resp.total_tests} test cases",
            details={
                "tests_passed": resp.tests_passed,
                "total_tests": resp.total_tests,
                "test_summary": safe_tests,
            },
        )
