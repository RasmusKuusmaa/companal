"""Checks a submission against a composition task's requirements.

Deterministic and free of AI cost - every function here is a fact-check
against what the analysis engines (or the raw document itself) already
measured, run the same way on every submission. This is what a free-tier
student's grading is built from entirely; the AI, where it's available,
only ever adds commentary on top of a checklist this module has already
decided.

Each validator takes a `RequirementContext` - the built score's analysis,
bundled once per submission - rather than re-deriving anything from the
document itself.
"""

from dataclasses import dataclass
from fractions import Fraction

from music21 import key as m21key
from music21 import pitch as m21pitch

from app.domains.analysis.schemas import HarmonyAnalysis, MelodyAnalysis, ScoreAnalysis
from app.domains.notation.requirements import (
    CadenceRequirement,
    DiatonicOnlyRequirement,
    ForbiddenPitchesRequirement,
    KeyRequirement,
    LeapRecoveryRequirement,
    MaxLeapRequirement,
    MeasureCountRequirement,
    RangeRequirement,
    RequiredScaleDegreesRequirement,
    RequirementResult,
    TimeSignatureRequirement,
)
from app.domains.notation.schemas import NotationDocument, NotationVoice, TimeSignature


@dataclass
class RequirementContext:
    """Everything a requirement might need to check itself against.

    `melody`/`harmony` are `None` when the corresponding engine couldn't
    analyze the submission at all (see `CompositionAnalysis.unavailable`
    for when that happens) - a requirement that depends on one reports a
    clear failure rather than raising, since "the engine couldn't read
    this" is itself something the student needs to see.
    """

    document: NotationDocument
    score: ScoreAnalysis
    melody: MelodyAnalysis | None
    harmony: HarmonyAnalysis | None


def check_key(context: RequirementContext, requirement: KeyRequirement) -> RequirementResult:
    actual = (context.score.key or "").strip().lower()
    expected = requirement.key.strip().lower()
    passed = actual == expected

    if not context.score.key:
        message = f"Could not determine a key for this piece; expected {requirement.key}."
    elif passed:
        message = f"Correctly in {context.score.key}."
    else:
        message = f"Written in {context.score.key}, but {requirement.key} was asked for."

    return RequirementResult(requirement=requirement, passed=passed, message=message)


# --------------------------------------------------------------------------- #
# Measure count
# --------------------------------------------------------------------------- #

_BASE_QUARTER_LENGTH: dict[str, Fraction] = {
    "whole": Fraction(4),
    "half": Fraction(2),
    "quarter": Fraction(1),
    "eighth": Fraction(1, 2),
    "16th": Fraction(1, 4),
    "32nd": Fraction(1, 8),
}


def _note_quarters(duration: str, dots: int) -> Fraction:
    return _BASE_QUARTER_LENGTH[duration] * (Fraction(2) - Fraction(1, 2**dots))


def _voice_quarters(voice: NotationVoice) -> Fraction:
    return sum((_note_quarters(n.duration, n.dots) for n in voice.notes), Fraction(0))


def _measure_quarters(time: TimeSignature) -> Fraction:
    return Fraction(time.beats) * Fraction(4, time.beat_type)


def _full_measure_count(document: NotationDocument) -> int:
    """Counts measures, not counting a short first measure as a full one.

    Only the first measure is treated as a possible anacrusis - this covers
    "write an 8-bar melody with a pickup", the shape every exercise in the
    curriculum actually uses, without also trying to infer a shortened
    final measure, which is a convention this editor doesn't otherwise ask
    students to observe.
    """
    if not document.staves:
        return 0
    measures = document.staves[0].measures
    if not measures:
        return 0

    expected = _measure_quarters(document.time)
    first_length = max(
        (_voice_quarters(voice) for voice in measures[0].voices), default=Fraction(0)
    )
    is_anacrusis = 0 < first_length < expected
    return len(measures) - 1 if is_anacrusis else len(measures)


def check_measure_count(
    context: RequirementContext, requirement: MeasureCountRequirement
) -> RequirementResult:
    actual = _full_measure_count(context.document)
    passed = actual == requirement.count

    if passed:
        message = f"Correctly {requirement.count} measures long."
    else:
        message = f"{actual} measures written, but {requirement.count} were asked for."

    return RequirementResult(requirement=requirement, passed=passed, message=message)


# --------------------------------------------------------------------------- #
# Cadence
# --------------------------------------------------------------------------- #

