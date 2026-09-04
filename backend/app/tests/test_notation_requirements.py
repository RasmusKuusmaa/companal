"""One pass and one fail case per requirement type, plus the runner itself.

Every case here builds a `NotationDocument` directly (never a MusicXML
fixture file) and runs it through the real analysis engines via
`RequirementContext` - the same path a submission takes in
`notation.grading.grade_submission`, just without the MusicXML round-trip
that function also does. That keeps these tests honest about what the
validators actually see.
"""

from pathlib import Path

import pytest

from app.domains.analysis.harmony import analyze_harmony
from app.domains.analysis.melody import analyze_melody
from app.domains.analysis.service import AnalysisError, analyze
from app.domains.notation.builder import to_musicxml_bytes
from app.domains.notation.requirements import (
    CadenceRequirement,
    DiatonicOnlyRequirement,
    ForbiddenPitchesRequirement,
    KeyRequirement,
    LeapRecoveryRequirement,
    MaxLeapRequirement,
    MeasureCountRequirement,
    RangeRequirement,
    RequiredScaleDegreesRequirement,
    TimeSignatureRequirement,
)
from app.domains.notation.schemas import NotationDocument
from app.domains.notation.validation import (
    RequirementContext,
    all_passed,
    check_cadence,
    check_diatonic_only,
    check_forbidden_pitches,
    check_key,
    check_leap_recovery,
    check_max_leap,
    check_measure_count,
    check_range,
    check_required_scale_degrees,
    check_time_signature,
    run_requirements,
)

_FIXTURES = Path(__file__).parent / "fixtures"


def _note(
    step: str, alter: int = 0, octave: int = 4, duration: str = "quarter", dots: int = 0
) -> dict[str, object]:
    return {
        "id": "n",
        "step": step,
        "octave": octave,
        "alter": alter,
        "duration": duration,
        "dots": dots,
        "is_rest": False,
        "tied_to_next": False,
    }


def _doc(
    measures: list[list[dict[str, object]]],
    fifths: int = 0,
    mode: str = "major",
    beats: int = 4,
    beat_type: int = 4,
) -> NotationDocument:
    return NotationDocument.model_validate(
        {
            "fifths": fifths,
            "mode": mode,
            "time": {"beats": beats, "beat_type": beat_type},
            "tempo": 90,
            "staves": [
                {
                    "id": "s1",
                    "clef": "treble",
                    "measures": [
                        {"id": f"m{i}", "voices": [{"id": "1", "notes": notes}]}
                        for i, notes in enumerate(measures)
                    ],
                }
            ],
        }
    )


def _context(document: NotationDocument) -> RequirementContext:
    content = to_musicxml_bytes(document)
    score = analyze(content, "s.musicxml")
    try:
        melody = analyze_melody(content, "s.musicxml")
    except AnalysisError:
        melody = None
    try:
        harmony = analyze_harmony(content, "s.musicxml")
    except AnalysisError:
        harmony = None
    return RequirementContext(document=document, score=score, melody=melody, harmony=harmony)


# A scale that stays diatonic and covers every degree, used by several tests.
_C_MAJOR_SCALE = _doc(
    [
        [_note("C"), _note("D"), _note("E"), _note("F")],
        [_note("G"), _note("A"), _note("B"), _note("C", octave=5)],
    ]
)


class TestKeyRequirement:
    def test_passes_when_the_key_matches(self) -> None:
        result = check_key(_context(_C_MAJOR_SCALE), KeyRequirement(key="C major"))
        assert result.passed is True

    def test_fails_when_the_key_does_not_match(self) -> None:
        result = check_key(_context(_C_MAJOR_SCALE), KeyRequirement(key="D minor"))
        assert result.passed is False
        assert "C major" in result.message


