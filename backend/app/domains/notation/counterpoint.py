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
from music21 import note as m21note
from music21 import pitch as m21pitch
from music21 import voiceLeading as m21voiceLeading
from pydantic import BaseModel

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


def identify_lines(
    document: NotationDocument, cantus_firmus_staff_index: int | None = None
) -> CounterpointLines | None:
    """Finds the cantus firmus and counterpoint voice in a two-voice exercise.

    Requires exactly two voices in the whole document - anything else isn't
    gradeable as species counterpoint at all.

    `cantus_firmus_staff_index`, when given, names the staff directly - a
    species exercise's cantus firmus is the given, locked staff (see
    `learning.schemas.CompositionPayload.locked_staff_indices`), which is
    known from the exercise itself rather than guessed at. Without it, the
    only voice written entirely in whole notes is used instead - but that
    guess can't tell the two apart in first species, where the
    counterpoint is *also* one whole note per measure, so callers that
    know which staff is given should always pass it.
    """
    keys = _voice_keys(document)
    if len(keys) != 2:
        return None

    if cantus_firmus_staff_index is not None:
        cf_position = next(
            (i for i, key in enumerate(keys) if key[0] == cantus_firmus_staff_index), None
        )
        if cf_position is None:
            return None
        cantus_firmus_notes = _notes_by_measure(document, *keys[cf_position])
        if not _is_cantus_firmus(cantus_firmus_notes):
            return None
        counterpoint_notes = _notes_by_measure(document, *keys[1 - cf_position])
        return CounterpointLines(
            cantus_firmus=[measure[0] for measure in cantus_firmus_notes],
            counterpoint_by_measure=counterpoint_notes,
        )

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


def _midi(note: NotationNote) -> int:
    return int(_pitch(note).midi)


def _quartet(
    before: AlignedInterval, after: AlignedInterval
) -> m21voiceLeading.VoiceLeadingQuartet:
    """The four notes of one transition, counterpoint first - matches
    `analysis.harmony`'s own `(v1n1, v1n2, v2n1, v2n2)` argument order for
    `VoiceLeadingQuartet`, which parallel/hidden detection doesn't care
    about the meaning of, only the pairing."""
    return m21voiceLeading.VoiceLeadingQuartet(
        m21note.Note(_pitch(before.counterpoint_note).nameWithOctave),
        m21note.Note(_pitch(after.counterpoint_note).nameWithOctave),
        m21note.Note(_pitch(before.cantus_firmus_note).nameWithOctave),
        m21note.Note(_pitch(after.cantus_firmus_note).nameWithOctave),
    )


class CounterpointFindingRead(BaseModel):
    """One rule's verdict at one point in a species exercise.

    `kind` names which rule it's from (`dissonance`, `parallel_fifth`,
    `parallel_octave`, `motion_preference`, `cadence`, ...) - the same
    open-ended, string-tagged shape `voicing.py`'s violation schemas use,
    since a species exercise's rule set grows by species (see
    `check_first_species`, `check_second_and_third_species`,
    `check_fourth_species`).
    """

    kind: str
    measure: int
    passed: bool
    message: str


# --------------------------------------------------------------------------- #
# First species
# --------------------------------------------------------------------------- #

_IMPERFECT_CONSONANCE_NAMES = frozenset({"m3", "M3", "m6", "M6"})
_PERFECT_CADENCE_NAMES = frozenset({"P1", "P8"})
# music21's own motion-type names for "both voices move the same direction" -
# the thing strict style prefers to avoid, whether or not the interval is
# actually preserved (parallel) or just similarly shaped (similar).
_SIMILAR_DIRECTION_MOTION = frozenset({"parallel", "similar"})


def _check_consonance_only(aligned: list[AlignedInterval]) -> list[CounterpointFindingRead]:
    """First species allows only consonant intervals - there's no rhythmic
    subdivision to place a passing dissonance against, unlike second
    species and beyond."""
    return [
        CounterpointFindingRead(
            kind="dissonance",
            measure=interval.measure,
            passed=False,
            message=(
                f"Measure {interval.measure}: {interval.interval_name} against the cantus "
                "firmus is dissonant - first species allows only consonant intervals."
            ),
        )
        for interval in aligned
        if not interval.is_consonant
    ]


