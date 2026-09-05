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
        LessonDef(
            slug="triad-inversions-and-figured-bass-symbols",
            title="Triad Inversions and Figured Bass Symbols",
            summary="Root position, first and second inversion, and the figures that name them.",
            estimated_minutes=10,
            steps=[
                StepDef(
                    slug="triad-inversions-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Triad inversions and figured bass symbols\n\n"
                            "A triad's **inversion** depends on which of its three notes "
                            "sits in the bass, not on which notes it contains - C-E-G, "
                            "E-G-C and G-C-E are all a C major triad, just rearranged.\n\n"
                            "- **Root position**: the root is in the bass. Figured bass "
                            "symbol **5/3**, almost always left blank since it's the "
                            "default.\n"
                            "- **First inversion**: the third is in the bass. Symbol "
                            "**6/3**, nearly always abbreviated to just **6**.\n"
                            "- **Second inversion**: the fifth is in the bass. Symbol "
                            "**6/4** - and this one is never abbreviated, since \"4\" "
                            "alone would be ambiguous.\n\n"
                            "The numbers in a figure count the interval each upper voice "
                            "makes **above the bass note**, not above the root - which is "
                            "exactly why first inversion reads 6/3 (a sixth and a third "
                            "above the bass) rather than reusing 5/3."
                        )
                    },
                    topics=["triad-inversions-and-figures"],
                ),
                StepDef(
                    slug="triad-inversions-quiz-first-inversion",
                    kind="quiz",
                    payload={
                        "question": "What figure represents a triad in first inversion?",
                        "choices": ["6/4", "6", "5/3", "7"],
                        "answer_index": 1,
                        "explanation": (
                            "First inversion's full figure is 6/3, but the 3 is "
                            "conventionally dropped, leaving just 6."
                        ),
                    },
                    topics=["triad-inversions-and-figures"],
                ),
                StepDef(
                    slug="triad-inversions-quiz-second-inversion",
                    kind="quiz",
                    payload={
                        "question": "In second inversion, which chord member sits in the bass?",
                        "choices": ["The root", "The third", "The fifth", "The seventh"],
                        "answer_index": 2,
                        "explanation": (
                            "Second inversion puts the fifth in the bass, giving the "
                            "6/4 figure - a sixth and a fourth above that fifth."
                        ),
                    },
                    topics=["triad-inversions-and-figures"],
                ),
            ],
        ),
    ],
)
