"""Configuration and deterministic versioned weights for Domain 10 Adaptive Remediation."""

from decimal import Decimal
from typing import Dict

# Current Algorithm Version
ALGORITHM_VERSION = "remediation-v1.0.0"

# Remediation Priority Formula Weights
# remediation_priority =
#   0.30 * mastery_gap
# + 0.20 * retention_risk
# + 0.20 * prerequisite_block
# + 0.15 * repeated_failure
# + 0.10 * overdue_learning
# + 0.05 * course_criticality
PRIORITY_WEIGHTS: Dict[str, Decimal] = {
    "mastery_gap": Decimal("0.30"),
    "retention_risk": Decimal("0.20"),
    "prerequisite_block": Decimal("0.20"),
    "repeated_failure": Decimal("0.15"),
    "overdue_learning": Decimal("0.10"),
    "course_criticality": Decimal("0.05"),
}

# Thresholds for deterministic decisions
MASTERY_PROFICIENCY_THRESHOLD = Decimal("0.7000")  # Minimum mastery for successful closure
MASTERY_DEVELOPING_THRESHOLD = Decimal("0.4000")   # Boundary below which mastery is severely deficient
PREREQUISITE_READINESS_THRESHOLD = Decimal("0.6000")
RETENTION_RISK_THRESHOLD = Decimal("0.5000")

# Maximum depth for recursive prerequisite graph traversal to prevent infinite loops
MAX_PREREQUISITE_TRAVERSAL_DEPTH = 6

# Maximum steps in a synthesized remediation plan
MAX_PLAN_STEPS = 8

# Scaffold Progression Levels
SCAFFOLD_LEVELS = {
    1: {"name": "Recall", "step_type": "PREREQUISITE"},
    2: {"name": "Guided", "step_type": "MICRO_LESSON"},
    3: {"name": "Partially Guided", "step_type": "GUIDED_PRACTICE"},
    4: {"name": "Independent Practice", "step_type": "PRACTICE_ASSESSMENT"},
    5: {"name": "Reassessment", "step_type": "REASSESSMENT"},
}
