"""DHRUVA.AI - Seed Script: National Academic Catalog (Domain 2.5).

Idempotent seeding of:
- Regulatory Sources and Version Tags
- Disciplines & Degree Types
- National Programs & Specializations
- Skill Taxonomy across all engineering and analytical categories
- Career Definitions
- Weighted Career-Skill, Program-Skill, and Program-Career Mappings
"""

import asyncio
import logging
from datetime import date
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.domains.catalog.models import (
    AcademicCatalogSource,
    AcademicCatalogVersion,
    AcademicDiscipline,
    DegreeType,
    ProgramCatalog,
    ProgramSpecialization,
    SkillCatalog,
    CareerCatalog,
    CareerSkillMapping,
    ProgramSkillMapping,
    ProgramCareerMapping,
)

logger = logging.getLogger("dhruva.seed_catalog")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


DISCIPLINES_DATA = [
    {
        "code": "COMP_INFO",
        "name": "Computer Science & Information Technology",
        "display_name": "Computer Science & IT",
        "slug": "computer-science-it",
        "description": "Foundational and applied computing, software engineering, systems, and algorithms.",
    },
    {
        "code": "AI_DS",
        "name": "Artificial Intelligence & Data Science",
        "display_name": "AI & Data Science",
        "slug": "ai-data-science",
        "description": "Machine learning, statistical computing, neural systems, and data intelligence.",
    },
    {
        "code": "ELEC_COMM",
        "name": "Electronics & Communication Engineering",
        "display_name": "Electronics & Communication",
        "slug": "electronics-communication",
        "description": "Semiconductor electronics, microprocessors, communication protocols, and embedded systems.",
    },
    {
        "code": "ELEC_ELEC",
        "name": "Electrical & Electronics Engineering",
        "display_name": "Electrical & Electronics",
        "slug": "electrical-electronics",
        "description": "Power systems, control theory, electric drives, and energy conversion.",
    },
    {
        "code": "MECH_ENGG",
        "name": "Mechanical Engineering",
        "display_name": "Mechanical Engineering",
        "slug": "mechanical-engineering",
        "description": "Thermal dynamics, fluid mechanics, materials engineering, and automated robotics.",
    },
    {
        "code": "CIVIL_ENGG",
        "name": "Civil Engineering",
        "display_name": "Civil Engineering",
        "slug": "civil-engineering",
        "description": "Structural mechanics, geotechnics, urban transportation, and environmental engineering.",
    },
]

DEGREE_TYPES_DATA = [
    {
        "code": "UG",
        "name": "Undergraduate",
        "short_name": "UG",
        "level": 3,
        "typical_duration_years": 4.0,
    },
    {
        "code": "PG",
        "name": "Postgraduate",
        "short_name": "PG",
        "level": 4,
        "typical_duration_years": 2.0,
    },
    {
        "code": "DIPLOMA",
        "name": "Polytechnic Diploma",
        "short_name": "Diploma",
        "level": 2,
        "typical_duration_years": 3.0,
    },
    {
        "code": "DOCTORAL",
        "name": "Doctor of Philosophy",
        "short_name": "Ph.D.",
        "level": 5,
        "typical_duration_years": 5.0,
    },
]

