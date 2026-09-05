import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.exams.definitions import ExamDef, ExamQuestionDef
from app.domains.exams.models import Exam, ExamAnswer, ExamAttempt, ExamQuestion
from app.domains.exams.schemas import (
    ExamCompositionAnswerPayload,
    ExamQuizAnswerPayload,
    ExamQuizQuestionRead,
)
from app.domains.exams.seeding import UnknownCourseError, seed_exams
from app.domains.exams.service import (
    ExamAnswerKindMismatchError,
    ExamAttemptAlreadySubmittedError,
    ExamAttemptNotFoundError,
    ExamNotFoundError,
    ExamQuestionNotFoundError,
    answer_question,
    grade_attempt,
    start_attempt,
)
from app.domains.learning.curriculum.definitions import CourseDef
from app.domains.learning.seeding import seed_curriculum
from app.domains.notation.schemas import NotationDocument
from app.domains.users.models import User


def _note() -> dict[str, object]:
    return {
        "id": "n",
        "step": "C",
        "octave": 4,
        "alter": 0,
        "duration": "whole",
        "dots": 0,
        "is_rest": False,
        "tied_to_next": False,
    }


def _document() -> NotationDocument:
    return NotationDocument.model_validate(
        {
            "fifths": 0,
            "mode": "major",
            "time": {"beats": 4, "beat_type": 4},
            "tempo": 90,
            "staves": [
                {
                    "id": "s1",
                    "clef": "treble",
                    "measures": [{"id": "m0", "voices": [{"id": "1", "notes": [_note()]}]}],
                }
            ],
        }
    )


def _composition(slug: str) -> ExamQuestionDef:
    return ExamQuestionDef(
        slug=slug, kind="composition", payload={"brief": "Write something.", "requirements": []}
    )


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


class TestAnswerQuestion:
    async def _started(self, db_session: AsyncSession) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
        """Seeds a final exam with one quiz and one composition question,
        starts an attempt, and returns (attempt_id, quiz_question_id,
        composition_question_id)."""
        await seed_exams(
            db_session,
            exams=[
                ExamDef(
                    slug="final-exam",
                    title="Final",
                    description="d",
                    questions=[_quiz("q1"), _composition("q2")],
                )
            ],
        )
        user = await _make_user(db_session)
        start = await start_attempt(db_session, user.id, "final-exam")
        return start.attempt_id, start.exam.questions[0].id, start.exam.questions[1].id

    async def test_holds_a_quiz_answer_without_grading_it(self, db_session: AsyncSession) -> None:
        attempt_id, quiz_id, _composition_id = await self._started(db_session)
        user_id = (await db_session.get(ExamAttempt, attempt_id)).user_id  # type: ignore[union-attr]

        result = await answer_question(
            db_session, user_id, attempt_id, quiz_id, ExamQuizAnswerPayload(choice_index=1)
        )

        assert result.answered is True
        answer = await db_session.scalar(
            select(ExamAnswer).where(
                ExamAnswer.attempt_id == attempt_id, ExamAnswer.question_id == quiz_id
            )
        )
        assert answer is not None
        assert answer.score is None
        assert answer.payload == {"kind": "quiz", "choice_index": 1}

    async def test_resubmitting_an_answer_replaces_it(self, db_session: AsyncSession) -> None:
        attempt_id, quiz_id, _composition_id = await self._started(db_session)
        user_id = (await db_session.get(ExamAttempt, attempt_id)).user_id  # type: ignore[union-attr]

        await answer_question(
            db_session, user_id, attempt_id, quiz_id, ExamQuizAnswerPayload(choice_index=1)
        )
        await answer_question(
            db_session, user_id, attempt_id, quiz_id, ExamQuizAnswerPayload(choice_index=0)
        )

        answers = (
            await db_session.scalars(
                select(ExamAnswer).where(
                    ExamAnswer.attempt_id == attempt_id, ExamAnswer.question_id == quiz_id
                )
            )
        ).all()
        assert len(answers) == 1
        assert answers[0].payload == {"kind": "quiz", "choice_index": 0}

    async def test_a_composition_answer_holds_the_document(self, db_session: AsyncSession) -> None:
        attempt_id, _quiz_id, composition_id = await self._started(db_session)
        user_id = (await db_session.get(ExamAttempt, attempt_id)).user_id  # type: ignore[union-attr]

        await answer_question(
            db_session,
            user_id,
            attempt_id,
            composition_id,
            ExamCompositionAnswerPayload(document=_document()),
        )

        answer = await db_session.scalar(
            select(ExamAnswer).where(
                ExamAnswer.attempt_id == attempt_id, ExamAnswer.question_id == composition_id
            )
        )
        assert answer is not None
        assert answer.payload["kind"] == "composition"

    async def test_answering_a_quiz_question_with_a_composition_answer_raises(
        self, db_session: AsyncSession
    ) -> None:
        attempt_id, quiz_id, _composition_id = await self._started(db_session)
        user_id = (await db_session.get(ExamAttempt, attempt_id)).user_id  # type: ignore[union-attr]

        with pytest.raises(ExamAnswerKindMismatchError):
            await answer_question(
                db_session,
                user_id,
                attempt_id,
                quiz_id,
                ExamCompositionAnswerPayload(document=_document()),
            )

    async def test_a_question_from_a_different_exam_raises(
        self, db_session: AsyncSession
    ) -> None:
        attempt_id, _quiz_id, _composition_id = await self._started(db_session)
        user_id = (await db_session.get(ExamAttempt, attempt_id)).user_id  # type: ignore[union-attr]
        await seed_exams(
            db_session,
            exams=[
                ExamDef(slug="final-exam", title="Final", description="d", questions=[]),
                ExamDef(
                    slug="another-exam", title="Another", description="d", questions=[_quiz("aq1")]
                ),
            ],
        )
        other_question = await db_session.scalar(
            select(ExamQuestion).where(ExamQuestion.slug == "aq1")
        )
        assert other_question is not None

        with pytest.raises(ExamQuestionNotFoundError):
            await answer_question(
                db_session,
                user_id,
                attempt_id,
                other_question.id,
                ExamQuizAnswerPayload(choice_index=0),
            )

    async def test_answering_a_submitted_attempt_raises(self, db_session: AsyncSession) -> None:
        attempt_id, quiz_id, _composition_id = await self._started(db_session)
        attempt = await db_session.get(ExamAttempt, attempt_id)
        assert attempt is not None
        user_id = attempt.user_id
        attempt.submitted_at = datetime.now(UTC)
        await db_session.commit()

        with pytest.raises(ExamAttemptAlreadySubmittedError):
            await answer_question(
                db_session, user_id, attempt_id, quiz_id, ExamQuizAnswerPayload(choice_index=0)
            )

    async def test_answering_someone_elses_attempt_raises(self, db_session: AsyncSession) -> None:
        attempt_id, quiz_id, _composition_id = await self._started(db_session)
        someone_else = await _make_user(db_session, "someone-else@example.com")

        with pytest.raises(ExamAttemptNotFoundError):
            await answer_question(
                db_session,
                someone_else.id,
                attempt_id,
                quiz_id,
                ExamQuizAnswerPayload(choice_index=0),
            )


