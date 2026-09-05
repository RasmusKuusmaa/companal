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
        LessonDef(
            slug="simple-and-compound-meter",
            title="Simple and Compound Meter",
            summary="How a beat divides in two or in three, and what a signature says about it.",
            estimated_minutes=12,
            steps=[
                StepDef(
                    slug="simple-compound-meter-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Simple and compound meter\n\n"
                            "A meter describes two things: how many beats are in a measure, "
                            "and how each beat divides into smaller notes.\n\n"
                            "## Simple meter\n\n"
                            "In **simple** meter, each beat divides naturally into **two** "
                            "equal parts. 2/4, 3/4 and 4/4 are simple duple, simple triple "
                            "and simple quadruple - the top number is literally the number "
                            "of beats, and the bottom number names the note value that gets "
                            "one beat (4 = quarter note).\n\n"
                            "## Compound meter\n\n"
                            "In **compound** meter, each beat instead divides into **three** "
                            "equal parts, and that beat is written as a dotted note. 6/8, "
                            "9/8 and 12/8 are compound duple, compound triple and compound "
                            "quadruple - here the top number counts eighth notes, not beats, "
                            "so the actual beat count is the top number divided by 3. 6/8 "
                            "has 2 beats (two groups of three eighths), each a dotted "
                            "quarter note long.\n\n"
                            "## Telling them apart\n\n"
                            "The fastest test: if the top number is 6, 9 or 12, the meter is "
                            "compound and divides into three. Otherwise it's simple and "
                            "divides into two."
                        )
                    },
                    topics=["simple-and-compound-meter"],
                ),
                StepDef(
                    slug="simple-compound-meter-quiz-beats",
                    kind="quiz",
                    payload={
                        "question": "In 6/8 time, how many beats are in each measure?",
                        "choices": ["6", "3", "2", "8"],
                        "answer_index": 2,
                        "explanation": (
                            "6/8 groups its six eighth notes into two sets of three, so "
                            "there are 2 beats per measure, each a dotted quarter note long."
                        ),
                    },
                    topics=["simple-and-compound-meter"],
                ),
                StepDef(
                    slug="simple-compound-meter-quiz-classify",
                    kind="quiz",
                    payload={
                        "question": "Which of these time signatures is compound triple?",
                        "choices": ["3/4", "9/8", "4/4", "2/4"],
                        "answer_index": 1,
                        "explanation": (
                            "9/8 groups nine eighth notes into three sets of three - three "
                            "beats, each dividing into three - which makes it compound "
                            "triple."
                        ),
                    },
                    topics=["simple-and-compound-meter"],
                ),
                StepDef(
                    slug="simple-compound-meter-task",
                    kind="composition",
                    payload={
                        "brief": "Write a four-measure melody in 6/8 time.",
                        "requirements": [
                            {"type": "time_signature", "value": "6/8"},
                            {"type": "measure_count", "count": 4},
                        ],
                    },
                    topics=["simple-and-compound-meter"],
                ),
            ],
        ),
        LessonDef(
            slug="irregular-meter-and-anacrusis",
            title="Irregular Meter and Anacrusis",
            summary="Asymmetrical groupings and pickup notes that begin before the downbeat.",
            estimated_minutes=10,
            steps=[
                StepDef(
                    slug="irregular-meter-anacrusis-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Irregular meter and anacrusis\n\n"
                            "## Irregular meter\n\n"
                            "Not every meter divides evenly into twos or threes. "
                            "**Irregular** (or asymmetrical) meters like 5/4 and 7/8 mix "
                            "groups of two and three beats within the same measure. A 5/4 "
                            "measure is usually felt as 3+2 or 2+3; a 7/8 measure as "
                            "2+2+3, 3+2+2 or 2+3+2. The grouping isn't arbitrary - it's "
                            "chosen by the composer and often marked in the score, and it "
                            "changes where the strong beats fall.\n\n"
                            "## Anacrusis\n\n"
                            "A phrase doesn't have to start on beat one. An **anacrusis** - "
                            "a pickup note or notes - leads into the first downbeat from "
                            "before it, borrowing time rather than adding it: the note "
                            "values in the pickup measure and the final measure of the "
                            "phrase together add up to one full measure, as if the last "
                            "measure lent the first one its missing beats. Countless "
                            "melodies begin this way - think of a tune that starts on an "
                            "upbeat rather than landing squarely on beat one."
                        )
                    },
                    topics=["irregular-meter-and-anacrusis"],
                ),
                StepDef(
                    slug="irregular-meter-anacrusis-quiz-grouping",
                    kind="quiz",
                    payload={
                        "question": "A 7/8 measure is most naturally grouped as:",
                        "choices": [
                            "2+2+3 (or another mix of twos and threes)",
                            "Seven equal quarter notes",
                            "3+4+1",
                            "One long undivided beat",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "7/8 doesn't divide evenly into twos or threes alone, so it "
                            "mixes them - commonly 2+2+3, though 3+2+2 and 2+3+2 are just "
                            "as valid depending on where the composer wants the accents."
                        ),
                    },
                    topics=["irregular-meter-and-anacrusis"],
                ),
                StepDef(
                    slug="irregular-meter-anacrusis-quiz-pickup",
                    kind="quiz",
                    payload={
                        "question": "What is an anacrusis?",
                        "choices": [
                            "A note played deliberately out of tune",
                            "A pickup note or notes before the first full measure",
                            "A rest that closes out a piece",
                            "A written-out slowing down at a cadence",
                        ],
                        "answer_index": 1,
                        "explanation": (
                            "An anacrusis is the pickup - one or more notes that lead into "
                            "the first downbeat from before the first full measure begins."
                        ),
                    },
                    topics=["irregular-meter-and-anacrusis"],
                ),
                StepDef(
                    slug="irregular-meter-anacrusis-task",
                    kind="composition",
                    payload={
                        "brief": (
                            "Write a four-measure phrase in 4/4 that begins with a "
                            "one-beat pickup."
                        ),
                        "requirements": [
                            {"type": "time_signature", "value": "4/4"},
                            {"type": "measure_count", "count": 4},
                        ],
                    },
                    topics=["irregular-meter-and-anacrusis"],
                ),
            ],
        ),
        LessonDef(
            slug="major-scales-and-key-signatures",
            title="Major Scales and Key Signatures",
            summary="Building major scales and reading the key signatures that name them.",
            estimated_minutes=12,
            steps=[
                StepDef(
                    slug="major-scales-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Major scales and key signatures\n\n"
                            "A major scale is built from a fixed pattern of whole steps "
                            "(W) and half steps (H): **W-W-H-W-W-W-H**. Starting on C and "
                            "following that pattern uses only the white keys - C-D-E-F-"
                            "G-A-B-C - which is why C major has no sharps or flats.\n\n"
                            "Start the same pattern on any other note and some steps land "
                            "on black keys instead, which is exactly what a **key "
                            "signature** records: the sharps or flats needed to keep that "
                            "same W-W-H-W-W-W-H shape starting from a different note.\n\n"
                            "## The order of sharps and flats\n\n"
                            "Sharps are always added in the order **F-C-G-D-A-E-B**, and "
                            "flats in the exact reverse, **B-E-A-D-G-C-F**. G major has one "
                            "sharp (F#); D major has two (F#, C#); F major has one flat "
                            "(Bb); Bb major has two (Bb, Eb). Each new sharp or flat is "
                            "added to all the ones before it, never replacing them."
                        )
                    },
                    topics=["major-scales-and-key-signatures"],
                ),
                StepDef(
                    slug="major-scales-quiz-pattern",
                    kind="quiz",
                    payload={
                        "question": "What is the whole-step/half-step pattern of a major scale?",
                        "choices": [
                            "W-W-H-W-W-W-H",
                            "W-H-W-W-H-W-W",
                            "H-W-W-H-W-W-W",
                            "W-W-W-H-W-W-H",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "Every major scale follows whole-whole-half-whole-whole-whole-"
                            "half, wherever it starts - that's what makes it a major scale."
                        ),
                    },
                    topics=["major-scales-and-key-signatures"],
                ),
                StepDef(
                    slug="major-scales-quiz-d-major",
                    kind="quiz",
                    payload={
                        "question": "How many sharps does D major have?",
                        "choices": ["1", "2", "3", "0"],
                        "answer_index": 1,
                        "explanation": (
                            "Following the sharp order F-C-G-D-A-E-B, D major needs the "
                            "first two: F# and C#."
                        ),
                    },
                    topics=["major-scales-and-key-signatures"],
                ),
                StepDef(
                    slug="major-scales-task",
                    kind="composition",
                    payload={
                        "brief": "Write a one-octave ascending C major scale in quarter notes.",
                        "requirements": [
                            {"type": "key", "key": "C major"},
                            {"type": "diatonic_only"},
                            {"type": "required_scale_degrees", "degrees": [1, 2, 3, 4, 5, 6, 7]},
                            {"type": "measure_count", "count": 2},
                        ],
                    },
                    topics=["major-scales-and-key-signatures"],
                ),
            ],
        ),
        LessonDef(
            slug="minor-scales-natural-harmonic-melodic",
            title="Minor Scales: Natural, Harmonic and Melodic",
            summary="The three forms of minor and why each one exists.",
            estimated_minutes=12,
            steps=[
                StepDef(
                    slug="minor-scales-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Minor scales: natural, harmonic and melodic\n\n"
                            "## Natural minor\n\n"
                            "The **natural minor** scale is the pattern W-H-W-W-H-W-W. It "
                            "shares a key signature with a major scale a minor third above "
                            "it - A natural minor uses exactly the same notes as C major, "
                            "just starting from A.\n\n"
                            "## Harmonic minor\n\n"
                            "Natural minor's 7th scale degree sits a whole step below the "
                            "tonic, which is a weak pull home. **Harmonic minor** raises "
                            "that 7th degree by a half step, turning it into a proper "
                            "leading tone a half step below the tonic - at the cost of an "
                            "unusual augmented second between the (unraised) 6th degree "
                            "and the (raised) 7th.\n\n"
                            "## Melodic minor\n\n"
                            "**Melodic minor** smooths that awkward gap by raising the 6th "
                            "degree too, but only going **up**. Coming back down, both "
                            "raised degrees revert, and melodic minor descending is "
                            "identical to natural minor. This asymmetry exists purely for "
                            "melodic smoothness - the raised 6th and 7th pull upward toward "
                            "the tonic, and there's no need for that pull on the way back "
                            "down."
                        )
                    },
                    topics=["minor-scales"],
                ),
                StepDef(
                    slug="minor-scales-quiz-harmonic",
                    kind="quiz",
                    payload={
                        "question": (
                            "Which scale degree does harmonic minor raise, compared to "
                            "natural minor?"
                        ),
                        "choices": ["The 7th", "The 6th", "Both the 6th and 7th", "The 3rd"],
                        "answer_index": 0,
                        "explanation": (
                            "Harmonic minor raises only the 7th degree, turning it into a "
                            "true leading tone a half step below the tonic."
                        ),
                    },
                    topics=["minor-scales"],
                ),
                StepDef(
                    slug="minor-scales-quiz-melodic-descending",
                    kind="quiz",
                    payload={
                        "question": "Descending, melodic minor is identical to:",
                        "choices": [
                            "Harmonic minor",
                            "Natural minor",
                            "The parallel major",
                            "The Dorian mode",
                        ],
                        "answer_index": 1,
                        "explanation": (
                            "Melodic minor only raises the 6th and 7th degrees ascending; "
                            "coming back down, both revert and it matches natural minor "
                            "exactly."
                        ),
                    },
                    topics=["minor-scales"],
                ),
                StepDef(
                    slug="minor-scales-task",
                    kind="composition",
                    payload={
                        "brief": (
                            "Write a one-octave ascending A natural minor scale in quarter "
                            "notes."
                        ),
                        "requirements": [
                            {"type": "key", "key": "a minor"},
                            {"type": "diatonic_only"},
                            {"type": "required_scale_degrees", "degrees": [1, 2, 3, 4, 5, 6, 7]},
                            {"type": "measure_count", "count": 2},
                        ],
                    },
                    topics=["minor-scales"],
                ),
            ],
        ),
        LessonDef(
            slug="intervals-number-quality-and-inversion",
            title="Intervals: Number, Quality and Inversion",
            summary="Naming the distance between two pitches and what happens when it inverts.",
            estimated_minutes=12,
            steps=[
                StepDef(
                    slug="intervals-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Intervals: number, quality and inversion\n\n"
                            "An interval names the distance between two pitches with two "
                            "pieces of information: a **number** and a **quality**.\n\n"
                            "## Number\n\n"
                            "Count the letter names from the lower note to the higher one, "
                            "inclusive. C up to G is C-D-E-F-G: five letters, so it's some "
                            "kind of fifth. C up to E is C-D-E: three letters, a third.\n\n"
                            "## Quality\n\n"
                            "Unisons, fourths, fifths and octaves can be **perfect**, "
                            "**augmented** or **diminished**. Seconds, thirds, sixths and "
                            "sevenths can be **major**, **minor**, **augmented** or "
                            "**diminished**. Major is a half step larger than minor; "
                            "augmented is a half step larger than perfect or major; "
                            "diminished is a half step smaller than perfect or minor.\n\n"
                            "## Inversion\n\n"
                            "Move the lower note up an octave (or the upper note down one) "
                            "and the interval **inverts**. The numbers always add up to 9: "
                            "a second inverts to a seventh, a third to a sixth, a fourth to "
                            "a fifth. Quality flips too, but perfect stays perfect: major "
                            "becomes minor, minor becomes major, augmented becomes "
                            "diminished, and diminished becomes augmented."
                        )
                    },
                    topics=["intervals"],
                ),
                StepDef(
                    slug="intervals-quiz-c-to-g",
                    kind="quiz",
                    payload={
                        "question": "What is the interval from C up to G?",
                        "choices": [
                            "Perfect fourth",
                            "Perfect fifth",
                            "Major sixth",
                            "Minor fifth",
                        ],
                        "answer_index": 1,
                        "explanation": (
                            "C-D-E-F-G is five letter names, and the natural white-key "
                            "distance from C to G is a perfect fifth (7 semitones)."
                        ),
                    },
                    topics=["intervals"],
                ),
                StepDef(
                    slug="intervals-quiz-inversion",
                    kind="quiz",
                    payload={
                        "question": "A major third inverts to a:",
                        "choices": [
                            "Minor sixth",
                            "Major sixth",
                            "Perfect sixth",
                            "Diminished sixth",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "A third inverts to a sixth (3 + 6 = 9), and major inverts to "
                            "minor - so a major third inverts to a minor sixth."
                        ),
                    },
                    topics=["intervals"],
                ),
            ],
        ),
    ],
)