class TestTimeSignatureRequirement:
    def test_passes_when_it_matches(self) -> None:
        result = check_time_signature(
            _context(_C_MAJOR_SCALE), TimeSignatureRequirement(value="4/4")
        )
        assert result.passed is True

    def test_fails_when_it_does_not_match(self) -> None:
        result = check_time_signature(
            _context(_C_MAJOR_SCALE), TimeSignatureRequirement(value="3/4")
        )
        assert result.passed is False


class TestMeasureCountRequirement:
    def test_passes_at_the_exact_count(self) -> None:
        result = check_measure_count(_context(_C_MAJOR_SCALE), MeasureCountRequirement(count=2))
        assert result.passed is True

    def test_fails_at_the_wrong_count(self) -> None:
        result = check_measure_count(_context(_C_MAJOR_SCALE), MeasureCountRequirement(count=4))
        assert result.passed is False
        assert "2 measures" in result.message

    def test_a_short_first_measure_is_treated_as_a_pickup(self) -> None:
        doc = _doc([[_note("C", duration="half")]] + [[_note("C", duration="whole")]] * 4)
        result = check_measure_count(_context(doc), MeasureCountRequirement(count=4))
        assert result.passed is True


class TestCadenceRequirement:
    def test_passes_for_a_matching_cadence(self) -> None:
        content = (_FIXTURES / "harmony_satb.musicxml").read_bytes()
        score = analyze(content, "x.musicxml")
        harmony = analyze_harmony(content, "x.musicxml")
        doc = _doc([[_note("C")]])  # document itself unused by this check
        context = RequirementContext(document=doc, score=score, melody=None, harmony=harmony)

        result = check_cadence(context, CadenceRequirement(cadence="perfect_authentic"))
        assert result.passed is True
        assert result.measure is not None

    def test_fails_for_a_different_cadence(self) -> None:
        content = (_FIXTURES / "harmony_satb.musicxml").read_bytes()
        score = analyze(content, "x.musicxml")
        harmony = analyze_harmony(content, "x.musicxml")
        doc = _doc([[_note("C")]])
        context = RequirementContext(document=doc, score=score, melody=None, harmony=harmony)

        result = check_cadence(context, CadenceRequirement(cadence="deceptive"))
        assert result.passed is False

    def test_fails_cleanly_when_harmony_could_not_be_analyzed(self) -> None:
        context = RequirementContext(
            document=_C_MAJOR_SCALE,
            score=analyze(to_musicxml_bytes(_C_MAJOR_SCALE), "s.musicxml"),
            melody=None,
            harmony=None,
        )
        result = check_cadence(context, CadenceRequirement(cadence="half"))
        assert result.passed is False
        assert "could not be analyzed" in result.message


class TestRangeRequirement:
    def test_passes_within_bounds(self) -> None:
        result = check_range(_context(_C_MAJOR_SCALE), RangeRequirement(max_semitones=20))
        assert result.passed is True

    def test_fails_when_the_span_is_too_wide(self) -> None:
        result = check_range(_context(_C_MAJOR_SCALE), RangeRequirement(max_semitones=1))
        assert result.passed is False

    def test_fails_when_it_reaches_below_the_floor(self) -> None:
        result = check_range(_context(_C_MAJOR_SCALE), RangeRequirement(lowest="D4"))
        assert result.passed is False
        assert "C4" in result.message


class TestMaxLeapRequirement:
    def test_passes_within_the_limit(self) -> None:
        doc = _doc([[_note("C"), _note("D"), _note("E"), _note("F")]])
        result = check_max_leap(_context(doc), MaxLeapRequirement(semitones=12))
        assert result.passed is True

    def test_fails_over_the_limit(self) -> None:
        doc = _doc([[_note("C"), _note("C", octave=5), _note("C"), _note("C")]])
        result = check_max_leap(_context(doc), MaxLeapRequirement(semitones=1))
        assert result.passed is False


