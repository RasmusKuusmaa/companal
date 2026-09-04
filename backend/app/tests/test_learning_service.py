import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.learning.curriculum.definitions import CourseDef, LessonDef, StepDef, TopicDef
from app.domains.learning.models import Lesson, LessonStep, StepAttempt
from app.domains.learning.schemas import LessonProgressStatus, QuizStepRead
from app.domains.learning.seeding import UnknownTopicError, seed_curriculum
from app.domains.learning.service import (
    LessonNotFoundError,
    StepKindError,
    StepNotFoundError,
    answer_quiz,
    complete_lesson,
    get_lesson,
    get_progress_summary,
    get_roadmap,
    mark_step_seen,
)
from app.domains.users.models import User

TOPICS = [
    TopicDef(
        slug="intervals",
        name="Intervals",
        area="fundamentals",
        description="Number, quality and inversion.",
    ),
    TopicDef(
        slug="cadences",
        name="Cadences",
        area="harmony",
        description="How phrases come to rest.",
    ),
]


def _course(slug: str, title: str, lessons: list[LessonDef]) -> CourseDef:
    return CourseDef(
        slug=slug, title=title, description=f"{title} stage.", level="beginner", lessons=lessons
    )


def _curriculum() -> list[CourseDef]:
    """Two stages, so previous/next can be tested across a stage boundary."""
    return [
        _course(
            "fundamentals",
            "Fundamentals",
            [
                LessonDef(
                    slug="intervals",
                    title="Intervals",
                    summary="Measuring the distance between two notes.",
                    steps=[
                        StepDef(
                            slug="intervals-reading",
                            kind="reading",
                            payload={"markdown": "# Intervals\n\nA fifth spans seven semitones."},
                            topics=["intervals"],
                        ),
                        StepDef(
                            slug="intervals-quiz",
                            kind="quiz",
                            payload={
                                "question": "How many semitones in a perfect fifth?",
                                "choices": ["5", "7", "8"],
                                "answer_index": 1,
                                "explanation": "Seven - count them on a keyboard.",
                            },
                            topics=["intervals"],
                        ),
                    ],
                ),
                LessonDef(
                    slug="scales",
                    title="Major scales",
                    summary="Tone, tone, semitone.",
                    steps=[
                        StepDef(
                            slug="scales-reading",
                            kind="reading",
                            payload={"markdown": "# Major scales"},
                        )
                    ],
                ),
            ],
        ),
        _course(
            "harmony",
            "Harmony",
            [
                LessonDef(
                    slug="cadences",
                    title="Cadences",
                    summary="Perfect, imperfect, half and deceptive.",
                    steps=[
                        StepDef(
                            slug="cadences-task",
                            kind="composition",
                            payload={
                                "brief": "Write a four-bar phrase ending with a perfect cadence.",
                                "requirements": {"measures": 4},
                            },
                            topics=["cadences"],
                        )
                    ],
                )
            ],
        ),
    ]


async def _seed(db_session: AsyncSession) -> None:
    await seed_curriculum(db_session, topics=TOPICS, courses=_curriculum())


