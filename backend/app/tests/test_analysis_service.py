import io
import zipfile
from pathlib import Path

import pytest

from app.domains.analysis.service import AnalysisError, analyze

_FIXTURES = Path(__file__).parent / "fixtures"
SIMPLE_SCORE = (_FIXTURES / "simple_score.musicxml").read_bytes()
MULTI_PART = (_FIXTURES / "multi_part.musicxml").read_bytes()


def _as_mxl(musicxml: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<container><rootfiles><rootfile full-path="score.xml"/></rootfiles></container>',
        )
        archive.writestr("score.xml", musicxml.decode())
    return buffer.getvalue()


class TestAnalyzeMetadata:
    def test_extracts_title_and_composer(self) -> None:
        result = analyze(SIMPLE_SCORE, "simple_score.musicxml")

        assert result.title == "Simple Melody"
        assert result.composer == "Test Composer"

    def test_extracts_explicit_key_with_full_confidence(self) -> None:
        result = analyze(SIMPLE_SCORE, "simple_score.musicxml")

        assert result.key == "C major"
        assert result.key_confidence == 1.0

    def test_extracts_time_signature_and_tempo(self) -> None:
        result = analyze(SIMPLE_SCORE, "simple_score.musicxml")

        assert result.time_signature == "4/4"
        assert result.tempo == 90


class TestAnalyzeMeasuresAndNotes:
    def test_counts_measures_and_parts(self) -> None:
        result = analyze(SIMPLE_SCORE, "simple_score.musicxml")

        assert result.measure_count == 2
        assert result.part_count == 1

    def test_extracts_notes_in_order(self) -> None:
        result = analyze(SIMPLE_SCORE, "simple_score.musicxml")

        first_measure = result.measures[0]
        assert first_measure.number == 1
        assert [n.pitch for n in first_measure.notes] == ["C4", "D4", "E4", None]
        assert [n.is_rest for n in first_measure.notes] == [False, False, False, True]
        assert first_measure.notes[0].midi == 60
        assert first_measure.notes[0].part_id == "P1"

    def test_second_measure_holds_a_whole_note(self) -> None:
        result = analyze(SIMPLE_SCORE, "simple_score.musicxml")

        second_measure = result.measures[1]
        assert second_measure.number == 2
        assert len(second_measure.notes) == 1
        assert second_measure.notes[0].pitch == "C4"
        assert second_measure.notes[0].duration == 4.0


class TestAnalyzeInstruments:
    def test_extracts_one_instrument_per_part(self) -> None:
        result = analyze(MULTI_PART, "multi_part.musicxml")

        part_ids = [i.part_id for i in result.instruments]
        names = [i.name for i in result.instruments]
        assert part_ids == ["P1", "P2"]
        assert names == ["Piano", "Violin"]
        assert result.instruments[1].midi_program == 40


class TestAnalyzeChords:
    def test_monophonic_score_has_no_chords(self) -> None:
        result = analyze(SIMPLE_SCORE, "simple_score.musicxml")

        assert result.chords == []

    def test_derives_vertical_chords_across_parts(self) -> None:
        result = analyze(MULTI_PART, "multi_part.musicxml")

        # Only the two beats where 2+ notes sound together across the piano
        # and violin parts qualify - the closing half rest in the piano
        # leaves only the violin's held note, which isn't a chord.
        assert len(result.chords) == 2

        octave_stack = result.chords[0]
        assert octave_stack.pitches == ["C4", "C5"]

        triad = result.chords[1]
        assert triad.pitches == ["E4", "G4", "C5"]
        assert triad.quality == "major"
        assert triad.common_name == "C-major triad"

    def test_written_chord_within_a_part_is_flagged_on_the_note(self) -> None:
        result = analyze(MULTI_PART, "multi_part.musicxml")

        piano_notes = [n for n in result.measures[0].notes if n.part_id == "P1"]
        chord_note = next(n for n in piano_notes if n.is_chord)
        assert chord_note.pitches == ["E4", "G4"]


class TestAnalyzeCompressedMxl:
    def test_parses_a_compressed_mxl_archive(self) -> None:
        result = analyze(_as_mxl(SIMPLE_SCORE), "piece.mxl")

        assert result.key == "C major"
        assert result.measure_count == 2


class TestAnalyzeErrors:
    def test_raises_for_unparseable_content(self) -> None:
        with pytest.raises(AnalysisError):
            analyze(b"this is not xml at all", "piece.musicxml")

    def test_raises_for_the_wrong_root_element(self) -> None:
        with pytest.raises(AnalysisError):
            analyze(b"<not-musicxml/>", "piece.musicxml")
