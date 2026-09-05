import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.exams.definitions import ExamDef, ExamQuestionDef
from app.domains.exams.models import Exam, ExamQuestion
from app.domains.exams.schemas import ExamQuizQuestionRead
from app.domains.exams.seeding import UnknownCourseError, seed_exams
from app.domains.exams.service import ExamNotFoundError, start_attempt
from app.domains.learning.curriculum.definitions import CourseDef
from app.domains.learning.seeding import seed_curriculum
from app.domains.users.models import User


def _quiz(slug: str) -> ExamQuestionDef:
    return ExamQuestionDef(
        slug=slug,
        kind="quiz",
        payload={
            "question": "How many semitones in a perfect fifth?",
            "choices": ["5", "7", "8"],
            "answer_index": 1,
            "explanation": "Seven - count them on a keyboard.",
        },
    )


async def _seed_course(db_session: AsyncSession, slug: str = "fundamentals") -> None:
    await seed_curriculum(
        db_session,
        topics=[],
        courses=[CourseDef(slug=slug, title="Fundamentals", description="d", level="beginner")],
    )


async def _make_user(db_session: AsyncSession, email: str = "examer@example.com") -> User:
    user = User(email=email, hashed_password="not-a-real-hash", full_name="Examer")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestSeedExams:
    async def test_creates_an_exam_and_its_questions(self, db_session: AsyncSession) -> None:
        await _seed_course(db_session)

        report = await seed_exams(
            db_session,
            exams=[
                ExamDef(
                    slug="stage-0-exam",
                    title="Stage 0 Exam",
                    description="d",
                    course_slug="fundamentals",
                    questions=[_quiz("s0-q1")],
                )
            ],
        )

        assert report.exams.created == 1
        assert report.questions.created == 1

        exam = await db_session.scalar(select(Exam).where(Exam.slug == "stage-0-exam"))
        assert exam is not None
        assert exam.course_id is not None

    async def test_the_comprehensive_final_has_no_course(self, db_session: AsyncSession) -> None:
        await seed_exams(
            db_session,
            exams=[ExamDef(slug="final-exam", title="Final", description="d", course_slug=None)],
        )

        exam = await db_session.scalar(select(Exam).where(Exam.slug == "final-exam"))
        assert exam is not None
        assert exam.course_id is None

    async def test_reseeding_updates_rather_than_duplicates(self, db_session: AsyncSession) -> None:
        await _seed_course(db_session)
        exam_def = ExamDef(
            slug="stage-0-exam",
            title="Stage 0 Exam",
            description="d",
            course_slug="fundamentals",
            questions=[_quiz("s0-q1")],
        )
        await seed_exams(db_session, exams=[exam_def])

        edited = exam_def.model_copy(update={"title": "Stage 0 Exam (revised)"})
        report = await seed_exams(db_session, exams=[edited])

        assert report.exams.updated == 1
        exam = await db_session.scalar(select(Exam).where(Exam.slug == "stage-0-exam"))
        assert exam is not None
        assert exam.title == "Stage 0 Exam (revised)"

    async def test_removed_questions_are_pruned(self, db_session: AsyncSession) -> None:
        await _seed_course(db_session)
        await seed_exams(
            db_session,
            exams=[
                ExamDef(
                    slug="stage-0-exam",
                    title="Stage 0 Exam",
                    description="d",
                    course_slug="fundamentals",
                    questions=[_quiz("s0-q1"), _quiz("s0-q2")],
                )
            ],
        )

        report = await seed_exams(
            db_session,
            exams=[
                ExamDef(
                    slug="stage-0-exam",
                    title="Stage 0 Exam",
                    description="d",
                    course_slug="fundamentals",
                    questions=[_quiz("s0-q1")],
                )
            ],
        )

        assert report.questions.deleted == 1
        remaining = (await db_session.scalars(select(ExamQuestion))).all()
        assert {q.slug for q in remaining} == {"s0-q1"}

    async def test_an_exam_removed_from_the_definitions_is_pruned(
        self, db_session: AsyncSession
    ) -> None:
        await seed_exams(
            db_session, exams=[ExamDef(slug="final-exam", title="Final", description="d")]
        )

        report = await seed_exams(db_session, exams=[])

        assert report.exams.deleted == 1
        assert await db_session.scalar(select(Exam).where(Exam.slug == "final-exam")) is None

    async def test_an_undeclared_course_slug_raises(self, db_session: AsyncSession) -> None:
        with pytest.raises(UnknownCourseError):
            await seed_exams(
                db_session,
                exams=[
                    ExamDef(
                        slug="stage-0-exam",
                        title="Stage 0 Exam",
                        description="d",
                        course_slug="no-such-course",
                    )
                ],
            )


class TestStartAttempt:
    async def test_starts_at_attempt_number_one(self, db_session: AsyncSession) -> None:
        await _seed_course(db_session)
        await seed_exams(
            db_session,
            exams=[
                ExamDef(
                    slug="stage-0-exam",
                    title="Stage 0 Exam",
                    description="d",
                    course_slug="fundamentals",
                    questions=[_quiz("s0-q1")],
                )
            ],
        )
        user = await _make_user(db_session)

        result = await start_attempt(db_session, user.id, "stage-0-exam")

        assert result.attempt_number == 1
        assert result.exam.slug == "stage-0-exam"
        assert result.exam.course_slug == "fundamentals"
        assert result.exam.question_count == 1
        assert result.started_at is not None

    async def test_quiz_questions_never_carry_the_answer_key(
        self, db_session: AsyncSession
    ) -> None:
        await _seed_course(db_session)
        await seed_exams(
            db_session,
            exams=[
                ExamDef(
                    slug="stage-0-exam",
                    title="Stage 0 Exam",
                    description="d",
                    course_slug="fundamentals",
                    questions=[_quiz("s0-q1")],
                )
            ],
        )
        user = await _make_user(db_session)

        result = await start_attempt(db_session, user.id, "stage-0-exam")

        question = result.exam.questions[0]
        assert isinstance(question, ExamQuizQuestionRead)
        assert not hasattr(question, "answer_index")

    async def test_each_new_attempt_gets_the_next_number(self, db_session: AsyncSession) -> None:
        await seed_exams(
            db_session, exams=[ExamDef(slug="final-exam", title="Final", description="d")]
        )
        user = await _make_user(db_session)

        first = await start_attempt(db_session, user.id, "final-exam")
        second = await start_attempt(db_session, user.id, "final-exam")
        third = await start_attempt(db_session, user.id, "final-exam")

        assert [first.attempt_number, second.attempt_number, third.attempt_number] == [1, 2, 3]
        assert len({first.attempt_id, second.attempt_id, third.attempt_id}) == 3

    async def test_attempt_numbering_is_per_student(self, db_session: AsyncSession) -> None:
        await seed_exams(
            db_session, exams=[ExamDef(slug="final-exam", title="Final", description="d")]
        )
        alice = await _make_user(db_session, "alice@example.com")
        bob = await _make_user(db_session, "bob@example.com")

        await start_attempt(db_session, alice.id, "final-exam")
        await start_attempt(db_session, alice.id, "final-exam")
        bob_first = await start_attempt(db_session, bob.id, "final-exam")

        assert bob_first.attempt_number == 1

    async def test_unknown_exam_slug_raises(self, db_session: AsyncSession) -> None:
        user = await _make_user(db_session)

        with pytest.raises(ExamNotFoundError):
            await start_attempt(db_session, user.id, uuid.uuid4().hex)
