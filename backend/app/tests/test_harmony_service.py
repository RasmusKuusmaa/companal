from pathlib import Path

import pytest
from music21 import key as m21key
from music21 import meter, stream
from music21 import note as m21note

from app.domains.analysis.harmony import analyze_harmony, analyze_harmony_from_score
from app.domains.analysis.service import AnalysisError

_FIXTURES = Path(__file__).parent / "fixtures"
# A three-bar SATB exercise carrying deliberate faults: parallel fifths and
# octaves on the V->vi move in m2, and a V7 in m3 whose seventh rises instead
# of falling. Everything else is textbook, so each finding below is planted.
SATB = (_FIXTURES / "harmony_satb.musicxml").read_bytes()
# Piano (with a written chord) plus violin - no part is a single voice, so
# this is the score that exercises the positional voice fallback.
MULTI_PART = (_FIXTURES / "multi_part.musicxml").read_bytes()
MELODY_LINE = (_FIXTURES / "melody_line.musicxml").read_bytes()

_VOICES = ("Soprano", "Alto", "Tenor", "Bass")


def _satb(chords: list[tuple[str, str, str, str]], key_name: str = "C") -> stream.Score:
    """Build a four-part score from (soprano, alto, tenor, bass) quarter notes."""
    score = stream.Score()
    for voice_index, part_name in enumerate(_VOICES):
        part = stream.Part()
        part.partName = part_name
        part.insert(0, m21key.Key(key_name))
        part.insert(0, meter.TimeSignature("4/4"))
        for chord in chords:
            part.append(m21note.Note(chord[voice_index], quarterLength=1))
        score.insert(0, part)
    score.makeMeasures(inPlace=True)
    return score


class TestHarmonyShape:
    def test_returns_the_documented_top_level_shape(self) -> None:
        result = analyze_harmony(SATB, "harmony_satb.musicxml")

        assert 0.0 <= result.score <= 100.0
        assert isinstance(result.strengths, list)
        assert isinstance(result.issues, list)
        assert result.technical_data.chord_count == 10

    def test_reports_the_key_it_analyzed_against(self) -> None:
        td = analyze_harmony(SATB, "harmony_satb.musicxml").technical_data

        assert td.key == "C major"
        assert td.mode == "major"
        # The key is written into the score, so it isn't an estimate.
        assert td.key_confidence == 1.0
        assert td.measure_count == 3


class TestChordProgression:
    def test_reads_the_vertical_sonorities_in_order(self) -> None:
        td = analyze_harmony(SATB, "harmony_satb.musicxml").technical_data

        assert [c.bass for c in td.chords] == [
            "C3", "F3", "G3", "C3", "G3", "A3", "F3", "G3", "G3", "C3",
        ]
        opening = td.chords[0]
        assert opening.pitches == ["C3", "G3", "E4", "C5"]
        assert opening.root == "C"
        assert opening.quality == "major"
        assert opening.inversion == 0
        assert opening.is_consonant is True

    def test_merges_a_held_chord_into_one_sonority(self) -> None:
        # The final I lasts a half note against no other movement; it must not
        # come back as two identical quarter-note chords.
        td = analyze_harmony(SATB, "harmony_satb.musicxml").technical_data

        final = td.chords[-1]
        assert final.duration == 2.0
        assert final.pitches == ["C3", "E4", "G4", "C5"]

    def test_describes_each_move_between_chords(self) -> None:
        td = analyze_harmony(SATB, "harmony_satb.musicxml").technical_data

        assert len(td.progression) == 9
        first = td.progression[0]
        assert (first.from_numeral, first.to_numeral) == ("I", "IV")
        assert first.root_motion == "up P4"
        assert first.kind == "functional"


class TestRomanNumerals:
    def test_labels_every_chord_in_the_key(self) -> None:
        td = analyze_harmony(SATB, "harmony_satb.musicxml").technical_data

        assert [c.roman_numeral for c in td.chords] == [
            "I", "IV", "V", "I", "V", "vi", "IV", "V", "V7", "I",
        ]
        assert [c.scale_degree for c in td.chords[:4]] == [1, 4, 5, 1]

    def test_labels_a_seventh_chord_and_its_inversion(self) -> None:
        td = analyze_harmony(SATB, "harmony_satb.musicxml").technical_data

        dominant_seventh = td.chords[8]
        assert dominant_seventh.roman_numeral == "V7"
        assert dominant_seventh.inversion == 0
        assert dominant_seventh.is_consonant is False

    def test_reads_a_minor_key_with_its_raised_leading_tone(self) -> None:
        # i - iv - V - i in A minor: the G# of the dominant belongs to the
        # key (harmonic minor), so nothing here is chromatic.
        score = _satb(
            [
                ("A4", "C4", "E3", "A2"),
                ("A4", "D4", "F3", "D3"),
                ("G#4", "B3", "E3", "E3"),
                ("A4", "C4", "E3", "A2"),
            ],
            key_name="a",
        )
        td = analyze_harmony_from_score(score).technical_data

        assert td.key == "a minor"
        assert [c.roman_numeral for c in td.chords] == ["i", "iv", "V", "i"]
        assert td.functional.diatonic_ratio == 1.0


