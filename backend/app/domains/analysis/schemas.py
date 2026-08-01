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


# --------------------------------------------------------------------------- #
# Melody analysis
#
# A purely algorithmic (non-AI) evaluation of a single melodic line, built on
# music21 measurements. Everything below describes the melody the engine
# actually scored - the top sounding line of the chosen part - so the caller
# can see the raw numbers behind the score, not just the verdict.
# --------------------------------------------------------------------------- #


class MelodicIntervalRead(BaseModel):
    """One step from a melody note to the next sounding note."""

    from_pitch: str
    to_pitch: str
    # Directed diatonic name, e.g. "M2" up a major second, "-P5" down a fifth.
    name: str
    semitones: int
    is_step: bool
    is_leap: bool


class IntervalData(BaseModel):
    count: int
    average_semitones: float  # mean absolute leap/step size
    largest_semitones: int
    # Histogram keyed by directed interval name (e.g. {"M2": 5, "-m3": 2}).
    by_name: dict[str, int]
    sequence: list[MelodicIntervalRead]


class RangeData(BaseModel):
    lowest: str
    highest: str
    semitones: int
    interval_name: str


class ContourData(BaseModel):
    # Parsons code: '*' for the first note, then 'u'/'d'/'r' per move.
    parsons: str
    direction_changes: int
    ascending_moves: int
    descending_moves: int
    repeated_moves: int
    shape: str


class RepeatedSequenceRead(BaseModel):
    pitches: list[str]
    occurrences: int


class RepetitionData(BaseModel):
    immediate_repeats: int
    repeated_note_ratio: float
    most_common_pitch: str | None
    most_common_pitch_count: int
    repeated_sequences: list[RepeatedSequenceRead]
    has_repeated_phrases: bool


class MotifRead(BaseModel):
    # The motif as a directed-interval pattern, so transposed restatements of
    # the same shape are recognised as the same motif.
    intervals: list[str]
    length_notes: int
    occurrences: int


class LeapData(BaseModel):
    count: int
    ratio: float
    largest_semitones: int
    largest_name: str | None
    # Leaps not resolved by a step in the opposite direction (a classic
    # voice-leading weakness), and the longest run of back-to-back leaps.
    unresolved: int
    consecutive_leaps_max: int


class StepwiseData(BaseModel):
    count: int
    ratio: float
    longest_run: int


class CadenceRead(BaseModel):
    measure: int
    final_pitch: str
    scale_degree: int | None
    approach: str
    type: str
    on_tonic: bool


class MelodyTechnicalData(BaseModel):
    part_id: str
    key: str | None
    note_count: int
    intervals: IntervalData
    range: RangeData
    contour: ContourData
    repetition: RepetitionData
    motifs: list[MotifRead]
    leaps: LeapData
    stepwise: StepwiseData
    cadences: list[CadenceRead]


class MelodyAnalysis(BaseModel):
    score: float
    strengths: list[str]
    issues: list[str]
    technical_data: MelodyTechnicalData