class TestGradeAttempt:
    async def _started_quiz_only(
        self, db_session: AsyncSession
    ) -> tuple[uuid.UUID, uuid.UUID, list[uuid.UUID]]:
        """Seeds a three-question quiz-only exam (each with `answer_index`
        1), starts an attempt, and returns (user_id, attempt_id,
        question_ids)."""
        await seed_exams(
            db_session,
            exams=[
                ExamDef(
                    slug="final-exam",
                    title="Final",
                    description="d",
                    questions=[_quiz("q1"), _quiz("q2"), _quiz("q3")],
                )
            ],
        )
        user = await _make_user(db_session)
        start = await start_attempt(db_session, user.id, "final-exam")
        return user.id, start.attempt_id, [q.id for q in start.exam.questions]

    async def test_scores_correct_wrong_and_unanswered_questions(
        self, db_session: AsyncSession
    ) -> None:
        user_id, attempt_id, question_ids = await self._started_quiz_only(db_session)
        await answer_question(
            db_session, user_id, attempt_id, question_ids[0], ExamQuizAnswerPayload(choice_index=1)
        )
        await answer_question(
            db_session, user_id, attempt_id, question_ids[1], ExamQuizAnswerPayload(choice_index=0)
        )
        # question_ids[2] is left unanswered.

        result = await grade_attempt(db_session, user_id, attempt_id)

        assert result.score == 1.0
        assert result.max_score == 3.0
        by_question = {r.question_id: r for r in result.question_results}
        assert by_question[question_ids[0]].detail["is_correct"] is True
        assert by_question[question_ids[1]].detail["is_correct"] is False
        assert by_question[question_ids[2]].detail["is_correct"] is False
        assert by_question[question_ids[2]].detail["choice_index"] is None

    async def test_marks_the_attempt_submitted(self, db_session: AsyncSession) -> None:
        user_id, attempt_id, _question_ids = await self._started_quiz_only(db_session)

        result = await grade_attempt(db_session, user_id, attempt_id)

        attempt = await db_session.get(ExamAttempt, attempt_id)
        assert attempt is not None
        assert attempt.submitted_at == result.submitted_at
        assert attempt.score == result.score
        assert attempt.max_score == result.max_score

    async def test_grading_persists_each_answers_own_verdict(
        self, db_session: AsyncSession
    ) -> None:
        user_id, attempt_id, question_ids = await self._started_quiz_only(db_session)
        await answer_question(
            db_session, user_id, attempt_id, question_ids[0], ExamQuizAnswerPayload(choice_index=1)
        )

        await grade_attempt(db_session, user_id, attempt_id)

        answer = await db_session.scalar(
            select(ExamAnswer).where(
                ExamAnswer.attempt_id == attempt_id, ExamAnswer.question_id == question_ids[0]
            )
        )
        assert answer is not None
        assert answer.score == 1.0
        assert answer.max_score == 1.0
        assert answer.result["is_correct"] is True

    async def test_grading_twice_raises(self, db_session: AsyncSession) -> None:
        user_id, attempt_id, _question_ids = await self._started_quiz_only(db_session)
        await grade_attempt(db_session, user_id, attempt_id)

        with pytest.raises(ExamAttemptAlreadySubmittedError):
            await grade_attempt(db_session, user_id, attempt_id)

    async def test_answering_after_grading_raises(self, db_session: AsyncSession) -> None:
        user_id, attempt_id, question_ids = await self._started_quiz_only(db_session)
        await grade_attempt(db_session, user_id, attempt_id)

        with pytest.raises(ExamAttemptAlreadySubmittedError):
            await answer_question(
                db_session,
                user_id,
                attempt_id,
                question_ids[0],
                ExamQuizAnswerPayload(choice_index=1),
            )

    async def test_grading_someone_elses_attempt_raises(self, db_session: AsyncSession) -> None:
        _user_id, attempt_id, _question_ids = await self._started_quiz_only(db_session)
        someone_else = await _make_user(db_session, "someone-else@example.com")

        with pytest.raises(ExamAttemptNotFoundError):
            await grade_attempt(db_session, someone_else.id, attempt_id)
