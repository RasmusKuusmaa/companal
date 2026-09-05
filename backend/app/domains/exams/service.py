"""Starting, answering and grading exam attempts.

Mirrors `learning.service`'s split between authored content and what a
student is served: `_public_question` strips a quiz's answer key the same
way `learning.service._public_step` does, for the same reason - there is
no field on the read model for it to leak through.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.billing import service as billing_service
from app.domains.billing.models import AiUsageKind
from app.domains.exams.models import Exam, ExamAnswer, ExamAttempt, ExamQuestion, ExamQuestionKind
from app.domains.exams.schemas import (
    ExamAnswerPayload,
    ExamAnswerRead,
    ExamAttemptResultRead,
    ExamAttemptStartRead,
    ExamCompositionQuestionRead,
    ExamQuestionRead,
    ExamQuestionResultRead,
    ExamQuizQuestionRead,
    ExamRead,
)
from app.domains.feedback.models import SkillLevel
from app.domains.learning.models import Course
from app.domains.learning.schemas import CompositionPayload, QuizPayload
from app.domains.notation.ai_grading import AIGradingError, generate_exercise_feedback
from app.domains.notation.grading import DeterministicGrade, analysis_bundle, grade_submission
from app.domains.notation.schemas import NotationDocument


class ExamNotFoundError(Exception):
    """No exam has this slug."""


class ExamAttemptNotFoundError(Exception):
    """No attempt with this id belongs to this user."""


class ExamAttemptAlreadySubmittedError(Exception):
    """An answer was held against an attempt that's already been graded."""


class ExamQuestionNotFoundError(Exception):
    """The question doesn't belong to the attempt's own exam."""


class ExamAnswerKindMismatchError(Exception):
    """The submitted answer's kind doesn't match the question's own kind."""


def _public_question(question: ExamQuestion) -> ExamQuestionRead:
    if question.kind is ExamQuestionKind.QUIZ:
        quiz = QuizPayload.model_validate(question.payload)
        return ExamQuizQuestionRead(
            id=question.id,
            slug=question.slug,
            position=question.position,
            question=quiz.question,
            choices=quiz.choices,
        )
    composition = CompositionPayload.model_validate(question.payload)
    return ExamCompositionQuestionRead(
        id=question.id,
        slug=question.slug,
        position=question.position,
        brief=composition.brief,
        requirements=composition.requirements,
        starter_notation=composition.starter_notation,
        locked_staff_indices=composition.locked_staff_indices,
    )


async def _get_exam_by_slug(db: AsyncSession, exam_slug: str) -> Exam:
    exam = await db.scalar(select(Exam).where(Exam.slug == exam_slug))
    if exam is None:
        raise ExamNotFoundError
    return exam


async def _exam_questions(db: AsyncSession, exam_id: uuid.UUID) -> list[ExamQuestion]:
    rows = await db.scalars(
        select(ExamQuestion)
        .where(ExamQuestion.exam_id == exam_id)
        .order_by(ExamQuestion.position)
    )
    return list(rows.all())


async def _course_slug(db: AsyncSession, course_id: uuid.UUID | None) -> str | None:
    if course_id is None:
        return None
    slug: str | None = await db.scalar(select(Course.slug).where(Course.id == course_id))
    return slug


async def _exam_read(db: AsyncSession, exam: Exam) -> ExamRead:
    questions = await _exam_questions(db, exam.id)
    course_slug = await _course_slug(db, exam.course_id)
    return ExamRead(
        id=exam.id,
        slug=exam.slug,
        title=exam.title,
        description=exam.description,
        course_slug=course_slug,
        question_count=len(questions),
        questions=[_public_question(question) for question in questions],
    )


async def _next_attempt_number(db: AsyncSession, user_id: uuid.UUID, exam_id: uuid.UUID) -> int:
    highest = await db.scalar(
        select(func.max(ExamAttempt.attempt_number)).where(
            ExamAttempt.user_id == user_id, ExamAttempt.exam_id == exam_id
        )
    )
    return (highest or 0) + 1


async def start_attempt(
    db: AsyncSession, user_id: uuid.UUID, exam_slug: str
) -> ExamAttemptStartRead:
    """Starts a new attempt at an exam.

    Always a new row, never a resume of an old one - "retake as often as
    you like" means every attempt is its own history entry (see
    `models.ExamAttempt`), and a new attempt starts with a blank slate of
    held answers, untouched by whatever an earlier attempt on the same exam
    submitted or left half-finished.
    """
    exam = await _get_exam_by_slug(db, exam_slug)
    attempt_number = await _next_attempt_number(db, user_id, exam.id)

    attempt = ExamAttempt(
        id=uuid.uuid4(),
        user_id=user_id,
        exam_id=exam.id,
        attempt_number=attempt_number,
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)

    exam_read = await _exam_read(db, exam)
    return ExamAttemptStartRead(
        attempt_id=attempt.id,
        attempt_number=attempt.attempt_number,
        exam=exam_read,
        started_at=attempt.started_at,
    )


