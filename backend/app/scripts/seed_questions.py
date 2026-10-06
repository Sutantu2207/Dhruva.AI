"""DHRUVA.AI - Seed Script: Question Banks, Multi-Type Questions & Assessments (Domain 5).

Idempotent seeding of:
- Institutional Question Banks
- Multi-Type Questions (Single Choice, Multiple Choice, True/False, Numeric, Short Answer, Coding)
- Question Versions, Options, Evaluation Rubrics, and Coding Sandbox Configurations
- Mappings to Canonical Concepts and Skills
- Assessment Blueprints, Versions, and Assessment Question Links
"""

import asyncio
import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.domains.academic.models import Institution
from app.domains.catalog.models import SkillCatalog
from app.domains.content.models import Concept
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
    AssessmentVersion,
    AssessmentQuestion,
)

logger = logging.getLogger("dhruva.seed_questions")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


QUESTION_BANKS_DATA = [
    {
        "code": "QB-PYTHON",
        "title": "Python Programming Question Bank",
        "description": "Comprehensive item bank testing Python syntax, data types, scoping, OOP, and algorithms.",
    },
    {
        "code": "QB-DSA",
        "title": "Data Structures & Algorithms Question Bank",
        "description": "Rigorous conceptual, tracing, and implementation questions on lists, trees, graphs, and dynamic programming.",
    },
    {
        "code": "QB-DBMS",
        "title": "Database Management Systems Question Bank",
        "description": "Relational calculus, SQL querying, normalization, indexing, and transaction ACID properties.",
    },
    {
        "code": "QB-WEB",
        "title": "Modern Web & React Architecture Question Bank",
        "description": "DOM APIs, JavaScript event loop, CSS layout models, React hooks, and REST protocol design.",
    },
    {
        "code": "QB-ML",
        "title": "Machine Learning Fundamentals Question Bank",
        "description": "Supervised algorithms, regression, evaluation metrics, overfitting, and gradient descent.",
    },
]

