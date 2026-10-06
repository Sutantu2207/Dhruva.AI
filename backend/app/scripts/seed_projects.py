"""DHRUVA.AI - Seed Script: Canonical Project Templates Library (Domain 8).

Defines canonical engineering project templates across three difficulty tiers:
- BEGINNER (Personal Portfolio, Expense Tracker, Weather Dashboard)
- INTERMEDIATE (Student Management System, E-Commerce Platform, Markdown Blog)
- ADVANCED (Full Stack LMS, AI Study Assistant, FinTech Transaction Ledger)

Provides complete blueprints:
- Objective & Problem Statement
- Required & Demonstrated Skills
- Mapped Canonical Concepts
- Deliverables, Evidence & Verification Criteria
- 10-Dimension Evaluation Rubric Baseline
"""

import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger("dhruva.seed_projects")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


PROJECT_TEMPLATES = [
    # --- BEGINNER TIER ---
    {
        "code": "PRJ-BEG-PORTFOLIO",
        "title": "Interactive Developer Portfolio & Showcase",
        "level": "beginner",
        "project_type": "personal",
        "career_target": "CAR-FRONTEND",
        "technologies": ["HTML5", "CSS3", "JavaScript", "Tailwind CSS"],
        "skills_required": ["SKL-HTMLCSS", "SKL-JAVASCRIPT", "SKL-GIT"],
        "concept_names": ["HTML5 Semantic Document Structure", "CSS Box Model, Flexbox & Grid", "JavaScript DOM Events & Manipulations"],
        "problem_statement": "Early-career developers lack a single-page accessible portfolio showcasing verified academic artifacts, live project demos, and resume credentials.",
        "solution": "Responsive, static-hosted developer portfolio featuring accessible navigation, dark mode toggle, dynamic project filtering, and contact form integration.",
        "deliverables": [
            "GitHub repository with clean Git commit history",
            "Live deployment link (Vercel / GitHub Pages)",
            "Lighthouse accessibility and performance audit report (>90)",
        ],
        "rubric_baseline": {
            "technical_depth": 65.0,
            "code_quality": 80.0,
            "architecture_quality": 70.0,
            "documentation_quality": 85.0,
            "testing_quality": 60.0,
            "practical_application": 85.0,
            "originality": 70.0,
            "professional_presentation": 90.0,
        },
    },
    {
        "code": "PRJ-BEG-EXPENSE",
        "title": "Personal Budget & Expense Tracker",
        "level": "beginner",
        "project_type": "academic",
        "career_target": "CAR-FRONTEND",
        "technologies": ["React", "JavaScript", "CSS3", "LocalStorage"],
        "skills_required": ["SKL-JAVASCRIPT", "SKL-REACT", "SKL-HTMLCSS"],
        "concept_names": ["React Components, Props & JSX", "React State Management with Hooks (useState, useEffect)"],
        "problem_statement": "Managing discretionary expenditures requires categorized transaction entry, visual percentage breakdowns, and persistent local storage without heavy backend overhead.",
        "solution": "Client-side React application with transaction creation, category filtering, summary metric cards, and responsive state updates.",
        "deliverables": [
            "Modular React component structure with custom hooks",
            "Responsive layout tested on mobile and desktop viewports",
            "Unit tests for budget calculation functions",
        ],
        "rubric_baseline": {
            "technical_depth": 70.0,
            "code_quality": 75.0,
            "architecture_quality": 75.0,
            "documentation_quality": 75.0,
            "testing_quality": 70.0,
            "practical_application": 80.0,
            "originality": 65.0,
            "professional_presentation": 75.0,
        },
    },
    {
        "code": "PRJ-BEG-WEATHER",
        "title": "Real-Time Weather & Forecast Dashboard",
        "level": "beginner",
        "project_type": "personal",
        "career_target": "CAR-FRONTEND",
        "technologies": ["JavaScript", "HTML5", "CSS3", "Fetch API"],
        "skills_required": ["SKL-JAVASCRIPT", "SKL-REST", "SKL-HTMLCSS"],
        "concept_names": ["Asynchronous JavaScript: Promises & Async/Await", "JavaScript DOM Events & Manipulations"],
        "problem_statement": "Students need practical exposure integrating third-party asynchronous REST APIs, handling error states, and dynamically rendering weather metrics.",
        "solution": "Single-page dashboard querying OpenWeatherMap API for multi-day temperature, humidity, wind velocity, and location geocoding.",
        "deliverables": [
            "Asynchronous HTTP fetching with try/catch error boundaries",
            "Loading skeletons and graceful failure handling for invalid cities",
            "Deployed live demonstration",
        ],
        "rubric_baseline": {
            "technical_depth": 70.0,
            "code_quality": 75.0,
            "architecture_quality": 70.0,
            "documentation_quality": 70.0,
            "testing_quality": 65.0,
            "practical_application": 75.0,
            "originality": 65.0,
            "professional_presentation": 80.0,
        },
    },

    # --- INTERMEDIATE TIER ---
    {
        "code": "PRJ-INT-SMS",
        "title": "Academic Student Management System",
        "level": "intermediate",
        "project_type": "academic",
        "career_target": "CAR-BACKEND",
        "technologies": ["Node.js", "Express", "PostgreSQL", "SQL"],
        "skills_required": ["SKL-NODEJS", "SKL-EXPRESS", "SKL-SQL", "SKL-POSTGRES", "SKL-REST"],
        "concept_names": ["HTTP Protocol & RESTful API Architecture", "SQL Joins and Multi-Table Queries", "Database Normalization (1NF, 2NF, 3NF, BCNF)"],
        "problem_statement": "Academic departments struggle with manual record keeping for course enrollments, attendance tracking, and student grades across multiple sections.",
        "solution": "RESTful backend microservice in Express and PostgreSQL supporting relational multi-table CRUD, normalized schema design, and parameterized SQL queries.",
        "deliverables": [
            "Normalized 3NF relational schema migration script",
            "Postman API collection with sample request payloads",
            "Automated integration tests verifying enrollment constraint checks",
        ],
        "rubric_baseline": {
            "technical_depth": 80.0,
            "code_quality": 80.0,
            "architecture_quality": 80.0,
            "documentation_quality": 85.0,
            "testing_quality": 75.0,
            "practical_application": 90.0,
            "originality": 75.0,
            "professional_presentation": 80.0,
        },
    },
    {
        "code": "PRJ-INT-ECOMM",
        "title": "E-Commerce Microstore with Cart & Stripe Checkout",
        "level": "intermediate",
        "project_type": "capstone",
        "career_target": "CAR-FULLSTACK",
        "technologies": ["React", "Node.js", "Express", "PostgreSQL", "Tailwind CSS"],
        "skills_required": ["SKL-REACT", "SKL-NODEJS", "SKL-REST", "SKL-SQL", "SKL-GIT"],
        "concept_names": ["React State Management with Hooks (useState, useEffect)", "Express Middleware & Routing Architecture", "SQL DDL and Basic Queries"],
        "problem_statement": "Modern e-commerce requires synchronized client-side cart states, server-authoritative inventory checks, and transactional checkout flows.",
        "solution": "Full stack web application featuring product catalog browsing, persistent shopping cart, quantity controls, and mock payment gateway webhooks.",
        "deliverables": [
            "Separate frontend and backend repositories or monorepo structure",
            "Database schema with foreign-key cascades for orders and items",
            "Live staging deployment with sample product seed data",
        ],
        "rubric_baseline": {
            "technical_depth": 85.0,
            "code_quality": 80.0,
            "architecture_quality": 85.0,
            "documentation_quality": 80.0,
            "testing_quality": 75.0,
            "practical_application": 90.0,
            "originality": 80.0,
            "professional_presentation": 85.0,
        },
    },
    {
        "code": "PRJ-INT-BLOG",
        "title": "Full Stack Markdown Engineering Blog Platform",
        "level": "intermediate",
        "project_type": "personal",
        "career_target": "CAR-FULLSTACK",
        "technologies": ["Next.js", "TypeScript", "PostgreSQL", "Tailwind CSS"],
        "skills_required": ["SKL-TYPESCRIPT", "SKL-NEXTJS", "SKL-POSTGRES", "SKL-REST"],
        "concept_names": ["React Components, Props & JSX", "SQL Joins and Multi-Table Queries", "HTTP Protocol & RESTful API Architecture"],
        "problem_statement": "Engineering students need a platform to publish technical articles, format syntax-highlighted code snippets, and receive peer reviews.",
        "solution": "Content management system built on Next.js App Router with Server Side Rendering, Markdown parsing, tagging, and author profiles.",
        "deliverables": [
            "TypeScript type safety across all components and server actions",
            "SEO metadata integration and dynamic Open Graph image generation",
            "Database seed script and Jest unit test coverage",
        ],
        "rubric_baseline": {
            "technical_depth": 80.0,
            "code_quality": 85.0,
            "architecture_quality": 80.0,
            "documentation_quality": 85.0,
            "testing_quality": 75.0,
            "practical_application": 85.0,
            "originality": 80.0,
            "professional_presentation": 85.0,
        },
    },

    # --- ADVANCED TIER ---
    {
        "code": "PRJ-ADV-LMS",
        "title": "Full Stack Multi-Tenant Learning Management System",
        "level": "advanced",
        "project_type": "capstone",
        "career_target": "CAR-FULLSTACK",
        "technologies": ["Next.js", "FastAPI", "PostgreSQL", "Redis", "Docker"],
        "skills_required": ["SKL-TYPESCRIPT", "SKL-FASTAPI", "SKL-POSTGRES", "SKL-REDIS", "SKL-DOCKER", "SKL-SYSTEM-DESIGN"],
        "concept_names": ["ACID Properties & Transaction Isolation", "JWT Authentication & Password Hashing", "Database Indexing & B-Trees"],
        "problem_statement": "University education requires multi-tenant isolation, course curriculum delivery, automated quizzes, and student progress telemetry at scale.",
        "solution": "Enterprise SaaS architecture with RBAC permissions, Redis distributed rate-limiting, Dockerized multi-stage container deployment, and ACID transaction safety.",
        "deliverables": [
            "Docker Compose multi-service topology (Next.js, FastAPI, PostgreSQL, Redis)",
            "Automated pytest test suite with >80% code coverage",
            "Comprehensive OpenAPI architecture documentation and entity diagram",
        ],
        "rubric_baseline": {
            "technical_depth": 95.0,
            "code_quality": 90.0,
            "architecture_quality": 95.0,
            "documentation_quality": 90.0,
            "testing_quality": 90.0,
            "practical_application": 95.0,
            "originality": 85.0,
            "professional_presentation": 95.0,
        },
    },
    {
        "code": "PRJ-ADV-AI-STUDY",
        "title": "AI Study Assistant & Syllabus Semantic Search",
        "level": "advanced",
        "project_type": "capstone",
        "career_target": "CAR-AI-ENGG",
        "technologies": ["Python", "FastAPI", "PostgreSQL", "pgvector", "Gemini API"],
        "skills_required": ["SKL-PYTHON", "SKL-ML", "SKL-FASTAPI", "SKL-POSTGRES"],
        "concept_names": ["Supervised Learning: Linear & Logistic Regression", "Model Evaluation Metrics & Validation", "Database Indexing & B-Trees"],
        "problem_statement": "Students struggle to locate relevant lecture notes across multi-semester syllabi and need supervised conceptual Q&A with exact source citations.",
        "solution": "Retrieval-Augmented Generation (RAG) platform indexing textbook chapters into vector embeddings via pgvector, providing verified citations and prompt injection defense.",
        "deliverables": [
            "Text chunking, embedding generation, and cosine similarity search engine",
            "Grounding verification module checking citation integrity",
            "Security evaluation suite verifying prompt injection filtering",
        ],
        "rubric_baseline": {
            "technical_depth": 95.0,
            "code_quality": 90.0,
            "architecture_quality": 95.0,
            "documentation_quality": 90.0,
            "testing_quality": 85.0,
            "practical_application": 95.0,
            "originality": 90.0,
            "professional_presentation": 90.0,
        },
    },
    {
        "code": "PRJ-ADV-FINTECH",
        "title": "FinTech High-Throughput Transaction Ledger Simulator",
        "level": "advanced",
        "project_type": "academic",
        "career_target": "CAR-BACKEND",
        "technologies": ["Node.js", "PostgreSQL", "Redis", "Docker"],
        "skills_required": ["SKL-SQL", "SKL-POSTGRES", "SKL-REDIS", "SKL-SYSTEM-DESIGN", "SKL-OOP"],
        "concept_names": ["ACID Properties & Transaction Isolation", "Database Indexing & B-Trees", "Asymptotic Big-O Complexity Analysis"],
        "problem_statement": "Financial applications must guarantee zero double-spending, strictly serialized ledger transactions, and auditability under concurrent request surges.",
        "solution": "Double-entry bookkeeping engine utilizing PostgreSQL row-level locks (`SELECT FOR UPDATE`), Redis distributed locks, and idempotency key checks.",
        "deliverables": [
            "Concurrent stress-test script demonstrating deadlock avoidance",
            "Immutable audit trail log with SHA-256 state hashing",
            "Benchmark report measuring transactions-per-second (TPS)",
        ],
        "rubric_baseline": {
            "technical_depth": 95.0,
            "code_quality": 90.0,
            "architecture_quality": 95.0,
            "documentation_quality": 90.0,
            "testing_quality": 95.0,
            "practical_application": 90.0,
            "originality": 85.0,
            "professional_presentation": 90.0,
        },
    },
]


def get_project_templates() -> List[Dict[str, Any]]:
    """Returns the canonical project templates library."""
    return PROJECT_TEMPLATES


async def main():
    logger.info("Project Template Library contains %d curated templates across Beginner, Intermediate, and Advanced tiers.", len(PROJECT_TEMPLATES))
    for t in PROJECT_TEMPLATES:
        logger.info("  [%s] %s (%s) -> Target: %s", t["level"].upper(), t["title"], t["code"], t["career_target"])


if __name__ == "__main__":
    asyncio.run(main())
