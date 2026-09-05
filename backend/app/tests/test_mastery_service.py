"""Unit tests for topic mastery: threshold behavior, recency capping, and
the harmony-analysis evidence extraction - see `learning.mastery`.

`record_result` is a pure mutation of an in-memory row and needs no
database; `get_or_create_topic_mastery` and `get_topic_by_slug` do, but
only a seeded topic, not a full curriculum. The end-to-end path - an
attempt updating a *persisted* row in the same transaction - is already
covered by test_learning_service.py and test_composition_submission.py.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analysis.harmony import analyze_harmony, analyze_harmony_from_score
from app.domains.learning.curriculum.definitions import TopicDef
from app.domains.learning.mastery import (
    evidence_from_harmony_analysis,
    get_or_create_topic_mastery,
    get_topic_by_slug,
    record_result,
)
from app.domains.learning.models import MasteryStatus, TopicMastery
from app.domains.learning.seeding import seed_curriculum
from app.domains.users.models import User
from app.tests.test_harmony_service import SATB, _satb


def _fresh_mastery() -> TopicMastery:
    return TopicMastery(
        user_id=uuid.uuid4(),
        topic_id=uuid.uuid4(),
        attempt_count=0,
        correct_count=0,
        accuracy=0.0,
        recent_results=[],
        status=MasteryStatus.LEARNING,
    )


async def _make_user(db_session: AsyncSession) -> User:
    user = User(email="mastery@example.com", hashed_password="not-a-real-hash", full_name="M")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _seed_one_topic(db_session: AsyncSession) -> None:
    await seed_curriculum(
        db_session,
        topics=[
            TopicDef(
                slug="intervals", name="Intervals", area="fundamentals", description="d"
            )
        ],
        courses=[],
    )


class TestRecordResult:
    def test_a_correct_result_increments_both_counts(self) -> None:
        mastery = _fresh_mastery()
        record_result(mastery, True)

        assert mastery.attempt_count == 1
        assert mastery.correct_count == 1
        assert mastery.accuracy == 1.0
        assert mastery.recent_results == [True]
        assert mastery.last_seen_at is not None

    def test_a_wrong_result_increments_only_the_attempt_count(self) -> None:
        mastery = _fresh_mastery()
        record_result(mastery, False)

        assert mastery.attempt_count == 1
        assert mastery.correct_count == 0
        assert mastery.accuracy == 0.0
        assert mastery.recent_results == [False]

    def test_recent_results_caps_at_ten_oldest_first(self) -> None:
        mastery = _fresh_mastery()
        for i in range(12):
            record_result(mastery, i % 2 == 0)

        assert len(mastery.recent_results) == 10
        assert mastery.recent_results == [(i % 2 == 0) for i in range(2, 12)]

    def test_accuracy_is_lifetime_not_just_recent(self) -> None:
        mastery = _fresh_mastery()
        for is_correct in [True, True, True, False]:
            record_result(mastery, is_correct)

        assert mastery.accuracy == 0.75


class TestMasteryStatusThresholds:
    def test_stays_learning_below_three_attempts_even_if_all_wrong(self) -> None:
        mastery = _fresh_mastery()
        record_result(mastery, False)
        record_result(mastery, False)

        assert mastery.status is MasteryStatus.LEARNING

    def test_needs_practice_once_three_attempts_are_half_or_more_wrong(self) -> None:
        mastery = _fresh_mastery()
        record_result(mastery, True)
        record_result(mastery, False)
        record_result(mastery, False)

        assert mastery.status is MasteryStatus.NEEDS_PRACTICE

    def test_solid_after_five_attempts_at_eighty_percent_or_better(self) -> None:
        mastery = _fresh_mastery()
        for is_correct in [True, True, True, True, False]:
            record_result(mastery, is_correct)

        assert mastery.accuracy == 0.8
        assert mastery.status is MasteryStatus.SOLID

    def test_not_solid_below_eighty_percent_even_after_five_attempts(self) -> None:
        mastery = _fresh_mastery()
        for is_correct in [True, True, True, False, False]:
            record_result(mastery, is_correct)

        assert mastery.accuracy == 0.6
        assert mastery.status is not MasteryStatus.SOLID

    def test_a_recent_slump_flips_a_decent_lifetime_record_to_needs_practice(self) -> None:
        # Ten correct, then five wrong: lifetime accuracy is a respectable
        # 0.67, but the last ten results are half wrong - `needs_practice`
        # reads recency, not the lifetime number, so it still fires.
        mastery = _fresh_mastery()
        for _ in range(10):
            record_result(mastery, True)
        for _ in range(5):
            record_result(mastery, False)

        assert mastery.accuracy > 0.5
        assert mastery.status is MasteryStatus.NEEDS_PRACTICE


class TestGetOrCreateTopicMastery:
    async def test_creates_a_zeroed_row_on_first_contact(
        self, db_session: AsyncSession
    ) -> None:
        await _seed_one_topic(db_session)
        topic = await get_topic_by_slug(db_session, "intervals")
        assert topic is not None
        user = await _make_user(db_session)

        mastery = await get_or_create_topic_mastery(db_session, user.id, topic.id)

        assert mastery.attempt_count == 0
        assert mastery.correct_count == 0
        assert mastery.accuracy == 0.0
        assert mastery.recent_results == []
        assert mastery.status is MasteryStatus.LEARNING

    async def test_returns_the_existing_row_on_a_second_call(
        self, db_session: AsyncSession
    ) -> None:
        await _seed_one_topic(db_session)
        topic = await get_topic_by_slug(db_session, "intervals")
        assert topic is not None
        user = await _make_user(db_session)

        first = await get_or_create_topic_mastery(db_session, user.id, topic.id)
        record_result(first, True)
        await db_session.commit()

        second = await get_or_create_topic_mastery(db_session, user.id, topic.id)
        assert second.attempt_count == 1


class TestGetTopicBySlug:
    async def test_returns_none_for_an_unseeded_slug(self, db_session: AsyncSession) -> None:
        assert await get_topic_by_slug(db_session, "no-such-topic") is None


class TestEvidenceFromHarmonyAnalysis:
    def test_no_analysis_means_no_evidence(self) -> None:
        assert evidence_from_harmony_analysis(None) == []

    def test_parallel_fifths_or_octaves_count_as_negative_evidence(self) -> None:
        harmony = analyze_harmony(SATB, "harmony_satb.musicxml")
        assert evidence_from_harmony_analysis(harmony) == [
            ("parallel-fifths-and-octaves", False)
        ]

    def test_clean_voice_leading_counts_as_positive_evidence(self) -> None:
        score = _satb(
            [("C5", "E4", "G3", "C3"), ("B4", "D4", "G3", "G2"), ("C5", "E4", "G3", "C3")]
        )
        harmony = analyze_harmony_from_score(score)
        assert evidence_from_harmony_analysis(harmony) == [
            ("parallel-fifths-and-octaves", True)
        ]
