"""MusicXML -> notation document: the inverse of `builder.py`.

Lets an uploaded score open in the editor. The parsing itself reuses
`analysis.service._parse_score`'s temp-file approach (music21 only reliably
parses from a path), and everything past that walks the resulting `Score`
directly rather than round-tripping through `ScoreAnalysis` - the editor
needs every note's exact duration and tie state, which that JSON doesn't
carry.

Only what the editor can represent comes back clean. A tuplet, an
unsupported duration, more than a double sharp/flat, a fifth clef - these
raise `NotationImportError` rather than being approximated, because a
silently-altered upload is worse than an upload the student has to fix in
whatever program wrote it. See `_DURATION_BY_QUARTER_LENGTH` for exactly
what's accepted.
"""

import io
import tempfile
import uuid
import zipfile
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException
from music21 import chord as m21chord
from music21 import clef as m21clef
from music21 import converter
from music21 import key as m21key
from music21 import meter as m21meter
from music21 import note as m21note
from music21 import stream as m21stream
from music21 import tempo as m21tempo
from music21.stream.base import Score

from app.domains.notation.schemas import (
    ClefName,
    DurationName,
    Mode,
    NotationDocument,
    NotationMeasure,
    NotationNote,
    NotationStaff,
    NotationVoice,
    PitchStep,
    TimeSignature,
)

_DEFAULT_SUFFIX = ".musicxml"
_DEFAULT_TEMPO = 90

_MUSICXML_ROOT_TAGS = {"score-partwise", "score-timewise"}
ALLOWED_MUSICXML_EXTENSIONS = {".xml", ".musicxml", ".mxl"}


class NotationImportError(Exception):
    """Raised when a file can't be represented as a notation document."""


def validate_musicxml_upload(filename: str, content: bytes) -> str:
    """Rejects an obviously-wrong upload before any parsing is attempted -
    wrong extension, malformed XML, a `.mxl` that isn't actually a zip.

    Shared by every upload path that accepts a MusicXML file (a composition
    version, a composition-step submission), so the same file is judged the
    same way regardless of where it's uploaded to. Deliberately shallow:
    enough to reject obviously-wrong files without parsing musical content -
    that's `import_musicxml`'s job, not this one's.

    Returns the normalized (lowercased) file extension.
    """
    if not content:
        raise NotationImportError("The uploaded file is empty.")

    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_MUSICXML_EXTENSIONS:
        raise NotationImportError(
            "Unsupported file type. Upload a .musicxml, .xml, or .mxl file."
        )

    if extension == ".mxl":
        buffer = io.BytesIO(content)
        if not zipfile.is_zipfile(buffer):
            raise NotationImportError("The .mxl file is not a valid compressed archive.")
        with zipfile.ZipFile(buffer) as archive:
            if "META-INF/container.xml" not in archive.namelist():
                raise NotationImportError(
                    "The .mxl archive is missing its META-INF/container.xml manifest."
                )
        return extension

    # Parsed with defusedxml, not stdlib ElementTree - this is untrusted
    # user input, and a plain XML parser is vulnerable to entity-expansion
    # ("billion laughs") and external-entity attacks.
    try:
        root = ElementTree.fromstring(content)
    except (ElementTree.ParseError, DefusedXmlException) as exc:
        raise NotationImportError("The file is not well-formed XML.") from exc

    if root.tag not in _MUSICXML_ROOT_TAGS:
        raise NotationImportError(
            "The file's root element is not <score-partwise> or <score-timewise>."
        )
    return extension


