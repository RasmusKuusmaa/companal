"""Loads authored exam content into the database, idempotently - mirrors
`learning.seeding` for the same reasons: slug is identity, an edited exam
updates in place, and an exam or question whose slug no longer appears in
the definitions is pruned.
"""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.exams.definitions import ExamDef, ExamQuestionDef
from app.domains.exams.models import Exam, ExamQuestion
from app.domains.learning.models import Course


class UnknownCourseError(Exception):
    """An exam names a course slug that no `Course` row has."""


@dataclass
class EntityCounts:
    created: int = 0
    updated: int = 0
    deleted: int = 0

    def __str__(self) -> str:
        return f"{self.created} created, {self.updated} updated, {self.deleted} deleted"


@dataclass
class ExamSeedReport:
    exams: EntityCounts = field(default_factory=EntityCounts)
    questions: EntityCounts = field(default_factory=EntityCounts)


async def _course_ids(db: AsyncSession) -> dict[str, uuid.UUID]:
    rows = await db.scalars(select(Course))
    return {course.slug: course.id for course in rows.all()}


async def _sync_exam(
    db: AsyncSession,
    exam_def: ExamDef,
    course_ids: dict[str, uuid.UUID],
    position: int,
    report: ExamSeedReport,
) -> Exam:
    exam = await db.scalar(select(Exam).where(Exam.slug == exam_def.slug))
    if exam is None:
        exam = Exam(slug=exam_def.slug)
        db.add(exam)
        report.exams.created += 1
    else:
        report.exams.updated += 1

    if exam_def.course_slug is not None and exam_def.course_slug not in course_ids:
        raise UnknownCourseError(
            f"exam '{exam_def.slug}' names undeclared course '{exam_def.course_slug}'"
        )

    exam.course_id = course_ids.get(exam_def.course_slug) if exam_def.course_slug else None
    exam.title = exam_def.title
    exam.description = exam_def.description
    exam.position = position
    await db.flush()
    return exam


async def _sync_question(
    db: AsyncSession,
    exam: Exam,
    question_def: ExamQuestionDef,
    position: int,
    report: ExamSeedReport,
) -> None:
    question = await db.scalar(select(ExamQuestion).where(ExamQuestion.slug == question_def.slug))
    if question is None:
        question = ExamQuestion(slug=question_def.slug)
        db.add(question)
        report.questions.created += 1
    else:
        report.questions.updated += 1

    question.exam_id = exam.id
    question.kind = question_def.kind
    question.payload = question_def.payload
    question.position = position
    await db.flush()


async def _prune(db: AsyncSession, exams: Sequence[ExamDef], report: ExamSeedReport) -> None:
    exam_slugs = {exam.slug for exam in exams}
    question_slugs = {question.slug for exam in exams for question in exam.questions}

    # Deepest first: deleting an exam cascades to its questions, and
    # counting those as pruned separately would double-count them.
    for model, keep, counts in (
        (ExamQuestion, question_slugs, report.questions),
        (Exam, exam_slugs, report.exams),
    ):
        deleted = await db.execute(delete(model).where(model.slug.not_in(keep)).returning(model.id))
        counts.deleted += len(deleted.scalars().all())


async def seed_exams(db: AsyncSession, *, exams: Sequence[ExamDef]) -> ExamSeedReport:
    """Makes the database match the authored exams, and reports what changed."""
    report = ExamSeedReport()
    course_ids = await _course_ids(db)

    for position, exam_def in enumerate(exams):
        exam = await _sync_exam(db, exam_def, course_ids, position, report)
        for question_position, question_def in enumerate(exam_def.questions):
            await _sync_question(db, exam, question_def, question_position, report)

    await _prune(db, exams, report)

    await db.commit()
    return report
