"""Stage 4 - Chromaticism: tonicization, modulation, and borrowed chords."""

from app.domains.learning.curriculum.definitions import CourseDef, LessonDef, StepDef

COURSE = CourseDef(
    slug="chromaticism",
    title="Chromaticism",
    description=(
        "Stepping outside the diatonic collection: secondary chords, tonicization and "
        "modulation, modal mixture, and the Neapolitan and augmented sixth chords."
    ),
    level="advanced",
    lessons=[
        LessonDef(
            slug="secondary-dominants",
            title="Secondary Dominants",
            summary="Borrowing V of a scale degree other than the tonic to tonicize it.",
            estimated_minutes=14,
            steps=[
                StepDef(
                    slug="secondary-dominants-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Secondary dominants\n\n"
                            "Any major or minor triad in a key can be briefly treated "
                            "as if it were its own tonic, borrowing **its own dominant** "
                            "from outside the home key to lean on it - a technique "
                            "called **tonicization**, and the borrowed chord that does "
                            "the leaning is a **secondary dominant**.\n\n"
                            "A secondary dominant is labeled V/x - \"five of x\" - naming "
                            "which chord it's the dominant *of*. In C major, the "
                            "dominant of the dominant, **V/V**, is a D major triad (or "
                            "D7): the real dominant of G, borrowed to strengthen the "
                            "arrival on V. **V/ii** would be the dominant of D minor "
                            "(A major or A7); **V/vi**, the dominant of A minor (E major "
                            "or E7).\n\n"
                            "A secondary dominant almost always introduces a note "
                            "outside the home key's signature - specifically, the "
                            "**leading tone of the chord it's tonicizing**. That "
                            "accidental is the clearest signal, on the page, that a "
                            "secondary dominant is in play rather than a plain diatonic "
                            "chord."
                        )
                    },
                    topics=["secondary-dominants"],
                ),
                StepDef(
                    slug="secondary-dominants-quiz-v-of-v",
                    kind="quiz",
                    payload={
                        "question": "In C major, V/V is built on which note?",
                        "choices": ["D", "G", "A", "F"],
                        "answer_index": 0,
                        "explanation": (
                            "V/V is the dominant of G (C major's own V), and the "
                            "dominant of G is built on D."
                        ),
                    },
                    topics=["secondary-dominants"],
                ),
                StepDef(
                    slug="secondary-dominants-quiz-accidental",
                    kind="quiz",
                    payload={
                        "question": (
                            "A secondary dominant most often introduces an accidental "
                            "that is:"
                        ),
                        "choices": [
                            "The leading tone of the chord it's tonicizing",
                            "A note from the parallel minor",
                            "An arbitrary chromatic passing tone",
                            "Always a lowered 7th scale degree",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "A secondary dominant needs a real leading tone a half step "
                            "below whatever chord it's tonicizing, and that leading "
                            "tone is usually the accidental that gives it away."
                        ),
                    },
                    topics=["secondary-dominants"],
                ),
            ],
        ),
        LessonDef(
            slug="secondary-leading-tone-chords",
            title="Secondary Leading-Tone Chords",
            summary="The diminished-seventh cousin of the secondary dominant.",
            estimated_minutes=12,
            steps=[
                StepDef(
                    slug="secondary-leading-tone-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Secondary leading-tone chords\n\n"
                            "Every secondary dominant has a close relative built the "
                            "same way a plain vii° relates to V: a **secondary "
                            "leading-tone chord**, labeled vii°/x (or vii°7/x for the "
                            "seventh-chord form), sits a half step below whatever chord "
                            "it tonicizes, exactly like V/x does, but as a diminished "
                            "triad or diminished seventh instead of a major or dominant "
                            "seventh chord.\n\n"
                            "In C major, vii°7/V - the secondary leading-tone seventh "
                            "of G - is built on F#, a half step below G. It tonicizes V "
                            "the same way V/V does, and the two are often "
                            "interchangeable: a secondary leading-tone chord is a common "
                            "substitute for a secondary dominant, especially when a "
                            "smooth, stepwise bass line matters more than a leap to a "
                            "dominant root."
                        )
                    },
                    topics=["secondary-leading-tone-chords"],
                ),
                StepDef(
                    slug="secondary-leading-tone-quiz-viio7-of-v",
                    kind="quiz",
                    payload={
                        "question": "In C major, vii°7/V is built on which note?",
                        "choices": ["F#", "B", "D", "G"],
                        "answer_index": 0,
                        "explanation": (
                            "vii°7/V sits a half step below V's own root, G - that's F#."
                        ),
                    },
                    topics=["secondary-leading-tone-chords"],
                ),
                StepDef(
                    slug="secondary-leading-tone-quiz-function",
                    kind="quiz",
                    payload={
                        "question": (
                            "Secondary leading-tone chords serve the same tonicizing "
                            "function as:"
                        ),
                        "choices": [
                            "Secondary dominants",
                            "Plagal cadences",
                            "Neapolitan chords",
                            "Augmented sixth chords",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "A secondary leading-tone chord tonicizes exactly the same "
                            "target a matching secondary dominant would - it's built "
                            "from the leading tone instead of the root, but points at "
                            "the same chord."
                        ),
                    },
                    topics=["secondary-leading-tone-chords"],
                ),
            ],
        ),
        LessonDef(
            slug="tonicization-versus-modulation",
            title="Tonicization Versus Modulation",
            summary="Telling a brief chromatic detour apart from an actual change of key.",
            estimated_minutes=12,
            steps=[
                StepDef(
                    slug="tonicization-modulation-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Tonicization versus modulation\n\n"
                            "A secondary dominant tonicizes its target for a moment - "
                            "one chord, maybe two - and then the music simply carries on "
                            "in the original key. Nothing has actually changed; the "
                            "tonic never moved, it was only leaned on briefly from "
                            "somewhere else.\n\n"
                            "**Modulation** is different: the music genuinely settles "
                            "into a new key, and stays there long enough to be "
                            "confirmed - almost always by an authentic cadence *in the "
                            "new key*. That confirming cadence is the real test. A "
                            "secondary dominant that resolves and moves straight back to "
                            "the original tonic is tonicization; a secondary dominant "
                            "that instead leads into a cadence establishing a new tonic, "
                            "with the music continuing to center on it afterward, is a "
                            "modulation.\n\n"
                            "The chromatic material - the borrowed accidentals of a "
                            "secondary dominant - can look identical either way. What "
                            "tells them apart isn't the chord itself, it's what happens "
                            "next."
                        )
                    },
                    topics=["tonicization-vs-modulation"],
                ),
                StepDef(
                    slug="tonicization-modulation-quiz-difference",
                    kind="quiz",
                    payload={
                        "question": (
                            "What is the key difference between tonicization and "
                            "modulation?"
                        ),
                        "choices": [
                            "Modulation is confirmed by a cadence in the new key; "
                            "tonicization is brief and doesn't establish a new tonic",
                            "Modulation always lasts for a shorter time than tonicization",
                            "Modulation never involves a secondary dominant",
                            "Tonicization can only happen in a minor key",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "A confirming cadence in the new key is what separates a "
                            "genuine modulation from a passing tonicization that simply "
                            "returns home."
                        ),
                    },
                    topics=["tonicization-vs-modulation"],
                ),
                StepDef(
                    slug="tonicization-modulation-quiz-evidence",
                    kind="quiz",
                    payload={
                        "question": "A secondary dominant by itself is evidence of:",
                        "choices": [
                            "Tonicization, not necessarily a modulation",
                            "A confirmed modulation",
                            "A deceptive cadence",
                            "A plagal cadence",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "A secondary dominant alone only tonicizes its target - "
                            "whether it becomes a real modulation depends on whether a "
                            "cadence in that key follows."
                        ),
                    },
                    topics=["tonicization-vs-modulation"],
                ),
            ],
        ),
        LessonDef(
            slug="pivot-chord-modulation",
            title="Pivot Chord Modulation",
            summary="Modulating smoothly through a chord shared by both keys.",
            estimated_minutes=14,
            steps=[
                StepDef(
                    slug="pivot-chord-modulation-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Pivot chord modulation\n\n"
                            "The smoothest way to modulate is to find a chord that "
                            "belongs to **both** the old key and the new key, reinterpret "
                            "it in the new key's terms, and use it as a hinge to swing "
                            "from one to the other. That shared chord is a **pivot "
                            "chord**, and this is the most common way tonal music "
                            "changes key.\n\n"
                            "A pivot-chord analysis is written with both readings "
                            "stacked, old key over new key - for example, modulating from "
                            "C major to G major, the ii chord of C (Dm) is also the vi "
                            "chord of G, so it can be labeled **ii/vi**, marking the "
                            "instant the reinterpretation happens. After the pivot, a "
                            "cadence in the new key (typically using the new key's own V "
                            "or V7) confirms the modulation has actually taken hold.\n\n"
                            "The strongest pivot chords are diatonic in **both** keys - "
                            "the chord itself contains no accidental, so nothing sounds "
                            "chromatic at the pivot. The first accidental usually arrives "
                            "just after the pivot, in the new key's own leading tone, as "
                            "the music heads toward the confirming cadence."
                        )
                    },
                    topics=["tonicization-vs-modulation"],
                ),
                StepDef(
                    slug="pivot-chord-modulation-quiz-label",
                    kind="quiz",
                    payload={
                        "question": (
                            "In a pivot-chord modulation, how is the pivot chord "
                            "typically labeled?"
                        ),
                        "choices": [
                            "With both roman numerals stacked, old key over new key",
                            "With only the new key's roman numeral",
                            "With only the old key's roman numeral",
                            "It is left unlabeled since it belongs to neither key",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "A pivot chord is analyzed in both keys at once - its "
                            "old-key roman numeral stacked over its new-key roman "
                            "numeral - to mark the exact moment of reinterpretation."
                        ),
                    },
                    topics=["tonicization-vs-modulation"],
                ),
                StepDef(
                    slug="pivot-chord-modulation-quiz-confirms",
                    kind="quiz",
                    payload={
                        "question": (
                            "After the pivot chord, what actually confirms the "
                            "modulation has taken hold?"
                        ),
                        "choices": [
                            "A cadence in the new key",
                            "The pivot chord itself",
                            "A return to the original key signature",
                            "A fermata",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The pivot chord only sets up the reinterpretation - a "
                            "cadence in the new key, usually built from its own V or V7, "
                            "is what confirms the modulation actually happened."
                        ),
                    },
                    topics=["tonicization-vs-modulation"],
                ),
            ],
        ),
        LessonDef(
            slug="modal-mixture",
            title="Modal Mixture",
            summary="Borrowing chords from the parallel mode for color.",
            estimated_minutes=13,
            steps=[
                StepDef(
                    slug="modal-mixture-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Modal mixture\n\n"
                            "**Modal mixture** (also called borrowed chords) is "
                            "borrowing a chord from the **parallel mode** - major "
                            "borrowing from minor, or minor borrowing from major - "
                            "without actually modulating anywhere. The key signature and "
                            "the tonic both stay put; only the color of one chord "
                            "changes.\n\n"
                            "In major keys, the most common borrowings come from parallel "
                            "minor: **iv** (instead of IV), **bVI**, **bIII**, and **bVII** "
                            "all show up constantly in otherwise major-key music, each "
                            "one darkening the harmony for a moment. The minor iv "
                            "resolving to I is common enough to have its own name, the "
                            "**\"borrowed\" or \"minor\" plagal cadence**, valued for a "
                            "bittersweet color a major IV can't produce.\n\n"
                            "Mixture is written with the borrowed scale degree's actual "
                            "accidental worked into the roman numeral - a lowered 6th "
                            "scale degree in a major key produces **bVI**, a lowered "
                            "3rd produces **bIII**. Unlike a secondary dominant, a "
                            "borrowed chord doesn't tonicize anything or point toward a "
                            "new key - it's simply a color drawn from the parallel mode, "
                            "with the actual tonic never in question."
                        )
                    },
                    topics=["modal-mixture"],
                ),
                StepDef(
                    slug="modal-mixture-quiz-definition",
                    kind="quiz",
                    payload={
                        "question": "Modal mixture borrows a chord from:",
                        "choices": [
                            "The parallel mode (major from minor, or minor from major)",
                            "The relative mode",
                            "A secondary key a fifth away",
                            "The dominant key",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "Mixture borrows color from the parallel mode - same tonic, "
                            "opposite mode - without changing key."
                        ),
                    },
                    topics=["modal-mixture"],
                ),
                StepDef(
                    slug="modal-mixture-quiz-iv",
                    kind="quiz",
                    payload={
                        "question": (
                            "In a major key, a minor iv borrowed from the parallel minor, "
                            "resolving to I, is known as:"
                        ),
                        "choices": [
                            "The borrowed (minor) plagal cadence",
                            "A deceptive cadence",
                            "A Phrygian half cadence",
                            "A secondary dominant resolution",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "iv-I, with iv borrowed from the parallel minor, is the "
                            "borrowed or minor plagal cadence - prized for a darker color "
                            "than the ordinary major IV-I plagal cadence."
                        ),
                    },
                    topics=["modal-mixture"],
                ),
            ],
        ),
        LessonDef(
            slug="the-neapolitan-sixth",
            title="The Neapolitan Sixth",
            summary="A borrowed, lowered supertonic chord that leans hard into V.",
            estimated_minutes=13,
            steps=[
                StepDef(
                    slug="neapolitan-sixth-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# The Neapolitan sixth\n\n"
                            "The **Neapolitan chord**, labeled **N6** (or bII6), is a "
                            "major triad built on the **lowered second scale degree**, "
                            "almost always used in **first inversion** - hence the "
                            "\"sixth\" in its name. In C major or C minor alike, N6 is a "
                            "Db major triad in first inversion, with **F, the chord's "
                            "third, in the bass**.\n\n"
                            "N6 behaves like a chromatic substitute for iv or ii°6, and "
                            "it typically resolves straight to **V** (often through a "
                            "cadential 6/4), with the bass stepping down from F to the "
                            "leading tone's neighbor or directly to the dominant root. "
                            "The lowered 2nd scale degree itself often falls by a half "
                            "step, or leaps down a diminished third to the raised 7th "
                            "scale degree - a distinctive, unmistakably chromatic voice-"
                            "leading gesture.\n\n"
                            "The Neapolitan works equally well in major and minor keys "
                            "(it's borrowed either way, since bII isn't diatonic in "
                            "either), and it's prized for the dramatic half-step pull it "
                            "creates on its way into the dominant."
                        )
                    },
                    topics=["neapolitan-sixth"],
                ),
                StepDef(
                    slug="neapolitan-sixth-quiz-built-on",
                    kind="quiz",
                    payload={
                        "question": "The Neapolitan chord is a major triad built on:",
                        "choices": [
                            "The lowered 2nd scale degree",
                            "The lowered 6th scale degree",
                            "The raised 4th scale degree",
                            "The tonic",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "N6 is a major triad on the lowered supertonic - bII - "
                            "almost always heard in first inversion."
                        ),
                    },
                    topics=["neapolitan-sixth"],
                ),
                StepDef(
                    slug="neapolitan-sixth-quiz-inversion",
                    kind="quiz",
                    payload={
                        "question": (
                            "Why is the Neapolitan chord called \"N6\" rather than just "
                            "\"N\"?"
                        ),
                        "choices": [
                            "It is almost always used in first inversion, "
                            "with the third in the bass",
                            "It contains a minor sixth interval above the root",
                            "It resolves to a chord six scale degrees away",
                            "It is the sixth chord borrowed from the parallel mode",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The \"6\" marks first inversion - N6 is conventionally "
                            "voiced with its third, not its root, in the bass."
                        ),
                    },
                    topics=["neapolitan-sixth"],
                ),
                StepDef(
                    slug="neapolitan-sixth-quiz-resolves-to",
                    kind="quiz",
                    payload={
                        "question": "The Neapolitan sixth typically resolves to:",
                        "choices": ["V", "IV", "vi", "ii"],
                        "answer_index": 0,
                        "explanation": (
                            "N6 functions as a predominant, most often resolving "
                            "directly into V (frequently by way of a cadential 6/4)."
                        ),
                    },
                    topics=["neapolitan-sixth"],
                ),
            ],
        ),
        LessonDef(
            slug="augmented-sixth-chords",
            title="Augmented Sixth Chords",
            summary="Italian, French, and German chords that squeeze into V from both sides.",
            estimated_minutes=15,
            steps=[
                StepDef(
                    slug="augmented-sixth-reading",
                    kind="reading",
                    payload={
                        "markdown": (
                            "# Augmented sixth chords\n\n"
                            "An **augmented sixth chord** is built around the interval "
                            "of an augmented 6th - the lowered 6th scale degree in the "
                            "bass against the raised 4th scale degree above it - and both "
                            "notes resolve **outward by half step** to the octave on "
                            "scale degree 5, converging on the dominant from opposite "
                            "directions at once. That double half-step pull is what gives "
                            "these chords their unmistakably strong predominant function.\n\n"
                            "There are three common flavors, distinguished by what else "
                            "is stacked between the two augmented-sixth notes (using A "
                            "minor as the example key, so scale degree 6 is F and scale "
                            "degree 4 is D#):\n\n"
                            "- **Italian sixth (It+6)**: just the augmented sixth plus a "
                            "doubled root - F, A, D# - only three distinct pitches.\n"
                            "- **French sixth (Fr+6)**: F, A, B, D# - adds the 2nd scale "
                            "degree, giving the chord a distinctive whole-tone flavor.\n"
                            "- **German sixth (Ger+6)**: F, A, C, D# - adds the lowered "
                            "3rd scale degree instead, which makes it sound and spell "
                            "exactly like a dominant seventh chord (enharmonically), "
                            "though it functions as a predominant, not a dominant.\n\n"
                            "All three resolve to V (often through a cadential 6/4) with "
                            "the augmented sixth interval expanding outward to an "
                            "octave on the dominant's root."
                        )
                    },
                    topics=["augmented-sixth-chords"],
                ),
                StepDef(
                    slug="augmented-sixth-quiz-interval",
                    kind="quiz",
                    payload={
                        "question": (
                            "An augmented sixth chord is built around which interval, "
                            "and how does it resolve?"
                        ),
                        "choices": [
                            "Lowered scale degree 6 against raised scale degree 4, "
                            "expanding outward to an octave on scale degree 5",
                            "A perfect fifth, contracting inward to a third",
                            "A diminished seventh, resolving down by step",
                            "A major sixth, staying stationary into the tonic",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "The chord's defining interval - lowered 6 in the bass "
                            "against raised 4 above - resolves outward by half step "
                            "to converge on scale degree 5 from both sides."
                        ),
                    },
                    topics=["augmented-sixth-chords"],
                ),
                StepDef(
                    slug="augmented-sixth-quiz-german",
                    kind="quiz",
                    payload={
                        "question": (
                            "The German sixth chord is spelled enharmonically the same "
                            "as which chord, despite functioning differently?"
                        ),
                        "choices": [
                            "A dominant seventh chord",
                            "A diminished seventh chord",
                            "A Neapolitan sixth chord",
                            "A half-diminished seventh chord",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "Ger+6 adds the lowered 3rd scale degree to the augmented "
                            "sixth interval, which spells exactly like a dominant "
                            "seventh chord - though it still functions as a predominant "
                            "resolving to V, not as a dominant."
                        ),
                    },
                    topics=["augmented-sixth-chords"],
                ),
                StepDef(
                    slug="augmented-sixth-quiz-french",
                    kind="quiz",
                    payload={
                        "question": (
                            "What distinguishes the French sixth from the Italian sixth?"
                        ),
                        "choices": [
                            "The French sixth adds scale degree 2, giving it a "
                            "whole-tone flavor the Italian sixth lacks",
                            "The French sixth resolves to IV instead of V",
                            "The French sixth has no augmented sixth interval",
                            "The French sixth is only used in major keys",
                        ],
                        "answer_index": 0,
                        "explanation": (
                            "It+6 is just three distinct pitches (with a doubled root); "
                            "Fr+6 adds the 2nd scale degree in between, producing its "
                            "characteristic whole-tone color."
                        ),
                    },
                    topics=["augmented-sixth-chords"],
                ),
            ],
        ),
    ],
)
