"""Reading the roadmap, running a lesson, and recording what the student did.

Two rules shape everything here.

Nothing is gated. The roadmap returns every lesson of every stage with its
status, and no function refuses to serve a lesson because an earlier one
isn't finished. Order is a recommendation the UI draws; it is not a lock.

Reads don't write. Opening a lesson is a `GET` that records nothing - the
progress row appears when the student actually does something (advances past
a step, answers a quiz), so a prefetch or an idle tab can't manufacture
progress the student didn't make.
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.learning.models import (
    Course,
    Lesson,
    LessonStatus,
    LessonStep,
    StepAttempt,
    StepKind,
    UserProgress,
)
from app.domains.learning.schemas import (
    CompositionPayload,
    CompositionStepRead,
    CourseProgress,
    CourseRef,
    CourseWithLessons,
    LessonCompleteRead,
    LessonProgressStatus,
    LessonRead,
    LessonStepRead,
    LessonSummary,
    ProgressSummary,
    QuizAnswerResult,
    QuizPayload,
    QuizStepRead,
    ReadingPayload,
    ReadingStepRead,
    RoadmapRead,
    StepSeenRead,
)


class LessonNotFoundError(Exception):
    pass


class StepNotFoundError(Exception):
    pass


class StepKindError(Exception):
    """The step exists but doesn't accept this kind of submission."""


def _status_of(progress: UserProgress | None) -> LessonProgressStatus:
    if progress is None:
        return LessonProgressStatus.NOT_STARTED
    if progress.status is LessonStatus.COMPLETED:
        return LessonProgressStatus.COMPLETED
    return LessonProgressStatus.IN_PROGRESS


def _public_step(step: LessonStep) -> LessonStepRead:
    """Maps a stored step onto what the student is allowed to see.

    The quiz branch is the reason this exists: `QuizStepRead` has no
    `answer_index` field, so the answer key cannot reach the browser even by
    accident.
    """
    if step.kind is StepKind.READING:
        reading = ReadingPayload.model_validate(step.payload)
        return ReadingStepRead(
            id=step.id, slug=step.slug, position=step.position, markdown=reading.markdown
        )
    if step.kind is StepKind.QUIZ:
        quiz = QuizPayload.model_validate(step.payload)
        return QuizStepRead(
            id=step.id,
            slug=step.slug,
            position=step.position,
            question=quiz.question,
            choices=quiz.choices,
        )
    composition = CompositionPayload.model_validate(step.payload)
    return CompositionStepRead(
        id=step.id,
        slug=step.slug,
        position=step.position,
        brief=composition.brief,
        requirements=composition.requirements,
        starter_notation=composition.starter_notation,
    )


async def _progress_by_lesson(
    db: AsyncSession, user_id: uuid.UUID
) -> dict[uuid.UUID, UserProgress]:
    rows = await db.scalars(select(UserProgress).where(UserProgress.user_id == user_id))
    return {row.lesson_id: row for row in rows.all()}


async def _step_counts(db: AsyncSession) -> dict[uuid.UUID, int]:
    rows = await db.execute(
        select(LessonStep.lesson_id, func.count(LessonStep.id)).group_by(LessonStep.lesson_id)
    )
    return {lesson_id: count for lesson_id, count in rows}


async def _ordered_lesson_slugs(db: AsyncSession) -> list[str]:
    """Every lesson slug in roadmap order, across stage boundaries.

    Used for the lesson player's previous/next links, which deliberately
    don't stop at the end of a stage - finishing the last lesson of one
    course should offer the first lesson of the next.
    """
    rows = await db.execute(
        select(Lesson.slug)
        .join(Course, Course.id == Lesson.course_id)
        .order_by(Course.position, Course.slug, Lesson.position, Lesson.slug)
    )
    return [slug for (slug,) in rows]


async def _get_lesson_by_slug(db: AsyncSession, lesson_slug: str) -> Lesson:
    lesson = await db.scalar(select(Lesson).where(Lesson.slug == lesson_slug))
    if lesson is None:
        raise LessonNotFoundError
    return lesson


async def _get_step(db: AsyncSession, lesson: Lesson, step_slug: str) -> LessonStep:
    step = await db.scalar(
        select(LessonStep).where(LessonStep.slug == step_slug, LessonStep.lesson_id == lesson.id)
    )
    if step is None:
        raise StepNotFoundError
    return step


