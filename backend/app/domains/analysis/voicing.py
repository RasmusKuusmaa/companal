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

from collections import Counter
from dataclasses import dataclass
from typing import cast

from music21 import note as m21note

from app.domains.analysis.schemas import (
    VoiceDoublingViolationRead,
    VoiceOverlapViolationRead,
    VoiceRangeViolationRead,
    VoiceSpacingViolationRead,
    VoicingReport,
)

SOPRANO, ALTO, TENOR, BASS = 0, 1, 2, 3


@dataclass
class ChordTones:
    """A slice's chord-tone pitch classes, read off the music21 chord
    harmony.py already built (`_chord_attr(chord, "root"/"third"/"seventh")`).

    `None` when music21 couldn't identify that tone on a degenerate
    sonority - `check_doubling` treats an unknown tone as nothing to check,
    not as absent.
    """

    root: int | None
    third: int | None
    seventh: int | None


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
    chord_tones: ChordTones | None = None

    def pitch(self, position: int) -> str:
        return (self.soprano, self.alto, self.tenor, self.bass)[position]


def four_part_chords(
    voice_source: str,
    voice_ids: list[str],
    grid: dict[str, list[str | None]],
    measures: list[int],
    chord_tones: list[ChordTones] | None = None,
) -> list[VoicedChord]:
    """The subset of slices usable for SATB-specific checks.

    Requires a real four-voice texture (`voice_source == "parts"`, exactly
    four voice ids) - see the module docstring for why the positional
    fallback is excluded - and all four voices sounding at that slice.

    `chord_tones`, when given, is parallel to `measures` (one entry per
    slice) - only `check_doubling` needs it, so range and spacing checks
    can build their chords without it.
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
                slice_index=i,
                measure=measure,
                soprano=soprano,
                alto=alto,
                tenor=tenor,
                bass=bass,
                chord_tones=chord_tones[i] if chord_tones is not None else None,
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


# --------------------------------------------------------------------------- #
# Doubling
# --------------------------------------------------------------------------- #


def check_doubling(
    chords: list[VoicedChord], leading_tone_pc: int | None
) -> list[VoiceDoublingViolationRead]:
    """Flags the three classic four-part doubling faults.

    A doubled leading tone almost always produces parallel octaves or an
    unresolved duplicate when it resolves up to the tonic; a doubled
    chordal seventh does the same on its resolution down. A missing third
    is checked against the chord music21 actually identified, not
    invented - a sonority with no clear third (a bare fifth, a cluster)
    has nothing here to be missing.
    """
    violations: list[VoiceDoublingViolationRead] = []
    for chord in chords:
        pitches = [chord.soprano, chord.alto, chord.tenor, chord.bass]
        pitch_classes = [pitch_class(p) for p in pitches]
        counts = Counter(pitch_classes)

        if leading_tone_pc is not None and counts[leading_tone_pc] > 1:
            violations.append(
                VoiceDoublingViolationRead(
                    kind="doubled_leading_tone",
                    chord_index=chord.slice_index,
                    measure=chord.measure,
                    pitches=pitches,
                )
            )

        tones = chord.chord_tones
        if tones is not None and tones.seventh is not None and counts[tones.seventh] > 1:
            violations.append(
                VoiceDoublingViolationRead(
                    kind="doubled_seventh",
                    chord_index=chord.slice_index,
                    measure=chord.measure,
                    pitches=pitches,
                )
            )

        if tones is not None and tones.third is not None and counts[tones.third] == 0:
            violations.append(
                VoiceDoublingViolationRead(
                    kind="missing_third",
                    chord_index=chord.slice_index,
                    measure=chord.measure,
                    pitches=pitches,
                )
            )

    return violations


# --------------------------------------------------------------------------- #
# Overlap
# --------------------------------------------------------------------------- #

# All three adjacent pairs, unlike spacing's upper-only pairs - overlap is
# about voice independence, which matters just as much between tenor and
# bass as it does higher in the texture.
_ADJACENT_PAIRS: tuple[tuple[int, int], ...] = ((SOPRANO, ALTO), (ALTO, TENOR), (TENOR, BASS))


def check_overlaps(chords: list[VoicedChord]) -> list[VoiceOverlapViolationRead]:
    """Flags a voice moving into the pitch territory an adjacent voice just
    vacated - distinct from a crossing, which is two voices out of order at
    the same instant (see `VoiceOverlapViolationRead`).

    Only checked between genuinely consecutive slices - `chords` can skip
    an index when a voice rested there (see `four_part_chords`), and
    comparing across that gap would be judging a transition that was never
    actually played.
    """
    violations: list[VoiceOverlapViolationRead] = []
    for i in range(len(chords) - 1):
        before, after = chords[i], chords[i + 1]
        if after.slice_index != before.slice_index + 1:
            continue

        for upper_pos, lower_pos in _ADJACENT_PAIRS:
            upper_before, upper_after = before.pitch(upper_pos), after.pitch(upper_pos)
            lower_before, lower_after = before.pitch(lower_pos), after.pitch(lower_pos)
            overlapped = (
                midi(upper_after) < midi(lower_before) or midi(lower_after) > midi(upper_before)
            )
            if overlapped:
                violations.append(
                    VoiceOverlapViolationRead(
                        upper_voice=_VOICE_NAMES[upper_pos],
                        lower_voice=_VOICE_NAMES[lower_pos],
                        from_index=before.slice_index,
                        to_index=after.slice_index,
                        measure=after.measure,
                        upper_motion=f"{upper_before}->{upper_after}",
                        lower_motion=f"{lower_before}->{lower_after}",
                    )
                )
    return violations


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #


def build_voicing_report(
    voice_source: str,
    voice_ids: list[str],
    grid: dict[str, list[str | None]],
    measures: list[int],
    chord_tones: list[ChordTones],
    leading_tone_pc: int | None,
) -> VoicingReport | None:
    """Runs every SATB voicing check and bundles the findings.

    `None` when the texture isn't a genuine four-real-voice score, or none
    of its sonorities have all four voices sounding at once - either way,
    there is nothing for these checks to judge.
    """
    chords = four_part_chords(voice_source, voice_ids, grid, measures, chord_tones)
    if not chords:
        return None

    return VoicingReport(
        range_violations=check_voice_ranges(chords),
        spacing_violations=check_spacing(chords),
        doubling_violations=check_doubling(chords, leading_tone_pc),
        overlaps=check_overlaps(chords),
    )
