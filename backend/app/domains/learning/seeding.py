"""Loads authored curriculum into the database, idempotently.

Slug is identity here, not the primary key: UUIDs are generated per database,
so a lesson seeded into a developer's machine and the same lesson seeded into
production share nothing but their slug. Upserting on slug is what makes
`seed-curriculum` safe to run on every deploy - the second run is a no-op,
and an edited lesson updates in place instead of appearing twice.

The definitions are treated as authoritative: a course, lesson or step whose
slug no longer appears in `curriculum` is deleted. That's what keeps a
removed lesson from lingering in the roadmap forever, and it's why the prune
runs as a second pass - a step moved from one lesson to another is an update
in pass one, so pass two never sees it as an orphan.

Removing a step does take its `StepAttempt` rows with it (they cascade), but
not the student's mastery: `TopicMastery` hangs off topics, which outlive any
particular exercise. Rewriting an exercise costs its attempt history and
leaves what the site actually knows about the student intact.
"""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.learning.curriculum.definitions import CourseDef, LessonDef, StepDef, TopicDef
from app.domains.learning.models import (
    Course,
    Lesson,
    LessonStep,
    LessonStepTopic,
    Topic,
)


class UnknownTopicError(Exception):
    """A step tagged a topic slug that no `TopicDef` declares."""


@dataclass
class EntityCounts:
    created: int = 0
    updated: int = 0
    deleted: int = 0

    def __str__(self) -> str:
        return f"{self.created} created, {self.updated} updated, {self.deleted} deleted"


@dataclass
class SeedReport:
    topics: EntityCounts = field(default_factory=EntityCounts)
    courses: EntityCounts = field(default_factory=EntityCounts)
    lessons: EntityCounts = field(default_factory=EntityCounts)
    steps: EntityCounts = field(default_factory=EntityCounts)


async def _sync_topics(
    db: AsyncSession, defs: Sequence[TopicDef], report: SeedReport
) -> dict[str, uuid.UUID]:
    existing = {topic.slug: topic for topic in (await db.scalars(select(Topic))).all()}
    ids: dict[str, uuid.UUID] = {}

    for position, topic_def in enumerate(defs):
        topic = existing.get(topic_def.slug)
        if topic is None:
            topic = Topic(slug=topic_def.slug)
            db.add(topic)
            report.topics.created += 1
        else:
            report.topics.updated += 1
        topic.name = topic_def.name
        topic.area = topic_def.area
        topic.description = topic_def.description
        topic.position = position
        # Flushed rather than committed: the whole seed is one transaction,
        # but the steps synced later need these ids to tag against.
        await db.flush()
        ids[topic_def.slug] = topic.id

    return ids


async def _sync_course(
    db: AsyncSession, course_def: CourseDef, position: int, report: SeedReport
) -> Course:
    course = await db.scalar(select(Course).where(Course.slug == course_def.slug))
    if course is None:
        course = Course(slug=course_def.slug)
        db.add(course)
        report.courses.created += 1
    else:
        report.courses.updated += 1

    course.title = course_def.title
    course.description = course_def.description
    course.level = course_def.level
    course.position = position
    await db.flush()
    return course


async def _sync_lesson(
    db: AsyncSession, course: Course, lesson_def: LessonDef, position: int, report: SeedReport
) -> Lesson:
    lesson = await db.scalar(select(Lesson).where(Lesson.slug == lesson_def.slug))
    if lesson is None:
        lesson = Lesson(slug=lesson_def.slug)
        db.add(lesson)
        report.lessons.created += 1
    else:
        report.lessons.updated += 1

    # Assigned unconditionally so a lesson moved to a different stage
    # follows its definition rather than staying where it was first seeded.
    lesson.course_id = course.id
    lesson.title = lesson_def.title
    lesson.summary = lesson_def.summary
    lesson.estimated_minutes = lesson_def.estimated_minutes
    lesson.position = position
    await db.flush()
    return lesson


async def _sync_step(
    db: AsyncSession,
    lesson: Lesson,
    step_def: StepDef,
    position: int,
    topic_ids: dict[str, uuid.UUID],
    report: SeedReport,
) -> None:
    step = await db.scalar(select(LessonStep).where(LessonStep.slug == step_def.slug))
    if step is None:
        step = LessonStep(slug=step_def.slug)
        db.add(step)
        report.steps.created += 1
    else:
        report.steps.updated += 1

    step.lesson_id = lesson.id
    step.kind = step_def.kind
    step.payload = step_def.payload
    step.position = position
    await db.flush()

    unknown = [slug for slug in step_def.topics if slug not in topic_ids]
    if unknown:
        raise UnknownTopicError(
            f"step '{step_def.slug}' tags undeclared topic(s): {', '.join(sorted(unknown))}"
        )

    # Re-tagged wholesale rather than diffed: the tag set is two columns and
    # a handful of rows, and replacing it is easier to be sure of than
    # working out which tags were added and which removed.
    await db.execute(delete(LessonStepTopic).where(LessonStepTopic.step_id == step.id))
    for topic_slug in step_def.topics:
        db.add(LessonStepTopic(step_id=step.id, topic_id=topic_ids[topic_slug]))
    await db.flush()


async def _prune(
    db: AsyncSession, courses: Sequence[CourseDef], topics: Sequence[TopicDef], report: SeedReport
) -> None:
    """Deletes anything whose slug the definitions no longer mention."""
    course_slugs = {course.slug for course in courses}
    lesson_slugs = {lesson.slug for course in courses for lesson in course.lessons}
    step_slugs = {
        step.slug for course in courses for lesson in course.lessons for step in lesson.steps
    }
    topic_slugs = {topic.slug for topic in topics}

    # Deepest first: deleting a course cascades to its lessons and steps, and
    # counting those as pruned separately would double-count them.
    for model, keep, counts in (
        (LessonStep, step_slugs, report.steps),
        (Lesson, lesson_slugs, report.lessons),
        (Course, course_slugs, report.courses),
        (Topic, topic_slugs, report.topics),
    ):
        # RETURNING rather than `rowcount`: the deleted ids come back typed,
        # so the count doesn't depend on a DBAPI attribute the async Result
        # protocol doesn't promise.
        deleted = await db.execute(delete(model).where(model.slug.not_in(keep)).returning(model.id))
        counts.deleted += len(deleted.scalars().all())


async def seed_curriculum(
    db: AsyncSession,
    *,
    topics: Sequence[TopicDef],
    courses: Sequence[CourseDef],
) -> SeedReport:
    """Makes the database match the authored curriculum, and reports what changed."""
    report = SeedReport()

    topic_ids = await _sync_topics(db, topics, report)

    for course_position, course_def in enumerate(courses):
        course = await _sync_course(db, course_def, course_position, report)
        for lesson_position, lesson_def in enumerate(course_def.lessons):
            lesson = await _sync_lesson(db, course, lesson_def, lesson_position, report)
            for step_position, step_def in enumerate(lesson_def.steps):
                await _sync_step(db, lesson, step_def, step_position, topic_ids, report)

    await _prune(db, courses, topics, report)

    await db.commit()
    return report