class TestFunctionalHarmony:
    def test_assigns_a_function_to_each_chord(self) -> None:
        td = analyze_harmony(SATB, "harmony_satb.musicxml").technical_data

        assert [c.function for c in td.chords] == [
            "tonic", "predominant", "dominant", "tonic", "dominant",
            "tonic", "predominant", "dominant", "dominant", "tonic",
        ]
        assert td.functional.function_counts == {
            "tonic": 4,
            "predominant": 2,
            "dominant": 4,
        }
        assert td.functional.diatonic_ratio == 1.0
        assert td.functional.distinct_numerals == 5
        assert td.functional.most_common_numeral == "I"

    def test_flags_a_dominant_falling_back_to_a_predominant(self) -> None:
        score = _satb(
            [
                ("C5", "E4", "G3", "C3"),
                ("B4", "G4", "D4", "G3"),  # V
                ("C5", "A4", "F4", "F3"),  # IV - retrogression
                ("C5", "E4", "G3", "C3"),
            ]
        )
        td = analyze_harmony_from_score(score).technical_data

        assert [s.kind for s in td.progression] == [
            "functional",
            "retrogression",
            "functional",
        ]
        assert [(r.from_numeral, r.to_numeral) for r in td.functional.retrogressions] == [
            ("V", "IV")
        ]

    def test_detects_an_applied_dominant_from_its_target(self) -> None:
        # music21 reads the D major triad as a chromatic "II"; naming it V/V
        # takes the chord that follows.
        score = _satb(
            [
                ("C5", "E4", "G3", "C3"),
                ("A4", "F#4", "D4", "D3"),
                ("B4", "G4", "D4", "G3"),
                ("C5", "E4", "G3", "C3"),
            ]
        )
        td = analyze_harmony_from_score(score).technical_data

        assert td.chords[1].is_diatonic is False
        assert td.chords[1].function == "chromatic"
        assert td.chords[1].applied_to == "V/V"
        assert td.functional.secondary_dominants == ["V/V"]
        assert td.functional.chromatic_chord_indices == [1]


class TestCadences:
    def test_identifies_the_closing_perfect_authentic_cadence(self) -> None:
        td = analyze_harmony(SATB, "harmony_satb.musicxml").technical_data

        final = td.cadences[-1]
        assert final.is_final is True
        assert final.type == "authentic"
        # Both chords root position, tonic in the soprano.
        assert final.strength == "perfect-authentic"
        assert (final.from_numeral, final.to_numeral) == ("V7", "I")

    def test_does_not_call_a_prolonged_dominant_a_cadence(self) -> None:
        # V -> V7 across the m2/m3 barline is one harmony continuing, not an
        # arrival on the dominant.
        td = analyze_harmony(SATB, "harmony_satb.musicxml").technical_data

        assert [(c.chord_index, c.type) for c in td.cadences] == [(4, "half"), (9, "authentic")]

    def test_an_imperfect_authentic_cadence_is_graded_lower(self) -> None:
        # Same V - I, but the soprano lands on the third rather than the tonic.
        score = _satb(
            [
                ("C5", "E4", "G3", "C3"),
                ("D5", "G4", "B3", "G3"),
                ("E5", "G4", "C4", "C3"),
            ]
        )
        td = analyze_harmony_from_score(score).technical_data

        final = td.cadences[-1]
        assert final.type == "authentic"
        assert final.strength == "imperfect-authentic"