async def _ensure_progress(
    db: AsyncSession, user_id: uuid.UUID, lesson_id: uuid.UUID
) -> UserProgress:
    """Returns this student's progress row for the lesson, creating it if needed.

    `ON CONFLICT DO NOTHING` rather than insert-and-catch: two tabs opening
    the same lesson at once both try to insert, and catching the resulting
    `IntegrityError` would mean rolling back - which in `answer_quiz` would
    discard the attempt row added moments earlier in the same transaction.
    Letting Postgres absorb the conflict keeps the transaction intact, so
    the loser of the race just reads back the winner's row.
    """
    insert_if_absent = (
        pg_insert(UserProgress)
        .values(
            id=uuid.uuid4(),
            user_id=user_id,
            lesson_id=lesson_id,
            status=LessonStatus.IN_PROGRESS,
        )
        .on_conflict_do_nothing(index_elements=["user_id", "lesson_id"])
    )
    await db.execute(insert_if_absent)

    progress = await db.scalar(
        select(UserProgress).where(
            UserProgress.user_id == user_id, UserProgress.lesson_id == lesson_id
        )
    )
    if progress is None:  # pragma: no cover - the insert above guarantees a row
        raise LessonNotFoundError
    return progress


async def get_roadmap(db: AsyncSession, user_id: uuid.UUID) -> RoadmapRead:
    """The whole path, with this student's status on every lesson.

    Four queries whatever the size of the curriculum - courses, lessons,
    step counts and progress are each fetched once and joined in memory,
    rather than walking courses and querying per lesson.
    """
    courses = (await db.scalars(select(Course).order_by(Course.position, Course.slug))).all()
    lessons = (await db.scalars(select(Lesson).order_by(Lesson.position, Lesson.slug))).all()
    step_counts = await _step_counts(db)
    progress = await _progress_by_lesson(db, user_id)

    lessons_by_course: dict[uuid.UUID, list[Lesson]] = {}
    for lesson in lessons:
        lessons_by_course.setdefault(lesson.course_id, []).append(lesson)

    course_reads: list[CourseWithLessons] = []
    completed_total = 0
    in_progress_total = 0

    for course in courses:
        summaries: list[LessonSummary] = []
        completed_here = 0
        for lesson in lessons_by_course.get(course.id, []):
            row = progress.get(lesson.id)
            status = _status_of(row)
            if status is LessonProgressStatus.COMPLETED:
                completed_here += 1
            elif status is LessonProgressStatus.IN_PROGRESS:
                in_progress_total += 1
            summaries.append(
                LessonSummary(
                    id=lesson.id,
                    slug=lesson.slug,
                    title=lesson.title,
                    summary=lesson.summary,
                    position=lesson.position,
                    estimated_minutes=lesson.estimated_minutes,
                    step_count=step_counts.get(lesson.id, 0),
                    status=status,
                    completed_at=row.completed_at if row is not None else None,
                )
            )

        completed_total += completed_here
        course_reads.append(
            CourseWithLessons(
                id=course.id,
                slug=course.slug,
                title=course.title,
                description=course.description,
                level=course.level,
                position=course.position,
                lesson_count=len(summaries),
                completed_lesson_count=completed_here,
                lessons=summaries,
            )
        )

    return RoadmapRead(
        courses=course_reads,
        lesson_count=len(lessons),
        completed_lesson_count=completed_total,
        in_progress_lesson_count=in_progress_total,
    )


async def get_lesson(db: AsyncSession, user_id: uuid.UUID, lesson_slug: str) -> LessonRead:
    lesson = await _get_lesson_by_slug(db, lesson_slug)
    course = await db.get(Course, lesson.course_id)
    if course is None:  # pragma: no cover - the FK makes this unreachable
        raise LessonNotFoundError

    steps = (
        await db.scalars(
            select(LessonStep)
            .where(LessonStep.lesson_id == lesson.id)
            .order_by(LessonStep.position, LessonStep.slug)
        )
    ).all()

    progress = await db.scalar(
        select(UserProgress).where(
            UserProgress.user_id == user_id, UserProgress.lesson_id == lesson.id
        )
    )

    slugs = await _ordered_lesson_slugs(db)
    index = slugs.index(lesson.slug)

    return LessonRead(
        id=lesson.id,
        slug=lesson.slug,
        title=lesson.title,
        summary=lesson.summary,
        position=lesson.position,
        estimated_minutes=lesson.estimated_minutes,
        course=CourseRef.model_validate(course),
        status=_status_of(progress),
        current_step_id=progress.current_step_id if progress is not None else None,
        completed_at=progress.completed_at if progress is not None else None,
        steps=[_public_step(step) for step in steps],
        previous_lesson_slug=slugs[index - 1] if index > 0 else None,
        next_lesson_slug=slugs[index + 1] if index + 1 < len(slugs) else None,
    )


