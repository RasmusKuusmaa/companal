from pathlib import Path

import pytest

from app.domains.analysis.combined import run_all_analyses
from app.domains.analysis.harmony import analyze_harmony
from app.domains.analysis.melody import analyze_melody
from app.domains.analysis.rhythm import analyze_rhythm
from app.domains.analysis.service import AnalysisError

_FIXTURES = Path(__file__).parent / "fixtures"
# Four parts: every engine has something to read.
SATB = (_FIXTURES / "harmony_satb.musicxml").read_bytes()
# A single line: melody and rhythm work, harmony has no chords to read.
MELODY_LINE = (_FIXTURES / "melody_line.musicxml").read_bytes()
RHYTHM_STUDY = (_FIXTURES / "rhythm_study.musicxml").read_bytes()
# A single whole rest: nothing for any engine to measure.
RESTS_ONLY = b"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list><score-part id="P1"><part-name>Music</part-name></score-part></part-list>
  <part id="P1"><measure number="1"><note><rest/><duration>4</duration></note></measure></part>
</score-partwise>
"""


class TestBundleShape:
    def test_returns_all_three_analyses_and_an_overall_score(self) -> None:
        bundle = run_all_analyses(SATB, "harmony_satb.musicxml")

        assert bundle.melody_analysis is not None
        assert bundle.harmony_analysis is not None
        assert bundle.rhythm_analysis is not None
        assert bundle.unavailable == []
        assert 0.0 <= bundle.overall_score <= 100.0

    def test_overall_score_is_the_mean_of_the_engines_that_ran(self) -> None:
        bundle = run_all_analyses(SATB, "harmony_satb.musicxml")

        scores = [
            bundle.melody_analysis.score,  # type: ignore[union-attr]
            bundle.harmony_analysis.score,  # type: ignore[union-attr]
            bundle.rhythm_analysis.score,  # type: ignore[union-attr]
        ]
        assert bundle.overall_score == round(sum(scores) / 3, 1)


class TestMatchesTheStandaloneEngines:
    """The bundle must equal what the three separate endpoints return.

    Each engine is given its own parse precisely so this holds: sharing one
    `Score` lets `chordify()` in the harmony engine disturb the offsets the
    rhythm engine reads, which silently shortened the piece.
    """

    @pytest.mark.parametrize(
        ("content", "filename"),
        [
            (SATB, "harmony_satb.musicxml"),
            (RHYTHM_STUDY, "rhythm_study.musicxml"),
            (MELODY_LINE, "melody_line.musicxml"),
        ],
    )
    def test_each_engine_matches_its_standalone_result(
        self, content: bytes, filename: str
    ) -> None:
        bundle = run_all_analyses(content, filename)

        assert bundle.melody_analysis == analyze_melody(content, filename)
        assert bundle.rhythm_analysis == analyze_rhythm(content, filename)
        if bundle.harmony_analysis is not None:
            assert bundle.harmony_analysis == analyze_harmony(content, filename)

    def test_the_rhythm_engine_still_sees_the_whole_piece(self) -> None:
        # The regression this design prevents: the harmony engine running
        # first used to cost the rhythm engine the final bar.
        bundle = run_all_analyses(RHYTHM_STUDY, "rhythm_study.musicxml")

        rhythm = bundle.rhythm_analysis
        assert rhythm is not None
        assert rhythm.technical_data.total_quarters == 28.0
        assert rhythm.technical_data.measure_count == 7

    def test_is_deterministic(self) -> None:
        first = run_all_analyses(SATB, "harmony_satb.musicxml")
        second = run_all_analyses(SATB, "harmony_satb.musicxml")

        assert first.model_dump() == second.model_dump()


class TestPartialAvailability:
    def test_an_engine_that_cannot_read_the_score_is_reported_not_fatal(self) -> None:
        bundle = run_all_analyses(MELODY_LINE, "melody_line.musicxml")

        assert bundle.melody_analysis is not None
        assert bundle.rhythm_analysis is not None
        # A single line has no simultaneous pitches to read as harmony.
        assert bundle.harmony_analysis is None
        assert [u.engine for u in bundle.unavailable] == ["harmony"]
        assert "no chords" in bundle.unavailable[0].reason

    def test_a_missing_engine_is_left_out_rather_than_scored_zero(self) -> None:
        bundle = run_all_analyses(MELODY_LINE, "melody_line.musicxml")

        ran = [
            a.score
            for a in (bundle.melody_analysis, bundle.harmony_analysis, bundle.rhythm_analysis)
            if a is not None
        ]
        assert len(ran) == 2
        assert bundle.overall_score == round(sum(ran) / 2, 1)
        # Averaging in a zero for the absent engine would drag it below this.
        assert bundle.overall_score > min(ran)

    def test_raises_only_when_no_engine_can_run(self) -> None:
        with pytest.raises(AnalysisError) as excinfo:
            run_all_analyses(RESTS_ONLY, "silence.musicxml")

        # The message names each engine's reason rather than just the first.
        message = str(excinfo.value)
        assert "melody" in message
        assert "harmony" in message
        assert "rhythm" in message

    def test_raises_for_unparseable_content(self) -> None:
        with pytest.raises(AnalysisError):
            run_all_analyses(b"this is not xml at all", "piece.musicxml")
