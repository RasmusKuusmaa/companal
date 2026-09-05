"""The exam registry: every authored exam, in the order they're seeded.

Mirrors `learning.curriculum`'s `COURSES` registry for the same reason - an
exam is written as Python data, not rows in a table, and `EXAMS` is what the
seed loader treats as authoritative (anything in the database whose slug
isn't found here is removed). Each stage exam's `course_slug` ties it back
to that stage's course in `learning.curriculum`; the comprehensive final
leaves `course_slug` unset, since it isn't scoped to one stage.
"""

from app.domains.exams.definitions import ExamDef, ExamQuestionDef

EXAMS: list[ExamDef] = [
    ExamDef(
        slug="fundamentals-exam",
        title="Fundamentals Exam",
        description=(
            "Clefs, note values, meter, scales, intervals and modes - the "
            "written vocabulary everything else in the course builds on."
        ),
        course_slug="fundamentals",
        questions=[
            ExamQuestionDef(
                slug="fundamentals-exam-clef",
                kind="quiz",
                payload={
                    "question": (
                        "Which clef is normally used for a cello's typical range?"
                    ),
                    "choices": ["Bass clef", "Treble clef", "Alto clef", "Tenor clef"],
                    "answer_index": 0,
                    "explanation": (
                        "The cello's normal range sits in the bass clef, though "
                        "it moves into tenor and treble clefs for its higher notes."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="fundamentals-exam-meter",
                kind="quiz",
                payload={
                    "question": "6/8 time is classified as:",
                    "choices": [
                        "Compound duple meter",
                        "Simple duple meter",
                        "Compound triple meter",
                        "Simple quadruple meter",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "6/8 groups two dotted-quarter beats, each subdividing "
                        "into three - compound duple meter."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="fundamentals-exam-key-signature",
                kind="quiz",
                payload={
                    "question": "How many sharps are in the key signature of D major?",
                    "choices": ["2", "1", "3", "0"],
                    "answer_index": 0,
                    "explanation": "D major's key signature has two sharps: F# and C#.",
                },
            ),
            ExamQuestionDef(
                slug="fundamentals-exam-minor-forms",
                kind="quiz",
                payload={
                    "question": (
                        "Which form of the minor scale raises both the 6th and "
                        "7th scale degrees on the way up, but not on the way down?"
                    ),
                    "choices": [
                        "Melodic minor",
                        "Natural minor",
                        "Harmonic minor",
                        "The major scale",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "Melodic minor raises both the 6th and 7th degrees "
                        "ascending, then reverts to natural minor descending."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="fundamentals-exam-interval",
                kind="quiz",
                payload={
                    "question": "The interval from C up to G is a:",
                    "choices": ["Perfect fifth", "Major sixth", "Perfect fourth", "Major fifth"],
                    "answer_index": 0,
                    "explanation": "C up to G spans seven semitones - a perfect fifth.",
                },
            ),
            ExamQuestionDef(
                slug="fundamentals-exam-mode",
                kind="quiz",
                payload={
                    "question": (
                        "Which church mode uses the same notes as C major but "
                        "starts and ends on D?"
                    ),
                    "choices": ["Dorian", "Phrygian", "Lydian", "Mixolydian"],
                    "answer_index": 0,
                    "explanation": (
                        "D to D on the white keys - the same collection as C "
                        "major - is the Dorian mode."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="fundamentals-exam-composition",
                kind="composition",
                payload={
                    "brief": (
                        "Write an eight-measure melody in G major, in 4/4 time, "
                        "using only notes diatonic to the key."
                    ),
                    "requirements": [
                        {"type": "key", "key": "G major"},
                        {"type": "time_signature", "value": "4/4"},
                        {"type": "measure_count", "count": 8},
                        {"type": "diatonic_only"},
                        {"type": "max_leap", "semitones": 9},
                        {"type": "leap_recovery", "max_unresolved": 1},
                    ],
                    "starter_notation": {
                        "fifths": 1,
                        "mode": "major",
                        "time": {"beats": 4, "beat_type": 4},
                        "tempo": 90,
                        "staves": [
                            {
                                "id": "melody",
                                "clef": "treble",
                                "measures": [
                                    {
                                        "id": f"m{i}",
                                        "voices": [
                                            {
                                                "id": "melody-voice",
                                                "notes": [
                                                    {
                                                        "id": f"melody-voice-{i}",
                                                        "step": "G",
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
                                    for i in range(8)
                                ],
                            }
                        ],
                    },
                },
            ),
        ],
    ),
]
