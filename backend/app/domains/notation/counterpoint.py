"""Species counterpoint: cantus firmus alignment and interval classification.

Works directly from the submitted `NotationDocument` rather than through
the analysis engines - a species exercise is always exactly two lines (the
given cantus firmus and the student's counterpoint), and the document's
own staff/voice structure already gives each one cleanly. None of
`analysis.harmony`'s vertical-slice inference is needed when the two lines
are already known by construction.

The cantus firmus is identified by its own defining property, true in
every species: it is written entirely in whole notes, one per measure.
Whichever of the exercise's two voices isn't that is the counterpoint,
whatever species it's written in.
"""

from dataclasses import dataclass
from fractions import Fraction

from music21 import interval as m21interval
from music21 import pitch as m21pitch

from app.domains.notation.schemas import NotationDocument, NotationNote
from app.domains.notation.validation import _note_quarters


def _pitch(note: NotationNote) -> m21pitch.Pitch:
    """Mirrors `builder._build_note`'s pitch construction - the one other
    place a `NotationNote` becomes a music21 pitch."""
    built = m21pitch.Pitch()
    built.step = note.step
    built.octave = note.octave
    built.accidental = m21pitch.Accidental(note.alter)
    return built


def _voice_keys(document: NotationDocument) -> list[tuple[int, str]]:
    """Every (staff index, voice id) pair in the document, taken from each
    staff's first measure - a species exercise never changes its voice ids
    partway through."""
    keys: list[tuple[int, str]] = []
    for staff_index, staff in enumerate(document.staves):
        if not staff.measures:
            continue
        for voice in staff.measures[0].voices:
            keys.append((staff_index, voice.id))
    return keys


def _notes_by_measure(
    document: NotationDocument, staff_index: int, voice_id: str
) -> list[list[NotationNote]]:
    result: list[list[NotationNote]] = []
    for measure in document.staves[staff_index].measures:
        voice = next((v for v in measure.voices if v.id == voice_id), None)
        result.append(voice.notes if voice is not None else [])
    return result


def _is_cantus_firmus(notes_by_measure: list[list[NotationNote]]) -> bool:
    return all(
        len(notes) == 1 and not notes[0].is_rest and notes[0].duration == "whole"
        and notes[0].dots == 0
        for notes in notes_by_measure
    )


@dataclass
class CounterpointLines:
    """The two identified lines of a species exercise.

    `cantus_firmus` has exactly one note per measure, by definition;
    `counterpoint_by_measure` has whatever that measure's species calls
    for - one note for first species, several for second/third, notes tied
    across the barline for fourth.
    """

    cantus_firmus: list[NotationNote]
    counterpoint_by_measure: list[list[NotationNote]]


def identify_lines(document: NotationDocument) -> CounterpointLines | None:
    """Finds the cantus firmus and counterpoint voice in a two-voice exercise.

    Requires exactly two voices in the whole document - anything else isn't
    gradeable as species counterpoint at all - and exactly one of them
    matching the cantus firmus's own defining shape.
    """
    keys = _voice_keys(document)
    if len(keys) != 2:
        return None

    lines = [_notes_by_measure(document, *key) for key in keys]
    cf_lines = [notes for notes in lines if _is_cantus_firmus(notes)]
    cp_lines = [notes for notes in lines if not _is_cantus_firmus(notes)]
    if len(cf_lines) != 1 or len(cp_lines) != 1:
        return None

    cantus_firmus = [measure[0] for measure in cf_lines[0]]
    return CounterpointLines(cantus_firmus=cantus_firmus, counterpoint_by_measure=cp_lines[0])


@dataclass
class AlignedInterval:
    """One vertical interval between the cantus firmus and the
    counterpoint, at one metric position within a measure."""

    measure: int  # 1-indexed, matching every other bar-numbered finding
    beat_offset: Fraction  # quarter notes from the start of the measure
    is_downbeat: bool
    cantus_firmus_note: NotationNote
    counterpoint_note: NotationNote
    interval_name: str  # music21's short name, e.g. "P5", "m3", "A4"
    is_consonant: bool


def classify_interval(
    cantus_firmus_note: NotationNote, counterpoint_note: NotationNote
) -> tuple[str, bool]:
    """The harmonic interval's name and whether it's consonant.

    Delegates consonance to music21's own `Interval.isConsonant()` rather
    than reimplementing it - it already applies the standard two-voice
    rule that a perfect fourth is dissonant against the lower voice, which
    a naive "perfect intervals are consonant" check would get wrong.
    """
    iv = m21interval.Interval(
        noteStart=_pitch(cantus_firmus_note), noteEnd=_pitch(counterpoint_note)
    )
    return iv.simpleName, bool(iv.isConsonant())


def align_intervals(lines: CounterpointLines) -> list[AlignedInterval]:
    """Every counterpoint note paired with the cantus firmus note sounding
    under it, in score order.

    A rest in either line has no interval and is skipped rather than
    guessed at - species counterpoint conventionally has no rests at all
    except an opening one in the counterpoint, and there's nothing to
    classify against silence.
    """
    aligned: list[AlignedInterval] = []
    for measure_index, (cf_note, cp_notes) in enumerate(
        zip(lines.cantus_firmus, lines.counterpoint_by_measure, strict=True)
    ):
        offset = Fraction(0)
        for cp_note in cp_notes:
            if not cf_note.is_rest and not cp_note.is_rest:
                name, consonant = classify_interval(cf_note, cp_note)
                aligned.append(
                    AlignedInterval(
                        measure=measure_index + 1,
                        beat_offset=offset,
                        is_downbeat=offset == 0,
                        cantus_firmus_note=cf_note,
                        counterpoint_note=cp_note,
                        interval_name=name,
                        is_consonant=consonant,
                    )
                )
            offset += _note_quarters(cp_note.duration, cp_note.dots)
    return aligned
