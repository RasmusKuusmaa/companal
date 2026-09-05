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
    ],
)
