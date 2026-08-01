from pathlib import Path

import pytest
from music21 import note as m21note
from music21 import stream

from app.domains.analysis.melody import analyze_melody, analyze_melody_from_score
from app.domains.analysis.service import AnalysisError

_FIXTURES = Path(__file__).parent / "fixtures"
MELODY_LINE = (_FIXTURES / "melody_line.musicxml").read_bytes()
SIMPLE_SCORE = (_FIXTURES / "simple_score.musicxml").read_bytes()
MULTI_PART = (_FIXTURES / "multi_part.musicxml").read_bytes()


class TestMelodyShape:
    def test_returns_the_documented_top_level_shape(self) -> None:
        result = analyze_melody(MELODY_LINE, "melody_line.musicxml")

        assert 0.0 <= result.score <= 100.0
        assert isinstance(result.strengths, list)
        assert isinstance(result.issues, list)
        # technical_data is a structured object that serialises to a plain
        # JSON object, exactly the {score, strengths, issues, technical_data}
        # contract the caller expects.
        assert result.technical_data.note_count > 0

    def test_reads_the_top_line_of_the_chosen_part(self) -> None:
        result = analyze_melody(MELODY_LINE, "melody_line.musicxml")

        td = result.technical_data
        assert td.part_id == "P1"
        assert td.key == "C major"
        assert td.note_count == 12


class TestMelodicIntervals:
    def test_measures_directed_intervals_between_consecutive_notes(self) -> None:
        td = analyze_melody(MELODY_LINE, "melody_line.musicxml").technical_data

        assert td.intervals.count == 11
        # C->D->E->C->G ... the opening four intervals of the line.
        opening = [(i.name, i.semitones) for i in td.intervals.sequence[:4]]
        assert opening == [("M2", 2), ("M2", 2), ("M-3", -4), ("P5", 7)]
        assert td.intervals.by_name["M2"] == 4
        assert td.intervals.largest_semitones == 7

    def test_classifies_steps_and_leaps_on_each_interval(self) -> None:
        td = analyze_melody(MELODY_LINE, "melody_line.musicxml").technical_data

        first = td.intervals.sequence[0]
        assert first.is_step and not first.is_leap
        # The C4 -> G4 jump is a leap, not a step.
        leap = td.intervals.sequence[3]
        assert leap.is_leap and not leap.is_step


class TestRange:
    def test_reports_ambitus_as_pitches_and_interval(self) -> None:
        td = analyze_melody(MELODY_LINE, "melody_line.musicxml").technical_data

        assert td.range.lowest == "C4"
        assert td.range.highest == "B4"
        assert td.range.semitones == 11
        assert td.range.interval_name == "Major Seventh"


class TestContour:
    def test_encodes_direction_and_classifies_an_arch(self) -> None:
        td = analyze_melody(MELODY_LINE, "melody_line.musicxml").technical_data

        assert td.contour.parsons == "*uuduuuddddd"
        assert td.contour.direction_changes == 3
        assert td.contour.shape == "arch"

    def test_all_ascending_line_is_classified_ascending(self) -> None:
        # C4 D4 E4 (rest) then held C4 - a short rising fragment.
        td = analyze_melody(SIMPLE_SCORE, "simple_score.musicxml").technical_data
        assert td.contour.ascending_moves == 2


class TestStepwiseAndLeaps:
    def test_counts_stepwise_motion_and_its_longest_run(self) -> None:
        td = analyze_melody(MELODY_LINE, "melody_line.musicxml").technical_data

        assert td.stepwise.count == 8
        assert td.stepwise.ratio == pytest.approx(0.727, abs=0.001)
        assert td.stepwise.longest_run == 4

    def test_flags_leaps_and_an_unresolved_large_leap(self) -> None:
        td = analyze_melody(MELODY_LINE, "melody_line.musicxml").technical_data

        assert td.leaps.count == 3
        assert td.leaps.largest_semitones == 7
        assert td.leaps.largest_name == "P5"
        # The rising fifth continues upward instead of turning back by step.
        assert td.leaps.unresolved == 1
        assert td.leaps.consecutive_leaps_max == 2


class TestMotifsAndRepetition:
    def test_detects_a_transposed_recurring_motif(self) -> None:
        td = analyze_melody(MELODY_LINE, "melody_line.musicxml").technical_data

        assert len(td.motifs) == 1
        motif = td.motifs[0]
        # C-D-E-C and its restatement G-A-B-G share the same interval shape.
        assert motif.intervals == ["M2", "M2", "M-3"]
        assert motif.length_notes == 4
        assert motif.occurrences == 2

    def test_monophonic_fragment_without_repetition_has_no_motif(self) -> None:
        td = analyze_melody(SIMPLE_SCORE, "simple_score.musicxml").technical_data

        assert td.motifs == []
        assert td.repetition.most_common_pitch == "C4"


class TestCadences:
    def test_segments_phrases_at_rests_and_classifies_endings(self) -> None:
        td = analyze_melody(MELODY_LINE, "melody_line.musicxml").technical_data

        assert len(td.cadences) == 2
        half, final = td.cadences
        # First phrase settles on the dominant across the rest.
        assert half.final_pitch == "G4"
        assert half.scale_degree == 5
        assert half.type == "half-like"
        # The piece closes by step onto the tonic - the strongest melodic close.
        assert final.final_pitch == "C4"
        assert final.scale_degree == 1
        assert final.approach == "step-down"
        assert final.type == "authentic-like"
        assert final.on_tonic is True


class TestScoring:
    def test_a_well_formed_melody_scores_high_with_matching_strengths(self) -> None:
        result = analyze_melody(MELODY_LINE, "melody_line.musicxml")

        assert result.score >= 90.0
        joined = " ".join(result.strengths).lower()
        assert "stepwise" in joined
        assert "motif" in joined
        assert "arch" in joined
        assert "tonic" in joined
        # Its one weakness - the unresolved rising fifth - is surfaced.
        assert any("leap" in issue.lower() for issue in result.issues)

    def test_scoring_is_deterministic(self) -> None:
        first = analyze_melody(MELODY_LINE, "melody_line.musicxml")
        second = analyze_melody(MELODY_LINE, "melody_line.musicxml")
        assert first.score == second.score
        assert first.model_dump() == second.model_dump()


class TestPartSelectionAndEdges:
    def test_picks_the_highest_sounding_part_as_the_melody(self) -> None:
        # In the two-part fixture the violin (P2) sits above the piano, so it
        # is taken as the melodic line - here a single held C5.
        result = analyze_melody(MULTI_PART, "multi_part.musicxml")

        assert result.technical_data.part_id == "P2"
        assert result.technical_data.note_count == 1
        # One note has no intervals to judge, so scoring bottoms out and says so.
        assert result.score == 0.0
        assert any("short" in issue.lower() for issue in result.issues)

    def test_raises_when_there_are_no_pitched_notes(self) -> None:
        rests_only = stream.Score()
        part = stream.Part()
        part.append(m21note.Rest(quarterLength=4))
        rests_only.append(part)

        with pytest.raises(AnalysisError):
            analyze_melody_from_score(rests_only)

    def test_raises_for_unparseable_content(self) -> None:
        with pytest.raises(AnalysisError):
            analyze_melody(b"this is not xml at all", "piece.musicxml")
