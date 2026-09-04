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

from app.domains.analysis.schemas import HarmonyAnalysis, MelodyAnalysis, ScoreAnalysis
from app.domains.notation.requirements import (
    CadenceRequirement,
    KeyRequirement,
    MeasureCountRequirement,
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