async def mark_step_seen(
    db: AsyncSession, user_id: uuid.UUID, lesson_slug: str, step_slug: str
) -> StepSeenRead:
    """Records that the student is on this step.

    This is where a lesson becomes "in progress" - the player calls it as the
    student arrives at each step, including the first one. It never moves a
    completed lesson back to in-progress: revisiting a finished lesson is
    revision, not a regression.
    """
    lesson = await _get_lesson_by_slug(db, lesson_slug)
    step = await _get_step(db, lesson, step_slug)

    progress = await _ensure_progress(db, user_id, lesson.id)
    progress.current_step_id = step.id
    await db.commit()
    await db.refresh(progress)

    return StepSeenRead(
        lesson_id=lesson.id,
        current_step_id=progress.current_step_id,
        status=_status_of(progress),
    )


async def answer_quiz(
    db: AsyncSession, user_id: uuid.UUID, lesson_slug: str, step_slug: str, choice_index: int
) -> QuizAnswerResult:
    """Grades one multiple-choice answer and records the attempt.

    Every attempt is stored, right or wrong - retries are free, but the
    history is what the skill map later reads to work out which topics keep
    catching this student out.
    """
    lesson = await _get_lesson_by_slug(db, lesson_slug)
    step = await _get_step(db, lesson, step_slug)
    if step.kind is not StepKind.QUIZ:
        raise StepKindError(f"step '{step_slug}' is a {step.kind.value} step, not a quiz")

    quiz = QuizPayload.model_validate(step.payload)
    is_correct = choice_index == quiz.answer_index

    attempt = StepAttempt(
        user_id=user_id,
        step_id=step.id,
        payload={"choice_index": choice_index},
        is_correct=is_correct,
        result={"correct_index": quiz.answer_index},
    )
    db.add(attempt)

    progress = await _ensure_progress(db, user_id, lesson.id)
    progress.current_step_id = step.id

    await db.commit()
    await db.refresh(attempt)

    return QuizAnswerResult(
        attempt_id=attempt.id,
        is_correct=is_correct,
        correct_index=quiz.answer_index,
        explanation=quiz.explanation,
    )


async def complete_lesson(
    db: AsyncSession, user_id: uuid.UUID, lesson_slug: str
) -> LessonCompleteRead:
    """Marks a lesson complete, idempotently.

    Completing an already-completed lesson returns the original completion
    time rather than moving it: the date a student first finished something
    is worth more than the date they last re-read it.
    """
    lesson = await _get_lesson_by_slug(db, lesson_slug)
    progress = await _ensure_progress(db, user_id, lesson.id)

    completed_at = progress.completed_at or datetime.now(UTC)
    progress.completed_at = completed_at
    progress.status = LessonStatus.COMPLETED
    await db.commit()

    slugs = await _ordered_lesson_slugs(db)
    index = slugs.index(lesson.slug)

    return LessonCompleteRead(
        lesson_id=lesson.id,
        status=LessonProgressStatus.COMPLETED,
        completed_at=completed_at,
        next_lesson_slug=slugs[index + 1] if index + 1 < len(slugs) else None,
    )


def _continue_slug(
    lessons_in_order: Sequence[tuple[str, LessonProgressStatus]],
) -> str | None:
    """Where "continue learning" should send the student.

    The lesson they're partway through, and failing that the first they
    haven't opened. Once everything is complete there's nothing to continue,
    and the caller says so rather than looping back to lesson one.
    """
    for slug, status in lessons_in_order:
        if status is LessonProgressStatus.IN_PROGRESS:
            return slug
    for slug, status in lessons_in_order:
        if status is LessonProgressStatus.NOT_STARTED:
            return slug
    return None


async def get_progress_summary(db: AsyncSession, user_id: uuid.UUID) -> ProgressSummary:
    roadmap = await get_roadmap(db, user_id)

    by_course = [
        CourseProgress(
            course_id=course.id,
            course_slug=course.slug,
            course_title=course.title,
            lesson_count=course.lesson_count,
            completed_lesson_count=course.completed_lesson_count,
            in_progress_lesson_count=sum(
                1 for lesson in course.lessons if lesson.status is LessonProgressStatus.IN_PROGRESS
            ),
        )
        for course in roadmap.courses
    ]

    ordered = [
        (lesson.slug, lesson.status) for course in roadmap.courses for lesson in course.lessons
    ]

    return ProgressSummary(
        lesson_count=roadmap.lesson_count,
        completed_lesson_count=roadmap.completed_lesson_count,
        in_progress_lesson_count=roadmap.in_progress_lesson_count,
        by_course=by_course,
        continue_lesson_slug=_continue_slug(ordered),
    )