PROGRAMS_DATA = [
    {
        "code": "BTECH_CSE",
        "name": "Bachelor of Technology in Computer Science & Engineering",
        "short_name": "B.Tech CSE",
        "discipline_code": "COMP_INFO",
        "degree_type_code": "UG",
        "duration_years": 4.0,
        "slug": "btech-cse",
        "description": "Four-year comprehensive undergraduate program in computer science, software systems, and network architecture.",
        "specializations": [
            {"code": "CSE-SE", "name": "Software Engineering & Architecture", "slug": "cse-software-engineering"},
            {"code": "CSE-CLOUD", "name": "Cloud Computing & Distributed Systems", "slug": "cse-cloud-computing"},
            {"code": "CSE-CYBER", "name": "Cybersecurity & Cryptography", "slug": "cse-cybersecurity"},
        ],
    },
    {
        "code": "BTECH_IT",
        "name": "Bachelor of Technology in Information Technology",
        "short_name": "B.Tech IT",
        "discipline_code": "COMP_INFO",
        "degree_type_code": "UG",
        "duration_years": 4.0,
        "slug": "btech-it",
        "description": "Applied computing program with emphasis on enterprise software, network administration, and web engineering.",
        "specializations": [
            {"code": "IT-WEB", "name": "Full Stack Web & Mobile Technologies", "slug": "it-web-tech"},
            {"code": "IT-INFOSEC", "name": "Enterprise Information Security", "slug": "it-infosec"},
        ],
    },
    {
        "code": "BTECH_AIDS",
        "name": "Bachelor of Technology in Artificial Intelligence & Data Science",
        "short_name": "B.Tech AI & DS",
        "discipline_code": "AI_DS",
        "degree_type_code": "UG",
        "duration_years": 4.0,
        "slug": "btech-ai-ds",
        "description": "Specialized curriculum combining machine learning, deep neural models, statistical analysis, and big data architectures.",
        "specializations": [
            {"code": "AIDS-ML", "name": "Machine Learning & Natural Language Processing", "slug": "aids-machine-learning"},
            {"code": "AIDS-BIGDATA", "name": "Big Data Engineering & Analytics", "slug": "aids-big-data"},
        ],
    },
    {
        "code": "BTECH_ECE",
        "name": "Bachelor of Technology in Electronics & Communication Engineering",
        "short_name": "B.Tech ECE",
        "discipline_code": "ELEC_COMM",
        "degree_type_code": "UG",
        "duration_years": 4.0,
        "slug": "btech-ece",
        "description": "Core engineering program covering analogue and digital circuits, signal processing, and telecommunications.",
        "specializations": [
            {"code": "ECE-EMBED", "name": "Embedded Systems & Internet of Things", "slug": "ece-embedded-iot"},
            {"code": "ECE-VLSI", "name": "VLSI Design & Semiconductor Technology", "slug": "ece-vlsi-design"},
        ],
    },
    {
        "code": "BTECH_MECH",
        "name": "Bachelor of Technology in Mechanical Engineering",
        "short_name": "B.Tech MECH",
        "discipline_code": "MECH_ENGG",
        "degree_type_code": "UG",
        "duration_years": 4.0,
        "slug": "btech-mech",
        "description": "Classical and advanced mechanical systems, CAD/CAM manufacturing, thermal dynamics, and robotics.",
        "specializations": [
            {"code": "MECH-ROBOT", "name": "Robotics & Industrial Automation", "slug": "mech-robotics"},
        ],
    },
    {
        "code": "BTECH_CIVIL",
        "name": "Bachelor of Technology in Civil Engineering",
        "short_name": "B.Tech CIVIL",
        "discipline_code": "CIVIL_ENGG",
        "degree_type_code": "UG",
        "duration_years": 4.0,
        "slug": "btech-civil",
        "description": "Infrastructure engineering, structural analysis, transportation planning, and geotechnical surveys.",
        "specializations": [
            {"code": "CIVIL-STRUCT", "name": "Structural Analysis & Seismic Design", "slug": "civil-structural"},
        ],
    },
]

