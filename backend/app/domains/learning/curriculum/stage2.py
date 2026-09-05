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
        LessonDef(
            slug="connecting-root-position-triads",
            title="Connecting Root Position Triads",
            summary="Common-tone and stepwise connection between root position chords.",
            estimated_minutes=14,
            steps=[
                StepDef(
                    slug="connecting-root-position-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Connecting root position triads\n\n"
                            "How you move the upper voices from one root-position triad "
                            "to the next depends on how far apart their roots are.\n\n"
                            "## Roots a fourth or fifth apart\n\n"
                            "These chords share exactly one common tone (I and V share a "
                            "G in C major, for instance). Keep that common tone in "
                            "whichever voice already has it, and move the other two "
                            "upper voices to the nearest note of the new chord.\n\n"
                            "## Roots a second or third apart\n\n"
                            "These chords share no comfortable common tone to hold onto. "
                            "Instead, move **all** the upper voices in the same direction "
                            "as each other, each to the nearest available note of the new "
                            "chord - contrary to the bass if the bass leaps, to avoid "
                            "everything piling up in the same direction at once.\n\n"
                            "Either way, the goal is the same: the smoothest possible "
                            "path from one chord to the next, checked afterward for "
                            "parallel fifths and octaves between every pair of voices."
                        )
                    },
                    topics=["connecting-root-position-triads"],
                ),
                StepDef(
                    slug="connecting-root-position-quiz-common-tone",
                    kind="quiz",
                    payload={
                        "question": (
                            "Connecting two root-position triads a fifth apart, what "
                            "should happen to their common tone?"
                        ),
                        "choices": [
                            "Keep it in the same voice",
                            "Move it to a different voice",
                            "Double it across two voices",
                            "Omit it from the second chord",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "Holding the common tone in the same voice is what makes the "
                            "connection smooth - it's one less voice that has to move at "
                            "all."
                        ),
                    },
                    topics=["connecting-root-position-triads"],
                ),
                StepDef(
                    slug="connecting-root-position-quiz-second-apart",
                    kind="quiz",
                    payload={
                        "question": (
                            "Connecting two root-position triads whose roots are a "
                            "second apart, how should the upper voices generally move?"
                        ),
                        "choices": [
                            "All in the same direction, to the nearest chord tone",
                            "Randomly, in whatever direction is convenient",
                            "All by leap, in contrary motion to each other",
                            "Not at all - every voice holds its note",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "With no common tone to anchor on, moving every upper voice "
                            "the same direction to the nearest chord tone keeps the "
                            "motion smooth and avoids voices crossing each other."
                        ),
                    },
                    topics=["connecting-root-position-triads"],
                ),
                StepDef(
                    slug="connecting-root-position-task",
                    kind="composition",
                    payload={
                        "brief": (
                            "The bass line below is given and locked (I - V - I, all "
                            "root position). Connect the chords smoothly, keeping the "
                            "common tone where you can and avoiding parallel fifths or "
                            "octaves."
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
                                                            "octave": octave,
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
                                        for i, (step, octave) in enumerate(
                                            [("C", 3), ("G", 2), ("C", 3)]
                                        )
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
                    topics=["connecting-root-position-triads", "parallel-fifths-and-octaves"],
                ),
            ],
        ),
        LessonDef(
            slug="first-inversion-triads-and-doubling-choices",
            title="First Inversion Triads and Doubling Choices",
            summary="Why the bass, not the root, usually gets doubled in first inversion.",
            estimated_minutes=12,
            steps=[
                StepDef(
                    slug="first-inversion-doubling-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# First inversion triads and doubling choices\n\n"
                            "In first inversion, the chord's **third** sits in the bass "
                            "instead of the root. Doubling that bass note is generally "
                            "avoided as a default habit - it's not forbidden, but it "
                            "tends to overemphasize the third at the expense of the root, "
                            "which is usually the note you want to feel most strongly. "
                            "More often, one of the upper voices gets doubled instead - "
                            "whichever choice produces the smoothest connection to the "
                            "surrounding chords.\n\n"
                            "## The diminished exception\n\n"
                            "A first-inversion diminished triad - most often the "
                            "leading-tone chord, **vii°6** - flips this guideline. Its "
                            "root and fifth form a tritone with each other and both carry "
                            "strong pulls toward resolution, so doubling either one "
                            "doubles that instability. Doubling the **bass note** (the "
                            "diminished triad's third) instead is the standard, safer "
                            "choice here."
                        )
                    },
                    topics=["first-inversion-triads"],
                ),
                StepDef(
                    slug="first-inversion-doubling-quiz-default",
                    kind="quiz",
                    payload={
                        "question": (
                            "In first inversion, which note is usually avoided as the "
                            "doubling choice?"
                        ),
                        "choices": [
                            "The bass note (the chord's third)",
                            "The chord's root",
                            "The chord's fifth",
                            "No note is preferred - any is equally fine",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "Doubling the bass in first inversion overemphasizes the "
                            "third at the root's expense, so an upper voice is usually "
                            "doubled instead."
                        ),
                    },
                    topics=["first-inversion-triads"],
                ),
                StepDef(
                    slug="first-inversion-doubling-quiz-diminished",
                    kind="quiz",
                    payload={
                        "question": "In vii°6, which note is the preferred doubling choice?",
                        "choices": [
                            "The bass note (the diminished triad's third)",
                            "The leading tone itself",
                            "The note that forms a tritone with the leading tone",
                            "vii°6 should never have a doubled note",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "vii°6's root and fifth form the unstable tritone, so the "
                            "bass note - the triad's third - is doubled instead, "
                            "leaving that tritone's two notes each appearing only once."
                        ),
                    },
                    topics=["first-inversion-triads"],
                ),
            ],
        ),
        LessonDef(
            slug="the-three-uses-of-the-six-four-chord",
            title="The Three Uses of the Six-Four Chord",
            summary="Cadential, passing and pedal six-four chords, and how each is used.",
            estimated_minutes=14,
            steps=[
                StepDef(
                    slug="six-four-chords-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# The three uses of the six-four chord\n\n"
                            "A second-inversion triad (6/4) is treated as unstable on its "
                            "own - its bass note isn't really acting as a chord root, but "
                            "as a **dissonance against the true harmony**, resolved in "
                            "one of three conventional ways.\n\n"
                            "## Cadential six-four\n\n"
                            "A I6/4 arrives on a strong beat right before V, then "
                            "resolves down by step into an actual V chord - the 6/4's "
                            "upper voices (a 6th and a 4th above the bass) fall to a 5th "
                            "and a 3rd as the same bass note becomes the root of V. "
                            "It's really a decorated dominant, not a tonic at all.\n\n"
                            "## Passing six-four\n\n"
                            "A 6/4 chord fills the gap between two chords a step apart in "
                            "the bass - I, then a passing I6/4 (or V6/4) as the bass "
                            "steps through, then I6 (or another chord) on the other side. "
                            "It appears on a weak beat, decorating a smooth bass line.\n\n"
                            "## Pedal (or pedal-point) six-four\n\n"
                            "The bass holds a single note while the upper voices move "
                            "around it, briefly passing through a 6/4 spelling before "
                            "settling back onto the chord the bass note actually belongs "
                            "to - I, then IV6/4 over that same bass note, then back to I."
                        )
                    },
                    topics=["six-four-chords"],
                ),
                StepDef(
                    slug="six-four-chords-quiz-cadential",
                    kind="quiz",
                    payload={
                        "question": "The cadential six-four chord typically resolves to:",
                        "choices": [
                            "V, over the same bass note",
                            "IV",
                            "vi",
                            "ii",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The cadential 6/4's bass note becomes the root of the V "
                            "chord it resolves to - it's a decorated dominant, not a "
                            "stable tonic."
                        ),
                    },
                    topics=["six-four-chords"],
                ),
                StepDef(
                    slug="six-four-chords-quiz-pedal",
                    kind="quiz",
                    payload={
                        "question": (
                            "Which six-four type has the bass hold one note while the "
                            "upper voices move around it?"
                        ),
                        "choices": [
                            "Pedal (or pedal-point) six-four",
                            "Cadential six-four",
                            "Passing six-four",
                            "There is no such type",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "A pedal six-four holds the bass steady while the harmony "
                            "shifts above it, briefly spelling a 6/4 before settling "
                            "back onto the chord that bass note belongs to."
                        ),
                    },
                    topics=["six-four-chords"],
                ),
            ],
        ),
        LessonDef(
            slug="the-dominant-seventh-and-its-resolution",
            title="The Dominant Seventh and Its Resolution",
            summary="Why the seventh falls and the leading tone rises when V7 resolves to I.",
            estimated_minutes=14,
            steps=[
                StepDef(
                    slug="dominant-seventh-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# The dominant seventh and its resolution\n\n"
                            "The **dominant seventh** chord (V7) is a major triad with a "
                            "minor seventh on top - in C major, G-B-D-F. It contains two "
                            "notes that form a **tritone** with each other (B and F), and "
                            "that tritone is what gives V7 its strong pull toward the "
                            "tonic.\n\n"
                            "Both tritone members have a required direction of travel "
                            "when V7 resolves to I:\n\n"
                            "- The **leading tone** (the chord's third, B) resolves "
                            "**up** by step to the tonic.\n"
                            "- The **chordal seventh** (F, the key's 4th scale degree) "
                            "resolves **down** by step to the third of the tonic chord.\n\n"
                            "Since V7 has four distinct notes but a root-position tonic "
                            "triad only needs three, one voice of the resolution usually "
                            "lands on a doubled tonic root rather than a fifth - a small, "
                            "expected compromise for keeping both tendency tones moving "
                            "the way they want to."
                        )
                    },
                    topics=["dominant-seventh-resolution"],
                ),
                StepDef(
                    slug="dominant-seventh-quiz-tendency-tones",
                    kind="quiz",
                    payload={
                        "question": (
                            "Which two members of a V7 chord must resolve in specific, "
                            "opposite directions?"
                        ),
                        "choices": [
                            "The leading tone (up) and the chordal seventh (down)",
                            "The root and the fifth",
                            "The bass and the soprano, always by leap",
                            "There are no required resolutions in a V7 chord",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The leading tone and the chordal seventh form the chord's "
                            "tritone, and each has a required direction: the leading "
                            "tone rises, the seventh falls."
                        ),
                    },
                    topics=["dominant-seventh-resolution"],
                ),
                StepDef(
                    slug="dominant-seventh-quiz-seventh-direction",
                    kind="quiz",
                    payload={
                        "question": (
                            "The chordal seventh of a V7 chord resolves by step in "
                            "which direction?"
                        ),
                        "choices": ["Down", "Up", "It holds over, unchanged", "Either, freely"],
                        "answer_index": 0,
                        "explanation": (
                            "The chordal seventh always falls by step to the third of "
                            "the following tonic chord."
                        ),
                    },
                    topics=["dominant-seventh-resolution"],
                ),
                StepDef(
                    slug="dominant-seventh-task",
                    kind="composition",
                    payload={
                        "brief": (
                            "The bass line below is given and locked: V7 resolving to "
                            "I. Realize the V7 chord in full, then resolve it - let the "
                            "leading tone rise and the chordal seventh fall by step."
                        ),
                        "requirements": [
                            {
                                "type": "figured_bass",
                                "bass_staff_index": 0,
                                "figures": ["7", ""],
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
                                                            "octave": octave,
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
                                        for i, (step, octave) in enumerate(
                                            [("G", 2), ("C", 3)]
                                        )
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
                                                {
                                                    "id": "v3",
                                                    "notes": [
                                                        {
                                                            "id": f"u3-{i}",
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
                                        for i in range(2)
                                    ],
                                },
                            ],
                        },
                        "locked_staff_indices": [0],
                    },
                    topics=["dominant-seventh-resolution"],
                ),
            ],
        ),
    ],
)
