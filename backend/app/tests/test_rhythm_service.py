from pathlib import Path

import pytest
from music21 import meter, stream
from music21 import note as m21note

from app.domains.analysis.rhythm import analyze_rhythm, analyze_rhythm_from_score
from app.domains.analysis.service import AnalysisError

_FIXTURES = Path(__file__).parent / "fixtures"
# A seven-bar two-part study written to exercise every measurement: a cell
# repeated in m1-m2, a syncopated half note in m3, a tie over the m4/m5
# barline, a rest closing the first phrase, triplets and a dotted figure in
# m6, and a whole note to finish.
RHYTHM_STUDY = (_FIXTURES / "rhythm_study.musicxml").read_bytes()
# Twelve unvaried quarter notes with a bar of rest in the middle.
MELODY_LINE = (_FIXTURES / "melody_line.musicxml").read_bytes()
# Four parts moving together - the case where note count and attack count
# diverge sharply.
SATB = (_FIXTURES / "harmony_satb.musicxml").read_bytes()


def _line(durations: list[float | None], time_signature: str = "4/4") -> stream.Score:
    """Build a one-part score from a list of quarter lengths; `None` is a rest."""
    score = stream.Score()
    part = stream.Part()
    part.partName = "Line"
    part.insert(0, meter.TimeSignature(time_signature))
    for quarter_length in durations:
        part.append(
            m21note.Rest(quarterLength=4.0)
            if quarter_length is None
            else m21note.Note("C4", quarterLength=quarter_length)
        )
    score.insert(0, part)
    score.makeMeasures(inPlace=True)
    return score


class TestRhythmShape:
    def test_returns_the_documented_top_level_shape(self) -> None:
        result = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml")

        assert 0.0 <= result.score <= 100.0
        assert isinstance(result.strengths, list)
        assert isinstance(result.issues, list)
        assert result.technical_data.density.note_count == 38

    def test_reports_the_metric_frame_it_measured_against(self) -> None:
        td = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml").technical_data

        assert td.time_signatures == ["4/4"]
        assert td.tempo == 96.0
        assert td.measure_count == 7
        assert td.total_quarters == 28.0
        assert td.part_count == 2


class TestRhythmicDensity:
    def test_separates_attack_points_from_raw_note_count(self) -> None:
        td = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml").technical_data

        density = td.density
        assert density.note_count == 38
        assert density.rest_count == 2
        # Two parts often articulate together, so there are fewer attack
        # points in time than there are notes.
        assert density.onset_count == 27
        assert density.notes_per_measure == 5.43
        assert density.onsets_per_measure == 3.86
        assert density.notes_per_quarter == 1.357

    def test_a_homophonic_texture_is_not_counted_as_four_times_denser(self) -> None:
        # All four voices of the chorale move together: 40 notes, but only 10
        # distinct attacks.
        td = analyze_rhythm(SATB, "harmony_satb.musicxml").technical_data

        assert td.density.note_count == 40
        assert td.density.onset_count == 10
        assert td.density.onsets_per_measure == 3.33

    def test_tracks_activity_bar_by_bar(self) -> None:
        td = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml").technical_data

        by_number = {m.measure: m for m in td.density.per_measure}
        assert len(td.density.per_measure) == 7
        # m5 is the tied note landing plus a long rest in both parts.
        assert by_number[5].onsets == 1
        assert by_number[5].sounding_ratio == 0.25
        assert by_number[6].onsets == 6
        assert td.density.busiest_measure == 6
        assert td.density.quietest_measure == 5

    def test_measures_how_much_of_the_time_is_rest(self) -> None:
        td = analyze_rhythm(MELODY_LINE, "melody_line.musicxml").technical_data

        # One bar of rest out of four.
        assert td.density.rest_ratio == 0.25


class TestNoteDurationVariety:
    def test_counts_every_distinct_note_value(self) -> None:
        td = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml").technical_data

        durations = td.durations
        assert durations.distinct_durations == 6
        names = [d.name for d in durations.by_duration]
        assert names[0] == "Quarter"
        assert "Dotted Quarter" in names
        assert "Eighth Triplet (1/3 QL)" in names
        assert durations.most_common == "Quarter"
        assert durations.most_common_ratio == 0.368

    def test_reports_the_span_between_shortest_and_longest(self) -> None:
        td = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml").technical_data

        durations = td.durations
        assert durations.shortest == pytest.approx(1 / 3)
        assert durations.longest == 4.0
        assert durations.range_ratio == 12.0

    def test_counts_dotted_notes_tuplets_and_ties(self) -> None:
        td = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml").technical_data

        durations = td.durations
        assert durations.dotted_count == 1
        assert durations.tuplet_count == 3
        assert durations.tied_count == 1

    def test_variety_index_is_zero_when_every_note_is_the_same(self) -> None:
        td = analyze_rhythm(MELODY_LINE, "melody_line.musicxml").technical_data

        assert td.durations.distinct_durations == 1
        assert td.durations.variety_index == 0.0

    def test_variety_index_is_one_when_values_are_used_equally(self) -> None:
        # Evenness, not breadth: two values in equal measure score 1.0.
        td = analyze_rhythm_from_score(_line([1.0, 0.5, 1.0, 0.5])).technical_data

        assert td.durations.distinct_durations == 2
        assert td.durations.variety_index == 1.0