SKILLS_DATA = [
    # Programming Languages
    {"code": "SKL-PYTHON", "name": "Python Programming", "category": "technical", "slug": "python-programming", "description": "Core syntax, data types, standard library, and algorithmic problem-solving in Python."},
    {"code": "SKL-JAVASCRIPT", "name": "JavaScript (ES6+)", "category": "technical", "slug": "javascript", "description": "Modern ECMAScript standards, asynchronous promises, event loop, and DOM manipulation."},
    {"code": "SKL-TYPESCRIPT", "name": "TypeScript", "category": "technical", "slug": "typescript", "description": "Static typing, generics, interfaces, and compile-time correctness for JavaScript."},
    {"code": "SKL-SQL", "name": "SQL & Relational Querying", "category": "technical", "slug": "sql-querying", "description": "Complex joins, indexing, aggregation, subqueries, and relational schema modeling."},
    {"code": "SKL-CPP", "name": "C++ Programming", "category": "technical", "slug": "cpp-programming", "description": "Memory pointers, STL containers, templates, and low-level resource management."},
    {"code": "SKL-JAVA", "name": "Java Programming", "category": "technical", "slug": "java-programming", "description": "Object-oriented principles, JVM memory model, multithreading, and collections framework."},

    # Frontend Technologies
    {"code": "SKL-HTMLCSS", "name": "HTML5 & Modern CSS", "category": "technical", "slug": "html5-css3", "description": "Semantic markup, responsive layouts, Flexbox, Grid, and accessibility (WCAG)."},
    {"code": "SKL-REACT", "name": "React.js", "category": "technical", "slug": "react-js", "description": "Component lifecycle, hooks, state management, memoization, and virtual DOM rendering."},
    {"code": "SKL-NEXTJS", "name": "Next.js", "category": "technical", "slug": "next-js", "description": "App Router, Server Components, SSR, static site generation, and route handlers."},
    {"code": "SKL-TAILWIND", "name": "Tailwind CSS", "category": "technical", "slug": "tailwind-css", "description": "Utility-first design system architecture and responsive UI layout engineering."},

    # Backend & APIs
    {"code": "SKL-NODEJS", "name": "Node.js Runtime", "category": "technical", "slug": "node-js", "description": "Asynchronous event-driven I/O, streams, buffers, and server-side package ecosystem."},
    {"code": "SKL-EXPRESS", "name": "Express.js", "category": "technical", "slug": "express-js", "description": "Middleware pipelines, routing, request validation, and error handling."},
    {"code": "SKL-FASTAPI", "name": "FastAPI", "category": "technical", "slug": "fastapi", "description": "Asynchronous Python web framework with OpenAPI schemas and Pydantic validation."},
    {"code": "SKL-REST", "name": "RESTful API Design", "category": "technical", "slug": "restful-apis", "description": "Resource URI modeling, HTTP verb conventions, status codes, and pagination."},

    # Databases & Storage
    {"code": "SKL-POSTGRES", "name": "PostgreSQL", "category": "technical", "slug": "postgresql", "description": "ACID guarantees, query plans, partitioning, and relational integrity constraints."},
    {"code": "SKL-MONGODB", "name": "MongoDB & NoSQL", "category": "technical", "slug": "mongodb-nosql", "description": "Document-oriented data storage, aggregation pipelines, and indexing."},
    {"code": "SKL-REDIS", "name": "Redis In-Memory Store", "category": "technical", "slug": "redis", "description": "Caching strategies, TTL expiration, distributed key-value storage, and pub/sub queues."},

    # Cloud, DevOps & Tools
    {"code": "SKL-GIT", "name": "Git & Version Control", "category": "technical", "slug": "git-version-control", "description": "Branching workflows, rebasing, merge conflict resolution, and pull requests."},
    {"code": "SKL-DOCKER", "name": "Docker & Containerization", "category": "technical", "slug": "docker", "description": "Dockerfile authoring, multi-stage images, networking, and container orchestration."},
    {"code": "SKL-LINUX", "name": "Linux & Bash Scripting", "category": "technical", "slug": "linux-bash", "description": "Command line navigation, file permissions, shell automation, and process management."},
    {"code": "SKL-CICD", "name": "CI/CD Pipelines", "category": "technical", "slug": "ci-cd-pipelines", "description": "Automated build, test, and container deployment workflows (e.g. GitHub Actions)."},
    {"code": "SKL-CLOUD", "name": "Cloud Computing Fundamentals", "category": "technical", "slug": "cloud-fundamentals", "description": "Compute instances, object buckets (S3), virtual networks, and serverless architectures."},

    # Data Structures, Algorithms & Computer Science Core
    {"code": "SKL-DSA", "name": "Data Structures", "category": "technical", "slug": "data-structures", "description": "Arrays, linked lists, stacks, queues, hash tables, trees, heaps, and graphs."},
    {"code": "SKL-ALGO", "name": "Algorithm Analysis & Design", "category": "technical", "slug": "algorithm-design", "description": "Asymptotic Big-O complexity, divide-and-conquer, greedy, dynamic programming, and graph search."},
    {"code": "SKL-DBMS", "name": "DBMS Theory & Transactions", "category": "technical", "slug": "dbms-theory", "description": "Relational calculus, Boyce-Codd normal forms, concurrency control, and WAL logging."},
    {"code": "SKL-OS", "name": "Operating Systems & Concurrency", "category": "technical", "slug": "operating-systems", "description": "Process scheduling, thread synchronisation, deadlocks, and virtual memory paging."},
    {"code": "SKL-NETWORKS", "name": "Computer Networks", "category": "technical", "slug": "computer-networks", "description": "OSI and TCP/IP stack, IP routing, TCP flow control, DNS, and TLS handshake."},

    # AI, Data Science & Machine Learning
    {"code": "SKL-ML", "name": "Machine Learning Fundamentals", "category": "technical", "slug": "machine-learning", "description": "Supervised regression and classification, unsupervised clustering, bias-variance tradeoff."},
    {"code": "SKL-DATA-ANALYSIS", "name": "Data Analysis & Pandas", "category": "technical", "slug": "data-analysis", "description": "Exploratory data analysis, Pandas dataframes, NumPy arrays, and data cleaning."},
    {"code": "SKL-DL", "name": "Deep Learning & Neural Networks", "category": "technical", "slug": "deep-learning", "description": "Forward and backpropagation, activation functions, CNNs, and sequence models."},

    # Software Engineering & Architecture
    {"code": "SKL-SYSTEM-DESIGN", "name": "System Design & Architecture", "category": "domain", "slug": "system-design", "description": "High-level architecture, load balancers, database sharding, microservices, and CAP theorem."},
    {"code": "SKL-TESTING", "name": "Software Testing & QA", "category": "technical", "slug": "software-testing", "description": "Unit testing, integration testing, mocking, test-driven development, and coverage analysis."},
    {"code": "SKL-OOP", "name": "Object-Oriented Design & SOLID", "category": "domain", "slug": "oop-solid-design", "description": "Inheritance, polymorphism, encapsulation, composition, and SOLID architectural principles."},

    # Design, UI/UX
    {"code": "SKL-UIDESIGN", "name": "UI Design & Typography", "category": "technical", "slug": "ui-design", "description": "Color theory, visual hierarchy, layout grids, typography scales, and component libraries."},
    {"code": "SKL-FIGMA", "name": "Figma & Interactive Prototyping", "category": "technical", "slug": "figma-prototyping", "description": "Wireframing, autolayout, design tokens, interactive components, and handoff workflows."},

    # Professional & Foundational Skills
    {"code": "SKL-TECH-COMM", "name": "Technical Communication", "category": "soft_skill", "slug": "technical-communication", "description": "Architecture documentation, code review discussions, API specifications, and presentation."},
    {"code": "SKL-PROBLEM-SOLVING", "name": "Analytical Problem Solving", "category": "analytical", "slug": "analytical-problem-solving", "description": "Deconstructing ambiguity, root-cause analysis, and systematic algorithmic derivation."},
    {"code": "SKL-APTITUDE", "name": "Quantitative Aptitude & Reasoning", "category": "analytical", "slug": "quantitative-aptitude", "description": "Arithmetic reasoning, permutations, probability, algebra, and logical deductions."},
]

