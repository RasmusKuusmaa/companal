from app.domains.notation.counterpoint import (
    align_intervals,
    build_counterpoint_report,
    check_first_species,
    check_fourth_species,
    check_second_and_third_species,
    classify_interval,
    identify_lines,
)
from app.domains.notation.schemas import NotationDocument, NotationNote


def _note(
    step: str,
    octave: int,
    duration: str = "whole",
    tied: bool = False,
    is_rest: bool = False,
    alter: int = 0,
) -> dict[str, object]:
    return {
        "id": "n",
        "step": step,
        "octave": octave,
        "alter": alter,
        "duration": duration,
        "dots": 0,
        "is_rest": is_rest,
        "tied_to_next": tied,
    }


def _document(
    cf_notes: list[dict[str, object]], cp_measures: list[list[dict[str, object]]]
) -> NotationDocument:
    return NotationDocument.model_validate(
        {
            "fifths": 0,
            "mode": "major",
            "time": {"beats": 4, "beat_type": 4},
            "tempo": 90,
            "staves": [
                {
                    "id": "cf",
                    "clef": "bass",
                    "measures": [
                        {"id": f"m{i}", "voices": [{"id": "1", "notes": [note]}]}
                        for i, note in enumerate(cf_notes)
                    ],
                },
                {
                    "id": "cp",
                    "clef": "treble",
                    "measures": [
                        {"id": f"m{i}", "voices": [{"id": "2", "notes": notes}]}
                        for i, notes in enumerate(cp_measures)
                    ],
                },
            ],
        }
    )


_CF_5_BAR = [_note("C", 3), _note("D", 3), _note("E", 3), _note("D", 3), _note("C", 3)]


class TestIdentifyLines:
    def test_names_the_given_staff_as_the_cantus_firmus(self) -> None:
        document = _document(_CF_5_BAR, [[_note("E", 4)]] * 5)
        lines = identify_lines(document, cantus_firmus_staff_index=0)
        assert lines is not None
        assert [n.step for n in lines.cantus_firmus] == ["C", "D", "E", "D", "C"]

    def test_disambiguates_first_species_by_the_named_staff(self) -> None:
        # Both voices are whole notes here - exactly first species - which
        # the shape-based heuristic alone can't tell apart (see the module
        # docstring); the named staff must be used.
        document = _document(_CF_5_BAR, [[_note("E", 4)]] * 5)
        assert identify_lines(document) is None
        assert identify_lines(document, cantus_firmus_staff_index=0) is not None

    def test_returns_none_for_more_than_two_voices(self) -> None:
        document = NotationDocument.model_validate(
            {
                "fifths": 0,
                "mode": "major",
                "time": {"beats": 4, "beat_type": 4},
                "tempo": 90,
                "staves": [
                    {
                        "id": "s",
                        "clef": "treble",
                        "measures": [
                            {
                                "id": "m0",
                                "voices": [
                                    {"id": "1", "notes": [_note("C", 4)]},
                                    {"id": "2", "notes": [_note("E", 4)]},
                                    {"id": "3", "notes": [_note("G", 4)]},
                                ],
                            }
                        ],
                    }
                ],
            }
        )
        assert identify_lines(document) is None


def _n(step: str, octave: int, alter: int = 0) -> NotationNote:
    return NotationNote.model_validate(_note(step, octave, alter=alter))


class TestClassifyInterval:
    def test_a_perfect_fifth_is_consonant(self) -> None:
        name, consonant = classify_interval(_n("C", 3), _n("G", 3))
        assert name == "P5"
        assert consonant

    def test_a_perfect_fourth_is_dissonant_against_the_bass(self) -> None:
        name, consonant = classify_interval(_n("C", 3), _n("F", 3))
        assert name == "P4"
        assert not consonant

    def test_a_tritone_is_dissonant(self) -> None:
        _name, consonant = classify_interval(_n("C", 3), _n("F", 3, alter=1))
        assert not consonant


class TestAlignIntervals:
    def test_pairs_each_counterpoint_note_with_its_cantus_firmus_note(self) -> None:
        document = _document(
            [_note("C", 3), _note("D", 3)],
            [[_note("E", 4, "half"), _note("F", 4, "half")], [_note("G", 4)]],
        )
        lines = identify_lines(document, cantus_firmus_staff_index=0)
        assert lines is not None
        aligned = align_intervals(lines)
        assert [(a.measure, a.is_downbeat) for a in aligned] == [
            (1, True),
            (1, False),
            (2, True),
        ]