class TestSyncopation:
    def test_finds_a_note_sustained_across_a_stronger_beat(self) -> None:
        td = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml").technical_data

        sustained = [
            i for i in td.syncopation.instances if i.kind == "sustained-over-beat"
        ]
        assert len(sustained) == 1
        found = sustained[0]
        assert found.measure == 3
        assert found.beat == 1.5
        assert found.duration == 2.0
        # Enters on the weakest position in the bar and holds across beat 2.
        assert found.onset_strength == 0.125
        assert found.crossed_strength == 0.25

    def test_finds_a_note_tied_over_the_barline(self) -> None:
        td = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml").technical_data

        tied = [i for i in td.syncopation.instances if i.kind == "tied-over-barline"]
        assert len(tied) == 1
        assert tied[0].measure == 4
        assert tied[0].beat == 4.0
        assert td.syncopation.tied_over_barline == 1

    def test_summarises_the_syncopation_and_offbeat_rates(self) -> None:
        td = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml").technical_data

        syncopation = td.syncopation
        assert syncopation.syncopated_note_count == 2
        assert syncopation.syncopation_ratio == 0.053
        # Offbeat attacks are counted separately: landing between beats is
        # only syncopation when something stronger goes unarticulated.
        assert syncopation.offbeat_onset_count == 7
        assert syncopation.offbeat_ratio == 0.184
        assert syncopation.by_kind == {
            "sustained-over-beat": 1,
            "tied-over-barline": 1,
        }

    def test_a_note_ending_on_the_next_beat_is_not_syncopated(self) -> None:
        # A plain quarter note on beat 2 reaches beat 3 without crossing it.
        td = analyze_rhythm_from_score(_line([1.0, 1.0, 1.0, 1.0])).technical_data

        assert td.syncopation.syncopated_note_count == 0

    def test_a_half_note_on_beat_two_is_syncopated(self) -> None:
        # The same onset, held one beat longer, now covers the stronger beat 3.
        td = analyze_rhythm_from_score(_line([1.0, 2.0, 1.0])).technical_data

        assert td.syncopation.syncopated_note_count == 1
        found = td.syncopation.instances[0]
        assert found.kind == "sustained-over-beat"
        assert found.onset_strength == 0.25
        assert found.crossed_strength == 0.5

    def test_a_bar_of_pure_rest_is_not_a_missed_downbeat(self) -> None:
        # m3 of the melody fixture is a whole rest - silence, not displacement.
        td = analyze_rhythm(MELODY_LINE, "melody_line.musicxml").technical_data

        assert td.syncopation.silent_downbeats == 0

    def test_counts_a_downbeat_played_around_but_never_struck(self) -> None:
        # The second note runs from beat 4 of bar 1 into bar 2, so bar 2 is
        # sounding but its downbeat is never articulated.
        td = analyze_rhythm_from_score(_line([3.0, 2.0, 3.0, 4.0])).technical_data

        assert td.syncopation.silent_downbeats == 1


class TestRepetition:
    def test_finds_a_recurring_rhythmic_cell(self) -> None:
        td = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml").technical_data

        patterns = td.repetition.repeated_patterns
        assert patterns
        best = patterns[0]
        assert best.part_id == "P1"
        assert best.pattern == ["Quarter", "Eighth", "Eighth", "Quarter"]
        assert best.quarter_lengths == [1.0, 0.5, 0.5, 1.0]
        assert best.occurrences == 2
        assert best.measures == [1, 2]

    def test_counts_restatements_without_overlapping_them(self) -> None:
        # Twelve steady quarters contain nine overlapping four-note windows
        # but only three actual restatements of the cell.
        td = analyze_rhythm(MELODY_LINE, "melody_line.musicxml").technical_data

        patterns = td.repetition.repeated_patterns
        assert len(patterns) == 1
        assert patterns[0].occurrences == 3
        assert patterns[0].measures == [1, 2, 4]

    def test_measures_how_often_a_bar_repeats_an_earlier_bars_rhythm(self) -> None:
        td = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml").technical_data

        repetition = td.repetition
        assert repetition.distinct_measure_rhythms == 5
        assert repetition.repeated_measure_count == 2
        assert repetition.measure_repetition_ratio == 0.286

    def test_detects_a_cell_repeated_back_to_back_as_an_ostinato(self) -> None:
        td = analyze_rhythm_from_score(
            _line([1.0, 0.5, 0.5] * 4)
        ).technical_data

        repetition = td.repetition
        assert repetition.has_ostinato is True
        assert repetition.ostinato_pattern == ["Quarter", "Eighth", "Eighth"]
        assert repetition.ostinato_occurrences == 4


