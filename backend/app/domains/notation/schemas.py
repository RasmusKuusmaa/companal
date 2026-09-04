"""The notation document: the editor's own score format.

A Pydantic mirror of `frontend/src/features/notation/types.ts` - field for
field, the same shape, so a document round-trips this boundary without a
translation layer on either side. Keep the two in sync by hand; there's no
codegen between them, and this file existing at all is what lets the
backend (`builder.py`, `requirements.py`) reason about a score without ever
touching MusicXML except at the edges.

Why this shape and not "just store MusicXML": MusicXML is the interchange
format for everything *outside* the editor - grading, storage, upload - but
the editor itself needs measures that can be half-full mid-edit, notes
addressed by id for selection, and a click resolved to an exact diatonic
position. None of that is what MusicXML is for. See `builder.py` for the
one place this document becomes MusicXML, and `importer.py` for the other
direction.
"""

from typing import Literal

from pydantic import BaseModel, Field

PitchStep = Literal["C", "D", "E", "F", "G", "A", "B"]
ClefName = Literal["treble", "bass", "alto", "tenor"]
DurationName = Literal["whole", "half", "quarter", "eighth", "16th", "32nd"]
Mode = Literal["major", "minor"]


class NotationNote(BaseModel):
    id: str
    step: PitchStep
    octave: int
    # Semitone offset from the natural: -2 (double flat) to 2 (double sharp).
    alter: int = Field(ge=-2, le=2)
    duration: DurationName
    dots: int = Field(ge=0, le=2)
    is_rest: bool
    tied_to_next: bool


class NotationVoice(BaseModel):
    id: str
    notes: list[NotationNote] = Field(default_factory=list)


class NotationMeasure(BaseModel):
    id: str
    voices: list[NotationVoice] = Field(default_factory=list)


class NotationStaff(BaseModel):
    id: str
    clef: ClefName
    name: str | None = None
    measures: list[NotationMeasure] = Field(default_factory=list)


class TimeSignature(BaseModel):
    beats: int = Field(gt=0)
    beat_type: int = Field(gt=0)


class NotationDocument(BaseModel):
    # Sharps (positive) or flats (negative) on the staff - see
    # `KEY_SIGNATURES` in builder.py for how this and `mode` become a tonic.
    fifths: int = Field(ge=-7, le=7)
    mode: Mode
    time: TimeSignature
    tempo: int = Field(gt=0)
    staves: list[NotationStaff] = Field(default_factory=list)
