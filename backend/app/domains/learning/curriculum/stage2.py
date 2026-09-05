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
    ],
)
