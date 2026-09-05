from pathlib import Path

from app.domains.analysis.harmony import analyze_harmony, analyze_harmony_from_score
from app.domains.analysis.voicing import (
    ChordTones,
    check_doubling,
    check_overlaps,
    four_part_chords,
)
from app.tests.test_harmony_service import _satb


def _grid(**voices: list[str | None]) -> dict[str, list[str | None]]:
    return dict(voices)


class TestFourPartChords:
    def test_builds_one_voiced_chord_per_slice_for_a_real_four_voice_score(self) -> None:
        score = _satb(
            [
                ("C5", "E4", "G3", "C3"),
                ("B4", "D4", "G3", "G3"),
                ("C5", "E4", "G3", "C3"),
            ]
        )
        result = analyze_harmony_from_score(score)
        assert result.technical_data.voicing is not None

    def test_returns_nothing_for_the_positional_fallback(self) -> None:
        grid = _grid(v1=["C5"], v2=["G4"], v3=["E4"])
        assert four_part_chords("vertical-positions", ["v1", "v2", "v3"], grid, [1]) == []

    def test_returns_nothing_when_not_exactly_four_voices(self) -> None:
        grid = _grid(v1=["C5"], v2=["E4"], v3=["G3"])
        assert four_part_chords("parts", ["v1", "v2", "v3"], grid, [1]) == []

    def test_skips_a_slice_where_a_voice_rests(self) -> None:
        grid = _grid(s=["C5", "B4"], a=["E4", None], t=["G3", "G3"], b=["C3", "G3"])
        chords = four_part_chords("parts", ["s", "a", "t", "b"], grid, [1, 2])
        assert len(chords) == 1
        assert chords[0].measure == 1


class TestVoiceRanges:
    def test_flags_a_voice_outside_its_conventional_tessitura(self) -> None:
        # The soprano's high C6 is well above the conventional A5 ceiling.
        score = _satb([("C6", "E4", "G3", "C3")])
        result = analyze_harmony_from_score(score)

        report = result.technical_data.voicing
        assert report is not None
        assert any(v.voice == "soprano" and v.pitch == "C6" for v in report.range_violations)

    def test_reports_nothing_for_voices_within_range(self) -> None:
        score = _satb([("C5", "E4", "G3", "C3")])
        result = analyze_harmony_from_score(score)

        report = result.technical_data.voicing
        assert report is not None
        assert report.range_violations == []


class TestSpacing:
    def test_flags_more_than_an_octave_between_soprano_and_alto(self) -> None:
        score = _satb([("C6", "A3", "G3", "C3")])
        result = analyze_harmony_from_score(score)

        report = result.technical_data.voicing
        assert report is not None
        assert any(
            v.upper_voice == "soprano" and v.lower_voice == "alto"
            for v in report.spacing_violations
        )

    def test_does_not_flag_a_wide_tenor_bass_gap(self) -> None:
        # Soprano/alto/tenor close together; tenor sits nearly two octaves
        # above the bass, which is ordinary voicing, not a fault.
        score = _satb([("C5", "G4", "E4", "E2")])
        result = analyze_harmony_from_score(score)

        report = result.technical_data.voicing
        assert report is not None
        assert report.spacing_violations == []


class TestDoubling:
    def test_flags_a_doubled_leading_tone(self) -> None:
        chords = four_part_chords(
            "parts",
            ["s", "a", "t", "b"],
            _grid(s=["F#5"], a=["F#4"], t=["D4"], b=["G2"]),
            [1],
        )
        violations = check_doubling(chords, leading_tone_pc=6)  # F# = pitch class 6
        assert any(v.kind == "doubled_leading_tone" for v in violations)

    def test_flags_a_doubled_seventh(self) -> None:
        chords = four_part_chords(
            "parts",
            ["s", "a", "t", "b"],
            _grid(s=["F5"], a=["F4"], t=["D4"], b=["G2"]),
            [1],
            [ChordTones(root=7, third=11, seventh=5)],  # G7: root G, third B, seventh F
        )
        violations = check_doubling(chords, leading_tone_pc=None)
        assert any(v.kind == "doubled_seventh" for v in violations)

    def test_flags_a_missing_third(self) -> None:
        chords = four_part_chords(
            "parts",
            ["s", "a", "t", "b"],
            _grid(s=["G5"], a=["D4"], t=["D4"], b=["G2"]),
            [1],
            [ChordTones(root=7, third=11, seventh=None)],  # G major: third is B, absent here
        )
        violations = check_doubling(chords, leading_tone_pc=None)
        assert any(v.kind == "missing_third" for v in violations)

    def test_a_complete_triad_with_no_leading_tone_has_no_violations(self) -> None:
        chords = four_part_chords(
            "parts",
            ["s", "a", "t", "b"],
            _grid(s=["G5"], a=["B4"], t=["D4"], b=["G2"]),
            [1],
            [ChordTones(root=7, third=11, seventh=None)],
        )
        assert check_doubling(chords, leading_tone_pc=None) == []


class TestOverlap:
    def test_flags_a_voice_moving_past_where_the_adjacent_one_just_was(self) -> None:
        chords = four_part_chords(
            "parts",
            ["s", "a", "t", "b"],
            # Alto's new E5 is above soprano's *previous* D5 - an overlap,
            # even though the two chords aren't crossed at either instant.
            _grid(s=["D5", "F5"], a=["A4", "E5"], t=["E4", "F4"], b=["C3", "D3"]),
            [1, 1],
        )
        violations = check_overlaps(chords)
        assert any(v.upper_voice == "soprano" and v.lower_voice == "alto" for v in violations)

    def test_ordinary_stepwise_motion_is_not_an_overlap(self) -> None:
        chords = four_part_chords(
            "parts",
            ["s", "a", "t", "b"],
            _grid(s=["D5", "E5"], a=["A4", "B4"], t=["E4", "F4"], b=["C3", "D3"]),
            [1, 1],
        )
        assert check_overlaps(chords) == []


class TestVoicingReportIntegration:
    def test_the_harmony_engine_omits_voicing_for_a_non_satb_score(self) -> None:
        # multi_part.musicxml (used elsewhere) falls back to positional
        # voices; the report should be absent, not an empty guess.
        content = (Path(__file__).parent / "fixtures" / "multi_part.musicxml").read_bytes()
        result = analyze_harmony(content, "multi_part.musicxml")
        assert result.technical_data.voicing is None

    def test_a_clean_four_part_progression_has_no_findings(self) -> None:
        score = _satb(
            [
                ("C5", "E4", "G3", "C3"),
                ("B4", "D4", "G3", "G3"),
                ("C5", "E4", "G3", "C3"),
            ]
        )
        report = analyze_harmony_from_score(score).technical_data.voicing
        assert report is not None
        assert report.range_violations == []
        assert report.spacing_violations == []
        assert report.overlaps == []