QUESTIONS_DATA = [
    # --- Python Programming ---
    {
        "bank_code": "QB-PYTHON",
        "title": "Python LEGB Variable Scoping",
        "question_type": "single_choice",
        "difficulty": "medium",
        "concept_name": "Python Functions and Scoping",
        "skill_code": "SKL-PYTHON",
        "points": Decimal("2.00"),
        "prompt": "In Python, which order of scope resolution does the interpreter follow when looking up variable identifiers?",
        "explanation": "Python resolves variables according to the LEGB rule: Local, Enclosing, Global, and Built-in.",
        "options": [
            ("Local -> Enclosing -> Global -> Built-in", True, "Correct: LEGB order is standard in Python."),
            ("Global -> Local -> Enclosing -> Built-in", False, "Incorrect: Local scope is searched first."),
            ("Local -> Global -> Enclosing -> Built-in", False, "Incorrect: Enclosing lexical scopes are searched before module global."),
            ("Built-in -> Global -> Enclosing -> Local", False, "Incorrect: This is the exact inverse of lookup order."),
        ],
    },
    {
        "bank_code": "QB-PYTHON",
        "title": "Python List Mutability and Slicing",
        "question_type": "single_choice",
        "difficulty": "easy",
        "concept_name": "Python Lists, Tuples, and Dictionaries",
        "skill_code": "SKL-PYTHON",
        "points": Decimal("1.00"),
        "prompt": "What is the result of evaluating: `nums = [1, 2, 3]; copy_nums = nums[:]; copy_nums.append(4); nums` in Python?",
        "explanation": "`nums[:]` creates a shallow copy of the list. Mutating `copy_nums` does not affect `nums`.",
        "options": [
            ("[1, 2, 3]", True, "Correct: Slice copy creates an independent list object."),
            ("[1, 2, 3, 4]", False, "Incorrect: nums was not modified."),
            ("[4]", False, "Incorrect."),
            ("Raises TypeError", False, "Incorrect: List slicing is valid."),
        ],
    },
    {
        "bank_code": "QB-PYTHON",
        "title": "Two-Sum Problem Implementation",
        "question_type": "coding",
        "difficulty": "medium",
        "concept_name": "Python Lists, Tuples, and Dictionaries",
        "skill_code": "SKL-PYTHON",
        "points": Decimal("10.00"),
        "prompt": "Write a Python function `two_sum(nums, target)` that returns the 0-indexed indices of the two numbers such that they add up to `target`. Exactly one solution exists. Return indices in ascending order.",
        "explanation": "Using a hash table dictionary allows solving this in O(N) time and O(N) auxiliary space.",
        "coding_config": {
            "language": "python",
            "starter_code": "def two_sum(nums: list[int], target: int) -> list[int]:\n    # Implement your solution here\n    pass\n",
            "function_signature": "two_sum(nums, target)",
            "test_cases": [
                ("[2, 7, 11, 15]\n9", "[0, 1]", False, Decimal("5.00")),
                ("[3, 2, 4]\n6", "[1, 2]", False, Decimal("3.00")),
                ("[3, 3]\n6", "[0, 1]", True, Decimal("2.00")),
            ],
        },
    },

    # --- Data Structures & Algorithms ---
    {
        "bank_code": "QB-DSA",
        "title": "Binary Search Tree In-Order Traversal Property",
        "question_type": "true_false",
        "difficulty": "easy",
        "concept_name": "Binary Search Trees (BST)",
        "skill_code": "SKL-DSA",
        "points": Decimal("1.00"),
        "prompt": "True or False: Performing an in-order depth-first traversal on any valid Binary Search Tree yields the stored keys in strictly non-decreasing sorted order.",
        "explanation": "Because in-order visits left-subtree, current node, then right-subtree, for a BST this always prints keys in ascending order.",
        "options": [
            ("True", True, "Correct: In-order traversal of a BST always yields sorted order."),
            ("False", False, "Incorrect: This is a fundamental invariant of Binary Search Trees."),
        ],
    },
    {
        "bank_code": "QB-DSA",
        "title": "Big-O Time Complexity of Quicksort Average vs Worst",
        "question_type": "single_choice",
        "difficulty": "medium",
        "concept_name": "Recursion and Divide-and-Conquer",
        "skill_code": "SKL-ALGO",
        "points": Decimal("2.00"),
        "prompt": "What are the average-case and worst-case time complexities of randomized Quicksort when sorting an array of N elements?",
        "explanation": "Quicksort has an average-case complexity of O(N log N) and a worst-case complexity of O(N^2) when partitions are unbalanced.",
        "options": [
            ("Average: O(N log N), Worst: O(N^2)", True, "Correct: Quicksort is O(N log N) expected, O(N^2) worst case."),
            ("Average: O(N log N), Worst: O(N log N)", False, "Incorrect: Worst case is quadratic without median-of-medians."),
            ("Average: O(N), Worst: O(N log N)", False, "Incorrect."),
            ("Average: O(N^2), Worst: O(N^2)", False, "Incorrect."),
        ],
    },
    {
        "bank_code": "QB-DSA",
        "title": "Dijkstra Algorithm Non-Negative Edge Constraint",
        "question_type": "multiple_choice",
        "difficulty": "hard",
        "concept_name": "Shortest Path Algorithms (Dijkstra)",
        "skill_code": "SKL-ALGO",
        "points": Decimal("3.00"),
        "prompt": "Which of the following statements about Dijkstra's shortest path algorithm are TRUE? (Select all that apply)",
        "explanation": "Dijkstra requires non-negative edge weights because greedy selection assumes relaxed vertices cannot be shortened further.",
        "options": [
            ("Dijkstra's algorithm may produce incorrect shortest path lengths if the graph contains negative-weight edges.", True, "Correct: Greedy choice property fails with negative edges."),
            ("Using a binary min-heap priority queue achieves an O((V + E) log V) time complexity.", True, "Correct: Standard heap implementation runs in O((V + E) log V)."),
            ("Dijkstra's algorithm is capable of detecting negative weight cycles in directed graphs.", False, "Incorrect: Bellman-Ford or SPFA is required to detect negative cycles."),
            ("It computes single-source shortest paths on both directed and undirected graphs with non-negative edge weights.", True, "Correct: Dijkstra applies to directed and undirected graphs with non-negative weights."),
        ],
    },

    # --- Database Management Systems ---
    {
        "bank_code": "QB-DBMS",
        "title": "Third Normal Form (3NF) Condition",
        "question_type": "single_choice",
        "difficulty": "medium",
        "concept_name": "Database Normalization (1NF, 2NF, 3NF, BCNF)",
        "skill_code": "SKL-DBMS",
        "points": Decimal("2.00"),
        "prompt": "A relational schema is in Third Normal Form (3NF) if it is in 2NF and for every non-trivial functional dependency X -> A, which of the following holds?",
        "explanation": "In 3NF, every functional dependency X -> A must satisfy: X is a superkey OR A is a prime attribute (part of a candidate key).",
        "options": [
            ("X is a superkey OR A is a prime attribute", True, "Correct: Eliminates transitive dependencies for non-prime attributes."),
            ("X is a superkey AND A is a prime attribute", False, "Incorrect: Either condition suffices."),
            ("Every attribute in the relation is a prime attribute", False, "Incorrect: Not a requirement for 3NF."),
            ("There are no multi-valued dependencies", False, "Incorrect: Multi-valued dependencies are addressed in 4NF."),
        ],
    },
    {
        "bank_code": "QB-DBMS",
        "title": "ACID Isolation Anomaly: Phantom Read",
        "question_type": "single_choice",
        "difficulty": "hard",
        "concept_name": "ACID Properties & Transaction Isolation",
        "skill_code": "SKL-DBMS",
        "points": Decimal("2.00"),
        "prompt": "Which SQL standard transaction isolation level is the MINIMUM level required to prevent Phantom Reads?",
        "explanation": "Read Committed allows non-repeatable reads and phantoms. Repeatable Read prevents non-repeatable reads. Serializable prevents phantoms.",
        "options": [
            ("Serializable", True, "Correct: Serializable isolation guarantees serial execution, preventing phantom inserts."),
            ("Repeatable Read", False, "Incorrect: In ANSI SQL-92, Repeatable Read permits phantom rows."),
            ("Read Committed", False, "Incorrect: Read Committed permits non-repeatable reads and phantoms."),
            ("Read Uncommitted", False, "Incorrect: Read Uncommitted permits dirty reads."),
        ],
    },

    # --- Web Development & React ---
    {
        "bank_code": "QB-WEB",
        "title": "React useEffect Dependency Array Semantics",
        "question_type": "single_choice",
        "difficulty": "medium",
        "concept_name": "React State Management with Hooks (useState, useEffect)",
        "skill_code": "SKL-REACT",
        "points": Decimal("2.00"),
        "prompt": "In React, if a `useEffect` hook specifies an empty dependency array `[]`, when does its effect callback execute?",
        "explanation": "An empty dependency array causes the effect to run exactly once after the initial component mount.",
        "options": [
            ("Once after the component mounts initially", True, "Correct: Empty array means effect runs on mount only."),
            ("Before every DOM render cycle", False, "Incorrect: Effects run asynchronously after render."),
            ("On every state change within the component", False, "Incorrect: That occurs when no dependency array is passed."),
            ("Only when the component unmounts", False, "Incorrect: The cleanup function runs on unmount."),
        ],
    },
    {
        "bank_code": "QB-WEB",
        "title": "JavaScript Event Loop and Microtask Queue",
        "question_type": "single_choice",
        "difficulty": "hard",
        "concept_name": "Asynchronous JavaScript: Promises & Async/Await",
        "skill_code": "SKL-JAVASCRIPT",
        "points": Decimal("3.00"),
        "prompt": "What is the console output order for: `console.log('1'); setTimeout(() => console.log('2'), 0); Promise.resolve().then(() => console.log('3')); console.log('4');`?",
        "explanation": "Synchronous code runs first ('1', '4'). Microtask queue (Promise.then '3') empties before Macrotask queue (setTimeout '2'). Order: 1, 4, 3, 2.",
        "options": [
            ("1, 4, 3, 2", True, "Correct: Synchronous -> Microtasks -> Macrotasks."),
            ("1, 2, 3, 4", False, "Incorrect."),
            ("1, 4, 2, 3", False, "Incorrect: Microtask queue runs before setTimeout macrotask."),
            ("1, 3, 4, 2", False, "Incorrect: '4' executes synchronously before promise callbacks."),
        ],
    },

    # --- Machine Learning ---
    {
        "bank_code": "QB-ML",
        "title": "Evaluation Metric for Highly Imbalanced Classification",
        "question_type": "single_choice",
        "difficulty": "medium",
        "concept_name": "Model Evaluation Metrics & Validation",
        "skill_code": "SKL-ML",
        "points": Decimal("2.00"),
        "prompt": "When evaluating a binary classifier on a highly imbalanced dataset (e.g. 99% negative class), why is raw classification Accuracy misleading?",
        "explanation": "A naive model predicting negative for 100% of samples achieves 99% accuracy while having 0% recall for the positive class of interest.",
        "options": [
            ("A naive baseline predicting only the majority class achieves high accuracy while failing to detect positive samples", True, "Correct: Accuracy paradox makes precision/recall/F1 necessary."),
            ("Accuracy cannot be computed when the number of classes exceeds one", False, "Incorrect."),
            ("Accuracy requires true negative counts to be strictly equal to false positive counts", False, "Incorrect."),
            ("Accuracy is undefined for probability outputs", False, "Incorrect."),
        ],
    },
]