def _check_no_parallel_perfects(aligned: list[AlignedInterval]) -> list[CounterpointFindingRead]:
    findings: list[CounterpointFindingRead] = []
    for i in range(len(aligned) - 1):
        before, after = aligned[i], aligned[i + 1]
        quartet = _quartet(before, after)
        if quartet.parallelFifth():
            findings.append(
                CounterpointFindingRead(
                    kind="parallel_fifth",
                    measure=after.measure,
                    passed=False,
                    message=f"Parallel fifths into measure {after.measure}.",
                )
            )
        if quartet.parallelOctave() or quartet.parallelUnison():
            findings.append(
                CounterpointFindingRead(
                    kind="parallel_octave",
                    measure=after.measure,
                    passed=False,
                    message=f"Parallel octaves (or unisons) into measure {after.measure}.",
                )
            )
    return findings


def _check_contrary_motion_preference(
    aligned: list[AlignedInterval],
) -> list[CounterpointFindingRead]:
    """Not a hard rule - strict style *prefers* contrary and oblique motion
    over similar motion, but doesn't forbid it outright. Reported once, as
    a summary over the whole exercise, rather than once per transition.
    """
    total = 0
    similar = 0
    for i in range(len(aligned) - 1):
        quartet = _quartet(aligned[i], aligned[i + 1])
        motion = quartet.motionType()
        if motion is None or motion.name == "noMotion":
            continue
        total += 1
        if motion.name in _SIMILAR_DIRECTION_MOTION:
            similar += 1

    if total == 0:
        return []

    passed = similar <= total / 2
    message = (
        f"{similar} of {total} note-to-note motions are similar motion - "
        f"{'within' if passed else 'more than'} the preference for contrary or oblique motion."
    )
    return [
        CounterpointFindingRead(
            kind="motion_preference", measure=aligned[-1].measure, passed=passed, message=message
        )
    ]


def _check_cadence_formula(aligned: list[AlignedInterval]) -> list[CounterpointFindingRead]:
    """The closing formula every species is judged on: a perfect unison or
    octave, reached from an imperfect consonance by step in the
    counterpoint.

    Only the counterpoint's own approach is judged - the cantus firmus's
    shape is given, not written by the student.
    """
    if len(aligned) < 2:
        return []

    penultimate, final = aligned[-2], aligned[-1]
    findings: list[CounterpointFindingRead] = []

    if final.interval_name not in _PERFECT_CADENCE_NAMES:
        return [
            CounterpointFindingRead(
                kind="cadence",
                measure=final.measure,
                passed=False,
                message=(
                    f"The piece must end on a perfect unison or octave; "
                    f"it ends on {final.interval_name}."
                ),
            )
        ]

    if penultimate.interval_name not in _IMPERFECT_CONSONANCE_NAMES:
        findings.append(
            CounterpointFindingRead(
                kind="cadence",
                measure=penultimate.measure,
                passed=False,
                message=(
                    "The note before the final one should form a third or sixth with the "
                    f"cantus firmus; it forms a {penultimate.interval_name}."
                ),
            )
        )

    step = abs(_midi(penultimate.counterpoint_note) - _midi(final.counterpoint_note))
    if step not in (1, 2):
        findings.append(
            CounterpointFindingRead(
                kind="cadence",
                measure=final.measure,
                passed=False,
                message="The counterpoint should approach its final note by step.",
            )
        )

    if not findings:
        findings.append(
            CounterpointFindingRead(
                kind="cadence",
                measure=final.measure,
                passed=True,
                message="Ends with a correct cadence formula.",
            )
        )
    return findings


def check_first_species(lines: CounterpointLines) -> list[CounterpointFindingRead]:
    """The rules a first-species (1:1) exercise is marked on: every interval
    consonant, no parallel fifths or octaves, a preference for contrary
    motion, and a correct closing cadence."""
    aligned = align_intervals(lines)
    return [
        *_check_consonance_only(aligned),
        *_check_no_parallel_perfects(aligned),
        *_check_contrary_motion_preference(aligned),
        *_check_cadence_formula(aligned),
    ]