async def _make_user(db_session: AsyncSession, email: str = "student@example.com") -> User:
    user = User(email=email, hashed_password="not-a-real-hash", full_name="Student")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestSeeding:
    async def test_seeds_the_whole_curriculum(self, db_session: AsyncSession) -> None:
        report = await seed_curriculum(db_session, topics=TOPICS, courses=_curriculum())

        assert report.topics.created == 2
        assert report.courses.created == 2
        assert report.lessons.created == 3
        assert report.steps.created == 4

    async def test_positions_follow_list_order(self, db_session: AsyncSession) -> None:
        await _seed(db_session)

        lesson = await db_session.scalar(select(Lesson).where(Lesson.slug == "scales"))
        assert lesson is not None
        assert lesson.position == 1

        steps = (
            await db_session.scalars(
                select(LessonStep)
                .where(LessonStep.slug.like("intervals-%"))
                .order_by(LessonStep.position)
            )
        ).all()
        assert [step.slug for step in steps] == ["intervals-reading", "intervals-quiz"]

    async def test_reseeding_is_idempotent(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        report = await seed_curriculum(db_session, topics=TOPICS, courses=_curriculum())

        assert report.lessons.created == 0
        assert report.lessons.updated == 3
        assert report.steps.deleted == 0

        lessons = (await db_session.scalars(select(Lesson))).all()
        assert len(lessons) == 3

    async def test_edited_content_updates_in_place(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        before = await db_session.scalar(select(Lesson).where(Lesson.slug == "intervals"))
        assert before is not None
        original_id = before.id

        edited = _curriculum()
        edited[0].lessons[0].title = "Intervals, revisited"
        await seed_curriculum(db_session, topics=TOPICS, courses=edited)

        after = await db_session.scalar(select(Lesson).where(Lesson.slug == "intervals"))
        assert after is not None
        # Same row, not a replacement - progress rows point at this id.
        assert after.id == original_id
        assert after.title == "Intervals, revisited"

    async def test_removed_step_is_pruned(self, db_session: AsyncSession) -> None:
        await _seed(db_session)

        trimmed = _curriculum()
        trimmed[0].lessons[0].steps = trimmed[0].lessons[0].steps[:1]
        report = await seed_curriculum(db_session, topics=TOPICS, courses=trimmed)

        assert report.steps.deleted == 1
        remaining = await db_session.scalar(
            select(LessonStep).where(LessonStep.slug == "intervals-quiz")
        )
        assert remaining is None

    async def test_unknown_topic_is_rejected(self, db_session: AsyncSession) -> None:
        broken = _curriculum()
        broken[0].lessons[0].steps[0].topics = ["not-a-topic"]

        with pytest.raises(UnknownTopicError, match="not-a-topic"):
            await seed_curriculum(db_session, topics=TOPICS, courses=broken)

    def test_quiz_answer_index_must_be_in_range(self) -> None:
        with pytest.raises(ValidationError, match="out of range"):
            StepDef(
                slug="broken",
                kind="quiz",
                payload={
                    "question": "?",
                    "choices": ["a", "b"],
                    "answer_index": 7,
                    "explanation": "x",
                },
            )


class TestRoadmap:
    async def test_returns_every_stage_in_order(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        roadmap = await get_roadmap(db_session, user.id)

        assert [course.slug for course in roadmap.courses] == ["fundamentals", "harmony"]
        assert [lesson.slug for lesson in roadmap.courses[0].lessons] == ["intervals", "scales"]
        assert roadmap.lesson_count == 3

    async def test_fresh_student_has_started_nothing(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        roadmap = await get_roadmap(db_session, user.id)

        statuses = {lesson.status for course in roadmap.courses for lesson in course.lessons}
        assert statuses == {LessonProgressStatus.NOT_STARTED}
        assert roadmap.completed_lesson_count == 0

    async def test_lesson_counts_reflect_progress(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        await mark_step_seen(db_session, user.id, "intervals", "intervals-reading")
        await complete_lesson(db_session, user.id, "scales")

        roadmap = await get_roadmap(db_session, user.id)
        fundamentals = roadmap.courses[0]

        assert fundamentals.completed_lesson_count == 1
        assert roadmap.in_progress_lesson_count == 1
        assert roadmap.completed_lesson_count == 1

    async def test_step_counts_are_reported(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        roadmap = await get_roadmap(db_session, user.id)
        by_slug = {lesson.slug: lesson for course in roadmap.courses for lesson in course.lessons}

        assert by_slug["intervals"].step_count == 2
        assert by_slug["scales"].step_count == 1


class TestLessonDetail:
    async def test_returns_steps_in_order(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        lesson = await get_lesson(db_session, user.id, "intervals")

        assert [step.slug for step in lesson.steps] == ["intervals-reading", "intervals-quiz"]
        assert lesson.course.slug == "fundamentals"

    async def test_quiz_step_has_no_answer_key(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        lesson = await get_lesson(db_session, user.id, "intervals")
        quiz = lesson.steps[1]

        assert isinstance(quiz, QuizStepRead)
        assert quiz.choices == ["5", "7", "8"]
        # Not merely absent from this instance - the type has no such field.
        assert "answer_index" not in quiz.model_dump()
        assert "answer_index" not in QuizStepRead.model_fields

    async def test_neighbours_cross_stage_boundaries(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        last_of_first_stage = await get_lesson(db_session, user.id, "scales")
        first_of_second_stage = await get_lesson(db_session, user.id, "cadences")

        assert last_of_first_stage.next_lesson_slug == "cadences"
        assert first_of_second_stage.previous_lesson_slug == "scales"
        assert first_of_second_stage.next_lesson_slug is None

    async def test_unknown_lesson_raises(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        with pytest.raises(LessonNotFoundError):
            await get_lesson(db_session, user.id, "no-such-lesson")

    async def test_reading_the_lesson_does_not_start_it(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        await get_lesson(db_session, user.id, "intervals")

        roadmap = await get_roadmap(db_session, user.id)
        assert roadmap.in_progress_lesson_count == 0


class TestQuizAnswers:
    async def test_correct_answer(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        result = await answer_quiz(db_session, user.id, "intervals", "intervals-quiz", 1)

        assert result.is_correct is True
        assert result.correct_index == 1
        assert "Seven" in result.explanation

    async def test_wrong_answer_still_explains(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        result = await answer_quiz(db_session, user.id, "intervals", "intervals-quiz", 0)

        assert result.is_correct is False
        assert result.correct_index == 1
        assert result.explanation

    async def test_every_attempt_is_kept(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        await answer_quiz(db_session, user.id, "intervals", "intervals-quiz", 0)
        await answer_quiz(db_session, user.id, "intervals", "intervals-quiz", 2)
        await answer_quiz(db_session, user.id, "intervals", "intervals-quiz", 1)

        attempts = (
            await db_session.scalars(
                select(StepAttempt)
                .where(StepAttempt.user_id == user.id)
                .order_by(StepAttempt.created_at)
            )
        ).all()

        # The wrong answers are the point: the skill map reads them later.
        assert [attempt.is_correct for attempt in attempts] == [False, False, True]
        assert [attempt.payload["choice_index"] for attempt in attempts] == [0, 2, 1]

    async def test_answering_starts_the_lesson(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        await answer_quiz(db_session, user.id, "intervals", "intervals-quiz", 1)

        lesson = await get_lesson(db_session, user.id, "intervals")
        assert lesson.status is LessonProgressStatus.IN_PROGRESS

    async def test_non_quiz_step_is_rejected(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        with pytest.raises(StepKindError, match="reading"):
            await answer_quiz(db_session, user.id, "intervals", "intervals-reading", 0)

    async def test_unknown_step_raises(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        with pytest.raises(StepNotFoundError):
            await answer_quiz(db_session, user.id, "intervals", "no-such-step", 0)

    async def test_step_from_another_lesson_raises(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        with pytest.raises(StepNotFoundError):
            await answer_quiz(db_session, user.id, "scales", "intervals-quiz", 1)


class TestProgress:
    async def test_marking_a_step_seen_records_position(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        result = await mark_step_seen(db_session, user.id, "intervals", "intervals-quiz")

        assert result.status is LessonProgressStatus.IN_PROGRESS
        lesson = await get_lesson(db_session, user.id, "intervals")
        assert lesson.current_step_id == result.current_step_id

    async def test_completion_is_idempotent(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        first = await complete_lesson(db_session, user.id, "intervals")
        second = await complete_lesson(db_session, user.id, "intervals")

        assert first.completed_at == second.completed_at
        assert second.status is LessonProgressStatus.COMPLETED

    async def test_completion_points_at_the_next_lesson(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        result = await complete_lesson(db_session, user.id, "intervals")

        assert result.next_lesson_slug == "scales"

    async def test_revisiting_a_finished_lesson_keeps_it_finished(
        self, db_session: AsyncSession
    ) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        await complete_lesson(db_session, user.id, "intervals")
        await mark_step_seen(db_session, user.id, "intervals", "intervals-reading")

        lesson = await get_lesson(db_session, user.id, "intervals")
        assert lesson.status is LessonProgressStatus.COMPLETED

    async def test_continue_points_at_the_lesson_in_progress(
        self, db_session: AsyncSession
    ) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        await complete_lesson(db_session, user.id, "intervals")
        await mark_step_seen(db_session, user.id, "cadences", "cadences-task")

        summary = await get_progress_summary(db_session, user.id)
        assert summary.continue_lesson_slug == "cadences"

    async def test_continue_falls_back_to_the_first_unstarted(
        self, db_session: AsyncSession
    ) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        await complete_lesson(db_session, user.id, "intervals")

        summary = await get_progress_summary(db_session, user.id)
        assert summary.continue_lesson_slug == "scales"

    async def test_continue_is_none_once_everything_is_done(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        for slug in ("intervals", "scales", "cadences"):
            await complete_lesson(db_session, user.id, slug)

        summary = await get_progress_summary(db_session, user.id)
        assert summary.continue_lesson_slug is None
        assert summary.completed_lesson_count == 3

    async def test_progress_is_per_student(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        student = await _make_user(db_session, "one@example.com")
        other = await _make_user(db_session, "two@example.com")

        await complete_lesson(db_session, student.id, "intervals")

        summary = await get_progress_summary(db_session, other.id)
        assert summary.completed_lesson_count == 0

    async def test_by_course_breakdown(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        await complete_lesson(db_session, user.id, "intervals")

        summary = await get_progress_summary(db_session, user.id)
        by_slug = {course.course_slug: course for course in summary.by_course}

        assert by_slug["fundamentals"].completed_lesson_count == 1
        assert by_slug["fundamentals"].lesson_count == 2
        assert by_slug["harmony"].completed_lesson_count == 0

    async def test_unknown_lesson_raises_on_completion(self, db_session: AsyncSession) -> None:
        await _seed(db_session)
        user = await _make_user(db_session)

        with pytest.raises(LessonNotFoundError):
            await complete_lesson(db_session, user.id, uuid.uuid4().hex)
