"""MusicXML -> structured JSON, via music21.

music21 only reliably parses from a file path (its `parseData` helper takes
raw text and can't unzip a compressed `.mxl`), so uploaded bytes are spooled
to a temp file matching the original extension and parsed from there; the
temp file is removed immediately whether parsing succeeded or not.

Chords are derived with `Score.chordify()` rather than by reading only notes
explicitly written as a chord within one part. Most multi-instrument scores
never use MusicXML's `<chord/>` tag at all - each simultaneous pitch is a
separate note in a separate part - so `chordify()` (which collapses every
part's simultaneous notes into vertical chord objects) is what actually
finds the piece's harmony.
"""

import tempfile
from pathlib import Path
from typing import Any

from music21 import chord as m21chord
from music21 import converter, meter, stream
from music21 import key as m21key
from music21 import tempo as m21tempo
from music21.stream.base import Score

from app.domains.analysis.schemas import (
    ChordRead,
    InstrumentRead,
    MeasureRead,
    NoteRead,
    ScoreAnalysis,
)

_DEFAULT_SUFFIX = ".musicxml"


class AnalysisError(Exception):
    """Raised when music21 cannot parse or analyze the supplied score."""


def _parse_score(content: bytes, filename: str) -> Score:
    suffix = Path(filename).suffix.lower() or _DEFAULT_SUFFIX
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        # music21 raises a variety of exception types across its parser
        # chain (bare xml.etree.ElementTree.ParseError for malformed XML,
        # music21.musicxml.xmlObjects.MusicXMLImportException for the wrong
        # root element, etc.) - catching broadly at this boundary and
        # re-raising as one domain error is simpler than enumerating them.
        parsed = converter.parse(tmp_path)
    except Exception as exc:
        raise AnalysisError(f"music21 could not parse the score: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    if isinstance(parsed, stream.Opus):
        # A file containing multiple scores - analyze the first.
        if not parsed.scores:
            raise AnalysisError("The file's <opus> contains no scores.")
        parsed = parsed.scores[0]
    if not isinstance(parsed, Score):
        raise AnalysisError("The file did not parse into a music21 Score.")
    return parsed


def _extract_key(score: Score) -> tuple[str | None, float | None]:
    # An explicit <key> with a <mode> (e.g. fifths=0, mode=major) parses to
    # a music21.key.Key, which is fully determined by the score itself - no
    # need to fall back to statistical estimation.
    explicit = score.recurse().getElementsByClass(m21key.Key).first()
    if explicit is not None:
        return str(explicit), 1.0

    try:
        # Raises DiscreteAnalysisException on a score with no pitched
        # content at all (e.g. rests-only) - nothing to estimate a key
        # from, which isn't a parse failure.
        analyzed = score.analyze("key")
    except Exception:
        return None, None
    if analyzed is None:
        return None, None
    return str(analyzed), getattr(analyzed, "correlationCoefficient", None)


def _extract_time_signature(score: Score) -> str | None:
    time_signature = score.recurse().getElementsByClass(meter.TimeSignature).first()
    return time_signature.ratioString if time_signature is not None else None


def _extract_tempo(score: Score) -> float | None:
    mark = score.recurse().getElementsByClass(m21tempo.MetronomeMark).first()
    if mark is None or mark.number is None:
        return None
    return float(mark.number)


def _instrument_part_id(part: Any, instrument: Any) -> str:
    # music21's MusicXML importer sets `Part.id` to the human-readable part
    # name (e.g. "Violin") when one is available, and keeps the original
    # <score-part id="..."> (e.g. "P2") on the resolved Instrument instead -
    # so the stable identifier lives on `instrument.partId`, not `part.id`.
    return str(instrument.partId) if instrument is not None and instrument.partId else str(part.id)


def _extract_instruments(score: Score) -> list[InstrumentRead]:
    instruments = []
    for part in score.parts:
        instrument = part.getInstrument(returnDefault=True)
        instruments.append(
            InstrumentRead(
                part_id=_instrument_part_id(part, instrument),
                name=part.partName or (instrument.instrumentName if instrument else None),
                abbreviation=part.partAbbreviation,
                midi_program=instrument.midiProgram if instrument else None,
            )
        )
    return instruments


def _describe_note(note_obj: Any, part_id: str) -> NoteRead:
    is_chord = bool(note_obj.isChord)
    is_rest = bool(note_obj.isRest)
    pitch = None
    midi = None
    pitches = None
    if is_chord:
        pitches = [p.nameWithOctave for p in note_obj.pitches]
    elif not is_rest:
        pitch = note_obj.pitch.nameWithOctave
        midi = note_obj.pitch.midi
    tie = note_obj.tie.type if note_obj.tie is not None else None
    return NoteRead(
        part_id=part_id,
        measure=note_obj.measureNumber or 0,
        offset=float(note_obj.offset),
        duration=float(note_obj.quarterLength),
        is_rest=is_rest,
        is_chord=is_chord,
        pitch=pitch,
        midi=midi,
        pitches=pitches,
        tie=tie,
    )


def _extract_measures(score: Score) -> list[MeasureRead]:
    # Aggregated across all parts by measure number, rather than kept as one
    # list per part, so the response has a single flat `measures` list (each
    # note tagged with `part_id`) instead of one nested per instrument.
    notes_by_measure: dict[int, list[NoteRead]] = {}
    for part in score.parts:
        instrument = part.getInstrument(returnDefault=True)
        part_id = _instrument_part_id(part, instrument)
        for measure in part.getElementsByClass(stream.Measure):
            bucket = notes_by_measure.setdefault(measure.number, [])
            for note_obj in measure.notesAndRests:
                bucket.append(_describe_note(note_obj, part_id))

    return [
        MeasureRead(number=number, notes=notes_by_measure[number])
        for number in sorted(notes_by_measure)
    ]


def _describe_chord(chord_obj: Any) -> ChordRead:
    try:
        root = chord_obj.root().nameWithOctave
    except Exception:
        root = None
    try:
        quality = chord_obj.quality
    except Exception:
        quality = None
    try:
        common_name = chord_obj.pitchedCommonName
    except Exception:
        common_name = None
    return ChordRead(
        measure=chord_obj.measureNumber or 0,
        offset=float(chord_obj.offset),
        duration=float(chord_obj.quarterLength),
        pitches=[p.nameWithOctave for p in chord_obj.pitches],
        root=root,
        quality=quality,
        common_name=common_name,
    )


def _extract_chords(score: Score) -> list[ChordRead]:
    chordified = score.chordify()
    return [
        _describe_chord(chord_obj)
        for chord_obj in chordified.recurse().getElementsByClass(m21chord.Chord)
        # A single sounding pitch (every other part resting) isn't a chord.
        if len(chord_obj.pitches) >= 2
    ]


def analyze(content: bytes, filename: str) -> ScoreAnalysis:
    """Parses MusicXML bytes and returns the full structured analysis.

    Raises `AnalysisError` if music21 cannot parse `content` at all. Music
    that parses but is missing some piece of metadata (no tempo mark, no
    explicit key, ...) is not an error - the corresponding field is simply
    `None`.
    """
    score = _parse_score(content, filename)

    key_name, key_confidence = _extract_key(score)
    measures = _extract_measures(score)

    return ScoreAnalysis(
        title=score.metadata.title if score.metadata else None,
        composer=score.metadata.composer if score.metadata else None,
        key=key_name,
        key_confidence=key_confidence,
        time_signature=_extract_time_signature(score),
        tempo=_extract_tempo(score),
        part_count=len(score.parts),
        measure_count=len(measures),
        instruments=_extract_instruments(score),
        measures=measures,
        chords=_extract_chords(score),
    )
