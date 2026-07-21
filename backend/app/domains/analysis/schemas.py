from pydantic import BaseModel


class NoteRead(BaseModel):
    part_id: str
    measure: int
    offset: float
    duration: float
    is_rest: bool
    is_chord: bool
    # `pitch`/`midi` are set for single-pitch notes; `pitches` is set instead
    # when the note is a written chord (multiple pitches sounding together
    # within one part, e.g. a `<note><chord/>...` group in MusicXML).
    pitch: str | None = None
    midi: int | None = None
    pitches: list[str] | None = None
    tie: str | None = None


class MeasureRead(BaseModel):
    number: int
    notes: list[NoteRead]


class ChordRead(BaseModel):
    """A vertical harmony at a given point in the score, derived across all
    parts (via music21's `chordify`) rather than only notes explicitly
    written as a chord within a single part."""

    measure: int
    offset: float
    duration: float
    pitches: list[str]
    root: str | None
    quality: str | None
    common_name: str | None


class InstrumentRead(BaseModel):
    part_id: str
    name: str | None
    abbreviation: str | None
    midi_program: int | None


class ScoreAnalysis(BaseModel):
    title: str | None
    composer: str | None
    key: str | None
    key_confidence: float | None
    time_signature: str | None
    tempo: float | None
    part_count: int
    measure_count: int
    instruments: list[InstrumentRead]
    measures: list[MeasureRead]
    chords: list[ChordRead]
