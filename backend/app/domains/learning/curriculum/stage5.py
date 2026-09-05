"""Stage 5 - Form and composition: assembling everything into whole pieces."""

from typing import Any

from app.domains.learning.curriculum.definitions import CourseDef, LessonDef, StepDef


def _blank_measures(count: int, voice_id: str, id_offset: int = 0) -> list[dict[str, Any]]:
    """`count` empty (rest-only) whole-note measures for one voice - a blank
    starting point with the right shape, not a hint at any particular
    solution. `id_offset` keeps measure ids unique when concatenating calls."""
    return [
        {
            "id": f"m{id_offset + i}",
            "voices": [
                {
                    "id": voice_id,
                    "notes": [
                        {
                            "id": f"{voice_id}-{id_offset + i}",
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
    slug="form-and-composition",
    title="Form and Composition",
    description=(
        "The shapes a whole piece takes - binary, ternary, rondo and sonata form, theme "
        "and variations - and writing a complete short piece of your own."
    ),
    level="advanced",
    lessons=[
        LessonDef(
            slug="binary-and-ternary-form",
            title="Binary and Ternary Form",
            summary="The two most basic ways to shape a short piece.",
            estimated_minutes=14,
            steps=[
                StepDef(
                    slug="binary-ternary-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Binary and ternary form\n\n"
                            "**Binary form** shapes a piece into two sections, "
                            "**A B**, usually each repeated. **Simple binary** keeps "
                            "both sections in the same key throughout; **rounded "
                            "binary** brings the A material back at the end of B "
                            "(often written A B A', since the return is usually "
                            "varied or shortened), giving the form a satisfying sense "
                            "of homecoming without being a full third section.\n\n"
                            "**Ternary form** is three sections, **A B A**, where B "
                            "is a genuinely contrasting middle section - a different "
                            "key, theme, or mood - and the final A is a full, "
                            "essentially exact return of the opening. The key "
                            "distinction from rounded binary is how complete and "
                            "how contrasting the middle section is: ternary's B is "
                            "its own self-sufficient section, while rounded binary's "
                            "B is usually still developing A's own material before "
                            "the return.\n\n"
                            "Both forms rest on the same structural logic: "
                            "**statement, departure, and return** - state an idea, "
                            "move away from it (harmonically and/or thematically), "
                            "then bring it back to close the piece."
                        )
                    },
                    topics=["binary-and-ternary-form"],
                ),
                StepDef(
                    slug="binary-ternary-quiz-difference",
                    kind="quiz",
                    payload={
                        "question": (
                            "What most distinguishes ternary form (A B A) from "
                            "rounded binary (A B A')?"
                        ),
                        "choices": [
                            "Ternary's B is a complete, self-sufficient contrasting "
                            "section, and its final A is an essentially exact return",
                            "Ternary form has no repeats",
                            "Rounded binary always has more sections than ternary",
                            "Ternary form never modulates",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "Ternary's middle section stands on its own rather than "
                            "developing A, and its return is a full, essentially "
                            "exact restatement, not merely a shortened rounding-off."
                        ),
                    },
                    topics=["binary-and-ternary-form"],
                ),
                StepDef(
                    slug="binary-ternary-quiz-structure",
                    kind="quiz",
                    payload={
                        "question": (
                            "The structural logic shared by binary and ternary "
                            "form is best described as:"
                        ),
                        "choices": [
                            "Statement, departure, and return",
                            "Constant, unchanging repetition of one idea",
                            "A single continuous idea with no sectional breaks",
                            "Strict variation of a bass line only",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "Both forms state an idea, move away from it, and bring "
                            "it back - the basic shape underlying nearly all "
                            "sectional forms."
                        ),
                    },
                    topics=["binary-and-ternary-form"],
                ),
            ],
        ),
        LessonDef(
            slug="minuet-and-trio-and-rondo",
            title="Minuet and Trio, and Rondo",
            summary="A large-scale ternary dance movement, and a form built on returns.",
            estimated_minutes=15,
            steps=[
                StepDef(
                    slug="minuet-trio-rondo-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Minuet and trio, and rondo\n\n"
                            "**Minuet and trio** is ternary form at a larger scale: "
                            "a Minuet (itself often in rounded binary form), a "
                            "contrasting **Trio** (also usually in rounded binary, "
                            "typically in a related key and a lighter texture), and "
                            "then the Minuet again - written as **Minuet - Trio - "
                            "Minuet da capo** rather than notated out twice. The whole "
                            "movement is therefore a ternary form built out of two "
                            "smaller binary forms.\n\n"
                            "**Rondo form** takes the idea of contrast-and-return "
                            "further, alternating a recurring main theme, the "
                            "**refrain (A)**, with contrasting **episodes (B, C, "
                            "...)**: common patterns are **A B A C A** (five-part "
                            "rondo) or the simpler **A B A** (which is really just "
                            "ternary form under a different name at small scale). "
                            "The refrain always returns in the tonic key, giving a "
                            "rondo's episodes room to wander harmonically without "
                            "ever losing the sense of a home base to come back to.\n\n"
                            "Both forms share the same underlying principle as "
                            "binary and ternary form - contrast followed by return "
                            "- just deployed across a longer, sectional span."
                        )
                    },
                    topics=["minuet-trio-rondo"],
                ),
                StepDef(
                    slug="minuet-trio-rondo-quiz-structure",
                    kind="quiz",
                    payload={
                        "question": "A minuet and trio movement is structured as:",
                        "choices": [
                            "Minuet, Trio, then the Minuet again (da capo)",
                            "Minuet, Trio, and a third unrelated section",
                            "Trio only, repeated three times",
                            "Minuet and Trio played simultaneously",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The Minuet returns after the Trio, conventionally "
                            "indicated 'da capo' rather than written out a second "
                            "time - a large-scale ternary form built from two "
                            "smaller binary forms."
                        ),
                    },
                    topics=["minuet-trio-rondo"],
                ),
                StepDef(
                    slug="minuet-trio-rondo-quiz-refrain",
                    kind="quiz",
                    payload={
                        "question": (
                            "In rondo form, what is true of the refrain (A) each "
                            "time it returns?"
                        ),
                        "choices": [
                            "It returns in the tonic key",
                            "It returns in a new key each time",
                            "It is always shortened on repetition",
                            "It never repeats more than once",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The refrain's return in the tonic is what anchors a "
                            "rondo, letting its episodes explore other keys and "
                            "material without losing the sense of home."
                        ),
                    },
                    topics=["minuet-trio-rondo"],
                ),
            ],
        ),
        LessonDef(
            slug="sonata-form",
            title="Sonata Form",
            summary="The three-part drama of exposition, development, and recapitulation.",
            estimated_minutes=16,
            steps=[
                StepDef(
                    slug="sonata-form-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Sonata form\n\n"
                            "**Sonata form** is a large three-part structure built "
                            "around a harmonic drama rather than just a sequence of "
                            "themes:\n\n"
                            "- **Exposition**: presents a **first theme (or theme "
                            "group)** in the tonic, moves through a **transition** "
                            "to a **second theme** in a contrasting key (the "
                            "dominant, in a major-key sonata; the relative major, in "
                            "a minor-key one), and closes with **closing material** "
                            "confirming that new key. The exposition is "
                            "conventionally repeated.\n"
                            "- **Development**: takes fragments of the exposition's "
                            "themes and works them through a series of unstable, "
                            "often rapidly modulating keys - the harmonically "
                            "restless heart of the movement, building tension toward "
                            "the return.\n"
                            "- **Recapitulation**: restates the exposition's material "
                            "in the same order, but now with the second theme "
                            "**also in the tonic** rather than the contrasting key - "
                            "resolving the exposition's central harmonic tension by "
                            "bringing everything home.\n\n"
                            "That single move - the second theme returning in the "
                            "tonic instead of its original key - is the defining "
                            "harmonic event of sonata form, and the entire "
                            "development section exists to build toward it."
                        )
                    },
                    topics=["sonata-form"],
                ),
                StepDef(
                    slug="sonata-form-quiz-second-theme-key",
                    kind="quiz",
                    payload={
                        "question": (
                            "In a major-key sonata's exposition, what key is the "
                            "second theme normally in, and where is it in the "
                            "recapitulation?"
                        ),
                        "choices": [
                            "The dominant in the exposition; the tonic in the "
                            "recapitulation",
                            "The tonic in both the exposition and recapitulation",
                            "The subdominant in the exposition; the dominant in "
                            "the recapitulation",
                            "The relative minor in both sections",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The second theme's key shift - dominant in the "
                            "exposition, resolved to tonic in the recapitulation - "
                            "is sonata form's central harmonic event."
                        ),
                    },
                    topics=["sonata-form"],
                ),
                StepDef(
                    slug="sonata-form-quiz-development",
                    kind="quiz",
                    payload={
                        "question": "The development section is best characterized by:",
                        "choices": [
                            "Harmonic instability, working fragments of the "
                            "exposition's themes through shifting keys",
                            "A stable, unchanging tonic throughout",
                            "Introducing entirely new themes not heard before",
                            "An exact repeat of the exposition",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The development is defined by harmonic restlessness - "
                            "fragmenting and modulating existing thematic material "
                            "rather than presenting new themes or staying put."
                        ),
                    },
                    topics=["sonata-form"],
                ),
            ],
        ),
        LessonDef(
            slug="theme-and-variations",
            title="Theme and Variations",
            summary="Stating an idea plainly, then transforming it again and again.",
            estimated_minutes=13,
            steps=[
                StepDef(
                    slug="theme-variations-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Theme and variations\n\n"
                            "**Theme and variations** states a clear, usually simple "
                            "**theme**, then follows it with a series of "
                            "**variations**, each one transforming the theme in a "
                            "different way while keeping something recognizable "
                            "underneath - most often its harmonic plan (the "
                            "underlying chord progression) or its phrase structure, "
                            "even when the melody itself is decorated beyond easy "
                            "recognition.\n\n"
                            "Typical variation techniques include:\n\n"
                            "- **Melodic decoration/embellishment** - filling in the "
                            "theme's melody with faster figuration around the same "
                            "harmonic skeleton.\n"
                            "- **Changing mode** - a variation in the parallel minor "
                            "(or major) of an otherwise unchanged harmonic plan.\n"
                            "- **Changing texture or accompaniment** - the same "
                            "harmony, presented in a new figuration pattern (broken "
                            "chords, a walking bass, a new countermelody).\n"
                            "- **Changing tempo or meter** - slowing a variation "
                            "into an expressive, ornamented adagio, or recasting it "
                            "in a new meter entirely.\n\n"
                            "Because so much can change on the surface, the "
                            "underlying harmonic plan is what actually holds a set "
                            "of variations together - a listener can lose the "
                            "melody entirely and still track the form by ear "
                            "through the recurring chord progression."
                        )
                    },
                    topics=["theme-and-variations"],
                ),
                StepDef(
                    slug="theme-variations-quiz-what-stays",
                    kind="quiz",
                    payload={
                        "question": (
                            "In theme and variations, what most reliably stays "
                            "recognizable across variations even when the melody is "
                            "heavily decorated?"
                        ),
                        "choices": [
                            "The underlying harmonic plan (chord progression) or "
                            "phrase structure",
                            "The exact rhythm of the melody",
                            "The instrumentation",
                            "The tempo, which never changes",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The harmonic skeleton (and/or phrase structure) is "
                            "what typically survives from variation to variation, "
                            "even when the surface melody is transformed beyond "
                            "easy recognition."
                        ),
                    },
                    topics=["theme-and-variations"],
                ),
                StepDef(
                    slug="theme-variations-quiz-technique",
                    kind="quiz",
                    payload={
                        "question": (
                            "Recasting a variation's harmonic plan in the parallel "
                            "minor is an example of which variation technique?"
                        ),
                        "choices": [
                            "Changing mode",
                            "Melodic decoration",
                            "Changing meter",
                            "Retrograde inversion",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "Shifting a variation into the parallel minor (or "
                            "major), while keeping the harmonic plan otherwise "
                            "intact, is a change of mode."
                        ),
                    },
                    topics=["theme-and-variations"],
                ),
            ],
        ),
        LessonDef(
            slug="motivic-development-techniques",
            title="Motivic Development Techniques",
            summary="Growing a whole passage out of one small musical idea.",
            estimated_minutes=14,
            steps=[
                StepDef(
                    slug="motivic-development-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Motivic development techniques\n\n"
                            "A **motive** is a short, distinctive musical idea - "
                            "sometimes just a few notes - that a composer can grow "
                            "an entire passage out of by transforming it in "
                            "systematic ways. Recognizing a motive as it's "
                            "developed, rather than as literal repetition, is a key "
                            "skill in following how a piece unfolds.\n\n"
                            "Common development techniques include:\n\n"
                            "- **Repetition** - restating the motive exactly, often "
                            "to establish it before it changes.\n"
                            "- **Sequence** - repeating the motive at a new pitch "
                            "level, preserving its contour and rhythm.\n"
                            "- **Fragmentation** - using only a piece of the motive, "
                            "rather than the whole thing, often to build momentum.\n"
                            "- **Augmentation** - stretching the motive into longer "
                            "note values.\n"
                            "- **Diminution** - compressing the motive into shorter "
                            "note values.\n"
                            "- **Inversion** - flipping the motive's melodic "
                            "contour upside down (each interval's direction "
                            "reversed).\n"
                            "- **Retrograde** - playing the motive's notes in "
                            "reverse order.\n\n"
                            "A skilled composer often layers several of these at "
                            "once - a fragment of a motive, augmented and inverted, "
                            "is still recognizably connected to its source even "
                            "though very little of the original surface remains."
                        )
                    },
                    topics=["motivic-development"],
                ),
                StepDef(
                    slug="motivic-development-quiz-sequence",
                    kind="quiz",
                    payload={
                        "question": (
                            "Repeating a motive at a new pitch level, keeping its "
                            "contour and rhythm intact, is called:"
                        ),
                        "choices": ["Sequence", "Retrograde", "Augmentation", "Inversion"],
                        "answer_index": 0,
                        "explanation": (
                            "A sequence restates the motive's shape at a different "
                            "pitch level - the classic building block of "
                            "developmental passages."
                        ),
                    },
                    topics=["motivic-development"],
                ),
                StepDef(
                    slug="motivic-development-quiz-inversion-retrograde",
                    kind="quiz",
                    payload={
                        "question": (
                            "What is the difference between melodic inversion and "
                            "retrograde as motivic development techniques?"
                        ),
                        "choices": [
                            "Inversion flips each interval's direction upside "
                            "down; retrograde plays the notes in reverse order",
                            "They are two names for the same technique",
                            "Inversion changes only rhythm; retrograde changes "
                            "only pitch",
                            "Retrograde only applies to harmony, never melody",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "Inversion mirrors the motive's contour (up becomes "
                            "down and vice versa); retrograde reverses the order "
                            "the notes are played in - genuinely different "
                            "transformations."
                        ),
                    },
                    topics=["motivic-development"],
                ),
            ],
        ),
        LessonDef(
            slug="writing-a-complete-short-piece",
            title="Writing a Complete Short Piece",
            summary="Bringing form, melody, and harmony together into one finished piece.",
            estimated_minutes=25,
            steps=[
                StepDef(
                    slug="writing-a-short-piece-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Writing a complete short piece\n\n"
                            "Everything from this course comes together in a single "
                            "act of composition: a short piece is, at heart, a "
                            "**phrase structure** (an antecedent phrase and a "
                            "consequent phrase, together forming a small binary or "
                            "rounded-binary shape) realized through **melodic "
                            "writing** that behaves itself (mostly stepwise, leaps "
                            "recovered, staying inside the key) and closed off by a "
                            "**cadence** strong enough to feel like an ending.\n\n"
                            "A practical checklist for a short two-phrase piece:\n\n"
                            "- Choose a key and a time signature, and stay in them.\n"
                            "- Write an **antecedent** phrase that moves away from "
                            "home - often pausing on a half cadence, or otherwise "
                            "left open rather than fully resolved.\n"
                            "- Write a **consequent** phrase that answers it, "
                            "using similar or related melodic material, and this "
                            "time closing with a full **perfect authentic "
                            "cadence** - the strongest possible ending.\n"
                            "- Keep melodic leaps recovered by step, stay "
                            "diatonic unless a chromatic gesture is a deliberate "
                            "choice, and keep the whole line within a comfortable "
                            "range.\n\n"
                            "None of this requires new machinery - it's the same "
                            "melodic and cadential tools from earlier in the course, "
                            "now all applied at once, in service of a single, "
                            "complete, satisfying whole."
                        )
                    },
                    topics=["writing-a-short-piece"],
                ),
                StepDef(
                    slug="writing-a-short-piece-quiz-antecedent",
                    kind="quiz",
                    payload={
                        "question": (
                            "In a classic antecedent-consequent phrase pair, what "
                            "typically happens at the end of the antecedent phrase?"
                        ),
                        "choices": [
                            "It pauses on a half cadence or is otherwise left open",
                            "It ends with the strongest possible perfect "
                            "authentic cadence",
                            "It modulates permanently to a new key",
                            "It repeats the consequent phrase exactly",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The antecedent poses the question - typically pausing "
                            "on a half cadence - so the consequent phrase can "
                            "answer it with a full, conclusive close."
                        ),
                    },
                    topics=["writing-a-short-piece"],
                ),
                StepDef(
                    slug="writing-a-short-piece-task",
                    kind="composition",
                    payload={
                        "brief": (
                            "Write a complete eight-measure short piece in C major: "
                            "an antecedent phrase (measures 1-4) followed by a "
                            "consequent phrase (measures 5-8) that closes with a "
                            "perfect authentic cadence. Keep the melody diatonic, "
                            "keep leaps recovered by step, and stay within a "
                            "reasonable range."
                        ),
                        "requirements": [
                            {"type": "key", "key": "C major"},
                            {"type": "time_signature", "value": "4/4"},
                            {"type": "measure_count", "count": 8},
                            {"type": "diatonic_only"},
                            {"type": "max_leap", "semitones": 9},
                            {"type": "leap_recovery", "max_unresolved": 1},
                            {"type": "cadence", "cadence": "perfect_authentic"},
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
                                    "measures": _blank_measures(8, "soprano-voice"),
                                },
                                {
                                    "id": "bass",
                                    "clef": "bass",
                                    "measures": _blank_measures(8, "bass-voice"),
                                },
                            ],
                        },
                    },
                    topics=["writing-a-short-piece"],
                ),
            ],
        ),
    ],
)
