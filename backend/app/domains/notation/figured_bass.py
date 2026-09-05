"""Figured bass realization checking: does the realization match the figures.

A figured bass exercise gives a bass line, one note per measure, each
annotated with a figure - the standard shorthand for which intervals above
the bass the realization's other voices must include. Works directly from
the submitted `NotationDocument`, the same way `notation.counterpoint`
does: the given bass is a named staff (the locked staff for this
exercise - see `learning.schemas.CompositionPayload.locked_staff_indices`),
and every other voice in the document is the realization to check against
it, whether that's one voice or three.
"""

from music21 import interval as m21interval
from pydantic import BaseModel

from app.domains.notation.counterpoint import _pitch
from app.domains.notation.schemas import NotationDocument, NotationNote

# Kostka & Payne's standard figured-bass table: the generic intervals above
# the bass a figure implies, whichever letter names they land on. Quality
# (major/minor/diminished) is a separate concern a plain digit figure
# never specifies either, so this checker doesn't judge it.
_FIGURE_INTERVALS: dict[str, tuple[int, ...]] = {
    "": (3, 5),
    "5/3": (3, 5),
    "6": (3, 6),
    "6/3": (3, 6),
    "6/4": (4, 6),
    "7": (3, 5, 7),
    "7/5/3": (3, 5, 7),
    "6/5": (3, 5, 6),
    "4/3": (3, 4, 6),
    "4/2": (2, 4, 6),
    "2": (2, 4, 6),
}

_INTERVAL_NAMES: dict[int, str] = {
    2: "second",
    3: "third",
    4: "fourth",
    5: "fifth",
    6: "sixth",
    7: "seventh",
}


class FiguredBassFindingRead(BaseModel):
    """One measure's verdict against its figure."""

    kind: str
    measure: int
    passed: bool
    message: str


def _generic_interval_above(bass: NotationNote, upper: NotationNote) -> int:
    iv = m21interval.Interval(noteStart=_pitch(bass), noteEnd=_pitch(upper))
    return abs(iv.generic.simpleUndirected)


def _bass_and_upper_notes(
    document: NotationDocument, bass_staff_index: int
) -> list[tuple[NotationNote, list[NotationNote]]] | None:
    """One (bass note, realization notes) pair per measure.

    The realization notes are the first note of every voice in the
    document other than the bass's own, at that same measure - `None` if
    the named staff isn't a single, one-note-per-measure bass line, the
    same shape a cantus firmus needs (see `counterpoint._is_cantus_firmus`).
    """
    if not (0 <= bass_staff_index < len(document.staves)):
        return None
    bass_staff = document.staves[bass_staff_index]
    if not bass_staff.measures or not bass_staff.measures[0].voices:
        return None
    bass_voice_id = bass_staff.measures[0].voices[0].id

    other_keys = [
        (staff_index, voice.id)
        for staff_index, staff in enumerate(document.staves)
        for voice in (staff.measures[0].voices if staff.measures else [])
        if not (staff_index == bass_staff_index and voice.id == bass_voice_id)
    ]

    pairs: list[tuple[NotationNote, list[NotationNote]]] = []
    for measure_index, bass_measure in enumerate(bass_staff.measures):
        bass_voice = next((v for v in bass_measure.voices if v.id == bass_voice_id), None)
        if bass_voice is None or not bass_voice.notes:
            return None

        upper_notes: list[NotationNote] = []
        for staff_index, voice_id in other_keys:
            staff = document.staves[staff_index]
            if measure_index >= len(staff.measures):
                continue
            voice = next(
                (v for v in staff.measures[measure_index].voices if v.id == voice_id), None
            )
            if voice is not None and voice.notes:
                upper_notes.append(voice.notes[0])

        pairs.append((bass_voice.notes[0], upper_notes))
    return pairs


def check_figured_bass(
    document: NotationDocument, bass_staff_index: int, figures: list[str]
) -> list[FiguredBassFindingRead] | None:
    """Checks each measure's realization against its figure.

    `None` when the document isn't shaped like a gradeable figured-bass
    exercise at all (wrong staff index, the bass isn't one note per
    measure, or the figure list doesn't match the bass's measure count) -
    a different failure than a rule violation, left for the caller to
    report as such.
    """
    pairs = _bass_and_upper_notes(document, bass_staff_index)
    if pairs is None or len(pairs) != len(figures):
        return None

    findings: list[FiguredBassFindingRead] = []
    for measure_index, ((bass_note, upper_notes), figure) in enumerate(
        zip(pairs, figures, strict=True)
    ):
        measure = measure_index + 1
        required = _FIGURE_INTERVALS.get(figure.strip())
        if required is None:
            findings.append(
                FiguredBassFindingRead(
                    kind="unknown_figure",
                    measure=measure,
                    passed=False,
                    message=(
                        f"Measure {measure}: '{figure}' isn't a figure this checker recognizes."
                    ),
                )
            )
            continue

        if bass_note.is_rest:
            findings.append(
                FiguredBassFindingRead(
                    kind="missing_bass",
                    measure=measure,
                    passed=False,
                    message=f"Measure {measure}: the given bass has no note to realize against.",
                )
            )
            continue

        present = {
            _generic_interval_above(bass_note, note) for note in upper_notes if not note.is_rest
        }
        missing = [interval for interval in required if interval not in present]
        if missing:
            missing_names = ", ".join(_INTERVAL_NAMES.get(n, str(n)) for n in missing)
            findings.append(
                FiguredBassFindingRead(
                    kind="missing_interval",
                    measure=measure,
                    passed=False,
                    message=(
                        f"Measure {measure}: the realization is missing the {missing_names} "
                        f"above the bass that the figure '{figure or '(none)'}' calls for."
                    ),
                )
            )
        else:
            findings.append(
                FiguredBassFindingRead(
                    kind="realization",
                    measure=measure,
                    passed=True,
                    message=f"Measure {measure}: realization matches the figure.",
                )
            )

    return findings
