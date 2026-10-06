"""DHRUVA.AI - Seed Script: Canonical Course Catalog & Knowledge Concepts (Domains 2.5 & 4).

Idempotent seeding of:
- 12 Canonical Courses with credits, difficulty, and curriculum blueprints
- Canonical Knowledge Units (Concepts) with definitions and difficulty
- Concept Prerequisite Directed Graph (Prerequisite Relationships)
- Concept-to-Skill & Course-to-Skill Mappings
"""

import asyncio
import logging
from typing import Dict, Any, List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.domains.catalog.models import (
    AcademicDiscipline,
    CourseCatalog,
    CourseSkillMapping,
    SkillCatalog,
)
from app.domains.content.models import (
    Concept,
    ConceptPrerequisite,
    ConceptSkill,
)

logger = logging.getLogger("dhruva.seed_courses")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


CANONICAL_COURSES = [
    {
        "code": "NAT-CS-PY",
        "title": "Python Programming Fundamentals",
        "discipline_code": "COMP_INFO",
        "default_credits": 3.0,
        "academic_level": "introductory",
        "slug": "python-programming-fundamentals",
        "description": "Foundations of computational problem solving using Python, covering syntax, data types, control flow, functions, OOP, and file I/O.",
        "skills": [("SKL-PYTHON", "foundational", 1.0), ("SKL-PROBLEM-SOLVING", "foundational", 0.8)],
    },
    {
        "code": "NAT-CS-DSA",
        "title": "Data Structures & Algorithms",
        "discipline_code": "COMP_INFO",
        "default_credits": 4.0,
        "academic_level": "intermediate",
        "slug": "data-structures-and-algorithms",
        "description": "Rigorous analysis of fundamental abstract data types, asymptotic complexity, sorting, searching, recursion, trees, graphs, and dynamic programming.",
        "skills": [("SKL-DSA", "expert", 1.0), ("SKL-ALGO", "expert", 1.0), ("SKL-PROBLEM-SOLVING", "applied", 0.9)],
    },
    {
        "code": "NAT-CS-DBMS",
        "title": "Database Management Systems",
        "discipline_code": "COMP_INFO",
        "default_credits": 3.0,
        "academic_level": "intermediate",
        "slug": "database-management-systems",
        "description": "Relational data modeling, SQL queries, normalization, ACID transaction management, indexing, query optimization, and concurrency control.",
        "skills": [("SKL-SQL", "applied", 1.0), ("SKL-POSTGRES", "applied", 0.9), ("SKL-DBMS", "applied", 0.8)],
    },
    {
        "code": "NAT-CS-WEB",
        "title": "Web Development Fundamentals",
        "discipline_code": "COMP_INFO",
        "default_credits": 3.0,
        "academic_level": "introductory",
        "slug": "web-development-fundamentals",
        "description": "Client-server web architecture, HTML5 semantic structure, CSS layout systems (Flexbox/Grid), JavaScript DOM manipulation, and asynchronous HTTP.",
        "skills": [("SKL-HTMLCSS", "applied", 1.0), ("SKL-JAVASCRIPT", "applied", 0.9), ("SKL-GIT", "foundational", 0.7)],
    },
    {
        "code": "NAT-CS-REACT",
        "title": "Modern Frontend Development with React",
        "discipline_code": "COMP_INFO",
        "default_credits": 3.0,
        "academic_level": "intermediate",
        "slug": "modern-frontend-development-react",
        "description": "Component-based architecture, declarative state with React hooks, props, lifecycle events, routing, and responsive CSS integration.",
        "skills": [("SKL-REACT", "applied", 1.0), ("SKL-TYPESCRIPT", "applied", 0.8), ("SKL-TAILWIND", "applied", 0.7)],
    },
    {
        "code": "NAT-CS-NODE",
        "title": "Backend Development with Node.js & REST APIs",
        "discipline_code": "COMP_INFO",
        "default_credits": 3.0,
        "academic_level": "intermediate",
        "slug": "backend-development-nodejs-rest",
        "description": "Server architecture using Node.js and Express, middleware design, JWT authentication, RESTful routing, and database integration.",
        "skills": [("SKL-NODEJS", "applied", 1.0), ("SKL-EXPRESS", "applied", 0.9), ("SKL-REST", "applied", 1.0), ("SKL-POSTGRES", "applied", 0.8)],
    },
    {
        "code": "NAT-CS-FULLSTACK",
        "title": "Full Stack Application Engineering",
        "discipline_code": "COMP_INFO",
        "default_credits": 4.0,
        "academic_level": "advanced",
        "slug": "full-stack-application-engineering",
        "description": "End-to-end multi-tier application engineering combining Next.js, FastAPI, PostgreSQL, Docker containerization, and production deployment.",
        "skills": [("SKL-REACT", "applied", 0.9), ("SKL-NEXTJS", "applied", 0.9), ("SKL-FASTAPI", "applied", 0.9), ("SKL-DOCKER", "applied", 0.8)],
    },
    {
        "code": "NAT-CS-ML",
        "title": "Machine Learning Fundamentals",
        "discipline_code": "AI_DS",
        "default_credits": 4.0,
        "academic_level": "intermediate",
        "slug": "machine-learning-fundamentals",
        "description": "Supervised and unsupervised learning, linear regression, logistic models, decision trees, neural networks, evaluation metrics, and scikit-learn.",
        "skills": [("SKL-PYTHON", "applied", 0.9), ("SKL-ML", "applied", 1.0), ("SKL-DATA-ANALYSIS", "applied", 0.9)],
    },
    {
        "code": "NAT-CS-SE",
        "title": "Software Engineering & System Architecture",
        "discipline_code": "COMP_INFO",
        "default_credits": 3.0,
        "academic_level": "advanced",
        "slug": "software-engineering-system-architecture",
        "description": "Software development life cycles, agile methodologies, design patterns, testing pyramids, microservices, and system scalability.",
        "skills": [("SKL-OOP", "expert", 1.0), ("SKL-SYSTEM-DESIGN", "applied", 0.9), ("SKL-TESTING", "applied", 0.9)],
    },
    {
        "code": "NAT-CS-UIUX",
        "title": "UI/UX Design & Human-Computer Interaction",
        "discipline_code": "COMP_INFO",
        "default_credits": 2.0,
        "academic_level": "introductory",
        "slug": "ui-ux-design-hci",
        "description": "Principles of user experience research, usability heuristics, wireframing, high-fidelity Figma prototyping, and design system creation.",
        "skills": [("SKL-UIDESIGN", "applied", 1.0), ("SKL-FIGMA", "applied", 1.0)],
    },
    {
        "code": "NAT-GEN-APT",
        "title": "Quantitative Aptitude & Logical Reasoning",
        "discipline_code": "COMP_INFO",
        "default_credits": 2.0,
        "academic_level": "introductory",
        "slug": "quantitative-aptitude-reasoning",
        "description": "Problem-solving under timed constraints, number theory, permutations & combinations, probability, data interpretation, and syllogisms.",
        "skills": [("SKL-APTITUDE", "applied", 1.0), ("SKL-PROBLEM-SOLVING", "applied", 0.9)],
    },
    {
        "code": "NAT-GEN-COMM",
        "title": "Technical Communication & Interview Preparation",
        "discipline_code": "COMP_INFO",
        "default_credits": 2.0,
        "academic_level": "introductory",
        "slug": "technical-communication-interviews",
        "description": "Engineering documentation, technical presentations, code review etiquette, resume crafting, and technical interview strategies.",
        "skills": [("SKL-TECH-COMM", "applied", 1.0)],
    },
]

