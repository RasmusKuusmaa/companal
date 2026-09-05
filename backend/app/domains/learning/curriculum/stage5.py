"""Stage 5 - Form and composition: assembling everything into whole pieces."""

from app.domains.learning.curriculum.definitions import CourseDef, LessonDef, StepDef

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
    ],
)