class TestVoiceLeading:
    def test_uses_the_parts_as_voices_when_each_is_a_single_line(self) -> None:
        td = analyze_harmony(SATB, "harmony_satb.musicxml").technical_data

        leading = td.voice_leading
        assert leading.voice_source == "parts"
        assert leading.voice_ids == ["Soprano", "Alto", "Tenor", "Bass"]
        assert leading.voice_count == 4
        assert leading.transitions == 9

    def test_measures_the_motion_between_every_pair_of_voices(self) -> None:
        td = analyze_harmony(SATB, "harmony_satb.musicxml").technical_data

        leading = td.voice_leading
        assert set(leading.motion_counts) <= {
            "parallel", "similar", "contrary", "oblique", "noMotion",
        }
        # Six voice pairs across nine transitions.
        assert sum(leading.motion_counts.values()) == 54
        assert leading.average_motion_semitones == 2.17

    def test_falls_back_to_positional_voices_when_a_part_has_chords(self) -> None:
        # The piano part writes E4 and G4 as one chord, so parts cannot serve
        # as voices; the analysis says so rather than guessing.
        td = analyze_harmony(MULTI_PART, "multi_part.musicxml").technical_data

        assert td.voice_leading.voice_source == "vertical-positions"
        assert td.voice_leading.voice_ids == ["v3", "v2", "v1"]

    def test_reports_no_faults_for_clean_part_writing(self) -> None:
        score = _satb(
            [
                ("C5", "E4", "G3", "C3"),
                ("B4", "D4", "G3", "G3"),
                ("C5", "E4", "G3", "C3"),
            ]
        )
        result = analyze_harmony_from_score(score)

        leading = result.technical_data.voice_leading
        assert leading.parallel_fifths == []
        assert leading.parallel_octaves == []
        assert leading.hidden_parallels == []
        assert leading.voice_crossings == []
        assert "No parallel fifths or octaves." in result.strengths


class TestParallelFifths:
    def test_finds_the_planted_parallel_fifths(self) -> None:
        td = analyze_harmony(SATB, "harmony_satb.musicxml").technical_data

        fifths = td.voice_leading.parallel_fifths
        assert len(fifths) == 2
        planted = fifths[1]
        assert planted.kind == "fifth"
        assert (planted.lower_voice, planted.upper_voice) == ("Bass", "Tenor")
        assert planted.lower_motion == "G3->A3"
        assert planted.upper_motion == "D4->E4"
        assert planted.from_interval == "P5"
        assert planted.to_interval == "P5"
        assert planted.measure == 2

    def test_surfaces_them_as_an_issue(self) -> None:
        result = analyze_harmony(SATB, "harmony_satb.musicxml")

        assert any("parallel fifths" in issue.lower() for issue in result.issues)

    def test_catches_antiparallel_fifths_too(self) -> None:
        # The bass falls while the tenor rises, so the motion is contrary -
        # but a fifth still becomes a fifth (P5 -> P12), which strict style
        # forbids just as it forbids consecutive fifths in similar motion.
        score = _satb(
            [
                ("C5", "E4", "G3", "C3"),
                ("B4", "G4", "D4", "G2"),
            ]
        )
        td = analyze_harmony_from_score(score).technical_data

        assert td.voice_leading.motion_counts.get("contrary", 0) > 0
        antiparallel = td.voice_leading.parallel_fifths
        assert len(antiparallel) == 1
        assert (antiparallel[0].from_interval, antiparallel[0].to_interval) == ("P5", "P12")

    def test_a_fifth_followed_by_another_interval_is_not_flagged(self) -> None:
        score = _satb(
            [
                ("C5", "E4", "G3", "C3"),
                ("B4", "D4", "G3", "G3"),
            ]
        )
        td = analyze_harmony_from_score(score).technical_data

        assert td.voice_leading.parallel_fifths == []


class TestParallelOctaves:
    def test_finds_the_planted_parallel_octave(self) -> None:
        td = analyze_harmony(SATB, "harmony_satb.musicxml").technical_data

        octaves = td.voice_leading.parallel_octaves
        assert len(octaves) == 1
        planted = octaves[0]
        assert planted.kind == "octave"
        assert (planted.lower_voice, planted.upper_voice) == ("Bass", "Alto")
        assert planted.lower_motion == "G3->A3"
        assert planted.upper_motion == "G4->A4"
        assert planted.from_interval == "P8"
        assert planted.to_interval == "P8"

    def test_surfaces_them_as_an_issue(self) -> None:
        result = analyze_harmony(SATB, "harmony_satb.musicxml")

        assert any("parallel octaves" in issue.lower() for issue in result.issues)

    def test_a_direct_octave_approached_by_step_is_not_reported(self) -> None:
        # Outer voices reach an octave by similar motion, but the soprano
        # arrives by step - the standard exemption, so it isn't a fault.
        score = _satb(
            [
                ("E4", "C4", "G3", "C3"),
                ("F4", "C4", "A3", "F3"),
            ]
        )
        td = analyze_harmony_from_score(score).technical_data

        assert td.voice_leading.hidden_parallels == []


