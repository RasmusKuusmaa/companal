import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.feedback.models import Feedback, SkillLevel
from app.domains.feedback.schemas import CompositionFeedback, FeedbackIssue, TheoryLesson
from app.domains.feedback.service import (
    AnalysisNotFoundError,
    FeedbackNotFoundError,
    generate_composition_feedback,
    get_composition_feedback,
)
from app.domains.projects.models import Composition, CompositionAnalysis, Version
from app.domains.projects.service import CompositionNotFoundError
from app.domains.users.models import User

_FAKE_FEEDBACK = CompositionFeedback(
    summary="A solid draft with one voice-leading issue to fix.",
    strengths=["Clear melodic contour"],
    issues=[
        FeedbackIssue(
            problem="Parallel fifths in measure 4.",
            explanation="Two voices move in parallel perfect fifths.",
            suggestion="Move one voice by a different interval.",
            theory=TheoryLesson(
                concept="Parallel fifths",
                lesson="Avoid two voices moving in parallel perfect fifths - it reduces "
                "their independence.",
            ),
        )
    ],
    suggestions=["Vary the accompaniment rhythm for more interest."],
)


async def _make_user(db_session: AsyncSession, email: str = "composer@example.com") -> User:
    user = User(email=email, hashed_password="not-a-real-hash", full_name="Composer")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _make_analyzed_composition(db_session: AsyncSession, owner: User) -> CompositionAnalysis:
    composition = Composition(owner_id=owner.id, title="Sonata No. 1")
    db_session.add(composition)
    await db_session.flush()

    version = Version(
        composition_id=composition.id,
        version_number=1,
        original_filename="piece.musicxml",
        storage_key=f"{composition.id}/v1.musicxml",
        file_size=10,
    )
    db_session.add(version)
    composition.version_count = 1
    await db_session.flush()

    analysis = CompositionAnalysis(
        composition_id=composition.id,
        version_id=version.id,
        overall_score=80.0,
        melody_score=80.0,
        harmony_analysis=None,
        rhythm_analysis=None,
        unavailable=[],
    )
    db_session.add(analysis)
    await db_session.commit()
    await db_session.refresh(analysis)
    return analysis


def _mock_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.domains.feedback.service.generate_feedback",
        lambda *_args, **_kwargs: _FAKE_FEEDBACK,
    )


class TestGenerateCompositionFeedback:
    async def test_raises_for_a_composition_owned_by_someone_else(
        self, db_session: AsyncSession
    ) -> None:
        owner = await _make_user(db_session, "owner@example.com")
        other = await _make_user(db_session, "other@example.com")
        analysis = await _make_analyzed_composition(db_session, owner)

        with pytest.raises(CompositionNotFoundError):
            await generate_composition_feedback(
                db_session, other.id, analysis.composition_id, SkillLevel.BEGINNER
            )

    async def test_raises_when_not_yet_analyzed(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session)
        composition = Composition(owner_id=owner.id, title="Unanalyzed")
        db_session.add(composition)
        await db_session.commit()
        await db_session.refresh(composition)

        with pytest.raises(AnalysisNotFoundError):
            await generate_composition_feedback(
                db_session, owner.id, composition.id, SkillLevel.BEGINNER
            )

    async def test_stores_the_ai_response(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _mock_ai(monkeypatch)
        owner = await _make_user(db_session)
        analysis = await _make_analyzed_composition(db_session, owner)

        feedback = await generate_composition_feedback(
            db_session, owner.id, analysis.composition_id, SkillLevel.BEGINNER
        )

        assert feedback.version_id == analysis.version_id
        assert feedback.skill_level == SkillLevel.BEGINNER
        assert feedback.summary == _FAKE_FEEDBACK.summary
        assert feedback.strengths == _FAKE_FEEDBACK.strengths
        assert feedback.issues[0]["problem"] == "Parallel fifths in measure 4."
        assert feedback.issues[0]["theory"]["concept"] == "Parallel fifths"
        assert feedback.suggestions == _FAKE_FEEDBACK.suggestions

    async def test_regenerating_overwrites_rather_than_adding_a_row(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _mock_ai(monkeypatch)
        owner = await _make_user(db_session)
        analysis = await _make_analyzed_composition(db_session, owner)

        first = await generate_composition_feedback(
            db_session, owner.id, analysis.composition_id, SkillLevel.BEGINNER
        )
        second = await generate_composition_feedback(
            db_session, owner.id, analysis.composition_id, SkillLevel.BEGINNER
        )

        assert first.id == second.id

    async def test_different_skill_levels_get_their_own_row(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _mock_ai(monkeypatch)
        owner = await _make_user(db_session)
        analysis = await _make_analyzed_composition(db_session, owner)

        beginner = await generate_composition_feedback(
            db_session, owner.id, analysis.composition_id, SkillLevel.BEGINNER
        )
        advanced = await generate_composition_feedback(
            db_session, owner.id, analysis.composition_id, SkillLevel.ADVANCED
        )

        assert beginner.id != advanced.id


class TestGetCompositionFeedback:
    async def test_raises_when_none_generated_yet(self, db_session: AsyncSession) -> None:
        owner = await _make_user(db_session)
        analysis = await _make_analyzed_composition(db_session, owner)

        with pytest.raises(FeedbackNotFoundError):
            await get_composition_feedback(
                db_session, owner.id, analysis.composition_id, SkillLevel.BEGINNER
            )

    async def test_returns_previously_generated_feedback(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _mock_ai(monkeypatch)
        owner = await _make_user(db_session)
        analysis = await _make_analyzed_composition(db_session, owner)
        generated = await generate_composition_feedback(
            db_session, owner.id, analysis.composition_id, SkillLevel.INTERMEDIATE
        )

        fetched = await get_composition_feedback(
            db_session, owner.id, analysis.composition_id, SkillLevel.INTERMEDIATE
        )

        assert fetched.id == generated.id
        assert isinstance(fetched, Feedback)
