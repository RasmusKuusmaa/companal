"""Stage 3 - Line and counterpoint: melody, phrase, cadence, and species."""

from app.domains.learning.curriculum.definitions import CourseDef, LessonDef, StepDef

COURSE = CourseDef(
    slug="line-and-counterpoint",
    title="Line and Counterpoint",
    description=(
        "Writing a convincing melodic line on its own terms: phrase structure, cadence "
        "strength, and the four species of strict counterpoint against a cantus firmus."
    ),
    level="intermediate",
    lessons=[
        LessonDef(
            slug="melodic-construction-and-tendency-tones",
            title="Melodic Construction and Tendency Tones",
            summary="What makes a line singable, and which scale degrees pull toward resolution.",
            estimated_minutes=15,
            steps=[
                StepDef(
                    slug="melodic-construction-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Melodic construction and tendency tones\n\n"
                            "A convincing melodic line follows a handful of habits more "
                            "than any strict rule:\n\n"
                            "- Move mostly **by step**; save leaps for moments that "
                            "should stand out.\n"
                            "- **Recover a leap** of a fourth or larger with a step in "
                            "the opposite direction - a big jump followed by another "
                            "leap the same way tends to feel like it's running away.\n"
                            "- Aim for a single clear **melodic climax** - one high (or "
                            "low) point the line builds toward, rather than several "
                            "competing peaks.\n"
                            "- Avoid immediate repetition; a melody that keeps "
                            "revisiting the same note or shape stalls.\n\n"
                            "## Tendency tones\n\n"
                            "Certain scale degrees pull toward a specific resolution "
                            "regardless of the harmony underneath them. The strongest is "
                            "the **leading tone** (scale degree 7), a half step below the "
                            "tonic and pulling up into it. The **4th scale degree** "
                            "carries a milder pull down to the 3rd. A melody that "
                            "respects these tendencies - resolving them rather than "
                            "leaping away from them - reads as purposeful rather than "
                            "arbitrary."
                        )
                    },
                    topics=["melodic-construction"],
                ),
                StepDef(
                    slug="melodic-construction-quiz-leap-recovery",
                    kind="quiz",
                    payload={
                        "question": (
                            "A melodic leap of a fourth or larger should usually be "
                            "followed by:"
                        ),
                        "choices": [
                            "A step in the opposite direction",
                            "Another leap in the same direction",
                            "A rest",
                            "The exact same note, repeated",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "Recovering a leap with a step back the other way keeps the "
                            "line feeling grounded rather than like it's running away "
                            "in one direction."
                        ),
                    },
                    topics=["melodic-construction"],
                ),
                StepDef(
                    slug="melodic-construction-quiz-tendency-tone",
                    kind="quiz",
                    payload={
                        "question": (
                            "Which scale degree is the strongest tendency tone, "
                            "pulling up to the tonic?"
                        ),
                        "choices": [
                            "The leading tone (7th degree)",
                            "The 2nd degree",
                            "The 4th degree",
                            "The 6th degree",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The leading tone sits a half step below the tonic, giving "
                            "it the strongest upward pull of any scale degree."
                        ),
                    },
                    topics=["melodic-construction"],
                ),
                StepDef(
                    slug="melodic-construction-task",
                    kind="composition",
                    payload={
                        "brief": (
                            "Write an eight-measure melody in C major. Stay diatonic, "
                            "keep every leap to a sixth or smaller, and answer every "
                            "leap of a fourth or more with a step in the opposite "
                            "direction."
                        ),
                        "requirements": [
                            {"type": "key", "key": "C major"},
                            {"type": "diatonic_only"},
                            {"type": "max_leap", "semitones": 9},
                            {"type": "leap_recovery", "max_unresolved": 0},
                            {"type": "measure_count", "count": 8},
                        ],
                    },
                    topics=["melodic-construction"],
                ),
            ],
        ),
    ],
)