def _parse_score(content: bytes, filename: str) -> Score:
    suffix = Path(filename).suffix.lower() or _DEFAULT_SUFFIX
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        parsed = converter.parse(tmp_path)
    except Exception as exc:
        raise NotationImportError(f"music21 could not parse the file: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    if isinstance(parsed, m21stream.Opus):
        if not parsed.scores:
            raise NotationImportError("The file's <opus> contains no scores.")
        parsed = parsed.scores[0]
    if not isinstance(parsed, Score):
        raise NotationImportError("The file did not parse into a music21 Score.")
    return parsed


_CLEF_BY_SIGN_LINE: dict[tuple[str, int], ClefName] = {
    ("G", 2): "treble",
    ("F", 4): "bass",
    ("C", 3): "alto",
    ("C", 4): "tenor",
}


def _clef_name(part: m21stream.Part) -> ClefName:
    found = part.recurse().getElementsByClass(m21clef.Clef).first()
    if found is None:
        return "treble"
    name = _CLEF_BY_SIGN_LINE.get((found.sign or "", found.line or 0))
    if name is None:
        raise NotationImportError(
            f"unsupported clef: {found.sign}{found.line} "
            "(only treble, bass, alto and tenor are supported)"
        )
    return name


def _key_signature(score: Score) -> tuple[int, Mode]:
    found = score.recurse().getElementsByClass(m21key.KeySignature).first()
    if found is None:
        return 0, "major"
    mode: Mode = "minor" if getattr(found, "mode", None) == "minor" else "major"
    return found.sharps, mode


def _time_signature(score: Score) -> TimeSignature:
    found = score.recurse().getElementsByClass(m21meter.TimeSignature).first()
    if found is None:
        return TimeSignature(beats=4, beat_type=4)
    return TimeSignature(beats=found.numerator, beat_type=found.denominator)


def _tempo(score: Score) -> int:
    found = score.recurse().getElementsByClass(m21tempo.MetronomeMark).first()
    if found is None or found.number is None:
        return _DEFAULT_TEMPO
    return round(float(found.number))


_BASE_QUARTER_LENGTH: dict[DurationName, Fraction] = {
    "whole": Fraction(4),
    "half": Fraction(2),
    "quarter": Fraction(1),
    "eighth": Fraction(1, 2),
    "16th": Fraction(1, 4),
    "32nd": Fraction(1, 8),
}


def _build_duration_lookup() -> dict[Fraction, tuple[DurationName, int]]:
    """Every (quarterLength, dots) this editor can represent, inverted.

    The forward mapping - duration name + dots -> length - is
    `constants.ts`'s DURATIONS table on the frontend; this is its inverse,
    built once at import time rather than searched linearly per note.
    """
    lookup: dict[Fraction, tuple[DurationName, int]] = {}
    for name, base in _BASE_QUARTER_LENGTH.items():
        for dots in range(3):
            length = base * (Fraction(2) - Fraction(1, 2**dots))
            lookup[length] = (name, dots)
    return lookup


_DURATION_BY_QUARTER_LENGTH = _build_duration_lookup()


def _duration_and_dots(general_note: m21note.GeneralNote) -> tuple[DurationName, int]:
    if general_note.duration.tuplets:
        raise NotationImportError(
            f"unsupported tuplet at measure {general_note.measureNumber}: "
            "the editor doesn't support tuplets"
        )
    length = Fraction(general_note.duration.quarterLength)
    found = _DURATION_BY_QUARTER_LENGTH.get(length)
    if found is None:
        raise NotationImportError(
            f"unsupported note length ({float(length)} quarter notes) "
            f"at measure {general_note.measureNumber}"
        )
    return found


_STEP_NAMES: frozenset[str] = frozenset({"C", "D", "E", "F", "G", "A", "B"})


def _build_note(general_note: m21note.GeneralNote, tied_to_next: bool) -> NotationNote:
    duration, dots = _duration_and_dots(general_note)

    if isinstance(general_note, m21note.Rest):
        return NotationNote(
            id=str(uuid.uuid4()),
            step="B",
            octave=4,
            alter=0,
            duration=duration,
            dots=dots,
            is_rest=True,
            tied_to_next=False,
        )

    if isinstance(general_note, m21chord.Chord):
        raise NotationImportError(
            f"unsupported chord at measure {general_note.measureNumber}: "
            "the editor writes one pitch per note; use a second voice for a second line"
        )

    if not isinstance(general_note, m21note.Note):
        raise NotationImportError(
            f"unsupported notation element at measure {general_note.measureNumber}"
        )

    step = general_note.pitch.step
    if step not in _STEP_NAMES:
        raise NotationImportError(f"unsupported pitch step: {step}")

    alter = int(general_note.pitch.accidental.alter) if general_note.pitch.accidental else 0
    if not -2 <= alter <= 2:
        raise NotationImportError(f"unsupported accidental ({alter} semitones)")

    return NotationNote(
        id=str(uuid.uuid4()),
        step=cast(PitchStep, step),
        octave=general_note.pitch.octave or 4,
        alter=alter,
        duration=duration,
        dots=dots,
        is_rest=False,
        tied_to_next=tied_to_next,
    )


def _voice_notes(elements: Any) -> list[NotationNote]:
    notes: list[NotationNote] = []
    for element in elements:
        if not isinstance(element, m21note.GeneralNote):
            continue
        tied_to_next = element.tie is not None and element.tie.type in ("start", "continue")
        notes.append(_build_note(element, tied_to_next))
    return notes


def _build_staff(part: m21stream.Part, staff_index: int) -> NotationStaff:
    clef_name = _clef_name(part)
    measures: list[NotationMeasure] = []

    for measure in part.getElementsByClass(m21stream.Measure):
        voices = list(measure.voices)
        if voices:
            built_voices = [
                NotationVoice(
                    id=voice.id or str(index + 1), notes=_voice_notes(voice.notesAndRests)
                )
                for index, voice in enumerate(voices)
            ]
        else:
            built_voices = [
                NotationVoice(id=str(staff_index + 1), notes=_voice_notes(measure.notesAndRests))
            ]
        measures.append(NotationMeasure(id=str(uuid.uuid4()), voices=built_voices))

    return NotationStaff(
        id=str(uuid.uuid4()),
        clef=clef_name,
        name=part.partName or None,
        measures=measures,
    )


def import_musicxml(content: bytes, filename: str) -> NotationDocument:
    """Parses a MusicXML upload into a document the editor can open."""
    score = _parse_score(content, filename)
    if not score.parts:
        raise NotationImportError("The file has no parts to import.")

    fifths, mode = _key_signature(score)
    return NotationDocument(
        fifths=fifths,
        mode=mode,
        time=_time_signature(score),
        tempo=_tempo(score),
        staves=[_build_staff(part, index) for index, part in enumerate(score.parts)],
    )
