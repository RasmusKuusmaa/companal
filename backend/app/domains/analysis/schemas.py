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


# --------------------------------------------------------------------------- #
# Harmony analysis
#
# The vertical counterpart to the melody engine above, and algorithmic in the
# same way: chords come from music21's `chordify`, roman numerals from
# `romanNumeralFromChord`, and parallel motion from music21's
# `VoiceLeadingQuartet` - so every finding points at a specific pair of voices
# moving between two specific chords.
# --------------------------------------------------------------------------- #


class HarmonicChordRead(BaseModel):
    """One sonority in the piece, with its harmonic reading in the key."""

    index: int
    measure: int
    offset: float  # absolute, in quarter notes from the start of the score
    duration: float
    pitches: list[str]
    bass: str
    root: str | None
    quality: str | None  # major / minor / diminished / augmented / other
    common_name: str | None
    inversion: int | None
    # Roman numeral in the prevailing key, e.g. "V7", "i6", "bII". `None` when
    # music21 cannot fit the sonority to a numeral at all.
    roman_numeral: str | None
    scale_degree: int | None  # of the chord root, 1-7
    # tonic / predominant / dominant / chromatic - see `_FUNCTION_BY_DEGREE`.
    function: str
    is_diatonic: bool
    # Set when the chord reads as an applied dominant of the chord that
    # follows it, e.g. "V/V". Detected from root motion, not from music21.
    applied_to: str | None
    is_consonant: bool


class ProgressionStepRead(BaseModel):
    """The move from one harmony to the next."""

    from_index: int
    to_index: int
    measure: int
    from_numeral: str | None
    to_numeral: str | None
    from_function: str
    to_function: str
    # Directed root motion, e.g. "down P5", "up M2", "same".
    root_motion: str
    # functional (T->PD->D->T order), repetition, retrogression (D->PD),
    # or chromatic (either side is non-diatonic).
    kind: str


class HarmonicCadenceRead(BaseModel):
    measure: int
    chord_index: int  # index of the chord the cadence lands on
    from_numeral: str | None
    to_numeral: str | None
    # authentic / half / plagal / deceptive
    type: str
    # perfect-authentic / imperfect-authentic / strong / weak
    strength: str
    is_final: bool


class FunctionalData(BaseModel):
    # How many chords fall into each function (tonic/predominant/dominant/
    # chromatic), and how much of the piece is diatonic to the key.
    function_counts: dict[str, int]
    diatonic_ratio: float
    chromatic_chord_indices: list[int]
    secondary_dominants: list[str]
    # Progressions running against the common-practice T->PD->D->T flow.
    retrogressions: list[ProgressionStepRead]
    # Distinct roman numerals used, and the most frequent harmony.
    distinct_numerals: int
    most_common_numeral: str | None
    tonic_ratio: float


class ParallelMotionRead(BaseModel):
    """Two voices moving from one perfect interval to the same perfect interval.

    Reported for consecutive fifths, octaves and unisons. Antiparallel cases
    count as well - voices moving in *contrary* motion from a fifth to a
    twelfth are forbidden in strict style for the same reason - so
    `from_interval` and `to_interval` are not always equal.

    Hidden (direct) fifths and octaves are listed separately: approaching a
    perfect interval by similar motion is only conventionally a fault between
    the outer voices, and only when the upper voice arrives by leap.
    """

    kind: str  # fifth / octave / unison / hidden-fifth / hidden-octave
    upper_voice: str
    lower_voice: str
    from_index: int
    to_index: int
    measure: int
    upper_motion: str  # e.g. "G4->A4"
    lower_motion: str  # e.g. "C3->D3"
    from_interval: str  # harmonic interval before the move, e.g. "P5"
    to_interval: str
    involves_outer_voices: bool


class VoiceMotionRead(BaseModel):
    upper_voice: str
    lower_voice: str
    from_index: int
    to_index: int
    measure: int
    motion: str  # parallel / similar / contrary / oblique / none


class VoiceLeapRead(BaseModel):
    voice: str
    from_index: int
    to_index: int
    measure: int
    motion: str
    semitones: int
    interval_name: str


class VoiceCrossingRead(BaseModel):
    upper_voice: str
    lower_voice: str
    chord_index: int
    measure: int
    upper_pitch: str
    lower_pitch: str


class VoiceLeadingData(BaseModel):
    # "parts" when each part of the score is a real monophonic voice (SATB,
    # a string quartet); "vertical-positions" when voices had to be inferred
    # by position within each sonority because at least one part carries
    # written chords. Parallel findings are only as reliable as this.
    voice_source: str
    voice_count: int
    voice_ids: list[str]
    transitions: int
    motion_counts: dict[str, int]
    average_motion_semitones: float
    # Share of transitions where no voice moves by more than a step.
    smooth_ratio: float
    parallel_fifths: list[ParallelMotionRead]
    parallel_octaves: list[ParallelMotionRead]
    parallel_unisons: list[ParallelMotionRead]
    hidden_parallels: list[ParallelMotionRead]
    large_leaps: list[VoiceLeapRead]
    voice_crossings: list[VoiceCrossingRead]


class DissonanceRead(BaseModel):
    """A dissonant tone and what became of it."""

    # chordal-seventh / leading-tone / tritone / final-chord
    kind: str
    chord_index: int
    measure: int
    voice: str | None
    pitch: str
    # What common-practice treatment expects, and what the voice actually did.
    expected: str
    actual: str
    resolved: bool


class DissonanceData(BaseModel):
    dissonant_chord_count: int
    dissonance_ratio: float
    seventh_count: int
    unresolved: list[DissonanceRead]
    resolved_count: int
    # True when the piece's last chord is itself dissonant.
    ends_dissonant: bool


class HarmonyTechnicalData(BaseModel):
    key: str | None
    key_confidence: float | None
    mode: str | None
    chord_count: int
    measure_count: int
    chords: list[HarmonicChordRead]
    progression: list[ProgressionStepRead]
    functional: FunctionalData
    cadences: list[HarmonicCadenceRead]
    voice_leading: VoiceLeadingData
    dissonances: DissonanceData


class HarmonyAnalysis(BaseModel):
    score: float
    strengths: list[str]
    issues: list[str]
    technical_data: HarmonyTechnicalData
