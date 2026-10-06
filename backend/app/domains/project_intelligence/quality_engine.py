"""Pure deterministic Project Quality Engine for Domain 8.

Calculates explainable, reproducible project quality across 6 key dimensions:
- Technical Depth
- Implementation Quality
- Documentation Quality
- Testing Quality
- Architecture Quality
- Verification Strength
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProjectQualityInput:
    """Deterministic inputs for evaluating project quality."""
    title: str
    description: Optional[str] = None
    problem_statement: Optional[str] = None
    solution: Optional[str] = None
    technologies: List[str] = field(default_factory=list)
    status: str = "in_progress"
    repository_url: Optional[str] = None
    live_url: Optional[str] = None
    documentation_url: Optional[str] = None
    demo_url: Optional[str] = None
    modules_contributed: List[str] = field(default_factory=list)
    skills_count: int = 0
    concepts_count: int = 0
    evidence_items_count: int = 0
    verified_evidence_count: int = 0
    has_test_evidence: bool = False
    has_architecture_diagram: bool = False
    faculty_review_score: Optional[float] = None
    faculty_review_breakdown: Optional[Dict[str, float]] = None
    is_verified: bool = False


@dataclass(frozen=True)
class ProjectQualityResult:
    """Output containing composite score and explainable dimension breakdown."""
    overall_score: float
    technical_depth: float
    implementation_quality: float
    documentation_quality: float
    testing_quality: float
    architecture_quality: float
    verification_strength: float
    dimension_breakdown: Dict[str, Any]
    missing_elements: List[str]
    algorithm_version: str = "v1.0.0-deterministic"


class ProjectQualityEngine:
    """Deterministic, versioned calculation of project quality without arbitrary scores."""

    def __init__(self, algorithm_version: str = "v1.0.0-deterministic"):
        self.algorithm_version = algorithm_version

    def evaluate_project(self, project_in: ProjectQualityInput) -> ProjectQualityResult:
        missing_elements: List[str] = []

        # 1. Technical Depth (0 - 100)
        # Evaluated from technologies count, concept integration, and faculty review if present
        tech_count = len(project_in.technologies)
        tech_score = min(40.0, tech_count * 10.0)  # Up to 4 technologies = 40 pts
        concept_score = min(30.0, project_in.concepts_count * 10.0)  # Up to 3 concepts = 30 pts
        skills_score = min(30.0, project_in.skills_count * 10.0)  # Up to 3 skills = 30 pts
        base_tech_depth = tech_score + concept_score + skills_score

        if tech_count < 2:
            missing_elements.append("Diverse technology stack (at least 2 technologies)")
        if project_in.concepts_count == 0:
            missing_elements.append("Mapped conceptual foundations (concepts)")

        if project_in.faculty_review_breakdown and "technical_depth" in project_in.faculty_review_breakdown:
            technical_depth = round(0.4 * base_tech_depth + 0.6 * project_in.faculty_review_breakdown["technical_depth"], 2)
        else:
            technical_depth = round(base_tech_depth, 2)

        # 2. Implementation Quality (0 - 100)
        # Evaluated from status, repository URL, live deployment URL, demo URL
        impl_pts = 0.0
        if project_in.status == "completed":
            impl_pts += 30.0
        elif project_in.status == "in_progress":
            impl_pts += 15.0

        if project_in.repository_url:
            impl_pts += 35.0
        else:
            missing_elements.append("Repository URL / source code reference")

        if project_in.live_url or project_in.demo_url:
            impl_pts += 35.0
        else:
            missing_elements.append("Live deployment or demonstration URL")

        if project_in.faculty_review_breakdown and "code_quality" in project_in.faculty_review_breakdown:
            implementation_quality = round(0.4 * impl_pts + 0.6 * project_in.faculty_review_breakdown["code_quality"], 2)
        else:
            implementation_quality = round(impl_pts, 2)

        # 3. Documentation Quality (0 - 100)
        # Evaluated from problem statement, solution, description length, documentation URL
        doc_pts = 0.0
        if project_in.problem_statement and len(project_in.problem_statement.strip()) > 20:
            doc_pts += 30.0
        else:
            missing_elements.append("Clear problem statement")

        if project_in.solution and len(project_in.solution.strip()) > 20:
            doc_pts += 30.0
        else:
            missing_elements.append("Detailed solution description")

        if project_in.description and len(project_in.description.strip()) > 30:
            doc_pts += 20.0

        if project_in.documentation_url:
            doc_pts += 20.0
        else:
            missing_elements.append("External technical documentation / README link")

        if project_in.faculty_review_breakdown and "documentation_quality" in project_in.faculty_review_breakdown:
            documentation_quality = round(0.4 * doc_pts + 0.6 * project_in.faculty_review_breakdown["documentation_quality"], 2)
        else:
            documentation_quality = round(doc_pts, 2)

        # 4. Testing Quality (0 - 100)
        test_pts = 20.0  # Base assumption of manual self-testing
        if project_in.has_test_evidence:
            test_pts += 50.0
        else:
            missing_elements.append("Automated test reports or verification evidence")

        # Check if technologies indicate testing frameworks
        testing_keywords = {"jest", "pytest", "cypress", "junit", "mocha", "playwright", "vitest", "selenium"}
        if any(t.lower() in testing_keywords for t in project_in.technologies):
            test_pts += 30.0

        test_pts = min(100.0, test_pts)
        if project_in.faculty_review_breakdown and "testing_quality" in project_in.faculty_review_breakdown:
            testing_quality = round(0.3 * test_pts + 0.7 * project_in.faculty_review_breakdown["testing_quality"], 2)
        else:
            testing_quality = round(test_pts, 2)

        # 5. Architecture Quality (0 - 100)
        arch_pts = 25.0
        if project_in.has_architecture_diagram:
            arch_pts += 40.0
        else:
            missing_elements.append("Architecture diagram or system design specification")

        if len(project_in.modules_contributed) >= 2:
            arch_pts += 35.0
        elif len(project_in.modules_contributed) == 1:
            arch_pts += 20.0

        arch_pts = min(100.0, arch_pts)
        if project_in.faculty_review_breakdown and "architecture_quality" in project_in.faculty_review_breakdown:
            architecture_quality = round(0.4 * arch_pts + 0.6 * project_in.faculty_review_breakdown["architecture_quality"], 2)
        else:
            architecture_quality = round(arch_pts, 2)

        # 6. Verification Strength (0 - 100)
        if project_in.is_verified:
            verification_strength = 100.0
        elif project_in.faculty_review_score is not None:
            verification_strength = min(100.0, max(60.0, project_in.faculty_review_score))
        elif project_in.verified_evidence_count > 0:
            verification_strength = min(80.0, 40.0 + project_in.verified_evidence_count * 20.0)
        elif project_in.evidence_items_count > 0:
            verification_strength = min(50.0, 25.0 + project_in.evidence_items_count * 10.0)
        else:
            verification_strength = 10.0
            missing_elements.append("Submitted empirical verification evidence")

        # Composite Score Calculation (0 - 100)
        # Weights: Tech (25%), Impl (20%), Doc (15%), Test (15%), Arch (15%), Verification (10%)
        composite = (
            0.25 * technical_depth +
            0.20 * implementation_quality +
            0.15 * documentation_quality +
            0.15 * testing_quality +
            0.15 * architecture_quality +
            0.10 * verification_strength
        )
        overall_score = round(min(100.0, max(0.0, composite)), 2)

        breakdown = {
            "technical_depth": {
                "score": technical_depth,
                "weight": 0.25,
                "contribution": round(0.25 * technical_depth, 2),
                "basis": f"{tech_count} technologies, {project_in.concepts_count} concepts, {project_in.skills_count} skills",
            },
            "implementation_quality": {
                "score": implementation_quality,
                "weight": 0.20,
                "contribution": round(0.20 * implementation_quality, 2),
                "basis": f"Status: {project_in.status}, repo={'yes' if project_in.repository_url else 'no'}, live={'yes' if (project_in.live_url or project_in.demo_url) else 'no'}",
            },
            "documentation_quality": {
                "score": documentation_quality,
                "weight": 0.15,
                "contribution": round(0.15 * documentation_quality, 2),
                "basis": f"Problem: {'yes' if project_in.problem_statement else 'no'}, Solution: {'yes' if project_in.solution else 'no'}",
            },
            "testing_quality": {
                "score": testing_quality,
                "weight": 0.15,
                "contribution": round(0.15 * testing_quality, 2),
                "basis": f"Test evidence: {'yes' if project_in.has_test_evidence else 'no'}",
            },
            "architecture_quality": {
                "score": architecture_quality,
                "weight": 0.15,
                "contribution": round(0.15 * architecture_quality, 2),
                "basis": f"Diagram: {'yes' if project_in.has_architecture_diagram else 'no'}, Modules: {len(project_in.modules_contributed)}",
            },
            "verification_strength": {
                "score": verification_strength,
                "weight": 0.10,
                "contribution": round(0.10 * verification_strength, 2),
                "basis": f"Verified: {project_in.is_verified}, evidence items: {project_in.evidence_items_count}",
            },
        }

        return ProjectQualityResult(
            overall_score=overall_score,
            technical_depth=technical_depth,
            implementation_quality=implementation_quality,
            documentation_quality=documentation_quality,
            testing_quality=testing_quality,
            architecture_quality=architecture_quality,
            verification_strength=verification_strength,
            dimension_breakdown=breakdown,
            missing_elements=missing_elements,
            algorithm_version=self.algorithm_version,
        )
