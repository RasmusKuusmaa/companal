"""Turns a notation document into a music21 `Score`, and that into MusicXML.

The one place a `NotationDocument` becomes MusicXML - every other consumer
(the analysis engines, the requirement validators, storage) works from the
`Score` or the bytes this produces, never from the document's own JSON. That
keeps "what MusicXML looks like for this note" decided in exactly one place.

Pitch is built from step/octave/alter directly (`pitch.Pitch()` fields), not
by formatting a string like `"F#4"` and having music21 re-parse it - the
document already has the pitch fully specified, and round-tripping it
through a string is a chance to get the double-sharp/double-flat spelling
wrong for no benefit.
"""

from music21 import clef as m21clef
from music21 import duration as m21duration
from music21 import key as m21key
from music21 import meter as m21meter
from music21 import note as m21note
from music21 import pitch as m21pitch
from music21 import stream as m21stream
from music21 import tempo as m21tempo
from music21 import tie as m21tie
from music21.musicxml.m21ToXml import GeneralObjectExporter

from app.domains.notation.schemas import (
    ClefName,
    DurationName,
    NotationDocument,
    NotationNote,
    NotationStaff,
)

_CLEF_CLASSES: dict[ClefName, type[m21clef.Clef]] = {
    "treble": m21clef.TrebleClef,
    "bass": m21clef.BassClef,
    "alto": m21clef.AltoClef,
    "tenor": m21clef.TenorClef,
}

# Major tonic name for each fifths count. The minor tonic is this scale's
# relative minor, which music21's `key.Key(tonic, mode)` derives on its own
# once given the right tonic letter - see `_key_object` below for how mode
# picks between the two names at the same fifths count.
_MAJOR_TONIC_BY_FIFTHS: dict[int, str] = {
    -7: "C-", -6: "G-", -5: "D-", -4: "A-", -3: "E-", -2: "B-", -1: "F",
    0: "C", 1: "G", 2: "D", 3: "A", 4: "E", 5: "B", 6: "F#", 7: "C#",
}  # fmt: skip

# The relative minor tonic at the same fifths count, e.g. 0 fifths -> "A"
# (A minor, no sharps or flats, same as C major).
_MINOR_TONIC_BY_FIFTHS: dict[int, str] = {
    -7: "A-", -6: "E-", -5: "B-", -4: "F", -3: "C", -2: "G", -1: "D",
    0: "A", 1: "E", 2: "B", 3: "F#", 4: "C#", 5: "G#", 6: "D#", 7: "A#",
}  # fmt: skip


class NotationBuildError(Exception):
    """Raised when a document can't be turned into a valid score."""


def _key_object(document: NotationDocument) -> m21key.Key:
    tonic = (
        _MAJOR_TONIC_BY_FIFTHS[document.fifths]
        if document.mode == "major"
        else _MINOR_TONIC_BY_FIFTHS[document.fifths]
    )
    return m21key.Key(tonic, document.mode)


def _build_note(note: NotationNote) -> m21note.GeneralNote:
    music21_duration = m21duration.Duration(type=_DURATION_TYPE[note.duration], dots=note.dots)

    if note.is_rest:
        rest = m21note.Rest()
        rest.duration = music21_duration
        return rest

    built_pitch = m21pitch.Pitch()
    built_pitch.step = note.step
    built_pitch.octave = note.octave
    built_pitch.accidental = m21pitch.Accidental(note.alter)

    built_note = m21note.Note()
    built_note.pitch = built_pitch
    built_note.duration = music21_duration
    return built_note


_DURATION_TYPE: dict[DurationName, str] = {
    "whole": "whole",
    "half": "half",
    "quarter": "quarter",
    "eighth": "eighth",
    "16th": "16th",
    "32nd": "32nd",
}


def _apply_ties(notes: list[m21note.GeneralNote], tied_flags: list[bool]) -> None:
    """Sets each note's tie state from the document's `tied_to_next` flags.

    A chain needs `start` on its first note, `continue` on every note in the
    middle, and `stop` on its last - music21 (and MusicXML) track a tie as a
    property of each note it touches, not as a single span object, so this
    has to walk the sequence rather than mark just the two ends.
    """
    for index, (built, tied_to_next) in enumerate(zip(notes, tied_flags, strict=True)):
        if isinstance(built, m21note.Rest):
            continue
        tied_from_previous = (
            index > 0 and tied_flags[index - 1] and not isinstance(notes[index - 1], m21note.Rest)
        )
        if tied_to_next and tied_from_previous:
            built.tie = m21tie.Tie("continue")
        elif tied_to_next:
            built.tie = m21tie.Tie("start")
        elif tied_from_previous:
            built.tie = m21tie.Tie("stop")


def _build_staff_part(document: NotationDocument, staff: NotationStaff) -> m21stream.Part:
    part = m21stream.Part()
    if staff.name:
        part.partName = staff.name

    clef_class = _CLEF_CLASSES.get(staff.clef)
    if clef_class is None:
        raise NotationBuildError(f"unknown clef: {staff.clef}")

    for measure_index, measure in enumerate(staff.measures):
        built_measure = m21stream.Measure(number=measure_index + 1)

        if measure_index == 0:
            built_measure.insert(0, clef_class())
            built_measure.insert(0, _key_object(document))
            built_measure.insert(
                0, m21meter.TimeSignature(f"{document.time.beats}/{document.time.beat_type}")
            )
            built_measure.insert(0, m21tempo.MetronomeMark(number=document.tempo))

        for voice_index, voice in enumerate(measure.voices):
            built_notes = [_build_note(note) for note in voice.notes]
            _apply_ties(built_notes, [note.tied_to_next for note in voice.notes])

            if len(measure.voices) == 1:
                # A single voice is written directly into the measure - an
                # explicit <voice> wrapper around it would be legal MusicXML
                # but is needless noise for the overwhelmingly common case
                # of one line per staff.
                for built_note in built_notes:
                    built_measure.append(built_note)
            else:
                built_voice = m21stream.Voice(id=voice.id or str(voice_index + 1))
                for built_note in built_notes:
                    built_voice.append(built_note)
                built_measure.insert(0, built_voice)

        part.append(built_measure)

    return part


def build_score(document: NotationDocument) -> m21stream.Score:
    """Builds a complete `Score` - every staff, every measure, in order."""
    score = m21stream.Score()
    for staff in document.staves:
        score.append(_build_staff_part(document, staff))
    return score


def to_musicxml_bytes(document: NotationDocument) -> bytes:
    """Renders a document straight to MusicXML bytes, no filesystem involved.

    `GeneralObjectExporter` rather than `Score.write("musicxml")`: `write`
    always goes through a temp file (see `analysis/service.py`'s own note on
    why parsing needs one), which this doesn't need - the score is already
    in memory and the caller wants bytes back, not a path.
    """
    score = build_score(document)
    return bytes(GeneralObjectExporter(score).parse())
