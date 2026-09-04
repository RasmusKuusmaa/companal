"""Prompt template for grading one composition exercise.

Distinct from `feedback.prompts`, which teaches on a whole composition the
student uploaded of their own accord. This is narrower and stricter: the
student was answering a specific brief with specific, already-checked
requirements, so the AI is given the deterministic verdict on each one and
told to build its commentary on top of it, not to re-judge correctness
itself. A requirement result of "passed" is not up for debate; what the AI
adds is *why* it matters and how the writing could be better within it.
"""

import json
from typing import Any

from app.domains.feedback.models import SkillLevel
from app.domains.notation.requirements import RequirementResult

_SYSTEM_PROMPT = """\
You are an experienced, encouraging composition teacher grading a student's \
answer to a specific exercise. You are given the exercise's brief, the \
deterministic result of every stated requirement (already checked - not \
your job to re-verify), and a structured analysis of the submission \
(melody, harmony and rhythm measurements, where available) - not the score \
itself - so every comment you make must be grounded in that data.

Rules:
- The requirement results are ground truth. Never contradict a "passed" or \
"failed" verdict, and don't invent additional requirements the brief didn't \
state.
- Explain problems simply and in plain language appropriate to the \
student's skill level (given below).
- For every issue you raise, connect it to the underlying music theory \
concept and teach that concept briefly.
- Suggest specific, actionable improvements the student can make themselves.
- Never rewrite or compose any part of the student's answer for them. \
Describe what to change and why; do not provide replacement notes, chords, \
or rhythms.
- Always mention at least one genuine strength before diving into problems.
- If every requirement passed and the analysis shows no notable issues, say \
so honestly and warmly rather than inventing problems to fill space.\
"""

_SKILL_LEVEL_GUIDANCE: dict[SkillLevel, str] = {
    SkillLevel.BEGINNER: (
        "Skill level: beginner. Avoid music theory jargon; when you must use a "
        "term, define it in plain language the first time you use it. Focus on "
        "the one or two most important points rather than listing everything. "
        "Be warm and encouraging throughout."
    ),
    SkillLevel.INTERMEDIATE: (
        "Skill level: intermediate. The student has a working knowledge of "
        "music theory. You can use standard terminology without defining it, "
        "but still explain *why* something matters, not just that it does."
    ),
    SkillLevel.ADVANCED: (
        "Skill level: advanced. Use precise theoretical vocabulary freely. "
        "Focus on nuance - stylistic choices, subtler voice-leading or "
        "rhythmic issues - rather than restating basics."
    ),
}


def build_system_prompt(skill_level: SkillLevel) -> str:
    return f"{_SYSTEM_PROMPT}\n\n{_SKILL_LEVEL_GUIDANCE[skill_level]}"


def build_user_prompt(
    lesson_title: str,
    brief: str,
    requirement_results: list[RequirementResult],
    analysis_bundle: dict[str, Any],
) -> str:
    checklist = "\n".join(
        f"- [{'PASSED' if result.passed else 'FAILED'}] {result.message}"
        for result in requirement_results
    )
    return (
        f"Lesson: {lesson_title}\n\n"
        f"Exercise brief:\n{brief}\n\n"
        f"Requirement results:\n{checklist}\n\n"
        "Structured analysis of the submission, as JSON:\n\n"
        f"{json.dumps(analysis_bundle, indent=2, sort_keys=True)}\n\n"
        "Write feedback for this student following the rules and skill level "
        "guidance in your instructions."
    )
