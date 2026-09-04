"""Assembles a submission's deterministic grade: the requirement checklist
plus whatever the analysis engines measured, with no AI involved.

This is the whole of a free-tier grading result, and it's also the
foundation every premium grading builds on - the AI, where it runs, is
handed this bundle as context and never asked to re-derive any of it (see
`ai_grading.py`). Nothing here touches the database or the filesystem; it's
a pure function from a document and its requirements to a verdict, which is
what makes it straightforward to test without either.
"""

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
from app.domains.notation.requirements import Requirement, RequirementResult
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

    grade = DeterministicGrade(
        requirement_results=results,
        passed=all_passed(results),
        overall_score=overall_score,
        melody_analysis=melody,
        harmony_analysis=harmony,
        rhythm_analysis=rhythm,
        unavailable=unavailable,
    )
    return grade, content
