"""Bulk import and ingestion engine for National Academic Catalog datasets.

Supports:
- CSV & JSON structured formats
- Validation & error collection
- Duplicate detection & idempotent imports
- Dry-run validation mode (rolls back transactional changes)
- Source tracking & version assignment
- Detailed execution audit reporting via CatalogImportJob
"""

import csv
import io
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.catalog.models import (
    AcademicDiscipline,
    DegreeType,
    ProgramCatalog,
    ProgramSpecialization,
    CourseCatalog,
    SkillCatalog,
    CareerCatalog,
    CatalogImportJob,
)
from app.domains.catalog.schemas import (
    CatalogImportRequest,
    AcademicDisciplineCreate,
    DegreeTypeCreate,
    ProgramCatalogCreate,
    ProgramSpecializationCreate,
    CourseCatalogCreate,
    SkillCatalogCreate,
    CareerCatalogCreate,
)
from app.domains.catalog.service import academic_catalog_service


class CatalogImporter:
    """Enterprise-grade catalog dataset ingestion engine."""

    @staticmethod
    def parse_csv(csv_text: str) -> List[Dict[str, Any]]:
        """Parses CSV text into a list of row dictionaries."""
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        return [dict(row) for row in reader]

    async def execute_import(
        self,
        db: AsyncSession,
        request: CatalogImportRequest,
        user_id: Optional[str] = None,
    ) -> CatalogImportJob:
        """Executes an idempotent batch import with dry-run support."""
        job = CatalogImportJob(
            entity_type=request.entity_type.lower().strip(),
            source_id=request.source_id,
            version_id=request.version_id,
            is_dry_run=request.is_dry_run,
            status="pending",
            total_records=len(request.records),
            initiated_by_user_id=user_id,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        errors: List[Dict[str, Any]] = []
        successful_count = 0
        duplicate_count = 0
        failed_count = 0

        entity_type = request.entity_type.lower().strip()

        for idx, row in enumerate(request.records):
            code = str(row.get("code", "")).strip().upper()
            if not code:
                failed_count += 1
                errors.append({"index": idx, "row": row, "error": "Missing mandatory 'code' field."})
                continue

            try:
                if entity_type == "discipline":
                    stmt = select(AcademicDiscipline).where(AcademicDiscipline.code == code)
                    if (await db.execute(stmt)).scalar_one_or_none():
                        duplicate_count += 1
                        continue

                    create_data = AcademicDisciplineCreate(
                        code=code,
                        name=row.get("name", code),
                        display_name=row.get("display_name", row.get("name", code)),
                        description=row.get("description"),
                        aliases=row.get("aliases") if isinstance(row.get("aliases"), list) else None,
                        status=row.get("status", "active"),
                        version_id=request.version_id,
                        source_id=request.source_id,
                    )
                    if not request.is_dry_run:
                        await academic_catalog_service.create_discipline(db, create_data)
                    successful_count += 1

                elif entity_type == "degree_type":
                    stmt = select(DegreeType).where(DegreeType.code == code)
                    if (await db.execute(stmt)).scalar_one_or_none():
                        duplicate_count += 1
                        continue

                    create_data = DegreeTypeCreate(
                        code=code,
                        name=row.get("name", code),
                        short_name=row.get("short_name", code),
                        level=int(row.get("level", 3)),
                        typical_duration_years=float(row.get("typical_duration_years", 4.0)),
                        status=row.get("status", "active"),
                    )
                    if not request.is_dry_run:
                        await academic_catalog_service.create_degree_type(db, create_data)
                    successful_count += 1

                elif entity_type == "program":
                    stmt = select(ProgramCatalog).where(ProgramCatalog.code == code)
                    if (await db.execute(stmt)).scalar_one_or_none():
                        duplicate_count += 1
                        continue

                    create_data = ProgramCatalogCreate(
                        code=code,
                        name=row.get("name", code),
                        short_name=row.get("short_name", code),
                        discipline_id=row["discipline_id"],
                        degree_type_id=row["degree_type_id"],
                        duration_years=float(row.get("duration_years", 4.0)),
                        description=row.get("description"),
                        aliases=row.get("aliases") if isinstance(row.get("aliases"), list) else None,
                        status=row.get("status", "active"),
                        version_id=request.version_id,
                        source_id=request.source_id,
                    )
                    if not request.is_dry_run:
                        await academic_catalog_service.create_program(db, create_data)
                    successful_count += 1

                elif entity_type == "course":
                    stmt = select(CourseCatalog).where(CourseCatalog.code == code)
                    if (await db.execute(stmt)).scalar_one_or_none():
                        duplicate_count += 1
                        continue

                    create_data = CourseCatalogCreate(
                        code=code,
                        title=row.get("title", code),
                        discipline_id=row["discipline_id"],
                        default_credits=float(row.get("default_credits", 3.0)),
                        academic_level=row.get("academic_level", "intermediate"),
                        description=row.get("description"),
                        prerequisites=row.get("prerequisites") if isinstance(row.get("prerequisites"), list) else None,
                        aliases=row.get("aliases") if isinstance(row.get("aliases"), list) else None,
                        status=row.get("status", "active"),
                        version_id=request.version_id,
                        source_id=request.source_id,
                    )
                    if not request.is_dry_run:
                        await academic_catalog_service.create_course(db, create_data)
                    successful_count += 1

                elif entity_type == "skill":
                    stmt = select(SkillCatalog).where(SkillCatalog.code == code)
                    if (await db.execute(stmt)).scalar_one_or_none():
                        duplicate_count += 1
                        continue

                    create_data = SkillCatalogCreate(
                        code=code,
                        name=row.get("name", code),
                        category=row.get("category", "technical"),
                        description=row.get("description"),
                        aliases=row.get("aliases") if isinstance(row.get("aliases"), list) else None,
                        status=row.get("status", "active"),
                    )
                    if not request.is_dry_run:
                        await academic_catalog_service.create_skill(db, create_data)
                    successful_count += 1

                elif entity_type == "career":
                    stmt = select(CareerCatalog).where(CareerCatalog.code == code)
                    if (await db.execute(stmt)).scalar_one_or_none():
                        duplicate_count += 1
                        continue

                    create_data = CareerCatalogCreate(
                        code=code,
                        title=row.get("title", code),
                        industry=row.get("industry", "Technology"),
                        description=row.get("description"),
                        aliases=row.get("aliases") if isinstance(row.get("aliases"), list) else None,
                        status=row.get("status", "active"),
                    )
                    if not request.is_dry_run:
                        await academic_catalog_service.create_career(db, create_data)
                    successful_count += 1

                else:
                    failed_count += 1
                    errors.append({"index": idx, "code": code, "error": f"Unsupported entity_type: '{entity_type}'"})

            except Exception as ex:
                failed_count += 1
                errors.append({"index": idx, "code": code, "error": str(ex)})

        # Finalize job report
        job.processed_records = len(request.records)
        job.successful_records = successful_count
        job.duplicate_records = duplicate_count
        job.failed_records = failed_count
        job.errors = errors
        job.status = "completed" if failed_count == 0 else "completed_with_errors"

        await db.commit()
        await db.refresh(job)
        return job


catalog_importer = CatalogImporter()
