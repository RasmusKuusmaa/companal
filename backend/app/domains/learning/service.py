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

from app.core import storage
from app.domains.billing import service as billing_service
from app.domains.billing.models import AiUsageKind
from app.domains.feedback.models import SkillLevel
from app.domains.feedback.schemas import CompositionFeedback
from app.domains.learning.mastery import (
    evidence_from_harmony_analysis,
    get_or_create_topic_mastery,
    get_topic_by_slug,
    record_result,
)
from app.domains.learning.models import (
    Course,
    Lesson,
    LessonStatus,
    LessonStep,
    LessonStepTopic,
    MasteryStatus,
    StepAttempt,
    StepKind,
    Topic,
    TopicMastery,
    UserProgress,
)
from app.domains.learning.schemas import (
    CompositionPayload,
    CompositionStepRead,
    CompositionSubmissionRead,
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
    SkillMapRead,
    StepSeenRead,
    TopicLessonRef,
    TopicMasteryRead,
)
from app.domains.notation.ai_grading import AIGradingError, generate_exercise_feedback
from app.domains.notation.grading import DeterministicGrade, analysis_bundle, grade_submission
from app.domains.notation.schemas import NotationDocument


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
        locked_staff_indices=composition.locked_staff_indices,
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


async def _update_mastery_for_step(
    db: AsyncSession, user_id: uuid.UUID, step_id: uuid.UUID, is_correct: bool
) -> None:
    """Folds one attempt's result into every topic the step is tagged with.

    Called from the same transaction that records the `StepAttempt` -
    see `models.TopicMastery`'s docstring for why this can't drift from
    the attempt history it's derived from. A step with no tagged topics
    (not yet authored, or a step type that doesn't carry one) simply
    updates nothing.
    """
    topic_ids = await db.scalars(
        select(LessonStepTopic.topic_id).where(LessonStepTopic.step_id == step_id)
    )
    for topic_id in topic_ids:
        mastery = await get_or_create_topic_mastery(db, user_id, topic_id)
        record_result(mastery, is_correct)


async def _update_mastery_from_rule_evidence(
    db: AsyncSession, user_id: uuid.UUID, grade: DeterministicGrade
) -> None:
    """Folds rule-level evidence from a submission's own analysis into
    mastery, on top of the step-level pass/fail `_update_mastery_for_step`
    already recorded. A parallel-fifths violation is evidence about voice
    leading whether or not the exercise's requirements checked for one -
    see `mastery.evidence_from_harmony_analysis`. A topic this evidence
    names that hasn't been seeded yet (Phase J) is silently skipped.
    """
    for slug, is_correct in evidence_from_harmony_analysis(grade.harmony_analysis):
        topic = await get_topic_by_slug(db, slug)
        if topic is None:
            continue
        mastery = await get_or_create_topic_mastery(db, user_id, topic.id)
        record_result(mastery, is_correct)


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
    await _update_mastery_for_step(db, user_id, step.id, is_correct)

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


def _attempt_storage_key(attempt_id: uuid.UUID) -> str:
    return f"learning-attempts/{attempt_id}.musicxml"


def _apply_locked_staves(
    document: NotationDocument, composition: CompositionPayload
) -> NotationDocument:
    """Overwrites each locked staff with its pristine starter version before
    grading.

    The editor's own lock (`useNotationEditor`'s `lockedStaffIndices`) is
    what stops a student from editing the given material in the first
    place, but nothing stops a request straight to this endpoint from
    carrying an edited one anyway - silently restoring the original here
    makes that pointless rather than needing to detect and reject it, and
    it means grading is always against the true given material regardless
    of what the client actually sent.
    """
    if not composition.locked_staff_indices or composition.starter_notation is None:
        return document

    starter_staves = composition.starter_notation.staves
    staves = list(document.staves)
    for index in composition.locked_staff_indices:
        if 0 <= index < len(staves) and index < len(starter_staves):
            staves[index] = starter_staves[index]
    return document.model_copy(update={"staves": staves})