# Canonical Concepts: (Name, Difficulty, Description, Associated Skill Code)
CANONICAL_CONCEPTS_DATA = [
    # Python & Programming Fundamentals
    ("Python Variables and Primitive Types", "beginner", "Integers, floats, strings, booleans, type casting and memory representation in Python.", "SKL-PYTHON"),
    ("Python Control Flow & Loops", "beginner", "Conditional if-else branches, while loops, for loops with range, break, and continue.", "SKL-PYTHON"),
    ("Python Functions and Scoping", "beginner", "Defining functions, positional and keyword arguments, *args, **kwargs, return statements, and LEGB scope.", "SKL-PYTHON"),
    ("Python Lists, Tuples, and Dictionaries", "beginner", "Indexing, slicing, list comprehensions, key-value mappings, dictionary methods, and hashability.", "SKL-PYTHON"),
    ("Object-Oriented Programming in Python", "intermediate", "Classes, instances, constructor __init__, inheritance, polymorphism, and encapsulation.", "SKL-PYTHON"),
    ("Python Exception Handling & File I/O", "intermediate", "Try-except-finally blocks, custom exceptions, context managers with open, and reading/writing files.", "SKL-PYTHON"),

    # Data Structures & Algorithms
    ("Asymptotic Big-O Complexity Analysis", "beginner", "Time and space complexity, worst-case, best-case, average-case analysis, and growth orders.", "SKL-ALGO"),
    ("Arrays and Dynamic Arrays", "beginner", "Contiguous memory layout, random access O(1), dynamic resizing amortized analysis, and array rotations.", "SKL-DSA"),
    ("Singly and Doubly Linked Lists", "intermediate", "Node pointers, traversal, head/tail insertion, deletion, and fast/slow pointer cycle detection.", "SKL-DSA"),
    ("Stacks and Queues", "intermediate", "LIFO and FIFO abstractions, balanced parenthesis matching, monotonic stack, and circular queue buffers.", "SKL-DSA"),
    ("Recursion and Divide-and-Conquer", "intermediate", "Base cases, recursive call stack, master theorem, merge sort, and quicksort partitioning.", "SKL-ALGO"),
    ("Binary Trees and Tree Traversals", "intermediate", "Tree hierarchy, depth-first traversals (preorder, inorder, postorder), and breadth-first level order traversal.", "SKL-DSA"),
    ("Binary Search Trees (BST)", "intermediate", "BST invariants, lookup, insertion, deletion with successor replacement, and tree balance properties.", "SKL-DSA"),
    ("Graph Representations and Traversals", "advanced", "Adjacency matrix vs adjacency list, Breadth-First Search (BFS), and Depth-First Search (DFS).", "SKL-DSA"),
    ("Shortest Path Algorithms (Dijkstra)", "advanced", "Single-source shortest paths on weighted graphs, priority queue min-heap implementation.", "SKL-ALGO"),
    ("Dynamic Programming Fundamentals", "advanced", "Optimal substructure, overlapping subproblems, memoization vs bottom-up tabulation, knapsack problem.", "SKL-ALGO"),

    # DBMS
    ("Relational Data Model & ER Diagrams", "beginner", "Entities, relationships, primary keys, foreign keys, cardinality, and relational schemas.", "SKL-DBMS"),
    ("SQL DDL and Basic Queries", "beginner", "CREATE TABLE, ALTER, DROP, SELECT, WHERE filtering, ORDER BY, and LIMIT clauses.", "SKL-SQL"),
    ("SQL Joins and Multi-Table Queries", "intermediate", "INNER JOIN, LEFT/RIGHT OUTER JOIN, FULL OUTER JOIN, CROSS JOIN, and self-joins.", "SKL-SQL"),
    ("SQL Aggregation and Grouping", "intermediate", "GROUP BY, HAVING, aggregate functions (COUNT, SUM, AVG, MIN, MAX), and window functions.", "SKL-SQL"),
    ("Database Normalization (1NF, 2NF, 3NF, BCNF)", "intermediate", "Functional dependencies, insertion/deletion anomalies, decomposition, and normal forms.", "SKL-DBMS"),
    ("ACID Properties & Transaction Isolation", "advanced", "Atomicity, consistency, isolation levels (dirty reads, non-repeatable reads, phantom reads), durability.", "SKL-DBMS"),
    ("Database Indexing & B-Trees", "advanced", "Clustered vs non-clustered indexes, B+ Tree data structures, query plan execution, and index optimization.", "SKL-POSTGRES"),

    # Web & Frontend Development
    ("HTML5 Semantic Document Structure", "beginner", "DOCTYPE, head/body, semantic tags (nav, main, section, article, footer), and accessibility attributes.", "SKL-HTMLCSS"),
    ("CSS Box Model, Flexbox & Grid", "beginner", "Content, padding, border, margin, flex direction, justify-content, align-items, grid template columns.", "SKL-HTMLCSS"),
    ("JavaScript DOM Events & Manipulations", "beginner", "document.querySelector, addEventListener, event bubbling, event delegation, and DOM updates.", "SKL-JAVASCRIPT"),
    ("Asynchronous JavaScript: Promises & Async/Await", "intermediate", "Event loop, call stack, task queue, microtasks, Promise chaining, and fetch API.", "SKL-JAVASCRIPT"),
    ("React Components, Props & JSX", "intermediate", "Declarative JSX syntax, functional components, immutable props, and unidirectional data flow.", "SKL-REACT"),
    ("React State Management with Hooks (useState, useEffect)", "intermediate", "useState state updates, useEffect side effects, dependency array hygiene, and custom hooks.", "SKL-REACT"),

    # Backend & APIs
    ("HTTP Protocol & RESTful API Architecture", "intermediate", "HTTP methods (GET, POST, PUT, DELETE, PATCH), status codes, headers, and idempotent operations.", "SKL-REST"),
    ("Node.js Event Loop & Module System", "intermediate", "CommonJS vs ES Modules, asynchronous non-blocking I/O, fs promises, and process lifecycle.", "SKL-NODEJS"),
    ("Express Middleware & Routing Architecture", "intermediate", "app.use middleware chain, error-handling middleware, route parameters, and query strings.", "SKL-EXPRESS"),
    ("JWT Authentication & Password Hashing", "advanced", "Bcrypt hashing, salted rounds, JWT payload signing, signature verification, and bearer tokens.", "SKL-NODEJS"),

    # Machine Learning
    ("Supervised Learning: Linear & Logistic Regression", "intermediate", "Hypothesis function, cost function MSE, gradient descent optimization, and classification decision boundaries.", "SKL-ML"),
    ("Model Evaluation Metrics & Validation", "intermediate", "Confusion matrix, precision, recall, F1-score, ROC-AUC curve, and cross-validation.", "SKL-ML"),
]

