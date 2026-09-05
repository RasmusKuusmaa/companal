from app.domains.notation.figured_bass import check_figured_bass
from app.domains.notation.schemas import NotationDocument


def _note(step: str, octave: int, alter: int = 0, is_rest: bool = False) -> dict[str, object]:
    return {
        "id": "n",
        "step": step,
        "octave": octave,
        "alter": alter,
        "duration": "whole",
        "dots": 0,
        "is_rest": is_rest,
        "tied_to_next": False,
    }


def _document(
    bass_notes: list[dict[str, object]], upper_measures: list[list[dict[str, object]]]
) -> NotationDocument:
    return NotationDocument.model_validate(
        {
            "fifths": 0,
            "mode": "major",
            "time": {"beats": 4, "beat_type": 4},
            "tempo": 90,
            "staves": [
                {
                    "id": "bass",
                    "clef": "bass",
                    "measures": [
                        {"id": f"m{i}", "voices": [{"id": "1", "notes": [note]}]}
                        for i, note in enumerate(bass_notes)
                    ],
                },
                {
                    "id": "upper",
                    "clef": "treble",
                    "measures": [
                        {
                            "id": f"m{i}",
                            "voices": [
                                {"id": f"v{j}", "notes": [note]} for j, note in enumerate(notes)
                            ],
                        }
                        for i, notes in enumerate(upper_measures)
                    ],
                },
            ],
        }
    )


class TestRootPositionAndFirstInversion:
    def test_a_correct_root_position_and_first_inversion_realization_passes(self) -> None:
        # C major root position (needs 3rd + 5th above C), then G major first
        # inversion with B in the bass, figure "6" (needs 3rd + 6th above B).
        document = _document(
            [_note("C", 3), _note("B", 2)],
            [
                [_note("E", 4), _note("G", 4)],
                [_note("D", 4), _note("G", 4)],
            ],
        )
        findings = check_figured_bass(document, bass_staff_index=0, figures=["", "6"])
        assert findings is not None
        assert all(f.passed for f in findings)

    def test_a_missing_fifth_in_root_position_is_caught(self) -> None:
        document = _document([_note("G", 2)], [[_note("B", 4), _note("B", 3)]])
        findings = check_figured_bass(document, bass_staff_index=0, figures=[""])
        assert findings is not None

        assert len(findings) == 1
        assert findings[0].kind == "missing_interval"
        assert not findings[0].passed
        assert "fifth" in findings[0].message


class TestSeventhChords:
    def test_a_correct_root_position_seventh_realization_passes(self) -> None:
        # G7: G-B-D-F. Root position needs 3rd, 5th and 7th above the bass.
        document = _document([_note("G", 2)], [[_note("B", 4), _note("D", 4), _note("F", 4)]])
        findings = check_figured_bass(document, bass_staff_index=0, figures=["7"])
        assert findings is not None
        assert all(f.passed for f in findings)

    def test_a_first_inversion_seventh_missing_the_sixth_is_caught(self) -> None:
        # G7 first inversion (bass = B): needs 3rd (D), 5th (F) and 6th (G)
        # above the bass. G (the sixth, i.e. the chord's root) is left out.
        document = _document([_note("B", 2)], [[_note("D", 4), _note("F", 4)]])
        findings = check_figured_bass(document, bass_staff_index=0, figures=["6/5"])
        assert findings is not None

        assert len(findings) == 1
        assert findings[0].kind == "missing_interval"
        assert "sixth" in findings[0].message


class TestUnrecognizedInput:
    def test_an_unknown_figure_is_reported_rather_than_silently_skipped(self) -> None:
        document = _document([_note("C", 3)], [[_note("E", 4), _note("G", 4)]])
        findings = check_figured_bass(document, bass_staff_index=0, figures=["9"])
        assert findings is not None

        assert len(findings) == 1
        assert findings[0].kind == "unknown_figure"
        assert not findings[0].passed

    def test_returns_none_when_the_bass_staff_does_not_exist(self) -> None:
        document = _document([_note("C", 3)], [[_note("E", 4), _note("G", 4)]])
        assert check_figured_bass(document, bass_staff_index=5, figures=[""]) is None

    def test_returns_none_when_the_figure_count_does_not_match_the_bass(self) -> None:
        document = _document(
            [_note("C", 3), _note("D", 3)], [[_note("E", 4)], [_note("F", 4)]]
        )
        assert check_figured_bass(document, bass_staff_index=0, figures=[""]) is None

    def test_a_rest_in_the_bass_is_reported_rather_than_crashing(self) -> None:
        document = _document([_note("C", 3, is_rest=True)], [[_note("E", 4)]])
        findings = check_figured_bass(document, bass_staff_index=0, figures=[""])
        assert findings is not None

        assert len(findings) == 1
        assert findings[0].kind == "missing_bass"
