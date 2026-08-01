"""Algorithmic melody analysis, via music21.

A deliberately non-AI engine: every number here comes from a music21
measurement or a plain counting/heuristic rule, so the same input always
yields the same score and each point of that score can be traced back to a
concrete musical fact. (LLM-driven critique lives elsewhere - this module
must never import or call into it.)

The line that gets scored is the *top sounding line of one part*: for a
multi-part score the part with the highest mean pitch is taken as the melody,
and any written chord is reduced to its highest note. Melodic intervals are
measured between consecutive sounding notes; rests are kept only to segment
the line into phrases for cadence detection.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Any

from music21 import interval as m21interval
from music21 import key as m21key
from music21 import note as m21note
from music21.stream.base import Score

from app.domains.analysis.schemas import (
    CadenceRead,
    ContourData,
    IntervalData,
    LeapData,
    MelodicIntervalRead,
    MelodyAnalysis,
    MelodyTechnicalData,
    MotifRead,
    RangeData,
    RepeatedSequenceRead,
    RepetitionData,
    StepwiseData,
)
from app.domains.analysis.service import AnalysisError, _parse_score

# A step is a second (1-2 semitones); anything a third or wider is a leap.
_STEP_MAX_SEMITONES = 2
# Only leaps this size or larger (a perfect fourth and up) are held to the
# "resolve by step in the opposite direction" expectation - a leap of a third
# is mild enough that leaving it unresolved isn't a real weakness.
_LARGE_LEAP_SEMITONES = 5
_OCTAVE_SEMITONES = 12


@dataclass
class _Event:
    """One melody slot in time: a sounding pitch, or a rest."""

    midi: int | None
    name: str | None  # nameWithOctave, e.g. "C4"; None for a rest
    pitch: Any | None  # music21 Pitch; None for a rest
    measure: int
    is_rest: bool


def _event_from_note(note_obj: Any) -> _Event:
    if note_obj.isRest:
        return _Event(None, None, None, note_obj.measureNumber or 0, True)
    # Reduce a written chord to its top note - the melody is the line a
    # listener follows, which for a chord is its highest pitch.
    top = note_obj.pitch if not note_obj.isChord else max(note_obj.pitches, key=lambda p: p.midi)
    return _Event(top.midi, top.nameWithOctave, top, note_obj.measureNumber or 0, False)


def _choose_melody_part(score: Score) -> Any:
    """Pick the part carrying the melody: the one with the highest mean pitch.

    Returns a stream to read the line from (a Part, or the whole score
    flattened when the score has no explicit parts).
    """
    parts = list(score.parts)
    if not parts:
        return score.flatten()
    if len(parts) == 1:
        return parts[0]

    def mean_midi(part: Any) -> float:
        midis = [m for n in part.recurse().notes if (m := _event_from_note(n).midi) is not None]
        return sum(midis) / len(midis) if midis else -1.0

    return max(parts, key=mean_midi)


def _extract_events(part: Any) -> list[_Event]:
    # flatten() so notes and rests come back in strict offset order even when
    # they're nested inside Measure objects.
    return [_event_from_note(n) for n in part.flatten().notesAndRests]


def _part_id(part: Any) -> str:
    instrument = part.getInstrument(returnDefault=True) if hasattr(part, "getInstrument") else None
    if instrument is not None and getattr(instrument, "partId", None):
        return str(instrument.partId)
    return str(getattr(part, "id", "melody"))


def _key_object(score: Score) -> Any | None:
    explicit = score.recurse().getElementsByClass(m21key.Key).first()
    if explicit is not None:
        return explicit
    try:
        return score.analyze("key")
    except Exception:
        # No pitched content to estimate a key from - cadences simply won't
        # know which degree is the tonic.
        return None


def _interval_between(a: _Event, b: _Event) -> tuple[str, int]:
    """Directed interval from event ``a`` to ``b`` as (name, signed semitones).

    Named against real pitches (via Note objects) so the diatonic spelling is
    correct - e.g. C->D reads "M2", not just "+2".
    """
    iv = m21interval.Interval(noteStart=m21note.Note(a.name), noteEnd=m21note.Note(b.name))
    return iv.directedName, int(iv.semitones)


# --------------------------------------------------------------------------- #
# Individual measurements
# --------------------------------------------------------------------------- #


def _build_intervals(pitched: list[_Event]) -> tuple[IntervalData, list[int]]:
    """Consecutive melodic intervals, plus the raw signed-semitone list the
    other measurements are derived from."""
    reads: list[MelodicIntervalRead] = []
    semis: list[int] = []
    by_name: Counter[str] = Counter()
    for a, b in zip(pitched, pitched[1:], strict=False):
        name, semitones = _interval_between(a, b)
        magnitude = abs(semitones)
        by_name[name] += 1
        semis.append(semitones)
        reads.append(
            MelodicIntervalRead(
                from_pitch=a.name or "",
                to_pitch=b.name or "",
                name=name,
                semitones=semitones,
                is_step=1 <= magnitude <= _STEP_MAX_SEMITONES,
                is_leap=magnitude > _STEP_MAX_SEMITONES,
            )
        )

    magnitudes = [abs(s) for s in semis]
    data = IntervalData(
        count=len(reads),
        average_semitones=round(sum(magnitudes) / len(magnitudes), 2) if magnitudes else 0.0,
        largest_semitones=max(magnitudes) if magnitudes else 0,
        by_name=dict(by_name),
        sequence=reads,
    )
    return data, semis


def _build_range(pitched: list[_Event]) -> RangeData:
    lowest = min(pitched, key=lambda e: e.midi)  # type: ignore[arg-type,return-value]
    highest = max(pitched, key=lambda e: e.midi)  # type: ignore[arg-type,return-value]
    iv = m21interval.Interval(
        noteStart=m21note.Note(lowest.name), noteEnd=m21note.Note(highest.name)
    )
    return RangeData(
        lowest=lowest.name or "",
        highest=highest.name or "",
        semitones=int(iv.semitones),
        interval_name=iv.niceName,
    )


def _build_contour(semis: list[int]) -> ContourData:
    moves = ["u" if s > 0 else "d" if s < 0 else "r" for s in semis]
    parsons = "*" + "".join(moves)
    ascending = moves.count("u")
    descending = moves.count("d")
    repeated = moves.count("r")

    # Direction changes: count sign flips, ignoring repeated notes (which
    # don't establish a direction).
    directions = [s for s in semis if s != 0]
    changes = sum(
        1 for x, y in zip(directions, directions[1:], strict=False) if (x > 0) != (y > 0)
    )
    return ContourData(
        parsons=parsons,
        direction_changes=changes,
        ascending_moves=ascending,
        descending_moves=descending,
        repeated_moves=repeated,
        shape=_classify_shape(semis, changes),
    )


def _classify_shape(semis: list[int], changes: int) -> str:
    if not semis:
        return "single-note"
    running = [0]
    for s in semis:
        running.append(running[-1] + s)
    span = max(running) - min(running)
    if span == 0:
        return "static"

    net = running[-1] - running[0]
    hi_idx = running.index(max(running))
    lo_idx = running.index(min(running))
    last = len(running) - 1
    interior = lambda idx: 0 < idx < last  # noqa: E731

    if changes <= 1:
        if net > _STEP_MAX_SEMITONES:
            return "ascending"
        if net < -_STEP_MAX_SEMITONES:
            return "descending"
        return "flat"
    # A clear peak in the middle with lower endpoints is the classic arch;
    # the mirror image (a dip in the middle) is a valley.
    if interior(hi_idx) and running[0] < running[hi_idx] and running[-1] < running[hi_idx]:
        return "arch"
    if interior(lo_idx) and running[0] > running[lo_idx] and running[-1] > running[lo_idx]:
        return "valley"
    return "wave"


def _ngram_counts(items: list[Any], n: int) -> Counter[tuple[Any, ...]]:
    return Counter(
        tuple(items[i : i + n]) for i in range(len(items) - n + 1)
    )


def _build_repetition(pitched: list[_Event], semis: list[int]) -> RepetitionData:
    immediate = sum(1 for s in semis if s == 0)
    names = [e.name for e in pitched if e.name]
    pitch_counts = Counter(names)
    most_common_pitch, most_common_count = (
        pitch_counts.most_common(1)[0] if pitch_counts else (None, 0)
    )

    # Literal restatements: the longest pitch runs (length >= 3) that recur.
    repeated: list[RepeatedSequenceRead] = []
    for length in (4, 3):
        for gram, occ in _ngram_counts(names, length).most_common():
            if occ < 2:
                break
            # Skip a 3-gram already covered by a reported 4-gram restatement.
            if any(set(gram).issubset(set(r.pitches)) for r in repeated):
                continue
            repeated.append(RepeatedSequenceRead(pitches=list(gram), occurrences=occ))
        if len(repeated) >= 3:
            break

    return RepetitionData(
        immediate_repeats=immediate,
        repeated_note_ratio=round(immediate / len(semis), 3) if semis else 0.0,
        most_common_pitch=most_common_pitch,
        most_common_pitch_count=most_common_count,
        repeated_sequences=repeated[:3],
        has_repeated_phrases=any(len(r.pitches) >= 4 for r in repeated),
    )


def _build_motifs(semis: list[int]) -> list[MotifRead]:
    """Recurring shapes, matched on directed intervals so a motif restated at
    a new pitch level still counts as the same motif."""
    motifs: list[MotifRead] = []
    seen: list[tuple[int, ...]] = []
    for n in (4, 3):  # motifs of 5 then 4 notes
        for gram, occ in _ngram_counts(semis, n).most_common():
            if occ < 2:
                break
            # Don't also report a 3-interval motif that's just the tail/head
            # of a longer 4-interval motif already captured.
            if any(_is_subsequence(gram, longer) for longer in seen):
                continue
            seen.append(gram)
            motifs.append(
                MotifRead(
                    intervals=[_semitones_to_name(s) for s in gram],
                    length_notes=n + 1,
                    occurrences=occ,
                )
            )
    motifs.sort(key=lambda m: (m.occurrences, m.length_notes), reverse=True)
    return motifs[:5]


def _is_subsequence(short: tuple[int, ...], long: tuple[int, ...]) -> bool:
    return any(long[i : i + len(short)] == short for i in range(len(long) - len(short) + 1))


def _semitones_to_name(semitones: int) -> str:
    return m21interval.Interval(semitones).directedName


def _build_leaps(pitched: list[_Event], semis: list[int]) -> LeapData:
    leaps = [s for s in semis if abs(s) > _STEP_MAX_SEMITONES]
    largest = max(semis, key=abs) if semis else 0

    unresolved = 0
    for i, s in enumerate(semis):
        if abs(s) < _LARGE_LEAP_SEMITONES:
            continue
        nxt = semis[i + 1] if i + 1 < len(semis) else None
        # Resolved = next motion is a step in the opposite direction.
        resolved = (
            nxt is not None
            and 1 <= abs(nxt) <= _STEP_MAX_SEMITONES
            and (nxt > 0) != (s > 0)
        )
        if not resolved:
            unresolved += 1

    consecutive_max = _longest_run(
        [abs(s) > _STEP_MAX_SEMITONES for s in semis], True
    )
    return LeapData(
        count=len(leaps),
        ratio=round(len(leaps) / len(semis), 3) if semis else 0.0,
        largest_semitones=abs(largest),
        largest_name=_semitones_to_name(largest) if largest else None,
        unresolved=unresolved,
        consecutive_leaps_max=consecutive_max,
    )


def _build_stepwise(semis: list[int]) -> StepwiseData:
    is_step = [1 <= abs(s) <= _STEP_MAX_SEMITONES for s in semis]
    count = sum(is_step)
    return StepwiseData(
        count=count,
        ratio=round(count / len(semis), 3) if semis else 0.0,
        longest_run=_longest_run(is_step, True),
    )


def _longest_run(flags: list[bool], target: bool) -> int:
    best = run = 0
    for f in flags:
        run = run + 1 if f == target else 0
        best = max(best, run)
    return best


def _build_cadences(events: list[_Event], key_obj: Any | None) -> list[CadenceRead]:
    """Segment the line into phrases at rests and classify how each one ends.

    Melodic (not harmonic) cadences: with only a single line to look at, a
    phrase that settles by step onto the tonic reads as a strong close, one
    that lands on the dominant as a half-cadence feel, and anything else as
    weak.
    """
    phrases: list[list[_Event]] = []
    current: list[_Event] = []
    for ev in events:
        if ev.is_rest:
            if current:
                phrases.append(current)
                current = []
        else:
            current.append(ev)
    if current:
        phrases.append(current)

    cadences: list[CadenceRead] = []
    for phrase in phrases:
        final = phrase[-1]
        degree = (
            key_obj.getScaleDegreeFromPitch(final.pitch) if key_obj is not None else None
        )
        approach = "none"
        approach_semis: int | None = None
        if len(phrase) >= 2:
            _, approach_semis = _interval_between(phrase[-2], final)
            magnitude = abs(approach_semis)
            if magnitude == 0:
                approach = "repeat"
            elif magnitude <= _STEP_MAX_SEMITONES:
                approach = "step-down" if approach_semis < 0 else "step-up"
            else:
                approach = "leap"

        on_tonic = degree == 1
        cadences.append(
            CadenceRead(
                measure=final.measure,
                final_pitch=final.name or "",
                scale_degree=degree,
                approach=approach,
                type=_classify_cadence(degree, approach),
                on_tonic=on_tonic,
            )
        )
    return cadences


def _classify_cadence(degree: int | None, approach: str) -> str:
    if degree == 1:
        if approach in ("step-down", "step-up"):
            return "authentic-like"
        # Lands on the tonic, but by leap/repeat or as an isolated note - a
        # weaker sense of arrival than a stepwise close.
        return "tonic arrival"
    if degree == 5:
        return "half-like"
    if degree in (2, 7):
        return "weak (unstable degree)"
    if degree is None:
        return "stepwise close" if approach.startswith("step") else "inconclusive"
    return "weak"


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #


def _score_melody(
    technical: MelodyTechnicalData,
) -> tuple[float, list[str], list[str]]:
    """Turn the measurements into a 0-100 score with matching strengths/issues.

    Six weighted components, each rewarding a well-known property of an
    effective melodic line. Every band and threshold is a heuristic, not a law
    - the goal is a transparent, repeatable rubric, not a verdict.
    """
    strengths: list[str] = []
    issues: list[str] = []
    total = technical.intervals.count

    if total == 0:
        issues.append("Melody is too short to analyze (needs at least two notes).")
        return 0.0, strengths, issues

    score = 0.0

    # 1. Conjunct/disjunct balance (25) --------------------------------------
    moving = technical.stepwise.count + technical.leaps.count
    step_ratio = technical.stepwise.count / moving if moving else 0.0
    if 0.55 <= step_ratio <= 0.82:
        score += 25
        strengths.append(
            f"Mostly stepwise motion ({step_ratio:.0%}) — smooth and singable."
        )
    elif step_ratio < 0.55:
        score += 25 * max(step_ratio / 0.55, 0.0)
        issues.append(
            f"Disjunct writing: only {step_ratio:.0%} of motion is stepwise, "
            f"{technical.leaps.ratio:.0%} is by leap."
        )
    else:  # > 0.82 - almost nothing but steps
        score += 25 - (step_ratio - 0.82) / 0.18 * 10
        issues.append(
            f"Nearly all motion is stepwise ({step_ratio:.0%}) — the line risks "
            "sounding scalar and predictable."
        )

    # 2. Range (15) ----------------------------------------------------------
    span = technical.range.semitones
    if 7 <= span <= 19:
        score += 15
        strengths.append(f"Comfortable {technical.range.interval_name.lower()} range.")
    elif span < 7:
        score += 15 * max(span / 7, 0.2)
        if span < 4:
            issues.append(
                f"Very narrow range ({technical.range.interval_name.lower()}) — little "
                "expressive contrast."
            )
    else:  # > 19
        score += max(15 - (span - 19) * 0.8, 4)
        if span > 24:
            issues.append(
                f"Very wide range ({technical.range.interval_name.lower()}) — demanding "
                "to sing or play."
            )

    # 3. Motivic coherence (20) ----------------------------------------------
    if technical.motifs:
        best = max(technical.motifs, key=lambda m: m.occurrences)
        coherence = min(20.0, 12 + (best.occurrences - 2) * 3 + (best.length_notes - 3) * 2)
        score += coherence
        strengths.append(
            f"Recurring motif ({best.length_notes}-note shape appears "
            f"{best.occurrences}×) gives the line coherence."
        )
    else:
        score += 4
        issues.append("No recurring motif — the melody lacks a memorable, repeated idea.")

    # 4. Contour interest (15) -----------------------------------------------
    changes_per_note = technical.contour.direction_changes / total
    if 0.2 <= changes_per_note <= 0.55:
        score += 15
    elif changes_per_note < 0.2:
        score += 15 * max(changes_per_note / 0.2, 0.3)
        issues.append("Contour changes direction rarely — the line feels one-directional.")
    else:
        score += max(15 - (changes_per_note - 0.55) * 20, 5)
        issues.append("Contour zig-zags frequently — the line feels restless.")
    if technical.contour.shape == "arch":
        score = min(100.0, score + 2)
        strengths.append("Clear arch contour — a natural rise and fall.")

    # 5. Leap handling (15) --------------------------------------------------
    leap_score = 15.0
    if technical.leaps.unresolved:
        leap_score -= min(technical.leaps.unresolved * 3, 9)
        issues.append(
            f"{technical.leaps.unresolved} large leap(s) not resolved by a step in "
            "the opposite direction."
        )
    if technical.leaps.consecutive_leaps_max >= 3:
        leap_score -= 3
        issues.append(
            f"Up to {technical.leaps.consecutive_leaps_max} leaps in a row — the line "
            "jumps around without settling."
        )
    if technical.leaps.largest_semitones >= _OCTAVE_SEMITONES and technical.leaps.largest_name:
        issues.append(f"Contains a wide leap of a {technical.leaps.largest_name}.")
    score += max(leap_score, 0.0)

    # 6. Closure (10) --------------------------------------------------------
    final = technical.cadences[-1] if technical.cadences else None
    if final is None:
        score += 3
    elif final.on_tonic and final.approach.startswith("step"):
        score += 10
        strengths.append("Ends with a clear stepwise cadence on the tonic.")
    elif final.on_tonic:
        score += 8
    elif final.scale_degree in (3, 5):
        score += 6
    elif final.scale_degree is None and final.approach.startswith("step"):
        score += 6
    else:
        score += 3
        issues.append("Melody does not resolve to the tonic — the ending feels unfinished.")

    # Excessive literal repetition is a coherence trap, not coherence.
    if technical.repetition.has_repeated_phrases and not technical.motifs:
        issues.append("Repeats material literally without developing it.")
    # Only meaningful once there are enough notes for one pitch to dominate;
    # a short fragment naturally reuses a handful of pitches.
    if (
        technical.note_count >= 8
        and technical.repetition.most_common_pitch_count / technical.note_count > 0.4
    ):
        score = max(0.0, score - 5)
        issues.append(
            f"Over-relies on one pitch ({technical.repetition.most_common_pitch}, "
            f"{technical.repetition.most_common_pitch_count} of {technical.note_count} notes)."
        )

    return round(max(0.0, min(100.0, score)), 1), strengths, issues


# --------------------------------------------------------------------------- #
# Public entry points
# --------------------------------------------------------------------------- #


def analyze_melody_from_score(score: Score) -> MelodyAnalysis:
    """Run the full melody analysis on an already-parsed music21 Score."""
    part = _choose_melody_part(score)
    events = _extract_events(part)
    pitched = [e for e in events if not e.is_rest]

    if not pitched:
        raise AnalysisError("The score has no pitched notes to analyze as a melody.")

    key_obj = _key_object(score)
    intervals, semis = _build_intervals(pitched)

    technical = MelodyTechnicalData(
        part_id=_part_id(part),
        key=str(key_obj) if key_obj is not None else None,
        note_count=len(pitched),
        intervals=intervals,
        range=_build_range(pitched),
        contour=_build_contour(semis),
        repetition=_build_repetition(pitched, semis),
        motifs=_build_motifs(semis),
        leaps=_build_leaps(pitched, semis),
        stepwise=_build_stepwise(semis),
        cadences=_build_cadences(events, key_obj),
    )

    score_value, strengths, issues = _score_melody(technical)
    return MelodyAnalysis(
        score=score_value,
        strengths=strengths,
        issues=issues,
        technical_data=technical,
    )


def analyze_melody(content: bytes, filename: str) -> MelodyAnalysis:
    """Parse MusicXML bytes and return the melody analysis.

    Raises ``AnalysisError`` if music21 cannot parse ``content`` or the score
    contains no pitched notes at all.
    """
    return analyze_melody_from_score(_parse_score(content, filename))
