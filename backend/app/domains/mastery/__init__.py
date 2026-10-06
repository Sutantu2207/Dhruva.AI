"""Domain 6: Knowledge State, Concept Mastery Engine & Spaced Repetition."""

# Backward-compatible exports
from app.domains.mastery.sm2 import calculate_sm2, SM2Result
from app.domains.mastery.engine import (
    calculate_mastery_tier,
    compute_updated_mastery,
    MasteryTier,
    ConceptMasteryRecord,
)

# Domain 6 Core Models
from app.domains.mastery.models import (
    StudentConceptKnowledgeState,
    KnowledgeStateHistory,
    ConceptEvidenceProcessing,
    ConceptReviewState,
    ConceptReviewHistory,
    LearningPrioritySnapshot,
    MasteryAdjustment,
)

# Clocks & Config
from app.domains.mastery.clock import Clock, SystemClock, FrozenClock
from app.domains.mastery.config import (
    KnowledgeStateConfig,
    DEFAULT_KNOWLEDGE_CONFIG,
    EvidenceWeightConfig,
    DifficultyWeightConfig,
    MasteryThresholdConfig,
    ConfidenceConfig,
    RecencyDecayConfig,
    RetentionConfig,
    SM2Config,
    PriorityWeightConfig,
)

# Pure Engines
from app.domains.mastery.mastery_engine import (
    ConceptMasteryEngine,
    EvidenceItemDTO,
    MasteryEvaluationOutput,
)
from app.domains.mastery.retention_engine import RetentionEngine
from app.domains.mastery.sm2_scheduler import SM2Scheduler, SM2ScheduleResult
from app.domains.mastery.prerequisite_engine import PrerequisiteReadinessEngine
from app.domains.mastery.priority_engine import (
    LearningPriorityEngine,
    ConceptStateContext,
    PriorityEvaluationResult,
    DailyMissionTask,
)

# Service
from app.domains.mastery.service import KnowledgeStateService, knowledge_state_service

__all__ = [
    # Legacy / foundational functions
    "calculate_sm2",
    "SM2Result",
    "calculate_mastery_tier",
    "compute_updated_mastery",
    "MasteryTier",
    "ConceptMasteryRecord",
    # Models
    "StudentConceptKnowledgeState",
    "KnowledgeStateHistory",
    "ConceptEvidenceProcessing",
    "ConceptReviewState",
    "ConceptReviewHistory",
    "LearningPrioritySnapshot",
    "MasteryAdjustment",
    # Clocks & Config
    "Clock",
    "SystemClock",
    "FrozenClock",
    "KnowledgeStateConfig",
    "DEFAULT_KNOWLEDGE_CONFIG",
    "EvidenceWeightConfig",
    "DifficultyWeightConfig",
    "MasteryThresholdConfig",
    "ConfidenceConfig",
    "RecencyDecayConfig",
    "RetentionConfig",
    "SM2Config",
    "PriorityWeightConfig",
    # Engines
    "ConceptMasteryEngine",
    "EvidenceItemDTO",
    "MasteryEvaluationOutput",
    "RetentionEngine",
    "SM2Scheduler",
    "SM2ScheduleResult",
    "PrerequisiteReadinessEngine",
    "LearningPriorityEngine",
    "ConceptStateContext",
    "PriorityEvaluationResult",
    "DailyMissionTask",
    # Service
    "KnowledgeStateService",
    "knowledge_state_service",
]
