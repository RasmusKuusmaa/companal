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
    ExamDef(
        slug="voice-leading-exam",
        title="Voice Leading Exam",
        description=(
            "Four-part texture, the parallel prohibitions, connecting triads, "
            "the six-four chord, dominant sevenths, and non-chord tones."
        ),
        course_slug="voice-leading",
        questions=[
            ExamQuestionDef(
                slug="voice-leading-exam-parallels",
                kind="quiz",
                payload={
                    "question": (
                        "Which motion between two voices is forbidden when it "
                        "produces two consecutive perfect fifths or octaves?"
                    ),
                    "choices": [
                        "Parallel motion",
                        "Contrary motion",
                        "Oblique motion",
                        "Similar motion by step",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "Parallel perfect fifths or octaves - both voices moving "
                        "the same direction by the same perfect interval - are "
                        "forbidden in standard four-part voice leading."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="voice-leading-exam-doubling",
                kind="quiz",
                payload={
                    "question": (
                        "In a first-inversion vii°6 chord, which note is "
                        "conventionally doubled instead of the bass?"
                    ),
                    "choices": [
                        "The bass note is not doubled; another chord tone is "
                        "doubled instead",
                        "The bass note is always doubled",
                        "The chord's fifth is always omitted entirely",
                        "The root is always doubled, even though it's diminished",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "vii°6's bass is the chord's third (the leading tone), "
                        "which shouldn't be doubled - another chord tone is "
                        "doubled instead, the standard exception to 'double the "
                        "bass in first inversion'."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="voice-leading-exam-six-four",
                kind="quiz",
                payload={
                    "question": (
                        "A six-four chord that sits between two statements of "
                        "the same root-position chord, approached and left by "
                        "step in the bass, is called a:"
                    ),
                    "choices": [
                        "Passing six-four",
                        "Cadential six-four",
                        "Pedal six-four",
                        "Neapolitan six-four",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "A passing six-four connects two chords a step apart in "
                        "the bass by filling in the space between them."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="voice-leading-exam-dominant-seventh",
                kind="quiz",
                payload={
                    "question": (
                        "In a V7-I resolution, the chordal seventh normally "
                        "resolves by:"
                    ),
                    "choices": [
                        "Stepping down",
                        "Leaping up a fourth",
                        "Staying on the same note",
                        "Stepping up",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "The dominant seventh's chordal seventh is a dissonance "
                        "that resolves down by step into the tonic chord."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="voice-leading-exam-nct",
                kind="quiz",
                payload={
                    "question": (
                        "A non-chord tone approached by step and left by step "
                        "in the same direction is called a:"
                    ),
                    "choices": [
                        "Passing tone",
                        "Neighbor tone",
                        "Suspension",
                        "Appoggiatura",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "A passing tone fills in the space between two chord "
                        "tones a third apart, approached and left by step in "
                        "the same direction."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="voice-leading-exam-harmonization-task",
                kind="composition",
                payload={
                    "brief": (
                        "The soprano line below is given and locked. Add alto, "
                        "tenor and bass parts to harmonize it in four-part "
                        "texture, ending with a perfect authentic cadence."
                    ),
                    "requirements": [
                        {"type": "key", "key": "G major"},
                        {"type": "measure_count", "count": 4},
                        {"type": "cadence", "cadence": "perfect_authentic"},
                    ],
                    "starter_notation": {
                        "fifths": 1,
                        "mode": "major",
                        "time": {"beats": 4, "beat_type": 4},
                        "tempo": 90,
                        "staves": [
                            {
                                "id": "soprano",
                                "clef": "treble",
                                "measures": [
                                    {
                                        "id": f"m{i}",
                                        "voices": [
                                            {
                                                "id": "soprano-voice",
                                                "notes": [
                                                    {
                                                        "id": f"soprano-voice-{i}",
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
                                        [("B", 4), ("C", 5), ("A", 4), ("G", 4)]
                                    )
                                ],
                            },
                            {
                                "id": "alto",
                                "clef": "treble",
                                "measures": [
                                    {
                                        "id": f"m{i}",
                                        "voices": [
                                            {
                                                "id": "alto-voice",
                                                "notes": [
                                                    {
                                                        "id": f"alto-voice-{i}",
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
                                    for i in range(4)
                                ],
                            },
                            {
                                "id": "tenor",
                                "clef": "bass",
                                "measures": [
                                    {
                                        "id": f"m{i}",
                                        "voices": [
                                            {
                                                "id": "tenor-voice",
                                                "notes": [
                                                    {
                                                        "id": f"tenor-voice-{i}",
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
                                    for i in range(4)
                                ],
                            },
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
                                                        "id": f"bass-voice-{i}",
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
                                    for i in range(4)
                                ],
                            },
                        ],
                    },
                    "locked_staff_indices": [0],
                },
            ),
        ],
    ),
    ExamDef(
        slug="line-and-counterpoint-exam",
        title="Line and Counterpoint Exam",
        description=(
            "Melodic construction, phrase structure, cadence types, and "
            "first species counterpoint."
        ),
        course_slug="line-and-counterpoint",
        questions=[
            ExamQuestionDef(
                slug="counterpoint-exam-tendency-tones",
                kind="quiz",
                payload={
                    "question": (
                        "A tendency tone, such as the leading tone, is best "
                        "described as a note that:"
                    ),
                    "choices": [
                        "Wants to resolve in a particular direction, most often "
                        "by step",
                        "Can be approached or left in any direction with equal "
                        "ease",
                        "Must always be doubled",
                        "Only occurs in minor keys",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "A tendency tone - the leading tone chief among them - "
                        "has a strong pull toward a specific resolution, "
                        "usually a stepwise one."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="counterpoint-exam-phrase-structure",
                kind="quiz",
                payload={
                    "question": (
                        "A period is best described as a pair of phrases where:"
                    ),
                    "choices": [
                        "The antecedent poses a question (often a half "
                        "cadence) and the consequent answers it with a more "
                        "conclusive cadence",
                        "Both phrases are harmonically and melodically "
                        "identical",
                        "The two phrases are unrelated in melodic material",
                        "Only the first phrase contains a cadence",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "A period pairs an open antecedent with a more "
                        "conclusive consequent, forming a small "
                        "question-and-answer structure."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="counterpoint-exam-cadence-strength",
                kind="quiz",
                payload={
                    "question": "Which cadence is the most conclusive close?",
                    "choices": [
                        "Perfect authentic cadence",
                        "Half cadence",
                        "Deceptive cadence",
                        "Plagal cadence",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "Root-position V to root-position I, with the soprano "
                        "landing on the tonic, is the strongest, most final "
                        "cadence in the common-practice vocabulary."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="counterpoint-exam-first-species-rule",
                kind="quiz",
                payload={
                    "question": (
                        "In first species counterpoint, what governs every "
                        "interval against the cantus firmus?"
                    ),
                    "choices": [
                        "It must be consonant",
                        "It must alternate consonant and dissonant",
                        "It must always be a perfect interval",
                        "It has no restriction at all",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "With one note against one note, first species has no "
                        "room to prepare or resolve a dissonance - every "
                        "interval must simply be consonant."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="counterpoint-exam-species-task",
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
                                    for i, step in enumerate(
                                        ["C", "D", "E", "F", "E", "D", "C"]
                                    )
                                ],
                            },
                            {
                                "id": "counterpoint",
                                "clef": "treble",
                                "measures": [
                                    {
                                        "id": f"m{i}",
                                        "voices": [
                                            {
                                                "id": "cp-voice",
                                                "notes": [
                                                    {
                                                        "id": f"cp-voice-{i}",
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
                                    for i in range(7)
                                ],
                            },
                        ],
                    },
                    "locked_staff_indices": [0],
                },
            ),
        ],
    ),
    ExamDef(
        slug="chromaticism-exam",
        title="Chromaticism Exam",
        description=(
            "Secondary dominants and leading-tone chords, tonicization versus "
            "modulation, pivot chords, modal mixture, the Neapolitan sixth, "
            "and augmented sixth chords."
        ),
        course_slug="chromaticism",
        questions=[
            ExamQuestionDef(
                slug="chromaticism-exam-secondary-dominant",
                kind="quiz",
                payload={
                    "question": "In C major, V/vi is built on which note?",
                    "choices": ["E", "A", "D", "G"],
                    "answer_index": 0,
                    "explanation": (
                        "V/vi tonicizes vi (A minor), and the dominant of A "
                        "minor is built on E."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="chromaticism-exam-secondary-leading-tone",
                kind="quiz",
                payload={
                    "question": (
                        "A secondary leading-tone chord differs from the "
                        "matching secondary dominant in that it is built as a:"
                    ),
                    "choices": [
                        "Diminished triad or diminished seventh chord",
                        "Major triad",
                        "Augmented triad",
                        "Half-diminished seventh chord only",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "Where a secondary dominant is major or dominant "
                        "seventh, the matching secondary leading-tone chord is "
                        "diminished - a triad or a diminished seventh chord."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="chromaticism-exam-modulation-test",
                kind="quiz",
                payload={
                    "question": (
                        "What confirms that a passage has genuinely modulated "
                        "rather than merely tonicized a chord?"
                    ),
                    "choices": [
                        "A cadence establishing the new key",
                        "The presence of any accidental",
                        "A change of time signature",
                        "A change of tempo",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "A confirming cadence in the new key is the test that "
                        "separates a real modulation from a passing "
                        "tonicization."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="chromaticism-exam-pivot-chord",
                kind="quiz",
                payload={
                    "question": "A strong pivot chord for a modulation is one that:",
                    "choices": [
                        "Is diatonic in both the old key and the new key",
                        "Contains an accidental from the new key",
                        "Only exists in the new key",
                        "Is always a secondary dominant",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "The smoothest pivot chords are diatonic in both keys, "
                        "so nothing sounds chromatic at the moment of the pivot "
                        "itself."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="chromaticism-exam-modal-mixture",
                kind="quiz",
                payload={
                    "question": (
                        "In a major key, a borrowed bVI chord is drawn from:"
                    ),
                    "choices": [
                        "The parallel minor",
                        "The relative minor",
                        "The dominant key",
                        "The subdominant key",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "Modal mixture borrows chords from the parallel mode - "
                        "a major key's bVI comes from its parallel minor."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="chromaticism-exam-neapolitan",
                kind="quiz",
                payload={
                    "question": (
                        "The Neapolitan chord (N6) is a major triad built on "
                        "which scale degree, and in what inversion is it "
                        "normally found?"
                    ),
                    "choices": [
                        "The lowered 2nd scale degree, in first inversion",
                        "The lowered 6th scale degree, in root position",
                        "The raised 4th scale degree, in second inversion",
                        "The tonic, in root position",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "N6 is a major triad on the lowered supertonic, almost "
                        "always heard in first inversion with its third in the "
                        "bass."
                    ),
                },
            ),
            ExamQuestionDef(
                slug="chromaticism-exam-augmented-sixth",
                kind="quiz",
                payload={
                    "question": (
                        "Which augmented sixth chord is spelled enharmonically "
                        "identical to a dominant seventh chord?"
                    ),
                    "choices": [
                        "The German sixth",
                        "The Italian sixth",
                        "The French sixth",
                        "None of them are",
                    ],
                    "answer_index": 0,
                    "explanation": (
                        "The German sixth adds the lowered 3rd scale degree, "
                        "which spells exactly like a dominant seventh chord, "
                        "despite functioning as a predominant."
                    ),
                },
            ),
        ],
    ),
]
