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
        LessonDef(
            slug="phrase-structure-period-and-sentence",
            title="Phrase Structure: Period and Sentence",
            summary="The two classic ways short musical ideas combine into a phrase.",
            estimated_minutes=14,
            steps=[
                StepDef(
                    slug="phrase-structure-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Phrase structure: period and sentence\n\n"
                            "## Period\n\n"
                            "A **period** is two phrases that together form one "
                            "complete musical thought: an **antecedent** ending with a "
                            "weaker cadence (typically half or imperfect authentic), "
                            "answered by a **consequent** that ends with a stronger one "
                            "(typically perfect authentic). If the two phrases begin "
                            "with the same or very similar material, it's a **parallel "
                            "period**; if they begin differently, it's a **contrasting "
                            "period**. Either way, the pattern is question-then-answer: "
                            "the antecedent opens something the consequent resolves.\n\n"
                            "## Sentence\n\n"
                            "A **sentence** is built differently. It opens with a "
                            "**presentation** - a short basic idea immediately repeated, "
                            "often at a different pitch level - and then moves into a "
                            "**continuation**: the material fragments into smaller "
                            "pieces, the harmonic rhythm often speeds up, and the phrase "
                            "drives forward to its cadence. Where a period balances two "
                            "roughly equal halves, a sentence accelerates toward its "
                            "ending."
                        )
                    },
                    topics=["phrase-structure"],
                ),
                StepDef(
                    slug="phrase-structure-quiz-antecedent",
                    kind="quiz",
                    payload={
                        "question": (
                            "In a parallel period, the antecedent phrase typically "
                            "ends with:"
                        ),
                        "choices": [
                            "A weaker cadence, such as a half or imperfect authentic",
                            "The same perfect authentic cadence as the consequent",
                            "No cadence at all",
                            "A deceptive cadence, always",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The antecedent poses the question with a weaker cadence; "
                            "the consequent answers it with something more conclusive."
                        ),
                    },
                    topics=["phrase-structure"],
                ),
                StepDef(
                    slug="phrase-structure-quiz-sentence-opening",
                    kind="quiz",
                    payload={
                        "question": "A sentence structure begins with:",
                        "choices": [
                            "A presentation phrase - a basic idea plus its repetition",
                            "A continuation phrase",
                            "A retransition back to the opening key",
                            "A full restatement of the whole theme",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "A sentence opens by presenting its basic idea and "
                            "immediately repeating it, before the continuation phrase "
                            "fragments and drives to a cadence."
                        ),
                    },
                    topics=["phrase-structure"],
                ),
            ],
        ),
    ],
)