class TestUnresolvedDissonances:
    def test_flags_a_chordal_seventh_that_rises(self) -> None:
        td = analyze_harmony(SATB, "harmony_satb.musicxml").technical_data

        unresolved = td.dissonances.unresolved
        assert len(unresolved) == 1
        seventh = unresolved[0]
        assert seventh.kind == "chordal-seventh"
        assert seventh.voice == "Alto"
        assert seventh.pitch == "F4"
        assert seventh.expected == "to fall by step into the next chord"
        assert seventh.actual == "moves to G4"
        assert seventh.resolved is False

    def test_counts_the_dissonant_sonorities(self) -> None:
        td = analyze_harmony(SATB, "harmony_satb.musicxml").technical_data

        dissonances = td.dissonances
        assert dissonances.seventh_count == 1
        assert dissonances.dissonant_chord_count == 1
        assert dissonances.ends_dissonant is False

    def test_a_seventh_that_falls_by_step_is_accepted(self) -> None:
        score = _satb(
            [
                ("C5", "E4", "G3", "C3"),
                ("B4", "F4", "D4", "G3"),  # V7, seventh F4 in the alto
                ("C5", "E4", "C4", "C3"),  # F4 -> E4
            ]
        )
        td = analyze_harmony_from_score(score).technical_data

        assert td.dissonances.unresolved == []
        assert td.dissonances.seventh_count == 1
        assert td.dissonances.resolved_count >= 1

    def test_a_held_seventh_is_judged_once_the_harmony_changes(self) -> None:
        # The V7 is prolonged over two sonorities; the seventh has not failed
        # to resolve while its own chord is still sounding.
        score = _satb(
            [
                ("B4", "F4", "D4", "G3"),
                ("D5", "F4", "B3", "G3"),  # same V7, upper voices rearranged
                ("C5", "E4", "C4", "C3"),
            ]
        )
        td = analyze_harmony_from_score(score).technical_data

        assert [d.chord_index for d in td.dissonances.unresolved] == []

    def test_flags_a_leading_tone_in_an_outer_voice_that_fails_to_rise(self) -> None:
        score = _satb(
            [
                ("C5", "E4", "G3", "C3"),
                ("B4", "G4", "D4", "G3"),  # V, leading tone B4 in the soprano
                ("A4", "E4", "C4", "A3"),  # falls to A4 instead of rising
            ]
        )
        td = analyze_harmony_from_score(score).technical_data

        leading_tones = [d for d in td.dissonances.unresolved if d.kind == "leading-tone"]
        assert len(leading_tones) == 1
        assert leading_tones[0].voice == "Soprano"
        assert leading_tones[0].pitch == "B4"
        assert leading_tones[0].expected == "to rise a semitone to the tonic"

    def test_reports_a_piece_that_ends_on_a_dissonance(self) -> None:
        score = _satb(
            [
                ("C5", "E4", "G3", "C3"),
                ("B4", "F4", "D4", "G3"),  # ends on V7
            ]
        )
        result = analyze_harmony_from_score(score)
        dissonances = result.technical_data.dissonances

        assert dissonances.ends_dissonant is True
        assert any(d.kind == "final-chord" for d in dissonances.unresolved)


class TestScoring:
    def test_clean_writing_scores_higher_than_faulty_writing(self) -> None:
        clean = analyze_harmony_from_score(
            _satb(
                [
                    ("C5", "E4", "G3", "C3"),
                    ("B4", "D4", "G3", "G3"),
                    ("C5", "E4", "G3", "C3"),
                ]
            )
        )
        faulty = analyze_harmony(SATB, "harmony_satb.musicxml")

        assert clean.score > faulty.score
        assert clean.score >= 90.0

    def test_the_exercise_scores_with_matching_strengths_and_issues(self) -> None:
        result = analyze_harmony(SATB, "harmony_satb.musicxml")

        joined_strengths = " ".join(result.strengths).lower()
        assert "perfect authentic cadence" in joined_strengths
        assert "functional" in joined_strengths

        joined_issues = " ".join(result.issues).lower()
        assert "parallel fifths" in joined_issues
        assert "parallel octaves" in joined_issues
        assert "unresolved dissonance" in joined_issues

    def test_scoring_is_deterministic(self) -> None:
        first = analyze_harmony(SATB, "harmony_satb.musicxml")
        second = analyze_harmony(SATB, "harmony_satb.musicxml")

        assert first.score == second.score
        assert first.model_dump() == second.model_dump()


class TestEdges:
    def test_raises_when_the_score_has_no_simultaneous_pitches(self) -> None:
        # A single melodic line has no harmony to read.
        with pytest.raises(AnalysisError):
            analyze_harmony(MELODY_LINE, "melody_line.musicxml")

    def test_raises_for_unparseable_content(self) -> None:
        with pytest.raises(AnalysisError):
            analyze_harmony(b"this is not xml at all", "piece.musicxml")

    def test_a_single_chord_is_too_short_to_score(self) -> None:
        score = _satb([("C5", "E4", "G3", "C3")])
        result = analyze_harmony_from_score(score)

        assert result.score == 0.0
        assert any("too few chords" in issue.lower() for issue in result.issues)
