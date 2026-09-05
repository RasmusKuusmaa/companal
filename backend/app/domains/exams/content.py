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
    ExamDef(
        slug="chords-and-figures-exam",
        title="Chords and Figures Exam",
        description=(
            "Triads, inversions, figured bass, seventh chords, roman numerals "
            "and harmonic function."
        ),
        course_slug="chords-and-figures",
        questions=[
            ExamQuestionDef(
                slug="chords-exam-triad-quality",
                kind="quiz",
                payload={
                    "question": "A triad built C-Eb-Gb is:",
                    "choices": ["Diminished", "Minor", "Augmented", "Major"],
                    "answer_index": 0,
                    "explanation": (
                        "A minor third stacked on a minor third (C-Eb, Eb-Gb) "
                        "produces a diminished triad."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="chords-exam-inversion-figure",
                kind="quiz",
                payload={
                    "question": "A second-inversion triad is figured:",
                    "choices": ["6/4", "6", "7", "no figure at all"],
                    "answer_index": 0,
                    "explanation": (
                        "6/4 names the sixth and fourth above the bass, which "
                        "is the fifth of the chord sitting in the bass - second "
                        "inversion."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="chords-exam-seventh-chord-figure",
                kind="quiz",
                payload={
                    "question": (
                        "A seventh chord in third inversion (the seventh in the "
                        "bass) is figured:"
                    ),
                    "choices": ["4/2", "6/5", "4/3", "7"],
                    "answer_index": 0,
                    "explanation": (
                        "4/2 (often abbreviated 2) is third inversion - the "
                        "chord's seventh in the bass."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="chords-exam-roman-numeral-minor",
                kind="quiz",
                payload={
                    "question": (
                        "In natural minor, the roman numeral for the triad built "
                        "on the tonic is:"
                    ),
                    "choices": ["i", "I", "i°", "I+"],
                    "answer_index": 0,
                    "explanation": (
                        "The tonic triad in natural minor is a minor triad - "
                        "lowercase roman numeral i."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="chords-exam-harmonic-function",
                kind="quiz",
                payload={
                    "question": "Which chord family does ii belong to?",
                    "choices": ["Predominant", "Tonic", "Dominant", "None of these"],
                    "answer_index": 0,
                    "explanation": (
                        "ii is a predominant chord, typically preparing the "
                        "arrival of V."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="chords-exam-figured-bass-task",
                kind="composition",
                payload={
                    "brief": (
                        "The bass line below is given and locked. Add upper "
                        "notes that realize each measure's figure: blank, then "
                        "6, then blank, then 6, then blank again."
                    ),
                    "requirements": [
                        {
                            "type": "figured_bass",
                            "bass_staff_index": 0,
                            "figures": ["", "6", "", "6", ""],
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
                                                        "id": f"bass-{i}",
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
                                        [("C", 3), ("E", 3), ("F", 3), ("G", 3), ("C", 3)]
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
                                    for i in range(5)
                                ],
                            },
                        ],
                    },
                    "locked_staff_indices": [0],
                },
            ),
        ],
    ),
]