# A requirement's plain-English cadence name to the harmony engine's own
# (type, strength) pair - see harmony.py's `_classify_cadence` for where
# those values come from. `None` for strength means "any strength counts".
_CADENCE_MATCH: dict[str, tuple[str, str | None]] = {
    "perfect_authentic": ("authentic", "perfect-authentic"),
    "imperfect_authentic": ("authentic", "imperfect-authentic"),
    "half": ("half", None),
    "plagal": ("plagal", None),
    "deceptive": ("deceptive", None),
}

_CADENCE_LABEL: dict[str, str] = {
    "perfect_authentic": "a perfect authentic cadence",
    "imperfect_authentic": "an imperfect authentic cadence",
    "half": "a half cadence",
    "plagal": "a plagal cadence",
    "deceptive": "a deceptive cadence",
}


def check_cadence(
    context: RequirementContext, requirement: CadenceRequirement
) -> RequirementResult:
    label = _CADENCE_LABEL[requirement.cadence]

    if context.harmony is None:
        return RequirementResult(
            requirement=requirement,
            passed=False,
            message=f"Harmony could not be analyzed; expected the piece to end with {label}.",
        )

    cadences = context.harmony.technical_data.cadences
    if not cadences:
        return RequirementResult(
            requirement=requirement,
            passed=False,
            message=f"No cadence was found at the end of the piece; expected {label}.",
        )

    final = next((c for c in cadences if c.is_final), cadences[-1])
    expected_type, expected_strength = _CADENCE_MATCH[requirement.cadence]
    passed = final.type == expected_type and (
        expected_strength is None or final.strength == expected_strength
    )

    if passed:
        message = f"Correctly ends with {label}."
    else:
        message = f"Ends with a {final.type} cadence ({final.strength}), not {label}."

    return RequirementResult(
        requirement=requirement, passed=passed, message=message, measure=final.measure
    )


# --------------------------------------------------------------------------- #
# Range and motion
# --------------------------------------------------------------------------- #


def _midi(pitch_name: str) -> int:
    return int(m21pitch.Pitch(pitch_name).midi)


def check_range(context: RequirementContext, requirement: RangeRequirement) -> RequirementResult:
    if context.melody is None:
        return RequirementResult(
            requirement=requirement,
            passed=False,
            message="Melody could not be analyzed, so its range could not be checked.",
        )

    observed = context.melody.technical_data.range
    problems: list[str] = []

    if requirement.max_semitones is not None and observed.semitones > requirement.max_semitones:
        problems.append(
            f"spans {observed.semitones} semitones ({observed.interval_name}), "
            f"more than the {requirement.max_semitones} allowed"
        )
    if requirement.lowest is not None and _midi(observed.lowest) < _midi(requirement.lowest):
        problems.append(f"goes down to {observed.lowest}, below {requirement.lowest}")
    if requirement.highest is not None and _midi(observed.highest) > _midi(requirement.highest):
        problems.append(f"goes up to {observed.highest}, above {requirement.highest}")

    passed = not problems
    message = (
        f"Range is {observed.lowest}-{observed.highest}, within bounds."
        if passed
        else f"Range is {observed.lowest}-{observed.highest}: " + "; ".join(problems) + "."
    )
    return RequirementResult(requirement=requirement, passed=passed, message=message)


def check_max_leap(
    context: RequirementContext, requirement: MaxLeapRequirement
) -> RequirementResult:
    if context.melody is None:
        return RequirementResult(
            requirement=requirement,
            passed=False,
            message="Melody could not be analyzed, so its leaps could not be checked.",
        )

    largest = context.melody.technical_data.leaps.largest_semitones
    passed = largest <= requirement.semitones
    message = (
        f"Largest leap is {largest} semitones, within the {requirement.semitones} allowed."
        if passed
        else f"Largest leap is {largest} semitones, more than the {requirement.semitones} allowed."
    )
    return RequirementResult(requirement=requirement, passed=passed, message=message)


def check_leap_recovery(
    context: RequirementContext, requirement: LeapRecoveryRequirement
) -> RequirementResult:
    """Every large leap should be answered by a step back the other way.

    Reads `leaps.unresolved` straight off the melody engine, which already
    makes this exact judgment per leap - see `_build_leaps` in melody.py.
    """
    if context.melody is None:
        return RequirementResult(
            requirement=requirement,
            passed=False,
            message="Melody could not be analyzed, so its leaps could not be checked.",
        )

    unresolved = context.melody.technical_data.leaps.unresolved
    passed = unresolved <= requirement.max_unresolved
    message = (
        f"{unresolved} unresolved leap(s), within the {requirement.max_unresolved} allowed."
        if passed
        else f"{unresolved} leap(s) not answered by a step in the opposite direction "
        f"(up to {requirement.max_unresolved} allowed)."
    )
    return RequirementResult(requirement=requirement, passed=passed, message=message)


