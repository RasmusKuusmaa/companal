"""Stage 3 - Line and counterpoint: melody, phrase, cadence, and species."""

from typing import Any

from app.domains.learning.curriculum.definitions import CourseDef, LessonDef, StepDef


def _blank_measures(count: int, voice_id: str) -> list[dict[str, Any]]:
    """`count` empty (whole-rest) measures for one voice - a blank starting
    point with the right shape, not a hint at any particular solution."""
    return [
        {
            "id": f"m{i}",
            "voices": [
                {
                    "id": voice_id,
                    "notes": [
                        {
                            "id": f"{voice_id}-{i}",
                            "step": "C",
                            "octave": 4,
                            "alter": 0,
                            "duration": "whole",
                            "dots": 0,
                            "is_rest": True,
                            "tied_to_next": False,
                        }
                    ],
                }
            ],
        }
        for i in range(count)
    ]

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
        LessonDef(
            slug="cadence-types-and-their-strength",
            title="Cadence Types and Their Strength",
            summary="Authentic, half, plagal and deceptive cadences, and how final each feels.",
            estimated_minutes=14,
            steps=[
                StepDef(
                    slug="cadence-types-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Cadence types and their strength\n\n"
                            "- **Perfect authentic (PAC)** - V (or V7) to I, both in "
                            "root position, soprano landing on the tonic. The strongest, "
                            "most conclusive close there is.\n"
                            "- **Imperfect authentic (IAC)** - the same V-I motion, but "
                            "with an inversion involved or the soprano landing somewhere "
                            "other than the tonic. Still a real ending, just a softer "
                            "one.\n"
                            "- **Half cadence** - the phrase ends *on* V rather than "
                            "moving through it. It doesn't close anything; it reads as a "
                            "question mark, expecting more music to follow.\n"
                            "- **Plagal cadence** - IV to I, the \"amen\" cadence. "
                            "Conclusive, but gentler than an authentic close - there's no "
                            "leading tone doing the pulling.\n"
                            "- **Deceptive cadence** - V moves to vi instead of the "
                            "expected I. The ear is set up for a full stop and gets a "
                            "surprise redirection instead.\n\n"
                            "Authentic and plagal cadences close a phrase; half and "
                            "deceptive cadences deliberately don't - they're for pausing "
                            "or surprising, not for ending."
                        )
                    },
                    topics=["cadence-types"],
                ),
                StepDef(
                    slug="cadence-types-quiz-strongest",
                    kind="quiz",
                    payload={
                        "question": "Which cadence type is the strongest, most conclusive close?",
                        "choices": ["Perfect authentic", "Half", "Deceptive", "Plagal"],
                        "answer_index": 0,
                        "explanation": (
                            "A perfect authentic cadence - root-position V to root-"
                            "position I, soprano on the tonic - is the most conclusive "
                            "close in the common-practice vocabulary."
                        ),
                    },
                    topics=["cadence-types"],
                ),
                StepDef(
                    slug="cadence-types-quiz-half",
                    kind="quiz",
                    payload={
                        "question": "A half cadence ends on which chord?",
                        "choices": ["V", "I", "IV", "vi"],
                        "answer_index": 0,
                        "explanation": (
                            "A half cadence arrives on the dominant and stops there - "
                            "an open question, not a resolution."
                        ),
                    },
                    topics=["cadence-types"],
                ),
                StepDef(
                    slug="cadence-types-task",
                    kind="composition",
                    payload={
                        "brief": (
                            "Write a four-measure phrase in C major that ends with a "
                            "half cadence."
                        ),
                        "requirements": [
                            {"type": "key", "key": "C major"},
                            {"type": "measure_count", "count": 4},
                            {"type": "cadence", "cadence": "half"},
                        ],
                        "starter_notation": {
                            "fifths": 0,
                            "mode": "major",
                            "time": {"beats": 4, "beat_type": 4},
                            "tempo": 90,
                            "staves": [
                                {
                                    "id": "soprano",
                                    "clef": "treble",
                                    "measures": _blank_measures(4, "soprano-voice"),
                                },
                                {
                                    "id": "bass",
                                    "clef": "bass",
                                    "measures": _blank_measures(4, "bass-voice"),
                                },
                            ],
                        },
                    },
                    topics=["cadence-types"],
                ),
            ],
        ),
        LessonDef(
            slug="first-species-counterpoint",
            title="First Species Counterpoint",
            summary="Note-against-note writing against a cantus firmus.",
            estimated_minutes=18,
            steps=[
                StepDef(
                    slug="first-species-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# First species counterpoint\n\n"
                            "Species counterpoint is a discipline for training the ear "
                            "and the pen at once: write one line against another - the "
                            "given **cantus firmus** - following a strict set of rules, "
                            "then relax those rules one species at a time. **First "
                            "species** is the strictest: exactly one note in the "
                            "counterpoint against each note of the cantus firmus.\n\n"
                            "## The rules\n\n"
                            "- Every interval against the cantus firmus must be "
                            "**consonant** - a unison, third, fifth, sixth or octave. "
                            "There's no rhythmic subdivision to hide a dissonance "
                            "against, so none is allowed.\n"
                            "- No parallel fifths or parallel octaves between the two "
                            "lines.\n"
                            "- Favor **contrary motion**, especially moving into a "
                            "perfect interval.\n"
                            "- Begin and end on a perfect consonance (a unison, fifth "
                            "or octave), with the final note approached by **step**.\n\n"
                            "Every one of these constraints exists to keep the "
                            "counterpoint independent of the cantus firmus - its own "
                            "line, not a shadow of the given one."
                        )
                    },
                    topics=["first-species-counterpoint"],
                ),
                StepDef(
                    slug="first-species-quiz-consonance",
                    kind="quiz",
                    payload={
                        "question": (
                            "In first species counterpoint, what's the rule for "
                            "consonance?"
                        ),
                        "choices": [
                            "Every interval against the cantus firmus must be consonant",
                            "Dissonance is allowed on the downbeat only",
                            "Any interval is fine as long as it eventually resolves",
                            "Only perfect intervals (unisons, fifths, octaves) are allowed",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "With one note against one note and no rhythmic "
                            "subdivision, first species has nowhere to place a passing "
                            "dissonance - every interval must be consonant."
                        ),
                    },
                    topics=["first-species-counterpoint"],
                ),
                StepDef(
                    slug="first-species-quiz-ending",
                    kind="quiz",
                    payload={
                        "question": "How should a first species exercise typically end?",
                        "choices": [
                            "On a perfect unison or octave, approached by step",
                            "On a perfect fifth, approached by leap",
                            "On any consonant interval, approached however",
                            "On a major third",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The final interval should be a perfect unison or octave, "
                            "with the counterpoint arriving there by step for a clean, "
                            "conclusive close."
                        ),
                    },
                    topics=["first-species-counterpoint"],
                ),
                StepDef(
                    slug="first-species-task",
                    kind="composition",
                    payload={
                        "brief": (
                            "The cantus firmus below is given and locked. Write a "
                            "first species (note-against-note) counterpoint above it."
                        ),
                        "requirements": [
                            {
                                "type": "species_counterpoint",
                                "species": 1,
                                "cantus_firmus_staff_index": 0,
                            }
                        ],
                        "starter_notation": {
                            "fifths": 0,
                            "mode": "major",
                            "time": {"beats": 4, "beat_type": 4},
                            "tempo": 90,
                            "staves": [
                                {
                                    "id": "cantus-firmus",
                                    "clef": "bass",
                                    "measures": [
                                        {
                                            "id": f"m{i}",
                                            "voices": [
                                                {
                                                    "id": "cf-voice",
                                                    "notes": [
                                                        {
                                                            "id": f"cf{i}",
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
                                        for i, step in enumerate(["C", "D", "E", "D", "C"])
                                    ],
                                },
                                {
                                    "id": "counterpoint",
                                    "clef": "treble",
                                    "measures": _blank_measures(5, "cp-voice"),
                                },
                            ],
                        },
                        "locked_staff_indices": [0],
                    },
                    topics=["first-species-counterpoint"],
                ),
            ],
        ),
    ],
)