class TestPhraseRhythm:
    def test_segments_the_texture_at_silences(self) -> None:
        td = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml").technical_data

        phrases = td.phrases
        assert phrases.phrase_count == 2
        first, second = phrases.phrases
        assert (first.start_measure, first.end_measure) == (1, 5)
        assert first.length_quarters == 17.0
        assert first.length_measures == 4.25
        assert first.note_count == 28
        # The rest that closed the phrase.
        assert first.following_rest_quarters == 3.0
        assert (second.start_measure, second.end_measure) == (6, 7)
        assert second.length_quarters == 8.0

    def test_reports_regular_phrasing_when_lengths_agree(self) -> None:
        # Two one-bar phrases split by a bar's rest.
        td = analyze_rhythm_from_score(
            _line([1.0, 1.0, 1.0, 1.0, None, 1.0, 1.0, 1.0, 1.0])
        ).technical_data

        assert td.phrases.phrase_count == 2
        assert td.phrases.is_regular is True
        assert td.phrases.distinct_lengths == 1
        assert td.phrases.most_common_length_measures == 1.0

    def test_reports_irregular_phrasing_when_lengths_differ(self) -> None:
        td = analyze_rhythm(MELODY_LINE, "melody_line.musicxml").technical_data

        assert td.phrases.phrase_count == 2
        assert td.phrases.is_regular is False
        assert td.phrases.distinct_lengths == 2

    def test_a_continuous_texture_is_one_phrase(self) -> None:
        td = analyze_rhythm(SATB, "harmony_satb.musicxml").technical_data

        assert td.phrases.phrase_count == 1
        assert td.phrases.phrases[0].length_measures == 3.0

    def test_detects_a_pickup_bar(self) -> None:
        score = stream.Score()
        part = stream.Part()
        part.partName = "Line"
        pickup = stream.Measure(number=1)
        pickup.insert(0, meter.TimeSignature("4/4"))
        pickup.paddingLeft = 3.0
        pickup.append(m21note.Note("C4", quarterLength=1.0))
        full = stream.Measure(number=2)
        full.append(m21note.Note("D4", quarterLength=4.0))
        part.append(pickup)
        part.append(full)
        score.insert(0, part)

        td = analyze_rhythm_from_score(score).technical_data

        assert td.phrases.has_anacrusis is True
        assert td.phrases.anacrusis_quarters == 1.0


class TestPartBreakdown:
    def test_reports_each_part_separately(self) -> None:
        td = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml").technical_data

        melody, bass = td.parts
        assert (melody.part_id, melody.name) == ("P1", "Melody")
        assert melody.note_count == 26
        assert melody.notes_per_measure == 3.71
        assert melody.distinct_durations == 6
        assert melody.syncopated_count == 2

        assert (bass.part_id, bass.name) == ("P2", "Bass")
        assert bass.note_count == 12
        assert bass.distinct_durations == 3
        # The bass keeps a plain half-note pulse.
        assert bass.syncopated_count == 0


class TestScoring:
    def test_the_study_scores_well_with_matching_strengths(self) -> None:
        result = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml")

        assert result.score >= 80.0
        joined = " ".join(result.strengths).lower()
        assert "density" in joined
        assert "varied note values" in joined
        assert "syncopation" in joined
        assert "recurring rhythmic cell" in joined
        assert "tuplets" in joined

    def test_an_unvaried_line_is_marked_down_for_it(self) -> None:
        result = analyze_rhythm(MELODY_LINE, "melody_line.musicxml")

        joined = " ".join(result.issues).lower()
        assert "same length" in joined
        assert "squarely on the beat" in joined
        assert result.score < 80.0

    def test_a_varied_rhythm_scores_above_an_unvaried_one(self) -> None:
        varied = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml")
        flat = analyze_rhythm(MELODY_LINE, "melody_line.musicxml")

        assert varied.score > flat.score

    def test_scoring_is_deterministic(self) -> None:
        first = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml")
        second = analyze_rhythm(RHYTHM_STUDY, "rhythm_study.musicxml")

        assert first.score == second.score
        assert first.model_dump() == second.model_dump()


class TestEdges:
    def test_raises_for_a_score_with_no_sounding_notes(self) -> None:
        score = stream.Score()
        part = stream.Part()
        part.insert(0, meter.TimeSignature("4/4"))
        part.append(m21note.Rest(quarterLength=4))
        score.insert(0, part)

        with pytest.raises(AnalysisError):
            analyze_rhythm_from_score(score)

    def test_raises_for_unparseable_content(self) -> None:
        with pytest.raises(AnalysisError):
            analyze_rhythm(b"this is not xml at all", "piece.musicxml")

    def test_a_single_note_is_too_short_to_score(self) -> None:
        result = analyze_rhythm_from_score(_line([4.0]))

        assert result.score == 0.0
        assert any("too few notes" in issue.lower() for issue in result.issues)

    def test_handles_a_compound_metre(self) -> None:
        # 6/8 groups as two dotted-quarter beats, so an eighth on the fourth
        # eighth of the bar is a strong position, not a weak one.
        td = analyze_rhythm_from_score(_line([0.5] * 12, "6/8")).technical_data

        assert td.time_signatures == ["6/8"]
        assert td.measure_count == 2
        assert td.syncopation.syncopated_note_count == 0