# Directed Prerequisite Relationships: (Concept Name, Prerequisite Concept Name)
PREREQUISITE_EDGES = [
    ("Python Control Flow & Loops", "Python Variables and Primitive Types"),
    ("Python Functions and Scoping", "Python Control Flow & Loops"),
    ("Python Lists, Tuples, and Dictionaries", "Python Functions and Scoping"),
    ("Object-Oriented Programming in Python", "Python Functions and Scoping"),
    ("Python Exception Handling & File I/O", "Object-Oriented Programming in Python"),

    ("Arrays and Dynamic Arrays", "Asymptotic Big-O Complexity Analysis"),
    ("Singly and Doubly Linked Lists", "Arrays and Dynamic Arrays"),
    ("Stacks and Queues", "Arrays and Dynamic Arrays"),
    ("Recursion and Divide-and-Conquer", "Stacks and Queues"),
    ("Binary Trees and Tree Traversals", "Recursion and Divide-and-Conquer"),
    ("Binary Search Trees (BST)", "Binary Trees and Tree Traversals"),
    ("Graph Representations and Traversals", "Binary Trees and Tree Traversals"),
    ("Shortest Path Algorithms (Dijkstra)", "Graph Representations and Traversals"),
    ("Dynamic Programming Fundamentals", "Recursion and Divide-and-Conquer"),

    ("SQL DDL and Basic Queries", "Relational Data Model & ER Diagrams"),
    ("SQL Joins and Multi-Table Queries", "SQL DDL and Basic Queries"),
    ("SQL Aggregation and Grouping", "SQL Joins and Multi-Table Queries"),
    ("Database Normalization (1NF, 2NF, 3NF, BCNF)", "SQL Joins and Multi-Table Queries"),
    ("ACID Properties & Transaction Isolation", "Database Normalization (1NF, 2NF, 3NF, BCNF)"),
    ("Database Indexing & B-Trees", "ACID Properties & Transaction Isolation"),

    ("CSS Box Model, Flexbox & Grid", "HTML5 Semantic Document Structure"),
    ("JavaScript DOM Events & Manipulations", "CSS Box Model, Flexbox & Grid"),
    ("Asynchronous JavaScript: Promises & Async/Await", "JavaScript DOM Events & Manipulations"),
    ("React Components, Props & JSX", "Asynchronous JavaScript: Promises & Async/Await"),
    ("React State Management with Hooks (useState, useEffect)", "React Components, Props & JSX"),

    ("Express Middleware & Routing Architecture", "HTTP Protocol & RESTful API Architecture"),
    ("JWT Authentication & Password Hashing", "Express Middleware & Routing Architecture"),

    ("Model Evaluation Metrics & Validation", "Supervised Learning: Linear & Logistic Regression"),
]