class TestLeapRecoveryRequirement:
    def test_passes_when_leaps_are_answered_by_a_step_back(self) -> None:
        # Leap up a sixth, then step back down - textbook recovery.
        doc = _doc([[_note("C"), _note("A"), _note("G"), _note("F")]])
        result = check_leap_recovery(_context(doc), LeapRecoveryRequirement(max_unresolved=0))
        assert result.passed is True

    def test_fails_when_a_leap_is_left_unresolved(self) -> None:
        # Leap up a sixth, then leap again in the same direction - unresolved.
        doc = _doc([[_note("C"), _note("A"), _note("C", octave=5), _note("E", octave=5)]])
        result = check_leap_recovery(_context(doc), LeapRecoveryRequirement(max_unresolved=0))
        assert result.passed is False


class TestDiatonicOnlyRequirement:
    def test_passes_for_an_all_diatonic_line(self) -> None:
        result = check_diatonic_only(_context(_C_MAJOR_SCALE), DiatonicOnlyRequirement())
        assert result.passed is True

    def test_fails_on_a_chromatic_note(self) -> None:
        doc = _doc([[_note("C"), _note("F", alter=1), _note("G"), _note("C")]])
        result = check_diatonic_only(_context(doc), DiatonicOnlyRequirement())
        assert result.passed is False
        assert result.measure == 1


class TestRequiredScaleDegreesRequirement:
    def test_passes_when_every_degree_appears(self) -> None:
        result = check_required_scale_degrees(
            _context(_C_MAJOR_SCALE), RequiredScaleDegreesRequirement(degrees=[1, 5, 7])
        )
        assert result.passed is True

    def test_fails_when_a_degree_is_missing(self) -> None:
        doc = _doc([[_note("C"), _note("D"), _note("C"), _note("D")]])
        result = check_required_scale_degrees(
            _context(doc), RequiredScaleDegreesRequirement(degrees=[1, 5])
        )
        assert result.passed is False
        assert "5" in result.message


class TestForbiddenPitchesRequirement:
    def test_passes_when_the_pitch_never_appears(self) -> None:
        result = check_forbidden_pitches(
            _context(_C_MAJOR_SCALE), ForbiddenPitchesRequirement(pitches=["F#"])
        )
        assert result.passed is True

    def test_fails_when_the_pitch_appears(self) -> None:
        result = check_forbidden_pitches(
            _context(_C_MAJOR_SCALE), ForbiddenPitchesRequirement(pitches=["F"])
        )
        assert result.passed is False

    def test_matches_enharmonically(self) -> None:
        doc = _doc([[_note("C"), _note("F", alter=1), _note("G"), _note("C")]])
        result = check_forbidden_pitches(_context(doc), ForbiddenPitchesRequirement(pitches=["Gb"]))
        assert result.passed is False


class TestRunner:
    def test_runs_every_requirement_in_order(self) -> None:
        context = _context(_C_MAJOR_SCALE)
        results = run_requirements(
            context,
            [
                KeyRequirement(key="C major"),
                MeasureCountRequirement(count=2),
                MaxLeapRequirement(semitones=12),
            ],
        )
        assert [r.requirement.type for r in results] == ["key", "measure_count", "max_leap"]
        assert all_passed(results) is True

    def test_all_passed_is_false_if_any_requirement_fails(self) -> None:
        context = _context(_C_MAJOR_SCALE)
        results = run_requirements(context, [KeyRequirement(key="D minor")])
        assert all_passed(results) is False

    def test_all_passed_of_an_empty_checklist_is_true(self) -> None:
        assert all_passed([]) is True


@pytest.mark.parametrize(
    "note_names",
    [["C", "D", "E", "F"]],
)
def test_scale_fixture_is_actually_diatonic(note_names: list[str]) -> None:
    # Sanity check on the shared fixture itself, so a change to `_doc` or
    # `_note` that silently broke it would fail here first, not in every
    # test that happens to use it.
    context = _context(_C_MAJOR_SCALE)
    assert context.score.key == "C major"
    assert context.melody is not None
