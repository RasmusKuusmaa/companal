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
    ],
)
