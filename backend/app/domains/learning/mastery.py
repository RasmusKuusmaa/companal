"""Topic mastery: how well one student is doing on one topic, derived from
every attempt that has touched it.

See `models.TopicMastery`'s own docstring for why this is materialized
rather than computed on read. Every function here is a pure mutation of
one `TopicMastery` row - the caller (`service.py`) is responsible for
finding or creating the row and committing the transaction, in the same
one that recorded the attempt itself.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analysis.schemas import HarmonyAnalysis
from app.domains.learning.models import MasteryStatus, Topic, TopicMastery

# Topic slug for evidence read off a composition's own analysis, independent
# of whatever the exercise's requirements checked - see `models.Topic`'s own
# docstring: a parallel-fifths violation is evidence about voice leading
# whether or not the exercise was about parallel fifths. The topic itself is
# seeded separately (Phase J) - see `get_topic_by_slug`.
_VOICE_LEADING_TOPIC_SLUG = "parallel-fifths-and-octaves"

# How many recent outcomes distinguish "struggled a year ago" from
# "getting it wrong now" - see the model's own docstring.
_RECENT_RESULTS_CAP = 10

# `needs_practice` looks at *recent* accuracy, not lifetime: three or more
# attempts is enough to trust the recent window, and if half or more of
# those recent results are wrong, this is a topic actively catching the
# student out right now - what the status exists to surface.
_NEEDS_PRACTICE_MIN_ATTEMPTS = 3
_NEEDS_PRACTICE_MAX_RECENT_ACCURACY = 0.5

# `solid` looks at lifetime accuracy instead: five attempts is enough to
# call a topic settled, and 80% is the conventional "mostly get this
# right" bar - high enough that a couple of early mistakes while still
# learning don't cost a topic its solid status once it's genuinely known.
_SOLID_MIN_ATTEMPTS = 5
_SOLID_MIN_ACCURACY = 0.8


def _mastery_status(
    attempt_count: int, accuracy: float, recent_results: list[bool]
) -> MasteryStatus:
    """`untouched` is never returned - a `TopicMastery` row (and this
    function) only exists once a topic has at least one attempt. It's the
    skill map's own synthesis for a topic with no row at all."""
    recent_accuracy = sum(recent_results) / len(recent_results) if recent_results else accuracy
    if (
        attempt_count >= _NEEDS_PRACTICE_MIN_ATTEMPTS
        and recent_accuracy <= _NEEDS_PRACTICE_MAX_RECENT_ACCURACY
    ):
        return MasteryStatus.NEEDS_PRACTICE
    if attempt_count >= _SOLID_MIN_ATTEMPTS and accuracy >= _SOLID_MIN_ACCURACY:
        return MasteryStatus.SOLID
    return MasteryStatus.LEARNING


async def get_or_create_topic_mastery(
    db: AsyncSession, user_id: uuid.UUID, topic_id: uuid.UUID
) -> TopicMastery:
    """Fetches the student's mastery row for this topic, creating one on
    first contact. `record_result` does the rest - this only ever hands
    back a row for it to update, never a fully-formed status on its own.
    """
    mastery = await db.scalar(
        select(TopicMastery).where(
            TopicMastery.user_id == user_id, TopicMastery.topic_id == topic_id
        )
    )
    if mastery is None:
        # Fields set explicitly rather than left to the column defaults -
        # those only apply at flush time, and `record_result` reads them
        # back immediately on this same, not-yet-flushed instance.
        mastery = TopicMastery(
            user_id=user_id,
            topic_id=topic_id,
            attempt_count=0,
            correct_count=0,
            accuracy=0.0,
            recent_results=[],
            status=MasteryStatus.LEARNING,
        )
        db.add(mastery)
    return mastery


def record_result(mastery: TopicMastery, is_correct: bool) -> None:
    """Folds one new result into a topic's mastery row.

    `mastery` is mutated in place rather than returned as a new object -
    it's always a row already attached to the session (see
    `service.get_or_create_topic_mastery`), and SQLAlchemy tracks the
    change on the existing instance.
    """
    mastery.attempt_count += 1
    if is_correct:
        mastery.correct_count += 1
    mastery.accuracy = mastery.correct_count / mastery.attempt_count
    mastery.recent_results = (mastery.recent_results + [is_correct])[-_RECENT_RESULTS_CAP:]
    mastery.status = _mastery_status(
        mastery.attempt_count, mastery.accuracy, mastery.recent_results
    )
    mastery.last_seen_at = datetime.now(UTC)


def evidence_from_harmony_analysis(harmony: HarmonyAnalysis | None) -> list[tuple[str, bool]]:
    """Topic evidence implicit in a composition's harmony analysis, as
    (topic_slug, was_correct) pairs - on top of whatever the exercise's own
    requirements graded. A submission with no parallel fifths or octaves is
    positive evidence for voice leading even in an exercise that never asked
    about it; one with either is negative evidence.
    """
    if harmony is None:
        return []
    voice_leading = harmony.technical_data.voice_leading
    no_parallels = not voice_leading.parallel_fifths and not voice_leading.parallel_octaves
    return [(_VOICE_LEADING_TOPIC_SLUG, no_parallels)]


async def get_topic_by_slug(db: AsyncSession, slug: str) -> Topic | None:
    """Looks up a topic by its slug, for callers that have a slug in hand
    rather than an id - such as rule-based evidence keyed to a fixed slug
    (see `evidence_from_harmony_analysis`). Returns `None` for a slug that
    hasn't been seeded yet rather than raising: curriculum content (Phase J)
    is seeded separately from the checks that reference its topics.
    """
    topic: Topic | None = await db.scalar(select(Topic).where(Topic.slug == slug))
    return topic
