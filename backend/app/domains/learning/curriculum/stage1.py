"""Stage 1 - Chords and figures: triads, sevenths, and roman numerals."""

from app.domains.learning.curriculum.definitions import CourseDef, LessonDef, StepDef

COURSE = CourseDef(
    slug="chords-and-figures",
    title="Chords and Figures",
    description=(
        "Building and naming chords: triads and seventh chords, their inversions and figures, "
        "and roman numeral analysis in major and minor."
    ),
    level="beginner",
    lessons=[
        LessonDef(
            slug="triads-and-their-qualities",
            title="Triads and Their Qualities",
            summary="Major, minor, diminished and augmented triads, and how to spell each.",
            estimated_minutes=12,
            steps=[
                StepDef(
                    slug="triads-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Triads and their qualities\n\n"
                            "A **triad** is three notes stacked in thirds: a root, the "
                            "third above it, and the fifth above the root. Which two "
                            "thirds get stacked - major or minor - decides the triad's "
                            "**quality**.\n\n"
                            "- **Major triad**: major third, then minor third (root to "
                            "fifth spans a perfect fifth). Bright and stable - C-E-G.\n"
                            "- **Minor triad**: minor third, then major third (also a "
                            "perfect fifth root to fifth, just built the other way up). "
                            "Darker - C-Eb-G.\n"
                            "- **Diminished triad**: minor third, then minor third, "
                            "which makes the outer interval a *diminished* fifth instead "
                            "of a perfect one. Tense and unstable - C-Eb-Gb.\n"
                            "- **Augmented triad**: major third, then major third, "
                            "making the outer interval an *augmented* fifth. Unsettled in "
                            "the opposite direction - C-E-G#.\n\n"
                            "Major and minor triads are the two you'll meet constantly; "
                            "diminished and augmented are rarer, and both get their "
                            "instability from an outer fifth that isn't perfect."
                        )
                    },
                    topics=["triads"],
                ),
                StepDef(
                    slug="triads-quiz-minor-stack",
                    kind="quiz",
                    payload={
                        "question": (
                            "A minor triad is built from which two stacked thirds, "
                            "bottom to top?"
                        ),
                        "choices": [
                            "Minor third, then major third",
                            "Major third, then minor third",
                            "Minor third, then minor third",
                            "Major third, then major third",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "A minor triad stacks a minor third below a major third - "
                            "C-Eb (minor third) then Eb-G (major third)."
                        ),
                    },
                    topics=["triads"],
                ),
                StepDef(
                    slug="triads-quiz-augmented",
                    kind="quiz",
                    payload={
                        "question": "Which triad quality is built from two stacked major thirds?",
                        "choices": ["Major", "Minor", "Diminished", "Augmented"],
                        "answer_index": 3,
                        "explanation": (
                            "Stacking a major third on a major third (C-E, E-G#) produces "
                            "an augmented fifth from root to top - the augmented triad."
                        ),
                    },
                    topics=["triads"],
                ),
            ],
        ),
    ],
)
