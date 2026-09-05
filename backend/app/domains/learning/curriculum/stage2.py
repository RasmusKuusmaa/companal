"""Stage 2 - Voice leading: four-part writing, motion, and non-chord tones."""

from app.domains.learning.curriculum.definitions import CourseDef, LessonDef, StepDef

COURSE = CourseDef(
    slug="voice-leading",
    title="Voice Leading",
    description=(
        "Writing in four real voices: ranges and spacing, the parallel prohibitions, "
        "connecting chords smoothly, and the non-chord tones that decorate a line."
    ),
    level="intermediate",
    lessons=[
        LessonDef(
            slug="four-part-texture-ranges-spacing-doubling",
            title="Four-Part Texture: Ranges, Spacing and Doubling",
            summary="Keeping SATB writing within range, properly spaced, and sensibly doubled.",
            estimated_minutes=12,
            steps=[
                StepDef(
                    slug="four-part-texture-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Four-part texture: ranges, spacing and doubling\n\n"
                            "Writing for four voices - soprano, alto, tenor, bass (SATB) - "
                            "means respecting three things at once.\n\n"
                            "## Ranges\n\n"
                            "Each voice has a comfortable range: soprano C4-A5, alto "
                            "F3-D5, tenor C3-G4, bass E2-C4. Writing outside these isn't "
                            "wrong in principle, but it's the first thing a real "
                            "choir would push back on.\n\n"
                            "## Spacing\n\n"
                            "Keep no more than an octave between soprano and alto, and no "
                            "more than an octave between alto and tenor - those pairs sit "
                            "close together in the texture. The gap between tenor and "
                            "bass can be wider, since the bass often needs room to leap "
                            "to its own chord roots.\n\n"
                            "## Doubling\n\n"
                            "A four-voice triad has to repeat one of its three notes. In "
                            "root position, **double the root** by default - it's the "
                            "most stable choice. Avoid doubling the leading tone (it wants "
                            "to resolve up, and two voices pulling the same direction get "
                            "in each other's way) and avoid doubling a chordal seventh "
                            "(it wants to resolve down, for the same reason)."
                        )
                    },
                    topics=["four-part-texture"],
                ),
                StepDef(
                    slug="four-part-texture-quiz-spacing",
                    kind="quiz",
                    payload={
                        "question": (
                            "Which pairs of adjacent voices should stay within an octave "
                            "of each other?"
                        ),
                        "choices": [
                            "Soprano-alto and alto-tenor",
                            "Tenor-bass only",
                            "Soprano-bass only",
                            "There is no spacing guideline between any voices",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "Soprano-alto and alto-tenor should each stay within an "
                            "octave; tenor-bass is allowed to open up wider."
                        ),
                    },
                    topics=["four-part-texture"],
                ),
                StepDef(
                    slug="four-part-texture-quiz-doubling",
                    kind="quiz",
                    payload={
                        "question": "In a root-position triad, which note is usually doubled?",
                        "choices": ["The root", "The third", "The fifth", "The seventh"],
                        "answer_index": 0,
                        "explanation": (
                            "The root is the default doubling choice in root position - "
                            "it's the most stable note and doesn't create a resolution "
                            "conflict the way doubling the leading tone or a seventh would."
                        ),
                    },
                    topics=["four-part-texture"],
                ),
            ],
        ),
        LessonDef(
            slug="types-of-motion-and-the-parallel-prohibitions",
            title="Types of Motion and the Parallel Prohibitions",
            summary="Parallel, similar, oblique and contrary motion, and why some are forbidden.",
            estimated_minutes=14,
            steps=[
                StepDef(
                    slug="motion-types-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Types of motion and the parallel prohibitions\n\n"
                            "Between any two voices, one chord to the next, there are "
                            "four possible kinds of motion:\n\n"
                            "- **Parallel**: both voices move in the same direction by "
                            "the same interval.\n"
                            "- **Similar**: both voices move in the same direction, but "
                            "by different intervals.\n"
                            "- **Oblique**: one voice holds its note while the other "
                            "moves.\n"
                            "- **Contrary**: the voices move in opposite directions.\n\n"
                            "## The parallel prohibitions\n\n"
                            "Parallel motion into or through a **perfect fifth** or a "
                            "**perfect octave** (or unison) between the same two voices "
                            "is forbidden. When two voices stay a perfect fifth or octave "
                            "apart while moving together, they briefly stop sounding like "
                            "two independent lines and start sounding like one line "
                            "doubled - exactly the opposite of what four-part texture is "
                            "for. This is the single most consistently enforced rule in "
                            "traditional voice leading, checked between every pair of "
                            "voices, though it matters most between the outer voices "
                            "(soprano and bass), which the ear tracks most closely."
                        )
                    },
                    topics=["motion-types-and-parallels"],
                ),
                StepDef(
                    slug="motion-types-quiz-parallel",
                    kind="quiz",
                    payload={
                        "question": (
                            "Which type of motion has both voices moving in the same "
                            "direction by the same interval?"
                        ),
                        "choices": ["Parallel", "Similar", "Oblique", "Contrary"],
                        "answer_index": 0,
                        "explanation": (
                            "Parallel motion means both voices move the same direction "
                            "by the same interval - similar motion allows different "
                            "intervals in that same direction."
                        ),
                    },
                    topics=["motion-types-and-parallels"],
                ),
                StepDef(
                    slug="motion-types-quiz-why-forbidden",
                    kind="quiz",
                    payload={
                        "question": (
                            "Why are parallel fifths and octaves avoided in traditional "
                            "four-part writing?"
                        ),
                        "choices": [
                            "They make two independent voices briefly sound like one",
                            "They are physically impossible to sing in tune",
                            "They always sound out of tune regardless of context",
                            "They are only a problem at fast tempos",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The whole point of four real voices is independence - "
                            "parallel perfect intervals momentarily erase that "
                            "independence by making two voices move as one."
                        ),
                    },
                    topics=["motion-types-and-parallels", "parallel-fifths-and-octaves"],
                ),
                StepDef(
                    slug="motion-types-task",
                    kind="composition",
                    payload={
                        "brief": (
                            "The bass line below is given and locked (I - IV - I, all "
                            "root position). Add upper voices that realize each chord "
                            "without any parallel fifths or octaves between the voices."
                        ),
                        "requirements": [
                            {
                                "type": "figured_bass",
                                "bass_staff_index": 0,
                                "figures": ["", "", ""],
                            }
                        ],
                        "starter_notation": {
                            "fifths": 0,
                            "mode": "major",
                            "time": {"beats": 4, "beat_type": 4},
                            "tempo": 90,
                            "staves": [
                                {
                                    "id": "bass",
                                    "clef": "bass",
                                    "measures": [
                                        {
                                            "id": f"m{i}",
                                            "voices": [
                                                {
                                                    "id": "bass-voice",
                                                    "notes": [
                                                        {
                                                            "id": f"b{i}",
                                                            "step": step,
                                                            "octave": 3,
                                                            "alter": 0,
                                                            "duration": "whole",
                                                            "dots": 0,
                                                            "is_rest": False,
                                                            "tied_to_next": False,
                                                        }
                                                    ],
                                                }
                                            ],
                                        }
                                        for i, step in enumerate(["C", "F", "C"])
                                    ],
                                },
                                {
                                    "id": "upper",
                                    "clef": "treble",
                                    "measures": [
                                        {
                                            "id": f"m{i}",
                                            "voices": [
                                                {
                                                    "id": "v1",
                                                    "notes": [
                                                        {
                                                            "id": f"u1-{i}",
                                                            "step": "C",
                                                            "octave": 4,
                                                            "alter": 0,
                                                            "duration": "whole",
                                                            "dots": 0,
                                                            "is_rest": True,
                                                            "tied_to_next": False,
                                                        }
                                                    ],
                                                },
                                                {
                                                    "id": "v2",
                                                    "notes": [
                                                        {
                                                            "id": f"u2-{i}",
                                                            "step": "C",
                                                            "octave": 4,
                                                            "alter": 0,
                                                            "duration": "whole",
                                                            "dots": 0,
                                                            "is_rest": True,
                                                            "tied_to_next": False,
                                                        }
                                                    ],
                                                },
                                            ],
                                        }
                                        for i in range(3)
                                    ],
                                },
                            ],
                        },
                        "locked_staff_indices": [0],
                    },
                    topics=["motion-types-and-parallels", "parallel-fifths-and-octaves"],
                ),
            ],
        ),
    ],
)