async def _reusable_ai_feedback(
    db: AsyncSession,
    user_id: uuid.UUID,
    step_id: uuid.UUID,
    document: NotationDocument,
    skill_level: SkillLevel,
) -> CompositionFeedback | None:
    """An identical resubmission - same document, same requested skill level -
    reuses the AI commentary from the matching prior attempt instead of
    paying for another Claude call: resubmitting unchanged work to see the
    checklist again shouldn't burn quota or spend.

    Compared in Python rather than as a JSONB query - one user's attempts at
    one step is a small, bounded set, and equality on the decoded payload is
    simpler to get right than a JSONB containment query.
    """
    document_json = document.model_dump(mode="json")
    attempts = await db.scalars(
        select(StepAttempt)
        .where(StepAttempt.user_id == user_id, StepAttempt.step_id == step_id)
        .order_by(StepAttempt.created_at.desc())
    )
    for attempt in attempts:
        if (
            attempt.payload.get("document") == document_json
            and attempt.payload.get("skill_level") == skill_level.value
        ):
            cached = attempt.result.get("ai_feedback")
            if cached is not None:
                return CompositionFeedback.model_validate(cached)
    return None


async def submit_composition(
    db: AsyncSession,
    user_id: uuid.UUID,
    lesson_slug: str,
    step_slug: str,
    document: NotationDocument,
    skill_level: SkillLevel = SkillLevel.BEGINNER,
    with_ai_feedback: bool = False,
) -> CompositionSubmissionRead:
    """Grades a composition submission and keeps it.

    Grading is entirely deterministic - `grade_submission` never calls the
    AI. `with_ai_feedback` adds commentary on top of that grade; it never
    gates it. A failure to get AI commentary (no API key configured, the
    request itself failing) is swallowed rather than raised: the
    deterministic checklist the student actually needs is already decided
    by the time AI grading is attempted, and losing that over an
    unavailable extra would be a worse failure than just not having the
    extra.

    Every submission is kept, the same as a quiz attempt: retries are free,
    and the skill map later reads the full history, not just the latest
    try. Resubmitting the exact same document at the same skill level
    reuses the AI commentary from that earlier attempt instead of paying
    for a new Claude call - see `_reusable_ai_feedback`.

    The MusicXML is written to storage before the database row - see
    `projects.service.add_version` for the same ordering and the reasoning
    behind it: a failed write costs nothing, a failed commit after a
    successful write leaves only an orphaned file.
    """
    lesson = await _get_lesson_by_slug(db, lesson_slug)
    step = await _get_step(db, lesson, step_slug)
    if step.kind is not StepKind.COMPOSITION:
        raise StepKindError(f"step '{step_slug}' is a {step.kind.value} step, not a composition")

    composition = CompositionPayload.model_validate(step.payload)
    document = _apply_locked_staves(document, composition)
    grade, musicxml = grade_submission(document, composition.requirements)

    ai_feedback: CompositionFeedback | None = None
    if with_ai_feedback:
        ai_feedback = await _reusable_ai_feedback(db, user_id, step.id, document, skill_level)
        if ai_feedback is None:
            try:
                ai_feedback, usage = generate_exercise_feedback(
                    lesson.title,
                    composition.brief,
                    grade.requirement_results,
                    analysis_bundle(grade),
                    skill_level,
                )
            except AIGradingError:
                ai_feedback = None
            else:
                await billing_service.record_ai_usage(
                    db, user_id, AiUsageKind.EXERCISE_GRADING, usage
                )

    attempt_id = uuid.uuid4()
    storage_key = _attempt_storage_key(attempt_id)
    await storage.save_file(storage_key, musicxml)

    result = grade.model_dump(mode="json")
    result["storage_key"] = storage_key
    result["ai_feedback"] = ai_feedback.model_dump(mode="json") if ai_feedback else None

    attempt = StepAttempt(
        id=attempt_id,
        user_id=user_id,
        step_id=step.id,
        payload={
            "document": document.model_dump(mode="json"),
            "skill_level": skill_level.value,
        },
        score=grade.overall_score,
        passed=grade.passed,
        result=result,
    )
    db.add(attempt)
    await _update_mastery_for_step(db, user_id, step.id, grade.passed)
    await _update_mastery_from_rule_evidence(db, user_id, grade)

    progress = await _ensure_progress(db, user_id, lesson.id)
    progress.current_step_id = step.id

    await db.commit()
    await db.refresh(attempt)

    return CompositionSubmissionRead(
        attempt_id=attempt.id,
        created_at=attempt.created_at,
        ai_feedback=ai_feedback,
        **grade.model_dump(),
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


def _continue_lesson(lessons_in_order: Sequence[LessonSummary]) -> LessonSummary | None:
    """Where "continue learning" should send the student.

    The lesson they're partway through, and failing that the first they
    haven't opened. Once everything is complete there's nothing to continue,
    and the caller says so rather than looping back to lesson one.
    """
    for lesson in lessons_in_order:
        if lesson.status is LessonProgressStatus.IN_PROGRESS:
            return lesson
    for lesson in lessons_in_order:
        if lesson.status is LessonProgressStatus.NOT_STARTED:
            return lesson
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

    ordered = [lesson for course in roadmap.courses for lesson in course.lessons]
    resume = _continue_lesson(ordered)

    return ProgressSummary(
        lesson_count=roadmap.lesson_count,
        completed_lesson_count=roadmap.completed_lesson_count,
        in_progress_lesson_count=roadmap.in_progress_lesson_count,
        by_course=by_course,
        continue_lesson_slug=resume.slug if resume else None,
        continue_lesson_title=resume.title if resume else None,
    )


async def _mastery_by_topic(
    db: AsyncSession, user_id: uuid.UUID
) -> dict[uuid.UUID, TopicMastery]:
    rows = await db.scalars(select(TopicMastery).where(TopicMastery.user_id == user_id))
    return {row.topic_id: row for row in rows.all()}


async def _lessons_by_topic(db: AsyncSession) -> dict[uuid.UUID, list[TopicLessonRef]]:
    """Every lesson that exercises each topic, in roadmap order.

    Joined through `LessonStepTopic` rather than read off a topic's own
    relationship - a topic has no ORM relationship to lessons, only to the
    steps that tag it, and a lesson can tag the same topic from more than
    one step, hence the `distinct()`.
    """
    rows = await db.execute(
        select(LessonStepTopic.topic_id, Lesson.slug, Lesson.title, Lesson.position)
        .join(LessonStep, LessonStep.id == LessonStepTopic.step_id)
        .join(Lesson, Lesson.id == LessonStep.lesson_id)
        .distinct()
        .order_by(Lesson.position, Lesson.slug)
    )
    lessons_by_topic: dict[uuid.UUID, list[TopicLessonRef]] = {}
    for topic_id, slug, title, _position in rows:
        lessons_by_topic.setdefault(topic_id, []).append(TopicLessonRef(slug=slug, title=title))
    return lessons_by_topic


async def get_skill_map(db: AsyncSession, user_id: uuid.UUID) -> SkillMapRead:
    """Every topic in the curriculum, folded together with this student's
    mastery of it and the lessons that teach it.

    A topic with no `TopicMastery` row is synthesised as `untouched` rather
    than omitted - see `models.MasteryStatus`'s own docstring - so the
    heatmap always shows the whole curriculum, not just what's been
    attempted.
    """
    topics = (
        await db.scalars(select(Topic).order_by(Topic.area, Topic.position, Topic.slug))
    ).all()
    mastery_by_topic = await _mastery_by_topic(db, user_id)
    lessons_by_topic = await _lessons_by_topic(db)

    reads: list[TopicMasteryRead] = []
    touched = 0
    for topic in topics:
        mastery = mastery_by_topic.get(topic.id)
        if mastery is not None:
            touched += 1
        reads.append(
            TopicMasteryRead(
                id=topic.id,
                slug=topic.slug,
                name=topic.name,
                area=topic.area,
                description=topic.description,
                status=mastery.status if mastery is not None else MasteryStatus.UNTOUCHED,
                attempt_count=mastery.attempt_count if mastery is not None else 0,
                correct_count=mastery.correct_count if mastery is not None else 0,
                accuracy=mastery.accuracy if mastery is not None else 0.0,
                last_seen_at=mastery.last_seen_at if mastery is not None else None,
                lessons=lessons_by_topic.get(topic.id, []),
            )
        )

    return SkillMapRead(topics=reads, topic_count=len(topics), touched_topic_count=touched)
