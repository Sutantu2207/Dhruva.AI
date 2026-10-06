import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

from app.core.config import settings
from app.core.database import Base, patch_alembic_version_table
# Import all identity and academic models to ensure they register on Base.metadata
from app.domains.identity.models import (
    User,
    UserSession,
    PasswordResetToken,
    EmailVerificationToken,
)
from app.domains.academic.models import (
    Institution,
    Department,
    Program,
    AcademicYear,
    Semester,
    Batch,
    Section,
    Course,
    CourseOffering,
    StudentAcademicProfile,
    TeacherAcademicProfile,
    StudentEnrollment,
    TeachingAssignment,
)
from app.domains.catalog.models import (
    AcademicCatalogVersion,
    AcademicCatalogSource,
    AcademicDiscipline,
    DegreeType,
    ProgramCatalog,
    ProgramSpecialization,
    CourseCatalog,
    SkillCatalog,
    CareerCatalog,
    ProgramSkillMapping,
    CourseSkillMapping,
    CareerSkillMapping,
    ProgramCareerMapping,
    InstitutionProgramMapping,
    CatalogImportJob,
)
from app.domains.profiles.models import (
    StudentProfileDetail,
    StudentAcademicStatusHistory,
    StudentSkill,
    StudentInterest,
    StudentCareerGoal,
    StudentProject,
    StudentProjectSkill,
    StudentCertification,
    StudentAchievement,
    StudentPortfolio,
    StudentResume,
    TeacherProfileDetail,
    MentorshipRelation,
    MentorGroup,
    MentorGroupMember,
    MentorNote,
    StudentIntervention,
    OnboardingImportJob,
)
from app.domains.profiles.audit import DomainAuditLog
from app.domains.content.models import (
    CourseContent,
    CourseContentVersion,
    Curriculum,
    Module,
    Lesson,
    LessonContentBlock,
    LearningObjective,
    Concept,
    ConceptPrerequisite,
    LessonConcept,
    ConceptSkill,
    LessonSkill,
    CourseSkill,
    LearningResource,
    ResourceVersion,
    LessonResource,
    ContentReview,
    ContentReviewComment,
    LessonProgress,
    CourseProgress,
    StudentBookmark,
    StudentLearningNote,
)
from app.domains.assessment.models import (
    QuestionBank,
    Question,
    QuestionVersion,
    QuestionOption,
    QuestionConcept,
    QuestionSkill,
    CodingConfiguration,
    CodingTestCase,
    EvaluationRubric,
    RubricCriterion,
    Assessment,
    AssessmentBlueprint,
    AssessmentVersion,
    AssessmentQuestion,
    AssessmentAttempt,
    AssessmentResponse,
    AssessmentEvaluation,
    ManualEvaluation,
    AssessmentResult,
    ConceptEvidence,
    SkillEvidence,
    GradeScheme,
    AssessmentIntegrityEvent,
    AssessmentReview,
)
from app.domains.mastery.models import (
    StudentConceptKnowledgeState,
    KnowledgeStateHistory,
    ConceptEvidenceProcessing,
    ConceptReviewState,
    ConceptReviewHistory,
    LearningPrioritySnapshot,
    MasteryAdjustment,
)
from app.domains.career_intelligence.models import (
    StudentSkillIntelligenceState,
    StudentSkillEvidenceRecord,
    StudentCareerReadinessState,
    CareerTrajectory,
    CareerTrajectoryStep,
    PlacementReadinessState,
)
from app.domains.remediation.models import (
    RemediationPlan,
    RemediationPlanStep,
    RemediationDiagnosis,
    RemediationAttempt,
    RemediationOutcome,
    RemediationSnapshot,
    AccreditationEvidenceSnapshot,
    ContentGapRecord,
)
from app.domains.ai.models import (
    AIConversation,
    AIMessage,
    AIToolInvocation,
    AIRetrievalCitation,
    AIUsageRecord,
    AIAuditEvent,
    AIFeedback,
    AIKnowledgeChunk,
)
from app.domains.audit.notification_models import (
    Notification,
    NotificationPreference,
)

from sqlalchemy import text

# Ensure DefaultImpl.version_table_impl creates alembic_version.version_num
# with VARCHAR(255) instead of Alembic's default VARCHAR(32).
patch_alembic_version_table(255)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    # Ensure alembic_version.version_num is widened if alembic_version was already
    # created on PostgreSQL with Alembic's legacy 32-character limit.
    if connection.dialect.name == "postgresql":
        try:
            connection.execute(
                text(
                    "DO $$ BEGIN "
                    "IF EXISTS (SELECT 1 FROM information_schema.columns "
                    "           WHERE table_name = 'alembic_version' "
                    "           AND column_name = 'version_num' "
                    "           AND character_maximum_length < 255) THEN "
                    "    ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255); "
                    "END IF; "
                    "END $$;"
                )
            )
        except Exception:
            pass  # Non-fatal if table does not exist or user lacks ALTER permissions

    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async SQLAlchemy engine."""
    connectable = create_async_engine(settings.DATABASE_URL)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