class TestFirstSpecies:
    def test_a_clean_exercise_has_no_violations(self) -> None:
        cp = [_note("C", 4), _note("A", 3), _note("G", 3), _note("B", 3), _note("C", 4)]
        lines = identify_lines(_document(_CF_5_BAR, [[n] for n in cp]), 0)
        assert lines is not None
        findings = check_first_species(lines)
        assert all(f.passed for f in findings)

    def test_a_faulty_exercise_is_caught(self) -> None:
        # Parallel fifths all the way through, and a cadence that neither
        # ends on a perfect interval by way of an imperfect one nor
        # approaches by step.
        cp = [_note("G", 4), _note("A", 4), _note("B", 4), _note("A", 4), _note("C", 5)]
        lines = identify_lines(_document(_CF_5_BAR, [[n] for n in cp]), 0)
        assert lines is not None
        findings = check_first_species(lines)

        kinds = {f.kind for f in findings if not f.passed}
        assert "parallel_fifth" in kinds
        assert "cadence" in kinds

    def test_a_counterpoint_left_entirely_as_rests_does_not_pass(self) -> None:
        # A rest is skipped by align_intervals rather than guessed at (see
        # its own docstring), which - without a dedicated check - would let
        # a counterpoint of nothing but rests sail through every other rule
        # with no aligned intervals left to violate.
        cp = [_note("C", 4, is_rest=True)] * 5
        lines = identify_lines(_document(_CF_5_BAR, [[n] for n in cp]), 0)
        assert lines is not None
        findings = check_first_species(lines)

        assert not all(f.passed for f in findings)
        assert {f.kind for f in findings if not f.passed} == {"missing_note"}


class TestSecondAndThirdSpecies:
    _CLEAN_CP = [
        [_note("E", 4, "half"), _note("G", 4, "half")],
        [_note("F", 4, "half"), _note("A", 4, "half")],
        [_note("G", 4, "half"), _note("B", 4, "half")],
        [_note("A", 4, "half"), _note("B", 4, "half")],
        [_note("C", 5)],
    ]

    def test_a_clean_exercise_has_no_violations(self) -> None:
        lines = identify_lines(_document(_CF_5_BAR, self._CLEAN_CP), 0)
        assert lines is not None
        findings = check_second_and_third_species(lines)
        assert all(f.passed for f in findings)

    def test_a_faulty_exercise_is_caught(self) -> None:
        # Measure 2's downbeat is dissonant against the bass, and measure
        # 3 leaps into and out of its weak beat instead of stepping.
        cp = [
            [_note("E", 4, "half"), _note("G", 4, "half")],
            [_note("G", 4, "half"), _note("A", 4, "half")],
            [_note("G", 4, "half"), _note("C", 5, "half")],
            [_note("A", 4, "half"), _note("B", 4, "half")],
            [_note("C", 5)],
        ]
        lines = identify_lines(_document(_CF_5_BAR, cp), 0)
        assert lines is not None
        findings = check_second_and_third_species(lines)

        kinds = {f.kind for f in findings if not f.passed}
        assert "dissonance" in kinds
        assert "unrecovered_leap" in kinds

    def test_a_counterpoint_left_entirely_as_rests_does_not_pass(self) -> None:
        cp = [[_note("C", 4, "half", is_rest=True), _note("C", 4, "half", is_rest=True)]] * 5
        lines = identify_lines(_document(_CF_5_BAR, cp), 0)
        assert lines is not None
        findings = check_second_and_third_species(lines)

        assert not all(f.passed for f in findings)
        assert {f.kind for f in findings if not f.passed} == {"missing_note"}


class TestFourthSpecies:
    _CF_3_BAR = [_note("C", 3, "whole"), _note("D", 3, "whole"), _note("C", 3, "whole")]

    def test_a_prepared_and_resolved_suspension_is_not_a_violation(self) -> None:
        cp = [
            [_note("C", 5, is_rest=True), _note("C", 5, tied=True)],
            [_note("C", 5), _note("B", 4)],
            [_note("C", 5, "whole")],
        ]
        lines = identify_lines(_document(self._CF_3_BAR, cp), 0)
        assert lines is not None
        findings = check_fourth_species(lines)
        assert all(f.passed for f in findings)

    def test_an_unprepared_dissonance_is_caught(self) -> None:
        cp = [
            [_note("C", 5, is_rest=True), _note("B", 4)],
            [_note("C", 5), _note("B", 4)],
            [_note("C", 5, "whole")],
        ]
        lines = identify_lines(_document(self._CF_3_BAR, cp), 0)
        assert lines is not None
        findings = check_fourth_species(lines)

        assert any(f.kind == "unprepared_dissonance" and not f.passed for f in findings)

    def test_a_counterpoint_left_entirely_as_rests_does_not_pass(self) -> None:
        cp = [[_note("C", 5, "whole", is_rest=True)]] * 3
        lines = identify_lines(_document(self._CF_3_BAR, cp), 0)
        assert lines is not None
        findings = check_fourth_species(lines)

        assert not all(f.passed for f in findings)
        assert {f.kind for f in findings if not f.passed} == {"missing_note"}


class TestBuildCounterpointReport:
    def test_ties_the_report_to_the_requested_species(self) -> None:
        cp = [_note("C", 4), _note("A", 3), _note("G", 3), _note("B", 3), _note("C", 4)]
        document = _document(_CF_5_BAR, [[n] for n in cp])

        report = build_counterpoint_report(document, species=1, cantus_firmus_staff_index=0)
        assert report is not None
        assert report.species == 1
        assert report.passed

    def test_returns_none_for_a_document_that_is_not_a_species_exercise(self) -> None:
        document = _document(_CF_5_BAR, [[_note("E", 4)]] * 5)
        # Wrong staff index named - there's no staff 5.
        assert build_counterpoint_report(document, species=1, cantus_firmus_staff_index=5) is None