async def _get_attempt(db: AsyncSession, user_id: uuid.UUID, attempt_id: uuid.UUID) -> ExamAttempt:
    attempt = await db.scalar(
        select(ExamAttempt).where(ExamAttempt.id == attempt_id, ExamAttempt.user_id == user_id)
    )
    if attempt is None:
        raise ExamAttemptNotFoundError
    return attempt


async def answer_question(
    db: AsyncSession,
    user_id: uuid.UUID,
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
    answer: ExamAnswerPayload,
) -> ExamAnswerRead:
    """Holds one answer against an in-progress attempt.

    Nothing is graded here - see `models.ExamAttempt`'s docstring for why
    grading waits for the whole attempt to be submitted. Answering the same
    question again replaces what was held rather than erroring or keeping
    both: changing an answer before submitting is the normal case, not an
    edge one.
    """
    attempt = await _get_attempt(db, user_id, attempt_id)
    if attempt.submitted_at is not None:
        raise ExamAttemptAlreadySubmittedError

    question = await db.scalar(
        select(ExamQuestion).where(
            ExamQuestion.id == question_id, ExamQuestion.exam_id == attempt.exam_id
        )
    )
    if question is None:
        raise ExamQuestionNotFoundError

    expected_kind = "quiz" if question.kind is ExamQuestionKind.QUIZ else "composition"
    if answer.kind != expected_kind:
        raise ExamAnswerKindMismatchError(
            f"question '{question.slug}' is a {question.kind.value} question, "
            f"not a {answer.kind} answer"
        )

    payload = answer.model_dump(mode="json")
    upsert = (
        pg_insert(ExamAnswer)
        .values(id=uuid.uuid4(), attempt_id=attempt.id, question_id=question.id, payload=payload)
        .on_conflict_do_update(
            index_elements=["attempt_id", "question_id"], set_={"payload": payload}
        )
    )
    await db.execute(upsert)
    await db.commit()

    return ExamAnswerRead(question_id=question.id, answered=True)


def _grade_quiz_question(
    question: ExamQuestion, answer: ExamAnswer | None
) -> ExamQuestionResultRead:
    quiz = QuizPayload.model_validate(question.payload)
    choice_index = None
    if answer is not None and answer.payload.get("kind") == "quiz":
        choice_index = answer.payload.get("choice_index")
    is_correct = choice_index == quiz.answer_index
    score = 1.0 if is_correct else 0.0

    detail = {
        "choice_index": choice_index,
        "correct_index": quiz.answer_index,
        "is_correct": is_correct,
        "explanation": quiz.explanation,
    }

    # The held answer keeps its own verdict too, alongside the attempt's
    # total - a question with no held answer simply has nothing to update.
    if answer is not None:
        answer.score = score
        answer.max_score = 1.0
        answer.result = detail

    return ExamQuestionResultRead(
        question_id=question.id,
        kind=ExamQuestionKind.QUIZ,
        score=score,
        max_score=1.0,
        detail=detail,
    )


async def _composition_ai_feedback(
    db: AsyncSession,
    user_id: uuid.UUID,
    exam_title: str,
    composition: CompositionPayload,
    grade: DeterministicGrade,
    skill_level: SkillLevel,
) -> dict[str, Any] | None:
    """Written commentary on one composition question, for premium.

    Mirrors `learning.service.submit_composition`'s AI feedback exactly:
    a failure to get commentary (no API key, a failed request) is swallowed
    rather than raised - the deterministic grade is already decided by the
    time this runs, and losing it over an unavailable extra would be a
    worse failure than just not having the extra. Gating *whether* this is
    even offered to a free user is the caller's job (`Feature.
    AI_EXAM_RUBRIC_GRADING`), not this function's.
    """
    try:
        feedback, usage = generate_exercise_feedback(
            exam_title,
            composition.brief,
            grade.requirement_results,
            analysis_bundle(grade),
            skill_level,
        )
    except AIGradingError:
        return None

    await billing_service.record_ai_usage(db, user_id, AiUsageKind.EXAM_RUBRIC_GRADING, usage)
    return feedback.model_dump(mode="json")


