"""Career Intelligence Domain 7 Package."""

from app.domains.career_intelligence.config import (
    CareerIntelligenceConfig,
    DEFAULT_CAREER_CONFIG,
)
from app.domains.career_intelligence.models import (
    StudentSkillIntelligenceState,
    StudentSkillEvidenceRecord,
    StudentCareerReadinessState,
    CareerTrajectory,
    CareerTrajectoryStep,
    PlacementReadinessState,
)
from app.domains.career_intelligence.skill_engine import (
    SkillIntelligenceEngine,
    SkillEvidenceInput,
    EvaluatedSkillResult,
)
from app.domains.career_intelligence.readiness_engine import (
    CareerReadinessEngine,
    CareerSkillReq,
    SkillGapItem,
    CareerReadinessCalculationResult,
)
from app.domains.career_intelligence.trajectory_engine import (
    CareerTrajectoryEngine,
    TrajectoryStepDraft,
    TrajectoryDraftResult,
)
from app.domains.career_intelligence.placement_engine import (
    PlacementReadinessEngine,
    PlacementEvaluationInput,
    PlacementReadinessResult,
)
from app.domains.career_intelligence.service import (
    CareerIntelligenceService,
    career_intelligence_service,
)
from app.domains.career_intelligence.engine import (
    SkillRequirement,
    CareerTargetProfile,
    CareerReadinessReport,
    calculate_career_readiness,
)

__all__ = [
    "CareerIntelligenceConfig",
    "DEFAULT_CAREER_CONFIG",
    "StudentSkillIntelligenceState",
    "StudentSkillEvidenceRecord",
    "StudentCareerReadinessState",
    "CareerTrajectory",
    "CareerTrajectoryStep",
    "PlacementReadinessState",
    "SkillIntelligenceEngine",
    "SkillEvidenceInput",
    "EvaluatedSkillResult",
    "CareerReadinessEngine",
    "CareerSkillReq",
    "SkillGapItem",
    "CareerReadinessCalculationResult",
    "CareerTrajectoryEngine",
    "TrajectoryStepDraft",
    "TrajectoryDraftResult",
    "PlacementReadinessEngine",
    "PlacementEvaluationInput",
    "PlacementReadinessResult",
    "CareerIntelligenceService",
    "career_intelligence_service",
    "SkillRequirement",
    "CareerTargetProfile",
    "CareerReadinessReport",
    "calculate_career_readiness",
]
