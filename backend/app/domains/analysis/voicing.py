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
