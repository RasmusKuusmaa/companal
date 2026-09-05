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


# --------------------------------------------------------------------------- #
# SATB voicing checks
#
# Only meaningful for a genuine four-real-voice texture - see
# `voicing.py`'s module docstring for why the positional voice-grid
# fallback is excluded from all of these.
# --------------------------------------------------------------------------- #


class VoiceRangeViolationRead(BaseModel):
    """One voice sounding outside its conventional tessitura."""

    voice: str  # soprano / alto / tenor / bass
    chord_index: int
    measure: int
    pitch: str
    expected_low: str
    expected_high: str


class VoiceSpacingViolationRead(BaseModel):
    """More than an octave between a pair of adjacent upper voices.

    Soprano-alto and alto-tenor only - a wide tenor-bass gap is normal
    voicing, not a fault (see `voicing.check_spacing`).
    """

    upper_voice: str
    lower_voice: str
    chord_index: int
    measure: int
    upper_pitch: str
    lower_pitch: str
    interval_semitones: int


class VoiceDoublingViolationRead(BaseModel):
    """A doubling or missing chord-tone fault in one SATB sonority.

    `kind` is one of `doubled_leading_tone`, `doubled_seventh` or
    `missing_third` (see `voicing.check_doubling`). `pitches` is the full
    voicing, soprano to bass, for context in the message.
    """

    kind: str
    chord_index: int
    measure: int
    pitches: list[str]


# --------------------------------------------------------------------------- #
# Rhythm analysis
#
# The temporal counterpart to the melody and harmony engines, and algorithmic
# in the same way: durations, beat positions and metric accent weights all
# come from music21, and everything else is counting against them. Unlike the
# other two engines this one reads *every* part - rhythm is a property of the
# whole texture - and reports a per-part breakdown alongside the totals.
# --------------------------------------------------------------------------- #


class DurationCountRead(BaseModel):
    name: str  # music21's full name, e.g. "Dotted Quarter", "Eighth Triplet"
    quarter_length: float
    count: int
    ratio: float


class DurationVarietyData(BaseModel):
    distinct_durations: int
    by_duration: list[DurationCountRead]
    shortest: float
    longest: float
    # longest / shortest - how wide a span of note values the piece uses.
    range_ratio: float
    most_common: str | None
    most_common_ratio: float
    # Normalised Shannon entropy of the duration distribution: 0.0 when every
    # note is the same length, 1.0 when all *observed* durations are equally
    # frequent. It measures evenness, so read it with `distinct_durations` -
    # a piece alternating two values scores 1.0 here too.
    variety_index: float
    dotted_count: int
    tuplet_count: int
    tied_count: int


class MeasureDensityRead(BaseModel):
    measure: int
    onsets: int  # distinct attack points across all parts
    notes: int
    # Share of the bar with at least one part sounding.
    sounding_ratio: float


class RhythmicDensityData(BaseModel):
    note_count: int
    rest_count: int
    # Distinct attack points in time. Lower than `note_count` whenever parts
    # articulate together, which is what separates a chorale from a fugue.
    onset_count: int
    notes_per_measure: float
    onsets_per_measure: float
    notes_per_quarter: float
    rest_ratio: float
    busiest_measure: int | None
    quietest_measure: int | None
    per_measure: list[MeasureDensityRead]


class RhythmicPatternRead(BaseModel):
    # The cell as note values, e.g. ["Quarter", "Eighth", "Eighth"].
    pattern: list[str]
    quarter_lengths: list[float]
    length_notes: int
    occurrences: int
    measures: list[int]
    part_id: str


class RhythmicRepetitionData(BaseModel):
    repeated_patterns: list[RhythmicPatternRead]
    # Measures sharing an identical attack pattern across the whole texture.
    distinct_measure_rhythms: int
    repeated_measure_count: int
    measure_repetition_ratio: float
    # An ostinato is a cell restated back-to-back rather than merely recurring.
    has_ostinato: bool
    ostinato_pattern: list[str] | None
    ostinato_occurrences: int


class SyncopationRead(BaseModel):
    part_id: str
    measure: int
    beat: float
    pitch: str | None
    duration: float
    # sustained-over-beat / tied-over-barline / offbeat-attack
    kind: str
    onset_strength: float
    crossed_strength: float | None
    description: str


class SyncopationData(BaseModel):
    syncopated_note_count: int
    syncopation_ratio: float
    offbeat_onset_count: int
    offbeat_ratio: float
    tied_over_barline: int
    # Measures where no part attacks the downbeat at all.
    silent_downbeats: int
    by_kind: dict[str, int]
    instances: list[SyncopationRead]


class PhraseRead(BaseModel):
    index: int
    start_measure: int
    end_measure: int
    start_offset: float
    length_quarters: float
    length_measures: float
    note_count: int
    # Length of the silence that closed the phrase, in quarter notes.
    following_rest_quarters: float


class PhraseRhythmData(BaseModel):
    phrase_count: int
    phrases: list[PhraseRead]
    average_length_quarters: float
    most_common_length_measures: float | None
    # True when every phrase spans the same number of bars.
    is_regular: bool
    distinct_lengths: int
    has_anacrusis: bool
    anacrusis_quarters: float


class RhythmPartRead(BaseModel):
    part_id: str
    name: str | None
    note_count: int
    notes_per_measure: float
    rest_ratio: float
    syncopated_count: int
    distinct_durations: int
    shortest: float
    longest: float


class RhythmTechnicalData(BaseModel):
    time_signatures: list[str]
    tempo: float | None
    measure_count: int
    total_quarters: float
    part_count: int
    density: RhythmicDensityData
    repetition: RhythmicRepetitionData
    syncopation: SyncopationData
    durations: DurationVarietyData
    phrases: PhraseRhythmData
    parts: list[RhythmPartRead]


class RhythmAnalysis(BaseModel):
    score: float
    strengths: list[str]
    issues: list[str]
    technical_data: RhythmTechnicalData


# --------------------------------------------------------------------------- #
# Combined analysis
#
# All three engines over one score. Each is independent, and a score that
# defeats one need not defeat the others - a single melodic line has no
# harmony to read, a percussion part has no pitch - so an engine that cannot
# run reports why instead of failing the whole bundle.
# --------------------------------------------------------------------------- #


class EngineUnavailable(BaseModel):
    engine: str  # melody / harmony / rhythm
    reason: str


class AnalysisBundle(BaseModel):
    melody_analysis: MelodyAnalysis | None
    harmony_analysis: HarmonyAnalysis | None
    rhythm_analysis: RhythmAnalysis | None
    # Unweighted mean of the engines that ran, 0-100. Engines that could not
    # run are left out rather than counted as zero: a monophonic piece should
    # not be marked down for having no harmony to analyze.
    overall_score: float
    unavailable: list[EngineUnavailable]