async def seed_courses_and_concepts(db: AsyncSession) -> Dict[str, int]:
    """Idempotently populates canonical courses, concepts, prerequisites, and skill bridges."""
    stats = {
        "courses": 0,
        "course_skill_mappings": 0,
        "concepts": 0,
        "concept_prerequisites": 0,
        "concept_skill_mappings": 0,
    }

    # Fetch disciplines and skills for mapping
    disc_res = await db.execute(select(AcademicDiscipline))
    disciplines = {d.code: d for d in disc_res.scalars().all()}

    skill_res = await db.execute(select(SkillCatalog))
    skills = {s.code: s for s in skill_res.scalars().all()}

    # 1. Seed Canonical Courses
    for c_data in CANONICAL_COURSES:
        res = await db.execute(select(CourseCatalog).where(CourseCatalog.code == c_data["code"]))
        course = res.scalar_one_or_none()
        if not course:
            disc = disciplines.get(c_data["discipline_code"])
            if not disc:
                continue
            course = CourseCatalog(
                code=c_data["code"],
                title=c_data["title"],
                discipline_id=disc.id,
                default_credits=c_data["default_credits"],
                academic_level=c_data["academic_level"],
                slug=c_data["slug"],
                description=c_data["description"],
                status="active",
            )
            db.add(course)
            await db.flush()
            stats["courses"] += 1

        for s_code, depth, weight in c_data.get("skills", []):
            if s_code in skills:
                sk_id = skills[s_code].id
                map_res = await db.execute(
                    select(CourseSkillMapping).where(
                        CourseSkillMapping.course_catalog_id == course.id,
                        CourseSkillMapping.skill_id == sk_id,
                    )
                )
                if not map_res.scalar_one_or_none():
                    mapping = CourseSkillMapping(
                        course_catalog_id=course.id,
                        skill_id=sk_id,
                        depth_level=depth,
                        weight=weight,
                    )
                    db.add(mapping)
                    stats["course_skill_mappings"] += 1

    # 2. Seed Canonical Concepts
    concepts_by_name: Dict[str, Concept] = {}
    default_disc = disciplines.get("COMP_INFO")

    for name, difficulty, description, skill_code in CANONICAL_CONCEPTS_DATA:
        res = await db.execute(select(Concept).where(Concept.name == name))
        concept = res.scalar_one_or_none()
        slug = name.lower().replace(" ", "-").replace("(", "").replace(")", "").replace(":", "").replace("&", "and")
        if not concept:
            concept = Concept(
                name=name,
                slug=slug,
                description=description,
                difficulty=difficulty,
                discipline_id=default_disc.id if default_disc else None,
                status="active",
            )
            db.add(concept)
            await db.flush()
            stats["concepts"] += 1
        concepts_by_name[name] = concept

        # Link to Skill
        if skill_code in skills:
            sk_id = skills[skill_code].id
            cs_res = await db.execute(
                select(ConceptSkill).where(
                    ConceptSkill.concept_id == concept.id,
                    ConceptSkill.skill_id == sk_id,
                )
            )
            if not cs_res.scalar_one_or_none():
                cs = ConceptSkill(concept_id=concept.id, skill_id=sk_id, weight=1.0)
                db.add(cs)
                stats["concept_skill_mappings"] += 1

    # 3. Seed Prerequisite Graph Edges
    for concept_name, prereq_name in PREREQUISITE_EDGES:
        if concept_name in concepts_by_name and prereq_name in concepts_by_name:
            c_id = concepts_by_name[concept_name].id
            p_id = concepts_by_name[prereq_name].id
            edge_res = await db.execute(
                select(ConceptPrerequisite).where(
                    ConceptPrerequisite.concept_id == c_id,
                    ConceptPrerequisite.prerequisite_concept_id == p_id,
                )
            )
            if not edge_res.scalar_one_or_none():
                edge = ConceptPrerequisite(
                    concept_id=c_id,
                    prerequisite_concept_id=p_id,
                    relationship_type="prerequisite",
                )
                db.add(edge)
                stats["concept_prerequisites"] += 1

    await db.commit()
    logger.info("Canonical courses and concepts seeded successfully: %s", stats)
    return stats


async def main():
    async with async_session_maker() as db:
        await seed_courses_and_concepts(db)


if __name__ == "__main__":
    asyncio.run(main())
