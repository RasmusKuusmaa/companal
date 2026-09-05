"""Stage 4 - Chromaticism: tonicization, modulation, and borrowed chords."""

from app.domains.learning.curriculum.definitions import CourseDef, LessonDef, StepDef

COURSE = CourseDef(
    slug="chromaticism",
    title="Chromaticism",
    description=(
        "Stepping outside the diatonic collection: secondary chords, tonicization and "
        "modulation, modal mixture, and the Neapolitan and augmented sixth chords."
    ),
    level="advanced",
    lessons=[
        LessonDef(
            slug="secondary-dominants",
            title="Secondary Dominants",
            summary="Borrowing V of a scale degree other than the tonic to tonicize it.",
            estimated_minutes=14,
            steps=[
                StepDef(
                    slug="secondary-dominants-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Secondary dominants\n\n"
                            "Any major or minor triad in a key can be briefly treated "
                            "as if it were its own tonic, borrowing **its own dominant** "
                            "from outside the home key to lean on it - a technique "
                            "called **tonicization**, and the borrowed chord that does "
                            "the leaning is a **secondary dominant**.\n\n"
                            "A secondary dominant is labeled V/x - \"five of x\" - naming "
                            "which chord it's the dominant *of*. In C major, the "
                            "dominant of the dominant, **V/V**, is a D major triad (or "
                            "D7): the real dominant of G, borrowed to strengthen the "
                            "arrival on V. **V/ii** would be the dominant of D minor "
                            "(A major or A7); **V/vi**, the dominant of A minor (E major "
                            "or E7).\n\n"
                            "A secondary dominant almost always introduces a note "
                            "outside the home key's signature - specifically, the "
                            "**leading tone of the chord it's tonicizing**. That "
                            "accidental is the clearest signal, on the page, that a "
                            "secondary dominant is in play rather than a plain diatonic "
                            "chord."
                        )
                    },
                    topics=["secondary-dominants"],
                ),
                StepDef(
                    slug="secondary-dominants-quiz-v-of-v",
                    kind="quiz",
                    payload={
                        "question": "In C major, V/V is built on which note?",
                        "choices": ["D", "G", "A", "F"],
                        "answer_index": 0,
                        "explanation": (
                            "V/V is the dominant of G (C major's own V), and the "
                            "dominant of G is built on D."
                        ),
                    },
                    topics=["secondary-dominants"],
                ),
                StepDef(
                    slug="secondary-dominants-quiz-accidental",
                    kind="quiz",
                    payload={
                        "question": (
                            "A secondary dominant most often introduces an accidental "
                            "that is:"
                        ),
                        "choices": [
                            "The leading tone of the chord it's tonicizing",
                            "A note from the parallel minor",
                            "An arbitrary chromatic passing tone",
                            "Always a lowered 7th scale degree",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "A secondary dominant needs a real leading tone a half step "
                            "below whatever chord it's tonicizing, and that leading "
                            "tone is usually the accidental that gives it away."
                        ),
                    },
                    topics=["secondary-dominants"],
                ),
            ],
        ),
    ],
)
