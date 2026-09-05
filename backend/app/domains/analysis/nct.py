"""Non-chord tone classification: passing, neighbor, suspension,
anticipation, appoggiatura, escape tone.

Builds on harmony.py's own voice grid and chord list - the caller supplies
each slice's chord-tone pitch classes (computed from the same music21
chord `_build_dissonances` already reads) rather than this module reaching
into harmony.py's internals itself, which would make the two modules
import each other.

Every melodic note that isn't a member of the chord sounding under it is
classified by how it's approached and left - the six standard figures all
reduce to that one question. A non-chord tone whose approach/departure
doesn't match any of them is left unclassified rather than forced into the
nearest one.
"""

from app.domains.analysis.schemas import NonChordToneRead
from app.domains.analysis.voicing import midi, pitch_class

_STEP_MAX_SEMITONES = 2


def _direction(a: int, b: int) -> int:
    return 1 if b > a else (-1 if b < a else 0)


def _is_step(a: int, b: int) -> bool:
    return 0 < abs(b - a) <= _STEP_MAX_SEMITONES


def classify_non_chord_tone(before: int | None, current: int, after: int | None) -> str:
    """Classifies one non-chord tone by its melodic shape, in MIDI semitones.

    `before`/`after` are `None` at the start or end of a voice's line - a
    note with nothing on one side can't be judged by any of these figures,
    every one of which needs to see both neighbours.
    """
    if before is None or after is None:
        return "unclassified"

    if before == current:
        return "suspension"
    if current == after:
        return "anticipation"

    approach_step = _is_step(before, current)
    departure_step = _is_step(current, after)
    approach_dir = _direction(before, current)
    departure_dir = _direction(current, after)
    opposite_direction = departure_dir == -approach_dir and approach_dir != 0

    if approach_step and departure_step:
        if approach_dir == departure_dir and approach_dir != 0:
            return "passing"
        if opposite_direction:
            return "neighbor"
        return "unclassified"
    if not approach_step and departure_step and opposite_direction:
        return "appoggiatura"
    if approach_step and not departure_step and opposite_direction:
        return "escape"
    return "unclassified"


def classify_non_chord_tones(
    voice_ids: list[str],
    grid: dict[str, list[str | None]],
    measures: list[int],
    chord_tone_pitch_classes: list[set[int]],
) -> list[NonChordToneRead]:
    """Every melodic note across every voice that isn't a member of the
    chord sounding under it, classified by shape.

    A slice with an empty chord-tone set (harmony.py couldn't identify the
    chord at all) contributes nothing - there's no membership to judge a
    note against.
    """
    findings: list[NonChordToneRead] = []
    for voice_id in voice_ids:
        row = grid[voice_id]
        for i, pitch in enumerate(row):
            if pitch is None:
                continue
            chord_tones = chord_tone_pitch_classes[i]
            if not chord_tones or pitch_class(pitch) in chord_tones:
                continue

            before = row[i - 1] if i > 0 else None
            after = row[i + 1] if i + 1 < len(row) else None
            kind = classify_non_chord_tone(
                midi(before) if before is not None else None,
                midi(pitch),
                midi(after) if after is not None else None,
            )
            findings.append(
                NonChordToneRead(
                    kind=kind, voice=voice_id, chord_index=i, measure=measures[i], pitch=pitch
                )
            )
    return findings
