"""Stage 0 - Fundamentals: notation, rhythm, scales and intervals.

Lessons land one at a time in their own commits; this module starts as the
shell `seed stage 0 fundamentals` creates and grows as each lands.
"""

from app.domains.learning.curriculum.definitions import CourseDef, LessonDef, StepDef

COURSE = CourseDef(
    slug="fundamentals",
    title="Fundamentals",
    description=(
        "Reading music and the raw material it's built from: the staff, rhythm, scales, "
        "intervals and modes."
    ),
    level="beginner",
    lessons=[
        LessonDef(
            slug="staff-clefs-and-ledger-lines",
            title="The Staff, Clefs and Ledger Lines",
            summary="Reading pitch from the five-line staff in treble, bass and the C-clefs.",
            estimated_minutes=10,
            steps=[
                StepDef(
                    slug="staff-clefs-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# The staff, clefs and ledger lines\n\n"
                            "Music is written on a **staff**: five horizontal lines and the "
                            "four spaces between them. Each line and space stands for one "
                            "pitch, but which pitch depends on the **clef** drawn at the "
                            "start of the staff.\n\n"
                            "## The treble clef\n\n"
                            "The treble (or G) clef curls around the second line from the "
                            "bottom, fixing that line as **G4**. From there the lines read "
                            "E-G-B-D-F (bottom to top) and the spaces read F-A-C-E. Treble "
                            "clef is used for melodies and instruments that sit above middle "
                            "C.\n\n"
                            "## The bass clef\n\n"
                            "The bass (or F) clef has two dots that bracket the second line "
                            "from the top, fixing that line as **F3**. The lines read "
                            "G-B-D-F-A and the spaces read A-C-E-G. Bass clef is used for "
                            "lower voices and instruments.\n\n"
                            "## The C-clefs\n\n"
                            "The alto clef points its center at the middle line, fixing it as "
                            "**middle C (C4)** - used for viola. The tenor clef points the "
                            "same symbol at the fourth line instead, also naming it C4 - used "
                            "for the upper range of cello, bassoon and trombone.\n\n"
                            "## Ledger lines\n\n"
                            "A pitch too high or too low for the staff gets its own short "
                            "**ledger line**, as if the staff briefly grew an extra line just "
                            "for that note. Middle C sits one ledger line below the treble "
                            "staff and one ledger line above the bass staff - the same pitch, "
                            "written from either side."
                        )
                    },
                    topics=["staff-clefs-ledger-lines"],
                ),
                StepDef(
                    slug="staff-clefs-quiz-treble",
                    kind="quiz",
                    payload={
                        "question": "In treble clef, which pitch does the clef's curl circle?",
                        "choices": ["F3", "G4", "C4", "A4"],
                        "answer_index": 1,
                        "explanation": (
                            "The treble clef is a stylized letter G, and its curl wraps "
                            "around the second line from the bottom - that line is G4."
                        ),
                    },
                    topics=["staff-clefs-ledger-lines"],
                ),
                StepDef(
                    slug="staff-clefs-quiz-middle-c",
                    kind="quiz",
                    payload={
                        "question": "Where does middle C sit on the bass staff?",
                        "choices": [
                            "On the middle line",
                            "One ledger line above the staff",
                            "One ledger line below the staff",
                            "On the top line",
                        ],
                        "answer_index": 1,
                        "explanation": (
                            "Middle C is just above the bass staff's top line (A3), so it "
                            "needs one ledger line above the staff - the mirror image of "
                            "where it sits below the treble staff."
                        ),
                    },
                    topics=["staff-clefs-ledger-lines"],
                ),
            ],
        ),
        LessonDef(
            slug="note-values-dots-ties-and-rests",
            title="Note Values, Dots, Ties and Rests",
            summary="Durations and silences, and how dots and ties extend them.",
            estimated_minutes=10,
            steps=[
                StepDef(
                    slug="note-values-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Note values, dots, ties and rests\n\n"
                            "Every note has a **duration** - how long it sounds - shown by "
                            "its shape. Each value is worth exactly half the one before it:\n\n"
                            "- **Whole note**: an open circle, worth 4 beats in 4/4.\n"
                            "- **Half note**: an open circle with a stem, worth 2 beats.\n"
                            "- **Quarter note**: a filled-in circle with a stem, worth 1 "
                            "beat.\n"
                            "- **Eighth note**: a filled circle with a stem and one flag "
                            "(or beam), worth half a beat.\n"
                            "- **Sixteenth note**: two flags or beams, worth a quarter of a "
                            "beat.\n\n"
                            "**Rests** are the same idea for silence - a whole rest, half "
                            "rest, quarter rest and so on, each lasting as long as the note "
                            "of the same name.\n\n"
                            "## Dots\n\n"
                            "A dot placed after a note adds **half that note's own value** "
                            "to it. A dotted half note is a half note (2 beats) plus a "
                            "quarter note (1 beat) - 3 beats total. A dotted quarter note is "
                            "a quarter (1 beat) plus an eighth (half a beat) - 1.5 beats.\n\n"
                            "## Ties\n\n"
                            "A **tie** is a curved line connecting two notes of the same "
                            "pitch, and it means: play this as one continuous sound lasting "
                            "both notes' durations added together. Ties are how a duration "
                            "that has no single symbol - or one that crosses a barline - gets "
                            "written down."
                        )
                    },
                    topics=["note-values-and-rests"],
                ),
                StepDef(
                    slug="note-values-quiz-dotted-half",
                    kind="quiz",
                    payload={
                        "question": "A dotted half note lasts as long as which combination?",
                        "choices": [
                            "A half note plus a quarter note",
                            "Two quarter notes",
                            "A whole note",
                            "Three eighth notes",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The dot adds half of the half note's own value (1 beat) to the "
                            "half note itself (2 beats), for 3 beats total - the same length "
                            "as a half note tied to a quarter note."
                        ),
                    },
                    topics=["note-values-and-rests"],
                ),
                StepDef(
                    slug="note-values-quiz-tie",
                    kind="quiz",
                    payload={
                        "question": (
                            "What does a tie between two notes of the same pitch mean?"
                        ),
                        "choices": [
                            "Play the second note more quietly",
                            "Slur smoothly between two different pitches",
                            "Combine both notes into one continuous sound",
                            "Repeat the note twice, staccato",
                        ],
                        "answer_index": 2,
                        "explanation": (
                            "A tie joins two notes of the same pitch into a single sound "
                            "whose duration is the sum of both notes - it never restrikes "
                            "the note."
                        ),
                    },
                    topics=["note-values-and-rests"],
                ),
            ],
        ),
    ],
)
