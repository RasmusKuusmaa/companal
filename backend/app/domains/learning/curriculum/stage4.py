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
    ],
)