async def seed_question_banks_and_assessments(db: AsyncSession) -> Dict[str, int]:
    """Idempotently populates question banks, question items, options, rubrics, and assessments."""
    stats = {
        "question_banks": 0,
        "questions": 0,
        "question_versions": 0,
        "question_options": 0,
        "coding_configs": 0,
        "coding_test_cases": 0,
        "assessments": 0,
        "assessment_versions": 0,
        "assessment_questions": 0,
    }

    # Ensure pilot institution exists
    inst_res = await db.execute(select(Institution).where(Institution.code == "DHRUVA-DEMO-U"))
    inst = inst_res.scalar_one_or_none()
    if not inst:
        inst = Institution(
            code="DHRUVA-DEMO-U",
            name="Dhruva Demo University (Synthetic Pilot)",
            email_domains="example.invalid,demo.invalid",
            status="active",
        )
        db.add(inst)
        await db.flush()

    # Pre-fetch concepts and skills
    c_res = await db.execute(select(Concept))
    concepts = {c.name: c for c in c_res.scalars().all()}

    s_res = await db.execute(select(SkillCatalog))
    skills = {s.code: s for s in s_res.scalars().all()}

    # 1. Seed Question Banks
    banks_by_code: Dict[str, QuestionBank] = {}
    for qb_data in QUESTION_BANKS_DATA:
        res = await db.execute(
            select(QuestionBank).where(
                QuestionBank.institution_id == inst.id,
                QuestionBank.title == qb_data["title"],
            )
        )
        bank = res.scalar_one_or_none()
        if not bank:
            bank = QuestionBank(
                institution_id=inst.id,
                title=qb_data["title"],
                description=qb_data["description"],
                status="active",
                visibility="institution",
            )
            db.add(bank)
            await db.flush()
            stats["question_banks"] += 1
        banks_by_code[qb_data["code"]] = bank

    # 2. Seed Questions, Versions, Options, Test Cases
    seeded_q_versions: List[QuestionVersion] = []

    for q_data in QUESTIONS_DATA:
        bank = banks_by_code.get(q_data["bank_code"])
        if not bank:
            continue

        q_res = await db.execute(
            select(Question).where(
                Question.bank_id == bank.id,
                Question.title == q_data["title"],
            )
        )
        question = q_res.scalar_one_or_none()

        if not question:
            question = Question(
                bank_id=bank.id,
                title=q_data["title"],
                question_type=q_data["question_type"],
                difficulty=q_data["difficulty"],
                status="approved",
                current_version=1,
            )
            db.add(question)
            await db.flush()
            stats["questions"] += 1

            # Question Version
            qv = QuestionVersion(
                question_id=question.id,
                version_number=1,
                prompt=q_data["prompt"],
                explanation=q_data["explanation"],
                points=q_data["points"],
                difficulty=q_data["difficulty"],
            )
            db.add(qv)
            await db.flush()
            stats["question_versions"] += 1

            # Concept link
            concept = concepts.get(q_data["concept_name"])
            if concept:
                qc = QuestionConcept(
                    question_version_id=qv.id,
                    concept_id=concept.id,
                    importance=1.0,
                    is_primary=True,
                    weight=Decimal("1.00"),
                )
                db.add(qc)

            # Skill link
            skill = skills.get(q_data["skill_code"])
            if skill:
                qs = QuestionSkill(
                    question_version_id=qv.id,
                    skill_id=skill.id,
                    weight=Decimal("1.00"),
                    evidence_type="assessment",
                )
                db.add(qs)

            # Options (for MCQs)
            for idx, (opt_text, is_corr, opt_expl) in enumerate(q_data.get("options", [])):
                opt = QuestionOption(
                    question_version_id=qv.id,
                    option_text=opt_text,
                    order_index=idx,
                    is_correct=is_corr,
                    explanation=opt_expl,
                )
                db.add(opt)
                stats["question_options"] += 1

            # Coding Config (if coding question)
            if "coding_config" in q_data:
                cc_data = q_data["coding_config"]
                cc = CodingConfiguration(
                    question_version_id=qv.id,
                    language=cc_data["language"],
                    starter_code=cc_data["starter_code"],
                    function_signature=cc_data["function_signature"],
                    time_limit_ms=2000,
                    memory_limit_mb=256,
                )
                db.add(cc)
                await db.flush()
                stats["coding_configs"] += 1

                for inp, exp, is_hid, pt in cc_data["test_cases"]:
                    tc = CodingTestCase(
                        coding_config_id=cc.id,
                        input_data=inp,
                        expected_output=exp,
                        is_hidden=is_hid,
                        points_weight=pt,
                    )
                    db.add(tc)
                    stats["coding_test_cases"] += 1

            seeded_q_versions.append(qv)
        else:
            # Fetch existing version
            qv_res = await db.execute(
                select(QuestionVersion).where(
                    QuestionVersion.question_id == question.id,
                    QuestionVersion.version_number == 1,
                )
            )
            existing_qv = qv_res.scalar_one_or_none()
            if existing_qv:
                seeded_q_versions.append(existing_qv)

    # 3. Seed Canonical Assessments
    assessments_blueprint = [
        {
            "title": "Python Programming Diagnostic Assessment",
            "assessment_type": "diagnostic",
            "description": "Deterministic diagnostic evaluation covering Python syntax, memory scoping, lists, and algorithmic problem solving.",
            "duration_minutes": 45,
            "total_marks": Decimal("15.00"),
            "passing_marks": Decimal("9.00"),
            "target_bank": "QB-PYTHON",
        },
        {
            "title": "Data Structures & Algorithms Comprehensive Assessment",
            "assessment_type": "midterm",
            "description": "Intermediate examination assessing Trees, Traversal properties, Asymptotic Complexity, and Graph algorithms.",
            "duration_minutes": 60,
            "total_marks": Decimal("15.00"),
            "passing_marks": Decimal("9.00"),
            "target_bank": "QB-DSA",
        },
    ]

    for asm_data in assessments_blueprint:
        res = await db.execute(
            select(Assessment).where(
                Assessment.institution_id == inst.id,
                Assessment.title == asm_data["title"],
            )
        )
        assessment = res.scalar_one_or_none()
        if not assessment:
            assessment = Assessment(
                institution_id=inst.id,
                title=asm_data["title"],
                assessment_type=asm_data["assessment_type"],
                description=asm_data["description"],
                duration_minutes=asm_data["duration_minutes"],
                total_marks=asm_data["total_marks"],
                passing_marks=asm_data["passing_marks"],
                attempts_allowed=3,
                status="open",
                current_version=1,
            )
            db.add(assessment)
            await db.flush()
            stats["assessments"] += 1

            av = AssessmentVersion(
                assessment_id=assessment.id,
                version_number=1,
                title=assessment.title,
                total_marks=assessment.total_marks,
                passing_marks=assessment.passing_marks,
                duration_minutes=assessment.duration_minutes,
                feedback_policy="after_submission",
                is_frozen=True,
            )
            db.add(av)
            await db.flush()
            stats["assessment_versions"] += 1

            # Attach relevant questions
            target_bank = banks_by_code.get(asm_data["target_bank"])
            if target_bank:
                target_q_res = await db.execute(
                    select(QuestionVersion)
                    .join(Question)
                    .where(Question.bank_id == target_bank.id)
                )
                bank_qvs = target_q_res.scalars().all()
                for idx, bqv in enumerate(bank_qvs):
                    aq = AssessmentQuestion(
                        assessment_version_id=av.id,
                        question_version_id=bqv.id,
                        order_index=idx,
                        section_name="Core Section",
                        custom_points=bqv.points,
                    )
                    db.add(aq)
                    stats["assessment_questions"] += 1

    await db.commit()
    logger.info("Question banks and assessments seeded successfully: %s", stats)
    return stats


async def main():
    async with async_session_maker() as db:
        await seed_question_banks_and_assessments(db)


if __name__ == "__main__":
    asyncio.run(main())
