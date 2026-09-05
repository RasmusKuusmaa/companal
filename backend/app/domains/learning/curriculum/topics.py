"""Every topic the skill map tracks, grouped by area.

One topic per lesson's own subject, plus `parallel-fifths-and-octaves` as
its own entry distinct from the broader `motion-types-and-parallels` lesson
it's introduced in - see `models.Topic`'s own docstring: a voice-leading
lesson teaches it, a counterpoint lesson leans on it, and half a dozen
composition tasks produce evidence about it independently of whichever
lesson a student learned it from (see `mastery.evidence_from_harmony_
analysis`, which reads this exact slug).
"""

from app.domains.learning.curriculum.definitions import TopicDef

TOPICS: list[TopicDef] = [
    # --- Fundamentals ------------------------------------------------- #
    TopicDef(
        slug="staff-clefs-ledger-lines",
        name="Staff, clefs and ledger lines",
        area="fundamentals",
        description="Reading pitch from the staff in treble, bass and the C-clefs.",
    ),
    TopicDef(
        slug="note-values-and-rests",
        name="Note values, dots, ties and rests",
        area="fundamentals",
        description="Durations and silences, and how dots and ties extend them.",
    ),
    TopicDef(
        slug="simple-and-compound-meter",
        name="Simple and compound meter",
        area="fundamentals",
        description="How a beat divides in two or in three, and what a signature says about it.",
    ),
    TopicDef(
        slug="irregular-meter-and-anacrusis",
        name="Irregular meter and anacrusis",
        area="fundamentals",
        description="Asymmetrical groupings and pickup notes that begin before the downbeat.",
    ),
    TopicDef(
        slug="major-scales-and-key-signatures",
        name="Major scales and key signatures",
        area="fundamentals",
        description="Building major scales and reading the key signatures that name them.",
    ),
    TopicDef(
        slug="minor-scales",
        name="Minor scales: natural, harmonic and melodic",
        area="fundamentals",
        description="The three forms of minor and why each one exists.",
    ),
    TopicDef(
        slug="intervals",
        name="Intervals: number, quality and inversion",
        area="fundamentals",
        description="Naming the distance between two pitches and what happens when it inverts.",
    ),
    TopicDef(
        slug="church-modes",
        name="The church modes",
        area="fundamentals",
        description="The seven modes as reorderings of the same diatonic collection.",
    ),
    # --- Harmony -------------------------------------------------------- #
    TopicDef(
        slug="triads",
        name="Triads and their qualities",
        area="harmony",
        description="Major, minor, diminished and augmented triads, and how to spell each.",
    ),
    TopicDef(
        slug="triad-inversions-and-figures",
        name="Triad inversions and figured bass symbols",
        area="harmony",
        description="Root position, first and second inversion, and the figures that name them.",
    ),
    TopicDef(
        slug="seventh-chords",
        name="Seventh chords and their figures",
        area="harmony",
        description="The five seventh-chord qualities and their inversion figures.",
    ),
    TopicDef(
        slug="roman-numerals-major",
        name="Roman numeral analysis in major",
        area="harmony",
        description="Labeling chords by scale degree and quality within a major key.",
    ),
    TopicDef(
        slug="roman-numerals-minor",
        name="Roman numeral analysis in minor",
        area="harmony",
        description="The same labeling in minor, where the raised leading tone complicates it.",
    ),
    TopicDef(
        slug="harmonic-function",
        name="Harmonic function and chord families",
        area="harmony",
        description="Tonic, predominant and dominant function, and which chords belong to each.",
    ),
    TopicDef(
        slug="figured-bass-realization",
        name="Realizing a figured bass",
        area="harmony",
        description="Turning a bass line and its figures into a full chord above it.",
    ),
    # --- Voice leading --------------------------------------------------- #
    TopicDef(
        slug="four-part-texture",
        name="Four-part texture: ranges, spacing and doubling",
        area="voice-leading",
        description="Keeping SATB writing within range, properly spaced, and sensibly doubled.",
    ),
    TopicDef(
        slug="motion-types-and-parallels",
        name="Types of motion and the parallel prohibitions",
        area="voice-leading",
        description="Parallel, similar, oblique and contrary motion, and why some are forbidden.",
    ),
    TopicDef(
        slug="parallel-fifths-and-octaves",
        name="Parallel fifths and octaves",
        area="voice-leading",
        description="The parallel-perfect-interval fault every voice-leading check watches for.",
    ),
    TopicDef(
        slug="connecting-root-position-triads",
        name="Connecting root position triads",
        area="voice-leading",
        description="Common-tone and stepwise connection between root position chords.",
    ),
    TopicDef(
        slug="first-inversion-triads",
        name="First inversion triads and doubling choices",
        area="voice-leading",
        description="Why the bass, not the root, usually gets doubled in first inversion.",
    ),
    TopicDef(
        slug="six-four-chords",
        name="The three uses of the six-four chord",
        area="voice-leading",
        description="Cadential, passing and pedal six-four chords, and how each is used.",
    ),
    TopicDef(
        slug="dominant-seventh-resolution",
        name="The dominant seventh and its resolution",
        area="voice-leading",
        description="Why the seventh falls and the leading tone rises when V7 resolves to I.",
    ),
    TopicDef(
        slug="non-chord-tones",
        name="Non-chord tones",
        area="voice-leading",
        description="Passing tones, neighbors, suspensions - notes outside the chord beneath them.",
    ),
    TopicDef(
        slug="harmonizing-a-soprano-line",
        name="Harmonizing a soprano line",
        area="voice-leading",
        description="Choosing a bass and inner voices to support a given melody.",
    ),
    TopicDef(
        slug="figured-bass-four-parts",
        name="Realizing a figured bass in four parts",
        area="voice-leading",
        description="Figured bass realization under the full weight of SATB voice-leading rules.",
    ),
    # --- Counterpoint ----------------------------------------------------- #
    TopicDef(
        slug="melodic-construction",
        name="Melodic construction and tendency tones",
        area="counterpoint",
        description="What makes a line singable, and which scale degrees pull toward resolution.",
    ),
    TopicDef(
        slug="phrase-structure",
        name="Phrase structure: period and sentence",
        area="counterpoint",
        description="The two classic ways short musical ideas combine into a phrase.",
    ),
    TopicDef(
        slug="cadence-types",
        name="Cadence types and their strength",
        area="counterpoint",
        description="Authentic, half, plagal and deceptive cadences, and how final each feels.",
    ),
    TopicDef(
        slug="first-species-counterpoint",
        name="First species counterpoint",
        area="counterpoint",
        description="Note-against-note writing against a cantus firmus.",
    ),
    TopicDef(
        slug="second-species-counterpoint",
        name="Second species counterpoint",
        area="counterpoint",
        description="Two notes against one, and the dissonant passing tone it allows.",
    ),
    TopicDef(
        slug="third-species-counterpoint",
        name="Third species counterpoint",
        area="counterpoint",
        description="Four notes against one, and the fuller dissonance treatment it allows.",
    ),
    TopicDef(
        slug="fourth-species-and-suspension",
        name="Fourth species and the suspension",
        area="counterpoint",
        description="Syncopated counterpoint built from prepared and resolved dissonance.",
    ),
    TopicDef(
        slug="florid-counterpoint",
        name="Florid counterpoint",
        area="counterpoint",
        description="Freely mixing every species' rhythms in one line.",
    ),
    # --- Chromaticism ------------------------------------------------------- #
    TopicDef(
        slug="secondary-dominants",
        name="Secondary dominants",
        area="chromaticism",
        description="Borrowing V of a scale degree other than the tonic to briefly tonicize it.",
    ),
    TopicDef(
        slug="secondary-leading-tone-chords",
        name="Secondary leading-tone chords",
        area="chromaticism",
        description="The diminished-seventh cousin of the secondary dominant.",
    ),
    TopicDef(
        slug="tonicization-vs-modulation",
        name="Tonicization versus modulation",
        area="chromaticism",
        description="Telling a brief chromatic detour apart from an actual change of key.",
    ),
    TopicDef(
        slug="pivot-chord-modulation",
        name="Pivot chord modulation",
        area="chromaticism",
        description="Modulating through a chord shared by the old and new key.",
    ),
    TopicDef(
        slug="modal-mixture",
        name="Modal mixture",
        area="chromaticism",
        description="Borrowing chords from the parallel major or minor.",
    ),
    TopicDef(
        slug="neapolitan-sixth",
        name="The Neapolitan sixth",
        area="chromaticism",
        description="The flat-two chord in first inversion, and its usual approach to V.",
    ),
    TopicDef(
        slug="augmented-sixth-chords",
        name="Augmented sixth chords",
        area="chromaticism",
        description="Italian, French and German sixths, and their pull toward the dominant.",
    ),
    # --- Form --------------------------------------------------------------- #
    TopicDef(
        slug="binary-and-ternary-form",
        name="Binary and ternary form",
        area="form",
        description="Two-part and three-part designs and how their sections relate.",
    ),
    TopicDef(
        slug="minuet-trio-rondo",
        name="Minuet and trio, and rondo",
        area="form",
        description="A ternary dance form and a form built from a recurring refrain.",
    ),
    TopicDef(
        slug="sonata-form",
        name="Sonata form",
        area="form",
        description="Exposition, development and recapitulation, and the keys each visits.",
    ),
    TopicDef(
        slug="theme-and-variations",
        name="Theme and variations",
        area="form",
        description="Restating one idea while systematically changing it.",
    ),
    TopicDef(
        slug="motivic-development",
        name="Motivic development techniques",
        area="form",
        description="Sequence, fragmentation, inversion and the other ways a motive gets reworked.",
    ),
    TopicDef(
        slug="writing-a-short-piece",
        name="Writing a complete short piece",
        area="form",
        description="Putting harmony, voice leading and form together into one finished piece.",
    ),
]