async def _grade_composition_question(
    db: AsyncSession,
    user_id: uuid.UUID,
    exam_title: str,
    question: ExamQuestion,
    answer: ExamAnswer | None,
    with_ai_feedback: bool,
    skill_level: SkillLevel,
) -> ExamQuestionResultRead:
    """Grades a composition question against its requirements, via the same
    deterministic pipeline `learning.service.submit_composition` grades a
    lesson's composition steps with (see `notation.grading.grade_submission`).
    AI commentary rides alongside that grade, exactly the way it rides
    alongside a lesson composition's - additive, and never gating whether
    the question passed.

    An unanswered question - or one whose held payload isn't a document,
    which shouldn't happen but is handled the same way rather than raising -
    scores zero without attempting to grade anything.
    """
    if answer is None or answer.payload.get("kind") != "composition":
        detail: dict[str, Any] = {"answered": False}
        if answer is not None:
            answer.score = 0.0
            answer.max_score = 1.0
            answer.result = detail
        return ExamQuestionResultRead(
            question_id=question.id,
            kind=ExamQuestionKind.COMPOSITION,
            score=0.0,
            max_score=1.0,
            detail=detail,
        )

    composition = CompositionPayload.model_validate(question.payload)
    document = NotationDocument.model_validate(answer.payload["document"])
    grade, _musicxml = grade_submission(document, composition.requirements)
    score = 1.0 if grade.passed else 0.0

    ai_feedback = None
    if with_ai_feedback:
        ai_feedback = await _composition_ai_feedback(
            db, user_id, exam_title, composition, grade, skill_level
        )

    grade_detail = grade.model_dump(mode="json")
    grade_detail["ai_feedback"] = ai_feedback

    answer.score = score
    answer.max_score = 1.0
    answer.result = grade_detail

    return ExamQuestionResultRead(
        question_id=question.id,
        kind=ExamQuestionKind.COMPOSITION,
        score=score,
        max_score=1.0,
        detail=grade_detail,
    )


async def _grade_question(
    db: AsyncSession,
    user_id: uuid.UUID,
    exam_title: str,
    question: ExamQuestion,
    answer: ExamAnswer | None,
    with_ai_feedback: bool,
    skill_level: SkillLevel,
) -> ExamQuestionResultRead:
    if question.kind is ExamQuestionKind.QUIZ:
        return _grade_quiz_question(question, answer)
    return await _grade_composition_question(
        db, user_id, exam_title, question, answer, with_ai_feedback, skill_level
    )


async def _answers_by_question(
    db: AsyncSession, attempt_id: uuid.UUID
) -> dict[uuid.UUID, ExamAnswer]:
    rows = await db.scalars(select(ExamAnswer).where(ExamAnswer.attempt_id == attempt_id))
    return {row.question_id: row for row in rows.all()}


async def grade_attempt(
    db: AsyncSession,
    user_id: uuid.UUID,
    attempt_id: uuid.UUID,
    *,
    with_ai_feedback: bool = False,
    skill_level: SkillLevel = SkillLevel.BEGINNER,
) -> ExamAttemptResultRead:
    """Grades every held answer and marks the attempt submitted.

    A one-way door: once graded, `answer_question` refuses new answers for
    this attempt (see `ExamAttemptAlreadySubmittedError`), and grading
    itself can only happen once for the same reason - a second submission
    isn't a re-grade, it's a new attempt (see `start_attempt`).

    `with_ai_feedback` asks for written commentary on every composition
    question in the attempt (see `_composition_ai_feedback`) - it never
    changes any score, and whether a free user is even allowed to ask for
    it is enforced by the caller, not here.
    """
    attempt = await _get_attempt(db, user_id, attempt_id)
    if attempt.submitted_at is not None:
        raise ExamAttemptAlreadySubmittedError

    exam = await db.get(Exam, attempt.exam_id)
    if exam is None:
        raise ExamNotFoundError

    questions = await _exam_questions(db, attempt.exam_id)
    answers = await _answers_by_question(db, attempt.id)

    question_results = [
        await _grade_question(
            db,
            user_id,
            exam.title,
            question,
            answers.get(question.id),
            with_ai_feedback,
            skill_level,
        )
        for question in questions
    ]

    attempt.score = sum(result.score for result in question_results)
    attempt.max_score = sum(result.max_score for result in question_results)
    attempt.submitted_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(attempt)

    return ExamAttemptResultRead(
        attempt_id=attempt.id,
        attempt_number=attempt.attempt_number,
        score=attempt.score,
        max_score=attempt.max_score,
        submitted_at=attempt.submitted_at,
        question_results=question_results,
    )