# --------------------------------------------------------------------------- #
# Pitch content
# --------------------------------------------------------------------------- #


def _parse_key(key_str: str) -> m21key.Key:
    """Parses `ScoreAnalysis.key` (e.g. "C major", "c# minor") into a `Key`.

    `key.Key(key_str)` can't take this directly - its constructor treats a
    single string argument as a *pitch* name, and "major"/"minor" isn't
    one. `ScoreAnalysis.key` is always `str(a music21 Key)`, which is
    exactly "<tonic> <mode>", so splitting on the last space recovers the
    two pieces `Key(tonic, mode)` wants.
    """
    tonic, _, mode = key_str.rpartition(" ")
    return m21key.Key(tonic, mode)


def _melody_pitches(score: ScoreAnalysis) -> list[tuple[str, int]]:
    """Every single-pitch note in the score, as (pitch name, measure number).

    Chords are skipped - these three requirements are about a melodic line,
    and a chord's constituent pitches aren't "the melody" in the sense any
    of them mean. For the monophonic exercises these requirements are
    written for, that's every note there is.
    """
    return [
        (note.pitch, measure.number)
        for measure in score.measures
        for note in measure.notes
        if not note.is_rest and not note.is_chord and note.pitch is not None
    ]


def check_diatonic_only(
    context: RequirementContext, requirement: DiatonicOnlyRequirement
) -> RequirementResult:
    if not context.score.key:
        return RequirementResult(
            requirement=requirement,
            passed=False,
            message="Could not determine a key, so diatonicism could not be checked.",
        )

    key_obj = _parse_key(context.score.key)
    chromatic_measures = sorted(
        {
            measure
            for pitch_name, measure in _melody_pitches(context.score)
            if key_obj.getScaleDegreeFromPitch(m21pitch.Pitch(pitch_name)) is None
        }
    )

    passed = not chromatic_measures
    message = (
        f"Every note is diatonic to {context.score.key}."
        if passed
        else f"Chromatic notes outside {context.score.key} in measure(s) "
        + ", ".join(str(m) for m in chromatic_measures)
        + "."
    )
    return RequirementResult(
        requirement=requirement,
        passed=passed,
        message=message,
        measure=chromatic_measures[0] if chromatic_measures else None,
    )


def check_required_scale_degrees(
    context: RequirementContext, requirement: RequiredScaleDegreesRequirement
) -> RequirementResult:
    if not context.score.key:
        return RequirementResult(
            requirement=requirement,
            passed=False,
            message="Could not determine a key, so scale degrees could not be checked.",
        )

    key_obj = _parse_key(context.score.key)
    observed = {
        degree
        for pitch_name, _measure in _melody_pitches(context.score)
        if (degree := key_obj.getScaleDegreeFromPitch(m21pitch.Pitch(pitch_name))) is not None
    }
    missing = sorted(set(requirement.degrees) - observed)

    passed = not missing
    message = (
        f"Uses every required scale degree ({sorted(requirement.degrees)})."
        if passed
        else f"Missing scale degree(s) {missing} of {context.score.key}."
    )
    return RequirementResult(requirement=requirement, passed=passed, message=message)


def check_forbidden_pitches(
    context: RequirementContext, requirement: ForbiddenPitchesRequirement
) -> RequirementResult:
    """Rejects any use of a forbidden pitch class, in any octave or spelling.

    Compared by `pitchClass` (0-11), not by name - F# and Gb are the same
    key on the keyboard and the same thing to forbid, whichever way a
    student happens to spell it.
    """
    forbidden_classes = {m21pitch.Pitch(name).pitchClass for name in requirement.pitches}
    hits = sorted(
        {
            measure
            for pitch_name, measure in _melody_pitches(context.score)
            if m21pitch.Pitch(pitch_name).pitchClass in forbidden_classes
        }
    )

    passed = not hits
    message = (
        f"None of {requirement.pitches} appear."
        if passed
        else f"{requirement.pitches} used in measure(s) " + ", ".join(str(m) for m in hits) + "."
    )
    return RequirementResult(
        requirement=requirement, passed=passed, message=message, measure=hits[0] if hits else None
    )


def check_time_signature(
    context: RequirementContext, requirement: TimeSignatureRequirement
) -> RequirementResult:
    actual = context.score.time_signature
    passed = actual == requirement.value

    if actual is None:
        message = f"No time signature found; expected {requirement.value}."
    elif passed:
        message = f"Correctly in {requirement.value}."
    else:
        message = f"Written in {actual}, but {requirement.value} was asked for."

    return RequirementResult(requirement=requirement, passed=passed, message=message)