CAREERS_DATA = [
    {
        "code": "CAR-FRONTEND",
        "title": "Frontend Software Engineer",
        "industry": "Technology / Web",
        "slug": "frontend-software-engineer",
        "description": "Builds responsive, high-performance web applications with modern client-side architectures.",
        "skills": [
            ("SKL-JAVASCRIPT", "required", 1.0),
            ("SKL-TYPESCRIPT", "required", 0.9),
            ("SKL-REACT", "required", 1.0),
            ("SKL-HTMLCSS", "required", 0.9),
            ("SKL-NEXTJS", "preferred", 0.8),
            ("SKL-TAILWIND", "preferred", 0.7),
            ("SKL-GIT", "required", 0.8),
            ("SKL-TESTING", "preferred", 0.7),
            ("SKL-UIDESIGN", "bonus", 0.5),
        ],
    },
    {
        "code": "CAR-BACKEND",
        "title": "Backend Software Engineer",
        "industry": "Technology / Systems",
        "slug": "backend-software-engineer",
        "description": "Architects resilient server systems, scalable microservices, database schemas, and secure REST APIs.",
        "skills": [
            ("SKL-PYTHON", "required", 0.9),
            ("SKL-NODEJS", "required", 0.9),
            ("SKL-REST", "required", 1.0),
            ("SKL-SQL", "required", 1.0),
            ("SKL-POSTGRES", "required", 0.9),
            ("SKL-REDIS", "preferred", 0.8),
            ("SKL-DOCKER", "preferred", 0.8),
            ("SKL-SYSTEM-DESIGN", "preferred", 0.8),
            ("SKL-GIT", "required", 0.8),
        ],
    },
    {
        "code": "CAR-FULLSTACK",
        "title": "Full Stack Engineer",
        "industry": "Technology / SaaS",
        "slug": "full-stack-engineer",
        "description": "Possesses end-to-end competency across client browser interfaces, application servers, databases, and deployments.",
        "skills": [
            ("SKL-JAVASCRIPT", "required", 1.0),
            ("SKL-TYPESCRIPT", "required", 0.9),
            ("SKL-REACT", "required", 0.9),
            ("SKL-NODEJS", "required", 0.9),
            ("SKL-REST", "required", 0.9),
            ("SKL-SQL", "required", 0.9),
            ("SKL-POSTGRES", "required", 0.8),
            ("SKL-GIT", "required", 0.8),
            ("SKL-DOCKER", "preferred", 0.7),
            ("SKL-TESTING", "preferred", 0.7),
        ],
    },
    {
        "code": "CAR-SWE",
        "title": "Core Software Engineer",
        "industry": "Technology",
        "slug": "software-engineer",
        "description": "Generalist software engineer proficient in fundamental algorithms, systems programming, and high-quality implementation.",
        "skills": [
            ("SKL-DSA", "required", 1.0),
            ("SKL-ALGO", "required", 1.0),
            ("SKL-OOP", "required", 0.9),
            ("SKL-OS", "preferred", 0.8),
            ("SKL-NETWORKS", "preferred", 0.8),
            ("SKL-GIT", "required", 0.8),
            ("SKL-TESTING", "required", 0.8),
            ("SKL-PROBLEM-SOLVING", "required", 0.9),
        ],
    },
    {
        "code": "CAR-DATA-ANALYST",
        "title": "Data Analyst",
        "industry": "Business Intelligence / Analytics",
        "slug": "data-analyst",
        "description": "Extracts operational insights, builds predictive data models, and communicates quantitative metrics.",
        "skills": [
            ("SKL-SQL", "required", 1.0),
            ("SKL-PYTHON", "required", 0.9),
            ("SKL-DATA-ANALYSIS", "required", 1.0),
            ("SKL-POSTGRES", "preferred", 0.8),
            ("SKL-APTITUDE", "required", 0.8),
            ("SKL-TECH-COMM", "preferred", 0.7),
        ],
    },
    {
        "code": "CAR-ML-ENGG",
        "title": "Machine Learning Engineer",
        "industry": "AI & Data",
        "slug": "machine-learning-engineer",
        "description": "Designs, trains, and productionizes predictive machine learning models, neural pipelines, and evaluation frameworks.",
        "skills": [
            ("SKL-PYTHON", "required", 1.0),
            ("SKL-ML", "required", 1.0),
            ("SKL-DATA-ANALYSIS", "required", 0.9),
            ("SKL-DL", "preferred", 0.8),
            ("SKL-DSA", "preferred", 0.8),
            ("SKL-DOCKER", "preferred", 0.7),
            ("SKL-GIT", "required", 0.8),
        ],
    },
    {
        "code": "CAR-DEVOPS",
        "title": "DevOps & Cloud Engineer",
        "industry": "Cloud Infrastructure",
        "slug": "devops-engineer",
        "description": "Automates continuous integration, manages cloud virtualization, enforces infrastructure-as-code and observability.",
        "skills": [
            ("SKL-DOCKER", "required", 1.0),
            ("SKL-LINUX", "required", 1.0),
            ("SKL-CICD", "required", 1.0),
            ("SKL-CLOUD", "required", 0.9),
            ("SKL-GIT", "required", 0.9),
            ("SKL-NETWORKS", "preferred", 0.8),
            ("SKL-SYSTEM-DESIGN", "preferred", 0.7),
        ],
    },
    {
        "code": "CAR-UIUX",
        "title": "UI/UX Product Designer",
        "industry": "Product Design",
        "slug": "ui-ux-product-designer",
        "description": "Translates complex human workflows into intuitive user experiences, design systems, and clickable prototypes.",
        "skills": [
            ("SKL-UIDESIGN", "required", 1.0),
            ("SKL-FIGMA", "required", 1.0),
            ("SKL-HTMLCSS", "preferred", 0.7),
            ("SKL-TECH-COMM", "preferred", 0.8),
        ],
    },
]


