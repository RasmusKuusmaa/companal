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

from app.domains.analysis.schemas import HarmonyAnalysis, MelodyAnalysis, ScoreAnalysis
from app.domains.notation.requirements import (
    KeyRequirement,
    RequirementResult,
    TimeSignatureRequirement,
)
from app.domains.notation.schemas import NotationDocument


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
