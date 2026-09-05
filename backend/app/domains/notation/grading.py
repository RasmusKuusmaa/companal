"""Assembles a submission's deterministic grade: the requirement checklist
plus whatever the analysis engines measured, with no AI involved.

This is the whole of a free-tier grading result, and it's also the
foundation every premium grading builds on - the AI, where it runs, is
handed this bundle as context and never asked to re-derive any of it (see
`ai_grading.py`). Nothing here touches the database or the filesystem; it's
a pure function from a document and its requirements to a verdict, which is
what makes it straightforward to test without either.
"""

from typing import Any

from pydantic import BaseModel

from app.domains.analysis.combined import run_all_analyses
from app.domains.analysis.schemas import (
    EngineUnavailable,
    HarmonyAnalysis,
    MelodyAnalysis,
    RhythmAnalysis,
)
from app.domains.analysis.service import AnalysisError, analyze
from app.domains.notation.builder import to_musicxml_bytes
from app.domains.notation.counterpoint import CounterpointReport, build_counterpoint_report
from app.domains.notation.figured_bass import FiguredBassFindingRead, check_figured_bass
from app.domains.notation.requirements import (
    FiguredBassRequirement,
    Requirement,
    RequirementResult,
    SpeciesCounterpointRequirement,
)
from app.domains.notation.schemas import NotationDocument
from app.domains.notation.validation import RequirementContext, all_passed, run_requirements

_SUBMISSION_FILENAME = "submission.musicxml"


class DeterministicGrade(BaseModel):
    """Everything a submission's grading is built from, before any AI runs.

    `passed` is decided entirely by `requirement_results` - the analysis
    scores ride along for the student to read, but a composition task is
    marked correct or not by whether its stated requirements hold, not by
    a score threshold.
    """

    requirement_results: list[RequirementResult]
    passed: bool
    overall_score: float | None
    melody_analysis: MelodyAnalysis | None
    harmony_analysis: HarmonyAnalysis | None
    rhythm_analysis: RhythmAnalysis | None
    unavailable: list[EngineUnavailable]
    # Set only when `requirements` includes a `SpeciesCounterpointRequirement` -
    # the per-bar findings behind that requirement's flat pass/fail, which
    # is all `requirement_results` itself carries (see `validation.
    # check_species_counterpoint`).
    counterpoint_report: CounterpointReport | None = None
    # Same idea for a `FiguredBassRequirement` - see `validation.
    # check_figured_bass_requirement`.
    figured_bass_findings: list[FiguredBassFindingRead] | None = None


def grade_submission(
    document: NotationDocument, requirements: list[Requirement]
) -> tuple[DeterministicGrade, bytes]:
    """Builds, analyzes and checks one submission.

    Returns the grade alongside the MusicXML it was graded from, since
    every caller that grades a submission also needs to store what was
    graded - see `learning.service.submit_composition`.

    A document that fails to parse into anything the analysis engines can
    read at all (see `AnalysisError`) still produces a grade: every
    requirement simply fails with its own "could not be analyzed" message
    (see `validation.py`'s `None`-context handling), which is a more useful
    result for a student than a 500.
    """
    content = to_musicxml_bytes(document)

    score = analyze(content, _SUBMISSION_FILENAME)
    try:
        bundle = run_all_analyses(content, _SUBMISSION_FILENAME)
        melody, harmony, rhythm = (
            bundle.melody_analysis,
            bundle.harmony_analysis,
            bundle.rhythm_analysis,
        )
        overall_score, unavailable = bundle.overall_score, bundle.unavailable
    except AnalysisError:
        melody = harmony = rhythm = None
        overall_score = None
        unavailable = []

    context = RequirementContext(document=document, score=score, melody=melody, harmony=harmony)
    results = run_requirements(context, requirements)

    counterpoint_report = None
    figured_bass_findings = None
    for requirement in requirements:
        if isinstance(requirement, SpeciesCounterpointRequirement):
            counterpoint_report = build_counterpoint_report(
                document, requirement.species, requirement.cantus_firmus_staff_index
            )
        elif isinstance(requirement, FiguredBassRequirement):
            figured_bass_findings = check_figured_bass(
                document, requirement.bass_staff_index, requirement.figures
            )

    grade = DeterministicGrade(
        requirement_results=results,
        passed=all_passed(results),
        overall_score=overall_score,
        melody_analysis=melody,
        harmony_analysis=harmony,
        rhythm_analysis=rhythm,
        unavailable=unavailable,
        counterpoint_report=counterpoint_report,
        figured_bass_findings=figured_bass_findings,
    )
    return grade, content


def analysis_bundle(grade: DeterministicGrade) -> dict[str, Any]:
    """The subset of a grade the AI prompt is given as context.

    Same shape as `feedback.service._bundle_from_analysis` - both hand the
    model melody/harmony/rhythm plus the overall score and what couldn't be
    analyzed. The requirement checklist isn't part of this; it's threaded
    into the prompt separately (see `ai_prompts.build_user_prompt`) since,
    unlike the analysis, it's ground truth the model must not contradict.
    """
    return {
        "melody_analysis": grade.melody_analysis.model_dump(mode="json")
        if grade.melody_analysis
        else None,
        "harmony_analysis": grade.harmony_analysis.model_dump(mode="json")
        if grade.harmony_analysis
        else None,
        "rhythm_analysis": grade.rhythm_analysis.model_dump(mode="json")
        if grade.rhythm_analysis
        else None,
        "overall_score": grade.overall_score,
        "unavailable": [item.model_dump(mode="json") for item in grade.unavailable],
    }