async def seed_academic_catalog(db: AsyncSession) -> Dict[str, int]:
    """Idempotently populates the national catalog taxonomy."""
    stats = {
        "sources": 0,
        "versions": 0,
        "disciplines": 0,
        "degree_types": 0,
        "programs": 0,
        "specializations": 0,
        "skills": 0,
        "careers": 0,
        "career_skill_mappings": 0,
        "program_skill_mappings": 0,
        "program_career_mappings": 0,
    }

    # 1. Source & Version
    source_res = await db.execute(
        select(AcademicCatalogSource).where(AcademicCatalogSource.code == "AICTE_UGC_CURATED")
    )
    source = source_res.scalar_one_or_none()
    if not source:
        source = AcademicCatalogSource(
            code="AICTE_UGC_CURATED",
            name="National Curricular Framework Model (Curated Dataset)",
            organization="All India Council for Technical Education & University Grants Commission",
            website_url="https://www.aicte-india.org",
            is_authoritative=True,
        )
        db.add(source)
        await db.flush()
        stats["sources"] += 1

    version_res = await db.execute(
        select(AcademicCatalogVersion).where(AcademicCatalogVersion.version_tag == "2026.1")
    )
    version = version_res.scalar_one_or_none()
    if not version:
        version = AcademicCatalogVersion(
            version_tag="2026.1",
            source_id=source.id,
            status="active",
            effective_date=date(2026, 1, 1),
            notes="Initial curated dataset for higher technical education programs, courses, and skills.",
        )
        db.add(version)
        await db.flush()
        stats["versions"] += 1

    # 2. Disciplines
    disciplines_by_code: Dict[str, AcademicDiscipline] = {}
    for d in DISCIPLINES_DATA:
        res = await db.execute(select(AcademicDiscipline).where(AcademicDiscipline.code == d["code"]))
        disc = res.scalar_one_or_none()
        if not disc:
            disc = AcademicDiscipline(
                code=d["code"],
                name=d["name"],
                display_name=d["display_name"],
                slug=d["slug"],
                description=d["description"],
                status="active",
                version_id=version.id,
                source_id=source.id,
            )
            db.add(disc)
            await db.flush()
            stats["disciplines"] += 1
        disciplines_by_code[d["code"]] = disc

    # 3. Degree Types
    degrees_by_code: Dict[str, DegreeType] = {}
    for dt in DEGREE_TYPES_DATA:
        res = await db.execute(select(DegreeType).where(DegreeType.code == dt["code"]))
        deg = res.scalar_one_or_none()
        if not deg:
            deg = DegreeType(
                code=dt["code"],
                name=dt["name"],
                short_name=dt["short_name"],
                level=dt["level"],
                typical_duration_years=dt["typical_duration_years"],
                status="active",
            )
            db.add(deg)
            await db.flush()
            stats["degree_types"] += 1
        degrees_by_code[dt["code"]] = deg

    # 4. Programs & Specializations
    programs_by_code: Dict[str, ProgramCatalog] = {}
    for p in PROGRAMS_DATA:
        res = await db.execute(select(ProgramCatalog).where(ProgramCatalog.code == p["code"]))
        prog = res.scalar_one_or_none()
        if not prog:
            prog = ProgramCatalog(
                code=p["code"],
                name=p["name"],
                short_name=p["short_name"],
                discipline_id=disciplines_by_code[p["discipline_code"]].id,
                degree_type_id=degrees_by_code[p["degree_type_code"]].id,
                duration_years=p["duration_years"],
                description=p["description"],
                slug=p["slug"],
                status="active",
                version_id=version.id,
                source_id=source.id,
            )
            db.add(prog)
            await db.flush()
            stats["programs"] += 1
        programs_by_code[p["code"]] = prog

        for spec in p.get("specializations", []):
            spec_res = await db.execute(
                select(ProgramSpecialization).where(
                    ProgramSpecialization.program_catalog_id == prog.id,
                    ProgramSpecialization.code == spec["code"],
                )
            )
            if not spec_res.scalar_one_or_none():
                sp = ProgramSpecialization(
                    program_catalog_id=prog.id,
                    code=spec["code"],
                    name=spec["name"],
                    slug=spec["slug"],
                    status="active",
                )
                db.add(sp)
                stats["specializations"] += 1

    # 5. Skills
    skills_by_code: Dict[str, SkillCatalog] = {}
    for s in SKILLS_DATA:
        res = await db.execute(select(SkillCatalog).where(SkillCatalog.code == s["code"]))
        skill = res.scalar_one_or_none()
        if not skill:
            skill = SkillCatalog(
                code=s["code"],
                name=s["name"],
                category=s["category"],
                description=s["description"],
                slug=s["slug"],
                status="active",
            )
            db.add(skill)
            await db.flush()
            stats["skills"] += 1
        skills_by_code[s["code"]] = skill

    # 6. Careers & CareerSkillMappings
    careers_by_code: Dict[str, CareerCatalog] = {}
    for c in CAREERS_DATA:
        res = await db.execute(select(CareerCatalog).where(CareerCatalog.code == c["code"]))
        career = res.scalar_one_or_none()
        if not career:
            career = CareerCatalog(
                code=c["code"],
                title=c["title"],
                industry=c["industry"],
                description=c["description"],
                slug=c["slug"],
                status="active",
            )
            db.add(career)
            await db.flush()
            stats["careers"] += 1
        careers_by_code[c["code"]] = career

        for skill_code, importance, weight in c.get("skills", []):
            if skill_code in skills_by_code:
                skill_id = skills_by_code[skill_code].id
                map_res = await db.execute(
                    select(CareerSkillMapping).where(
                        CareerSkillMapping.career_id == career.id,
                        CareerSkillMapping.skill_id == skill_id,
                    )
                )
                if not map_res.scalar_one_or_none():
                    mapping = CareerSkillMapping(
                        career_id=career.id,
                        skill_id=skill_id,
                        importance=importance,
                        weight=weight,
                    )
                    db.add(mapping)
                    stats["career_skill_mappings"] += 1

    # 7. Connect Programs to Core Foundational Skills
    core_cse_skills = ["SKL-DSA", "SKL-ALGO", "SKL-PYTHON", "SKL-SQL", "SKL-OOP", "SKL-GIT", "SKL-PROBLEM-SOLVING"]
    for prog_code in ["BTECH_CSE", "BTECH_IT", "BTECH_AIDS"]:
        if prog_code in programs_by_code:
            prog_id = programs_by_code[prog_code].id
            for s_code in core_cse_skills:
                if s_code in skills_by_code:
                    sk_id = skills_by_code[s_code].id
                    ps_res = await db.execute(
                        select(ProgramSkillMapping).where(
                            ProgramSkillMapping.program_catalog_id == prog_id,
                            ProgramSkillMapping.skill_id == sk_id,
                        )
                    )
                    if not ps_res.scalar_one_or_none():
                        ps = ProgramSkillMapping(
                            program_catalog_id=prog_id,
                            skill_id=sk_id,
                            relevance_weight=1.0,
                            is_core=True,
                        )
                        db.add(ps)
                        stats["program_skill_mappings"] += 1

    # 8. Connect Programs to Career Destination Pathways
    prog_career_pairs = [
        ("BTECH_CSE", "CAR-SWE", 0.95),
        ("BTECH_CSE", "CAR-FULLSTACK", 0.90),
        ("BTECH_CSE", "CAR-BACKEND", 0.88),
        ("BTECH_IT", "CAR-FRONTEND", 0.90),
        ("BTECH_IT", "CAR-FULLSTACK", 0.88),
        ("BTECH_AIDS", "CAR-ML-ENGG", 0.95),
        ("BTECH_AIDS", "CAR-DATA-ANALYST", 0.90),
    ]
    for p_code, c_code, strength in prog_career_pairs:
        if p_code in programs_by_code and c_code in careers_by_code:
            p_id = programs_by_code[p_code].id
            c_id = careers_by_code[c_code].id
            pc_res = await db.execute(
                select(ProgramCareerMapping).where(
                    ProgramCareerMapping.program_catalog_id == p_id,
                    ProgramCareerMapping.career_id == c_id,
                )
            )
            if not pc_res.scalar_one_or_none():
                pc = ProgramCareerMapping(
                    program_catalog_id=p_id,
                    career_id=c_id,
                    match_strength=strength,
                )
                db.add(pc)
                stats["program_career_mappings"] += 1

    await db.commit()
    logger.info("Academic catalog seeded successfully: %s", stats)
    return stats


async def main():
    async with async_session_maker() as db:
        await seed_academic_catalog(db)


if __name__ == "__main__":
    asyncio.run(main())
