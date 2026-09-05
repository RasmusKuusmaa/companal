"""Topic mastery: how well one student is doing on one topic, derived from
every attempt that has touched it.

See `models.TopicMastery`'s own docstring for why this is materialized
rather than computed on read. Every function here is a pure mutation of
one `TopicMastery` row - the caller (`service.py`) is responsible for
finding or creating the row and committing the transaction, in the same
one that recorded the attempt itself.
"""

from datetime import UTC, datetime

from app.domains.learning.models import MasteryStatus, TopicMastery

# How many recent outcomes distinguish "struggled a year ago" from
# "getting it wrong now" - see the model's own docstring.
_RECENT_RESULTS_CAP = 10


def _mastery_status(
    attempt_count: int, accuracy: float, recent_results: list[bool]
) -> MasteryStatus:
    recent_accuracy = sum(recent_results) / len(recent_results) if recent_results else accuracy
    if attempt_count >= 3 and recent_accuracy <= 0.5:
        return MasteryStatus.NEEDS_PRACTICE
    if attempt_count >= 5 and accuracy >= 0.8:
        return MasteryStatus.SOLID
    return MasteryStatus.LEARNING


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
