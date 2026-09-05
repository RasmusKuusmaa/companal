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
        LessonDef(
            slug="seventh-chords-and-their-figures",
            title="Seventh Chords and Their Figures",
            summary="The five seventh-chord qualities and their inversion figures.",
            estimated_minutes=12,
            steps=[
                StepDef(
                    slug="seventh-chords-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Seventh chords and their figures\n\n"
                            "Stack one more third on top of a triad and it becomes a "
                            "**seventh chord**: root, third, fifth and seventh. The "
                            "triad's own quality plus the size of that top seventh gives "
                            "five common types:\n\n"
                            "- **Major seventh**: major triad + major seventh "
                            "(C-E-G-B).\n"
                            "- **Dominant seventh**: major triad + minor seventh "
                            "(C-E-G-Bb) - the chord built on the fifth degree of a key.\n"
                            "- **Minor seventh**: minor triad + minor seventh "
                            "(C-Eb-G-Bb).\n"
                            "- **Half-diminished seventh**: diminished triad + minor "
                            "seventh (C-Eb-Gb-Bb).\n"
                            "- **Fully diminished seventh**: diminished triad + "
                            "diminished seventh (C-Eb-Gb-Bbb) - every interval a minor "
                            "third.\n\n"
                            "## Figures\n\n"
                            "A seventh chord has four inversions instead of a triad's "
                            "three, since there's one more note to put in the bass:\n\n"
                            "- Root position: **7**\n"
                            "- First inversion (third in bass): **6/5**\n"
                            "- Second inversion (fifth in bass): **4/3**\n"
                            "- Third inversion (seventh in bass): **4/2**, often just "
                            "**2**"
                        )
                    },
                    topics=["seventh-chords"],
                ),
                StepDef(
                    slug="seventh-chords-quiz-dominant",
                    kind="quiz",
                    payload={
                        "question": "A dominant seventh chord is built from which combination?",
                        "choices": [
                            "Major triad + minor seventh",
                            "Major triad + major seventh",
                            "Minor triad + minor seventh",
                            "Diminished triad + diminished seventh",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The dominant seventh is a major triad topped with a minor "
                            "seventh - C-E-G-Bb, not C-E-G-B."
                        ),
                    },
                    topics=["seventh-chords"],
                ),
                StepDef(
                    slug="seventh-chords-quiz-third-inversion",
                    kind="quiz",
                    payload={
                        "question": (
                            "What figure represents a seventh chord in third inversion?"
                        ),
                        "choices": ["6/5", "4/3", "4/2", "7"],
                        "answer_index": 2,
                        "explanation": (
                            "Third inversion puts the seventh itself in the bass, giving "
                            "the figure 4/2."
                        ),
                    },
                    topics=["seventh-chords"],
                ),
            ],
        ),
        LessonDef(
            slug="roman-numeral-analysis-in-major",
            title="Roman Numeral Analysis in Major",
            summary="Labeling chords by scale degree and quality within a major key.",
            estimated_minutes=12,
            steps=[
                StepDef(
                    slug="roman-numerals-major-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Roman numeral analysis in major\n\n"
                            "Build a triad on every degree of a major scale, using only "
                            "notes from that scale, and the qualities come out fixed - "
                            "always in the same order. **Roman numerals** name each chord "
                            "by which scale degree it's built on, and their case records "
                            "the quality: uppercase for major, lowercase for minor, a "
                            "small circle for diminished.\n\n"
                            "In any major key, the seven diatonic triads are:\n\n"
                            "- **I** (major) - the tonic\n"
                            "- **ii** (minor)\n"
                            "- **iii** (minor)\n"
                            "- **IV** (major) - the subdominant\n"
                            "- **V** (major) - the dominant\n"
                            "- **vi** (minor)\n"
                            "- **vii°** (diminished) - the leading-tone triad\n\n"
                            "This pattern - major, minor, minor, major, major, minor, "
                            "diminished - falls directly out of the major scale's own "
                            "whole-step/half-step layout, so it's worth memorizing once "
                            "rather than re-deriving it every time."
                        )
                    },
                    topics=["roman-numerals-major"],
                ),
                StepDef(
                    slug="roman-numerals-major-quiz-diminished",
                    kind="quiz",
                    payload={
                        "question": "In a major key, which scale degree's triad is diminished?",
                        "choices": ["ii", "V", "vii", "IV"],
                        "answer_index": 2,
                        "explanation": (
                            "The triad on the 7th degree (vii°) is diminished - it's the "
                            "only diminished triad among the seven diatonic triads in "
                            "major."
                        ),
                    },
                    topics=["roman-numerals-major"],
                ),
                StepDef(
                    slug="roman-numerals-major-quiz-iv",
                    kind="quiz",
                    payload={
                        "question": (
                            "The triad built on the 4th scale degree of a major key is:"
                        ),
                        "choices": ["Minor", "Major", "Diminished", "Augmented"],
                        "answer_index": 1,
                        "explanation": (
                            "The 4th degree carries a major triad (IV), the subdominant."
                        ),
                    },
                    topics=["roman-numerals-major"],
                ),
            ],
        ),
        LessonDef(
            slug="roman-numeral-analysis-in-minor",
            title="Roman Numeral Analysis in Minor",
            summary="The same labeling in minor, where the raised leading tone complicates it.",
            estimated_minutes=12,
            steps=[
                StepDef(
                    slug="roman-numerals-minor-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Roman numeral analysis in minor\n\n"
                            "Minor's diatonic triads start from natural minor, using only "
                            "the key signature's own notes:\n\n"
                            "- **i** (minor) - the tonic\n"
                            "- **ii°** (diminished)\n"
                            "- **III** (major)\n"
                            "- **iv** (minor)\n"
                            "- **v** (minor)\n"
                            "- **VI** (major)\n"
                            "- **VII** (major)\n\n"
                            "That lowercase **v** is the catch: a minor dominant has no "
                            "leading tone and only a weak pull back to the tonic. In "
                            "practice, harmony almost always **raises the 7th degree** - "
                            "borrowing from harmonic minor - specifically to fix this, "
                            "turning v into a proper major **V** with a leading tone a "
                            "half step below the tonic, exactly the way a dominant is "
                            "supposed to behave. The other diatonic triads (i, ii°, III, "
                            "iv, VI) are normally left in their natural-minor form; only "
                            "the chords that need the leading tone borrow it."
                        )
                    },
                    topics=["roman-numerals-minor"],
                ),
                StepDef(
                    slug="roman-numerals-minor-quiz-why-raise",
                    kind="quiz",
                    payload={
                        "question": (
                            "Why is the raised (harmonic minor) 7th degree normally used "
                            "when building the dominant chord in a minor key?"
                        ),
                        "choices": [
                            "To create a major dominant triad with a real leading tone",
                            "To lower the 6th scale degree",
                            "Purely for melodic smoothness, with no harmonic effect",
                            "It has no effect on the dominant chord",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "Raising the 7th degree turns the weak, minor v chord into a "
                            "major V with a proper leading tone a half step below the "
                            "tonic - restoring the dominant's normal pull home."
                        ),
                    },
                    topics=["roman-numerals-minor"],
                ),
                StepDef(
                    slug="roman-numerals-minor-quiz-natural-v",
                    kind="quiz",
                    payload={
                        "question": (
                            "Built strictly from natural minor (no raised 7th), the "
                            "triad on the 5th degree is:"
                        ),
                        "choices": ["Minor", "Major", "Diminished", "Augmented"],
                        "answer_index": 0,
                        "explanation": (
                            "Without the raised 7th, the 5th degree's triad comes out "
                            "minor - a minor third stacked under a major third - which "
                            "is exactly the weak dominant harmonic minor's raised 7th is "
                            "there to fix."
                        ),
                    },
                    topics=["roman-numerals-minor"],
                ),
            ],
        ),
    ],
)
