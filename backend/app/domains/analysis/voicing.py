"""SATB voicing checks: range, spacing, doubling, voice overlap.

Builds on harmony.py's voice grid - the same `(voice_source, voice_ids,
grid)` triple `_build_voice_leading` already reads - rather than
re-deriving pitches from the score.

Every check in this module is specific to a genuine four-real-voice
texture: a chorale, a string quartet, anything where `voice_source ==
"parts"` and there are exactly four voices. The positional fallback grid
(`voice_source == "vertical-positions"`) infers "the Nth-highest note right
now" per sonority, not a stable singer across time - treating its rows as
soprano/alto/tenor/bass would be judging a voice that doesn't exist.

Voice order follows the grid's own convention: `voice_ids[0]` is the
highest voice (soprano), `voice_ids[-1]` the lowest (bass) - see
`harmony._voice_grid_from_parts`.
"""

from dataclasses import dataclass
from typing import cast

from music21 import note as m21note

from app.domains.analysis.schemas import VoiceRangeViolationRead, VoiceSpacingViolationRead

SOPRANO, ALTO, TENOR, BASS = 0, 1, 2, 3


@dataclass
class VoicedChord:
    """One sonority's SATB voicing.

    Only built for slices where all four voices actually sound - a rest in
    any voice makes range, spacing and doubling unanswerable there, so that
    slice is skipped rather than guessed at (see `four_part_chords`).
    """

    slice_index: int
    measure: int
    soprano: str
    alto: str
    tenor: str
    bass: str

    def pitch(self, position: int) -> str:
        return (self.soprano, self.alto, self.tenor, self.bass)[position]


def four_part_chords(
    voice_source: str,
    voice_ids: list[str],
    grid: dict[str, list[str | None]],
    measures: list[int],
) -> list[VoicedChord]:
    """The subset of slices usable for SATB-specific checks.

    Requires a real four-voice texture (`voice_source == "parts"`, exactly
    four voice ids) - see the module docstring for why the positional
    fallback is excluded - and all four voices sounding at that slice.
    """
    if voice_source != "parts" or len(voice_ids) != 4:
        return []

    chords: list[VoicedChord] = []
    for i, measure in enumerate(measures):
        pitches = [grid[voice_id][i] for voice_id in voice_ids]
        if any(pitch is None for pitch in pitches):
            continue
        soprano, alto, tenor, bass = cast(list[str], pitches)
        chords.append(
            VoicedChord(
                slice_index=i, measure=measure, soprano=soprano, alto=alto, tenor=tenor, bass=bass
            )
        )
    return chords


def pitch_class(name: str) -> int:
    return int(m21note.Note(name).pitch.pitchClass)


def midi(name: str) -> int:
    return int(m21note.Note(name).pitch.midi)


# --------------------------------------------------------------------------- #
# Range
# --------------------------------------------------------------------------- #

# The tessitura a textbook part-writing exercise is judged against (Kostka
# & Payne, "Tonal Harmony") - not any real singer's absolute limit, and
# deliberately a little generous so a well-written exercise doesn't trip
# it at the edges.
_VOICE_RANGES: dict[int, tuple[str, str]] = {
    SOPRANO: ("C4", "A5"),
    ALTO: ("F3", "D5"),
    TENOR: ("C3", "G4"),
    BASS: ("E2", "C4"),
}
_VOICE_NAMES: dict[int, str] = {SOPRANO: "soprano", ALTO: "alto", TENOR: "tenor", BASS: "bass"}


def check_voice_ranges(chords: list[VoicedChord]) -> list[VoiceRangeViolationRead]:
    """Flags every chord where a voice sings outside its conventional range.

    Every offending occurrence is reported, not just the first per voice -
    a passage that sits out of range for eight bars is a bigger problem
    than one that strays for a beat, and the checklist should say so.
    """
    violations: list[VoiceRangeViolationRead] = []
    for position, (low, high) in _VOICE_RANGES.items():
        low_midi, high_midi = midi(low), midi(high)
        for chord in chords:
            pitch = chord.pitch(position)
            if midi(pitch) < low_midi or midi(pitch) > high_midi:
                violations.append(
                    VoiceRangeViolationRead(
                        voice=_VOICE_NAMES[position],
                        chord_index=chord.slice_index,
                        measure=chord.measure,
                        pitch=pitch,
                        expected_low=low,
                        expected_high=high,
                    )
                )
    return violations


# --------------------------------------------------------------------------- #
# Spacing
# --------------------------------------------------------------------------- #

_OCTAVE_SEMITONES = 12

# Only the upper adjacent pairs - a wide gap between tenor and bass is
# ordinary voicing (it's what lets the bass leap for a strong root), not a
# fault the way an open soprano-alto or alto-tenor gap is.
_ADJACENT_UPPER_PAIRS: tuple[tuple[int, int], ...] = ((SOPRANO, ALTO), (ALTO, TENOR))


def check_spacing(chords: list[VoicedChord]) -> list[VoiceSpacingViolationRead]:
    """Flags a gap of more than an octave between an adjacent pair of upper voices."""
    violations: list[VoiceSpacingViolationRead] = []
    for chord in chords:
        for upper_pos, lower_pos in _ADJACENT_UPPER_PAIRS:
            upper, lower = chord.pitch(upper_pos), chord.pitch(lower_pos)
            gap = midi(upper) - midi(lower)
            if gap > _OCTAVE_SEMITONES:
                violations.append(
                    VoiceSpacingViolationRead(
                        upper_voice=_VOICE_NAMES[upper_pos],
                        lower_voice=_VOICE_NAMES[lower_pos],
                        chord_index=chord.slice_index,
                        measure=chord.measure,
                        upper_pitch=upper,
                        lower_pitch=lower,
                        interval_semitones=gap,
                    )
                )
    return violations
