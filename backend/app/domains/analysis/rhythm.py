"""Algorithmic rhythm analysis, via music21.

The temporal counterpart to `melody.py` and `harmony.py`, and non-AI in the
same deliberate way: note durations, beat positions and metric accent weights
all come from music21, and every number here is counting against those. The
same score always yields the same result, and each finding points at a
specific note in a specific bar. (LLM-driven critique lives elsewhere - this
module must never import or call into it.)

Unlike the melody engine (one line) and the harmony engine (one vertical
slice at a time), this one reads *every* part: rhythmic density and phrase
rhythm are properties of the whole texture, not of any single voice. Totals
therefore cover the score, with a per-part breakdown alongside them.

Syncopation is judged by the standard displacement test rather than by
guessing at accents: a note is syncopated when it *sustains through* a metric
position stronger than the one it began on - a half note starting on beat 2
of 4/4 holds across beat 3, which is stronger, so the accent lands where no
attack does. Notes tied over a barline (the downbeat never re-articulated)
count too, and attacks falling between beats are tracked separately as
offbeat onsets, since an offbeat attack is only syncopation when something
stronger goes unarticulated.
"""

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from music21 import meter
from music21 import tempo as m21tempo
from music21.stream.base import Score

from app.domains.analysis.schemas import (
    DurationCountRead,
    DurationVarietyData,
    MeasureDensityRead,
    PhraseRead,
    PhraseRhythmData,
    RhythmAnalysis,
    RhythmicDensityData,
    RhythmicPatternRead,
    RhythmicRepetitionData,
    RhythmPartRead,
    RhythmTechnicalData,
    SyncopationData,
    SyncopationRead,
)
from app.domains.analysis.service import AnalysisError, _parse_score

# Offsets are compared in quarter notes; music21 uses exact Fractions for
# tuplets but arithmetic here goes through float, so comparisons need slack.
_EPSILON = 1e-6
# A gap shorter than this reads as articulation (a staccato lift, a breath
# mark) rather than the end of a phrase.
_PHRASE_GAP_QUARTERS = 1.0
# Rhythmic cells are matched at these lengths, longest first.
_PATTERN_LENGTHS = (4, 3)
_DEFAULT_BAR_QUARTERS = 4.0


@dataclass
class _Event:
    """One note or rest in one part, with its metric position."""

    part_id: str
    part_name: str | None
    measure: int
    offset: float  # absolute, in quarter notes from the start of the score
    bar_offset: float  # within its own measure
    duration: float
    beat: float
    strength: float  # music21 beatStrength: 1.0 on a downbeat
    is_rest: bool
    pitch: str | None
    tie: str | None
    duration_name: str
    quarter_length: float
    dots: int
    is_tuplet: bool
    time_signature: Any | None


@dataclass
class _PartEvents:
    part_id: str
    name: str | None
    events: list[_Event] = field(default_factory=list)


def _safe(getter: Any) -> Any:
    """music21 raises from beat/beatStrength when a note has no metric context."""
    try:
        return getter()
    except Exception:
        return None


def _is_articulated(event: _Event) -> bool:
    """True when the event is a fresh attack.

    The far side of a tie is the same note still sounding, so it is not a new
    articulation - which is the whole point of tying over a barline.
    """
    return not event.is_rest and event.tie not in ("stop", "continue")


# --------------------------------------------------------------------------- #
# Extracting events
# --------------------------------------------------------------------------- #


def _part_id(part: Any, position: int) -> str:
    instrument = part.getInstrument(returnDefault=True) if hasattr(part, "getInstrument") else None
    if instrument is not None and getattr(instrument, "partId", None):
        return str(instrument.partId)
    return str(getattr(part, "id", None) or f"part-{position + 1}")


def _describe_event(
    element: Any, part_id: str, part_name: str | None, score: Score
) -> _Event:
    duration_obj = element.duration
    # A written chord is one rhythmic event, not one per pitch - its top note
    # stands in for the attack.
    pitch = None
    if not element.isRest:
        pitch = (
            max(element.pitches, key=lambda p: p.midi).nameWithOctave
            if element.isChord
            else element.pitch.nameWithOctave
        )

    strength = _safe(lambda: float(element.beatStrength))
    beat = _safe(lambda: float(element.beat))
    return _Event(
        part_id=part_id,
        part_name=part_name,
        measure=element.measureNumber or 0,
        offset=float(_safe(lambda: element.getOffsetInHierarchy(score)) or element.offset),
        bar_offset=float(element.offset),
        duration=float(element.quarterLength),
        beat=beat if beat is not None else 1.0,
        strength=strength if strength is not None else 1.0,
        is_rest=bool(element.isRest),
        pitch=pitch,
        tie=element.tie.type if element.tie is not None else None,
        duration_name=str(duration_obj.fullName),
        quarter_length=float(duration_obj.quarterLength),
        dots=int(duration_obj.dots),
        is_tuplet=bool(duration_obj.tuplets),
        time_signature=_safe(lambda: element.getContextByClass(meter.TimeSignature)),
    )


def _extract_parts(score: Score) -> list[_PartEvents]:
    parts = list(score.parts)
    if not parts:
        # A score with no explicit parts still has a rhythmic surface.
        flat = score.flatten()
        events = [_describe_event(e, "part-1", None, score) for e in flat.notesAndRests]
        return [_PartEvents("part-1", None, events)]

    extracted: list[_PartEvents] = []
    for position, part in enumerate(parts):
        part_id = _part_id(part, position)
        name = getattr(part, "partName", None)
        events = [
            _describe_event(element, part_id, name, score)
            for element in part.recurse().notesAndRests
        ]
        extracted.append(_PartEvents(part_id, name, events))
    return extracted


def _time_signatures(score: Score) -> list[str]:
    seen: list[str] = []
    for signature in score.recurse().getElementsByClass(meter.TimeSignature):
        if signature.ratioString not in seen:
            seen.append(signature.ratioString)
    return seen


def _tempo(score: Score) -> float | None:
    mark = score.recurse().getElementsByClass(m21tempo.MetronomeMark).first()
    if mark is None or mark.number is None:
        return None
    return float(mark.number)


def _bar_quarters(event: _Event) -> float:
    if event.time_signature is None:
        return _DEFAULT_BAR_QUARTERS
    return float(event.time_signature.barDuration.quarterLength)


def _beat_quarters(event: _Event) -> float:
    if event.time_signature is None:
        return 1.0
    return float(event.time_signature.beatDuration.quarterLength)


# --------------------------------------------------------------------------- #
# Rhythmic density
# --------------------------------------------------------------------------- #


def _build_density(
    parts: list[_PartEvents], measures: list[int], total_quarters: float
) -> RhythmicDensityData:
    notes = [e for p in parts for e in p.events if not e.is_rest]
    rests = [e for p in parts for e in p.events if e.is_rest]
    attacks = [e for e in notes if _is_articulated(e)]
    onsets = {round(e.offset, 4) for e in attacks}
    measure_count = len(measures) or 1

    notes_by_measure: Counter[int] = Counter(e.measure for e in notes)
    onsets_by_measure: dict[int, set[float]] = {}
    for event in attacks:
        onsets_by_measure.setdefault(event.measure, set()).add(round(event.offset, 4))

    per_measure = [
        MeasureDensityRead(
            measure=number,
            onsets=len(onsets_by_measure.get(number, set())),
            notes=notes_by_measure.get(number, 0),
            sounding_ratio=_sounding_ratio(parts, number),
        )
        for number in measures
    ]

    # Sounding time is measured per part and summed, so a rest in one part
    # against a held note in another still counts as rest time for that part.
    sounding = sum(e.duration for e in notes)
    resting = sum(e.duration for e in rests)
    span = sounding + resting

    return RhythmicDensityData(
        note_count=len(notes),
        rest_count=len(rests),
        onset_count=len(onsets),
        notes_per_measure=round(len(notes) / measure_count, 2),
        onsets_per_measure=round(len(onsets) / measure_count, 2),
        notes_per_quarter=round(len(notes) / total_quarters, 3) if total_quarters else 0.0,
        rest_ratio=round(resting / span, 3) if span else 0.0,
        busiest_measure=max(per_measure, key=lambda m: m.notes).measure if per_measure else None,
        quietest_measure=min(per_measure, key=lambda m: m.notes).measure if per_measure else None,
        per_measure=per_measure,
    )


def _sounding_ratio(parts: list[_PartEvents], measure: int) -> float:
    """Share of the bar with at least one part sounding."""
    spans: list[tuple[float, float]] = []
    bar_quarters = 0.0
    for part in parts:
        for event in part.events:
            if event.measure != measure:
                continue
            bar_quarters = max(bar_quarters, _bar_quarters(event))
            if not event.is_rest:
                spans.append((event.bar_offset, event.bar_offset + event.duration))
    if not spans or bar_quarters <= 0:
        return 0.0

    covered = 0.0
    current_start, current_end = spans[0]
    for start, end in sorted(spans)[1:]:
        if start > current_end + _EPSILON:
            covered += current_end - current_start
            current_start, current_end = start, end
        else:
            current_end = max(current_end, end)
    covered += current_end - current_start
    return round(min(covered / bar_quarters, 1.0), 3)


# --------------------------------------------------------------------------- #
# Note duration variety
# --------------------------------------------------------------------------- #


def _build_durations(parts: list[_PartEvents]) -> DurationVarietyData:
    notes = [e for p in parts for e in p.events if not e.is_rest]
    if not notes:
        return DurationVarietyData(
            distinct_durations=0,
            by_duration=[],
            shortest=0.0,
            longest=0.0,
            range_ratio=0.0,
            most_common=None,
            most_common_ratio=0.0,
            variety_index=0.0,
            dotted_count=0,
            tuplet_count=0,
            tied_count=0,
        )

    by_name: Counter[str] = Counter(e.duration_name for e in notes)
    lengths = {e.duration_name: e.quarter_length for e in notes}
    total = len(notes)

    counts = [
        DurationCountRead(
            name=name,
            quarter_length=lengths[name],
            count=count,
            ratio=round(count / total, 3),
        )
        for name, count in by_name.most_common()
    ]
    shortest = min(e.quarter_length for e in notes)
    longest = max(e.quarter_length for e in notes)
    most_common_name, most_common_count = by_name.most_common(1)[0]

    return DurationVarietyData(
        distinct_durations=len(by_name),
        by_duration=counts,
        shortest=shortest,
        longest=longest,
        range_ratio=round(longest / shortest, 2) if shortest else 0.0,
        most_common=most_common_name,
        most_common_ratio=round(most_common_count / total, 3),
        variety_index=_normalised_entropy(list(by_name.values())),
        dotted_count=sum(1 for e in notes if e.dots),
        tuplet_count=sum(1 for e in notes if e.is_tuplet),
        tied_count=sum(1 for e in notes if e.tie in ("start", "continue")),
    )


def _normalised_entropy(counts: list[int]) -> float:
    """Shannon entropy of a distribution, scaled to 0..1 by its own maximum.

    Measures evenness rather than breadth: two durations used equally often
    score 1.0, exactly as five would. `distinct_durations` carries breadth.
    """
    total = sum(counts)
    if total == 0 or len(counts) < 2:
        return 0.0
    entropy = -sum((c / total) * math.log(c / total) for c in counts if c)
    return round(entropy / math.log(len(counts)), 3)


# --------------------------------------------------------------------------- #
# Syncopation
# --------------------------------------------------------------------------- #


def _build_syncopation(parts: list[_PartEvents], measures: list[int]) -> SyncopationData:
    instances: list[SyncopationRead] = []
    offbeat = 0
    tied_over_barline = 0
    notes = [e for p in parts for e in p.events if not e.is_rest]

    for event in notes:
        beat_quarters = _beat_quarters(event)
        on_beat = (
            beat_quarters > 0
            and abs(event.bar_offset % beat_quarters) < _EPSILON
        )
        if not on_beat:
            offbeat += 1

        crossed = _crossed_stronger_position(event)
        if crossed is not None:
            position, strength = crossed
            instances.append(
                SyncopationRead(
                    part_id=event.part_id,
                    measure=event.measure,
                    beat=round(event.beat, 3),
                    pitch=event.pitch,
                    duration=event.duration,
                    kind="sustained-over-beat",
                    onset_strength=event.strength,
                    crossed_strength=strength,
                    description=(
                        f"{event.duration_name.lower()} entering on beat "
                        f"{_format_beat(event.beat)} holds across the stronger beat "
                        f"{_format_beat(position / max(beat_quarters, _EPSILON) + 1)}"
                    ),
                )
            )
            continue

        if _ties_over_barline(event):
            tied_over_barline += 1
            instances.append(
                SyncopationRead(
                    part_id=event.part_id,
                    measure=event.measure,
                    beat=round(event.beat, 3),
                    pitch=event.pitch,
                    duration=event.duration,
                    kind="tied-over-barline",
                    onset_strength=event.strength,
                    crossed_strength=1.0,
                    description=(
                        f"tied across the barline into m.{event.measure + 1}, so that "
                        "downbeat is never re-articulated"
                    ),
                )
            )

    syncopated = len(instances)
    total = len(notes)
    by_kind = Counter(i.kind for i in instances)

    return SyncopationData(
        syncopated_note_count=syncopated,
        syncopation_ratio=round(syncopated / total, 3) if total else 0.0,
        offbeat_onset_count=offbeat,
        offbeat_ratio=round(offbeat / total, 3) if total else 0.0,
        tied_over_barline=tied_over_barline,
        silent_downbeats=_count_silent_downbeats(parts, measures),
        by_kind=dict(by_kind),
        instances=instances,
    )


def _crossed_stronger_position(event: _Event) -> tuple[float, float] | None:
    """The first metric position inside the note that outweighs its onset.

    Walking the beat grid strictly *between* onset and release: a note ending
    exactly on the next beat has not crossed it, so an ordinary quarter note
    on beat 2 is not syncopated, while a half note there is.
    """
    signature = event.time_signature
    if signature is None:
        return None
    beat_quarters = _beat_quarters(event)
    if beat_quarters <= 0:
        return None

    bar_quarters = _bar_quarters(event)
    end = min(event.bar_offset + event.duration, bar_quarters)
    position = (math.floor(event.bar_offset / beat_quarters) + 1) * beat_quarters

    while position < end - _EPSILON:
        weight = _safe(
            lambda p=position: float(signature.getAccentWeight(p, forcePositionMatch=False))
        )
        if weight is not None and weight > event.strength + _EPSILON:
            return position, weight
        position += beat_quarters
    return None


def _ties_over_barline(event: _Event) -> bool:
    if event.tie not in ("start", "continue"):
        return False
    return abs((event.bar_offset + event.duration) - _bar_quarters(event)) < _EPSILON


def _count_silent_downbeats(parts: list[_PartEvents], measures: list[int]) -> int:
    """Bars that are active but never attack beat 1.

    A bar of pure rest is silence, not metric displacement, so it doesn't
    count - only a bar that plays *around* its downbeat does.
    """
    attacked: set[int] = set()
    active: set[int] = set()
    for part in parts:
        for event in part.events:
            if event.is_rest:
                continue
            active.add(event.measure)
            if abs(event.bar_offset) < _EPSILON and _is_articulated(event):
                attacked.add(event.measure)
    # The first bar of an anacrusis has no downbeat to miss.
    return sum(1 for number in measures[1:] if number in active and number not in attacked)


def _format_beat(beat: float) -> str:
    return str(int(beat)) if abs(beat - round(beat)) < _EPSILON else f"{beat:.2f}".rstrip("0")


# --------------------------------------------------------------------------- #
# Repetition
# --------------------------------------------------------------------------- #


def _build_repetition(
    parts: list[_PartEvents], measures: list[int]
) -> RhythmicRepetitionData:
    patterns = _repeated_patterns(parts)
    ostinato = _find_ostinato(parts)

    signatures = [_measure_signature(parts, number) for number in measures]
    distinct = len(set(signatures))
    repeated = len(signatures) - distinct

    return RhythmicRepetitionData(
        repeated_patterns=patterns,
        distinct_measure_rhythms=distinct,
        repeated_measure_count=repeated,
        measure_repetition_ratio=round(repeated / len(signatures), 3) if signatures else 0.0,
        has_ostinato=ostinato is not None,
        ostinato_pattern=ostinato[0] if ostinato else None,
        ostinato_occurrences=ostinato[1] if ostinato else 0,
    )


def _cells(part: _PartEvents) -> list[tuple[float, bool]]:
    """The part's rhythm as (duration, is_rest) pairs.

    Rests are kept and tagged: a bar of quarter-rest-quarter-quarter is not
    the same rhythm as four quarter notes, even though the durations match.
    """
    return [(round(e.quarter_length, 4), e.is_rest) for e in part.events]


def _repeated_patterns(parts: list[_PartEvents]) -> list[RhythmicPatternRead]:
    found: list[RhythmicPatternRead] = []
    for part in parts:
        cells = _cells(part)
        names = _duration_names(part)
        seen: list[tuple[tuple[float, bool], ...]] = []
        covered: set[int] = set()
        for length in _PATTERN_LENGTHS:
            if len(cells) < length * 2:
                continue
            # Cheap sliding-window counting first: only cells that recur at
            # all are worth the cost of a non-overlapping recount.
            windows = Counter(
                tuple(cells[i : i + length]) for i in range(len(cells) - length + 1)
            )
            matched = [
                (gram, hits)
                for gram, count in windows.items()
                if count >= 2 and len(hits := _nonoverlapping_matches(cells, gram)) >= 2
            ]
            matched.sort(key=lambda item: len(item[1]), reverse=True)
            for gram, hits in matched:
                # Skip a short cell already covered by a longer one reported
                # for this part.
                if any(_is_subsequence(gram, longer) for longer in seen):
                    continue
                # Shifted windows over the same repeating bar describe one
                # figure, not several - keep the first and drop restatements
                # sitting mostly on top of it.
                span = {i for hit in hits for i in range(hit, hit + length)}
                if len(span & covered) * 2 > len(span):
                    continue
                covered |= span
                seen.append(gram)
                found.append(
                    RhythmicPatternRead(
                        pattern=[_cell_label(cell, names) for cell in gram],
                        quarter_lengths=[cell[0] for cell in gram],
                        length_notes=length,
                        occurrences=len(hits),
                        measures=[part.events[i].measure for i in hits],
                        part_id=part.part_id,
                    )
                )
    found.sort(key=lambda p: (p.occurrences, p.length_notes), reverse=True)
    return found[:5]


def _nonoverlapping_matches(
    cells: list[tuple[float, bool]], gram: tuple[tuple[float, bool], ...]
) -> list[int]:
    """Start indices of the cell's restatements, counted without overlap.

    Sliding-window counting would call four steady quarter notes a cell
    recurring six times; a restatement only counts once the previous one has
    finished, which is what "the figure comes back" means.
    """
    length = len(gram)
    hits: list[int] = []
    index = 0
    while index <= len(cells) - length:
        if tuple(cells[index : index + length]) == gram:
            hits.append(index)
            index += length
        else:
            index += 1
    return hits


def _duration_names(part: _PartEvents) -> dict[float, str]:
    return {round(e.quarter_length, 4): e.duration_name for e in part.events}


def _cell_label(cell: tuple[float, bool], names: dict[float, str]) -> str:
    quarter_length, is_rest = cell
    name = names.get(quarter_length, f"{quarter_length}QL")
    return f"{name} rest" if is_rest else name


def _is_subsequence(short: tuple[Any, ...], long: tuple[Any, ...]) -> bool:
    return any(long[i : i + len(short)] == short for i in range(len(long) - len(short) + 1))


def _find_ostinato(parts: list[_PartEvents]) -> tuple[list[str], int] | None:
    """The longest cell that repeats immediately back-to-back, if any."""
    best: tuple[list[str], int] | None = None
    for part in parts:
        cells = _cells(part)
        for length in _PATTERN_LENGTHS:
            for start in range(len(cells) - length * 2 + 1):
                gram = cells[start : start + length]
                repeats = 1
                cursor = start + length
                while cells[cursor : cursor + length] == gram:
                    repeats += 1
                    cursor += length
                if repeats >= 2 and (best is None or repeats > best[1]):
                    best = ([_cell_label(cell, _duration_names(part)) for cell in gram], repeats)
    return best


def _measure_signature(parts: list[_PartEvents], number: int) -> tuple[Any, ...]:
    """A measure's rhythm across the whole texture: its distinct attack points."""
    onsets = sorted(
        {
            round(event.bar_offset, 4)
            for part in parts
            for event in part.events
            if event.measure == number and not event.is_rest
        }
    )
    return tuple(onsets)


# --------------------------------------------------------------------------- #
# Phrase rhythm
# --------------------------------------------------------------------------- #


def _build_phrases(parts: list[_PartEvents], score: Score) -> PhraseRhythmData:
    """Segment the texture into phrases at silences of a beat or more."""
    spans = sorted(
        (e.offset, e.offset + e.duration)
        for part in parts
        for e in part.events
        if not e.is_rest
    )
    if not spans:
        return PhraseRhythmData(
            phrase_count=0,
            phrases=[],
            average_length_quarters=0.0,
            most_common_length_measures=None,
            is_regular=False,
            distinct_lengths=0,
            has_anacrusis=False,
            anacrusis_quarters=0.0,
        )

    bar_quarters = _score_bar_quarters(parts)
    groups: list[list[tuple[float, float]]] = [[spans[0]]]
    reach = spans[0][1]
    for start, end in spans[1:]:
        if start > reach + _PHRASE_GAP_QUARTERS - _EPSILON:
            groups.append([])
            reach = end
        else:
            reach = max(reach, end)
        groups[-1].append((start, end))

    phrases: list[PhraseRead] = []
    for index, group in enumerate(groups):
        start = min(s for s, _ in group)
        end = max(e for _, e in group)
        following = 0.0
        if index + 1 < len(groups):
            following = min(s for s, _ in groups[index + 1]) - end
        phrases.append(
            PhraseRead(
                index=index,
                start_measure=_measure_at(parts, start),
                end_measure=_measure_at(parts, max(start, end - _EPSILON)),
                start_offset=round(start, 3),
                length_quarters=round(end - start, 3),
                length_measures=round((end - start) / bar_quarters, 2),
                note_count=sum(
                    1
                    for part in parts
                    for e in part.events
                    if not e.is_rest and start - _EPSILON <= e.offset < end
                ),
                following_rest_quarters=round(max(following, 0.0), 3),
            )
        )

    lengths = [p.length_measures for p in phrases]
    length_counts = Counter(lengths)
    anacrusis = _anacrusis_quarters(score, bar_quarters)

    return PhraseRhythmData(
        phrase_count=len(phrases),
        phrases=phrases,
        average_length_quarters=round(sum(p.length_quarters for p in phrases) / len(phrases), 2),
        most_common_length_measures=length_counts.most_common(1)[0][0] if length_counts else None,
        is_regular=len(length_counts) == 1 and len(phrases) > 1,
        distinct_lengths=len(length_counts),
        has_anacrusis=anacrusis > 0.0,
        anacrusis_quarters=anacrusis,
    )


def _score_bar_quarters(parts: list[_PartEvents]) -> float:
    for part in parts:
        for event in part.events:
            if event.time_signature is not None:
                return _bar_quarters(event)
    return _DEFAULT_BAR_QUARTERS


def _measure_at(parts: list[_PartEvents], offset: float) -> int:
    """The measure sounding at this point: that of the latest event to start
    at or before it."""
    latest: _Event | None = None
    for part in parts:
        for event in part.events:
            if event.is_rest or event.offset > offset + _EPSILON:
                continue
            if latest is None or event.offset > latest.offset:
                latest = event
    return latest.measure if latest is not None else 0


def _anacrusis_quarters(score: Score, bar_quarters: float) -> float:
    """Length of a pickup bar, or 0.0 when the piece starts on a downbeat."""
    parts = list(score.parts)
    source = parts[0] if parts else score
    first = _safe(lambda: source.getElementsByClass("Measure").first())
    if first is None:
        return 0.0
    padding = float(getattr(first, "paddingLeft", 0.0) or 0.0)
    if padding > 0:
        return round(bar_quarters - padding, 3)
    actual = float(first.duration.quarterLength)
    if 0 < actual < bar_quarters - _EPSILON:
        return round(actual, 3)
    return 0.0


# --------------------------------------------------------------------------- #
# Per-part breakdown
# --------------------------------------------------------------------------- #


def _build_parts(
    parts: list[_PartEvents], measures: list[int], syncopation: SyncopationData
) -> list[RhythmPartRead]:
    syncopated_by_part = Counter(i.part_id for i in syncopation.instances)
    measure_count = len(measures) or 1

    reads: list[RhythmPartRead] = []
    for part in parts:
        notes = [e for e in part.events if not e.is_rest]
        rests = [e for e in part.events if e.is_rest]
        span = sum(e.duration for e in notes) + sum(e.duration for e in rests)
        reads.append(
            RhythmPartRead(
                part_id=part.part_id,
                name=part.name,
                note_count=len(notes),
                notes_per_measure=round(len(notes) / measure_count, 2),
                rest_ratio=(
                    round(sum(e.duration for e in rests) / span, 3) if span else 0.0
                ),
                syncopated_count=syncopated_by_part.get(part.part_id, 0),
                distinct_durations=len({e.duration_name for e in notes}),
                shortest=min((e.quarter_length for e in notes), default=0.0),
                longest=max((e.quarter_length for e in notes), default=0.0),
            )
        )
    return reads


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #


def _dominant_phrase_share(phrases: PhraseRhythmData) -> float:
    """Share of phrases running to the single most common length.

    Two phrases of different lengths are not "consistent" just because there
    are only two of them, so consistency is measured as agreement rather than
    by counting distinct values.
    """
    if not phrases.phrases:
        return 0.0
    counts = Counter(p.length_measures for p in phrases.phrases)
    return counts.most_common(1)[0][1] / len(phrases.phrases)


def _score_rhythm(technical: RhythmTechnicalData) -> tuple[float, list[str], list[str]]:
    """Turn the measurements into a 0-100 score with matching strengths/issues.

    Five equally weighted components, one per area the analysis covers. Every
    band and threshold is a heuristic, not a law - the goal is a transparent,
    repeatable rubric, not a verdict.
    """
    strengths: list[str] = []
    issues: list[str] = []

    density = technical.density
    if density.note_count < 2:
        issues.append("Too few notes to analyze (needs at least two).")
        return 0.0, strengths, issues

    score = 0.0
    durations = technical.durations
    syncopation = technical.syncopation
    repetition = technical.repetition
    phrases = technical.phrases

    # 1. Density (20) ---------------------------------------------------------
    # Judged on attack points rather than raw note count: four parts moving in
    # step are one rhythmic event, not four, so a homophonic chorale should
    # not read as four times denser than the same rhythm played solo.
    per_measure = density.onsets_per_measure
    if 2.0 <= per_measure <= 12.0:
        score += 20
        strengths.append(
            f"Well-paced rhythmic density ({per_measure} attacks per bar across "
            f"{technical.part_count} part(s))."
        )
    elif per_measure < 2.0:
        score += 20 * max(per_measure / 2.0, 0.15)
        issues.append(
            f"Very sparse rhythm - only {per_measure} attacks per bar; the music "
            "has little forward motion."
        )
    else:
        score += max(20 - (per_measure - 12.0) * 1.2, 6)
        issues.append(
            f"Very dense rhythm ({per_measure} attacks per bar) - the texture "
            "leaves little breathing room."
        )
    if density.rest_ratio > 0.6:
        score = max(0.0, score - 3)
        issues.append(
            f"{density.rest_ratio:.0%} of each part's time is rest - the writing "
            "is mostly silence."
        )

    # 2. Duration variety (20) ------------------------------------------------
    distinct = durations.distinct_durations
    if distinct >= 4:
        variety_score = 14 + min(durations.variety_index * 6, 6)
    elif distinct == 3:
        variety_score = 11 + durations.variety_index * 4
    elif distinct == 2:
        variety_score = 7 + durations.variety_index * 3
    else:
        variety_score = 3.0
        issues.append(
            f"Every note is the same length ({durations.most_common}) - the rhythm "
            "never varies."
        )
    score += variety_score
    if distinct >= 4 and durations.variety_index >= 0.7:
        strengths.append(
            f"Varied note values ({distinct} distinct durations, evenly used)."
        )
    if durations.most_common_ratio > 0.85 and distinct > 1:
        score = max(0.0, score - 3)
        issues.append(
            f"{durations.most_common_ratio:.0%} of notes are the same value "
            f"({durations.most_common}) - the other values barely register."
        )
    if durations.tuplet_count:
        strengths.append(f"Uses tuplets ({durations.tuplet_count} note(s)) for rhythmic colour.")

    # 3. Syncopation (20) -----------------------------------------------------
    ratio = syncopation.syncopation_ratio
    if 0.05 <= ratio <= 0.4:
        score += 20
        strengths.append(
            f"Effective syncopation ({ratio:.0%} of notes displace the metric accent)."
        )
    elif ratio < 0.05:
        score += 11 + ratio * 100
        if ratio == 0.0 and syncopation.offbeat_ratio < 0.1:
            issues.append(
                "No syncopation and almost no offbeat activity - the rhythm sits "
                "squarely on the beat throughout."
            )
    else:
        score += max(20 - (ratio - 0.4) * 25, 8)
        issues.append(
            f"Heavy syncopation ({ratio:.0%} of notes) - the pulse becomes hard to feel."
        )
    if syncopation.silent_downbeats and technical.measure_count > 1:
        missed = syncopation.silent_downbeats
        if missed <= technical.measure_count // 2:
            strengths.append(
                f"{missed} downbeat(s) left unarticulated, pulling against the barline."
            )
        else:
            issues.append(
                f"{missed} of {technical.measure_count} downbeats are never attacked - "
                "the metre loses its anchor."
            )

    # 4. Repetition (20) ------------------------------------------------------
    repetition_score = 0.0
    if repetition.repeated_patterns:
        best = repetition.repeated_patterns[0]
        repetition_score = min(20.0, 12 + (best.occurrences - 2) * 2 + best.length_notes)
        strengths.append(
            f"Recurring rhythmic cell ({best.length_notes} values, {best.occurrences}x) "
            "gives the rhythm an identity."
        )
    else:
        repetition_score = 7.0
        issues.append("No recurring rhythmic cell - the rhythm lacks a memorable figure.")
    if repetition.has_ostinato and repetition.ostinato_occurrences >= 3:
        strengths.append(
            f"Ostinato: a cell repeated {repetition.ostinato_occurrences}x back-to-back."
        )
    if repetition.measure_repetition_ratio > 0.75 and technical.measure_count >= 4:
        repetition_score = max(repetition_score - 6, 0.0)
        issues.append(
            f"{repetition.measure_repetition_ratio:.0%} of bars repeat an earlier bar's "
            "rhythm exactly - the rhythm is static."
        )
    score += repetition_score

    # 5. Phrase rhythm (20) ---------------------------------------------------
    if phrases.phrase_count == 0:
        score += 6
    elif phrases.phrase_count == 1:
        score += 12
        issues.append(
            "The music runs as a single unbroken phrase - no rhythmic breathing points."
        )
    elif phrases.is_regular:
        score += 20
        strengths.append(
            f"{phrases.phrase_count} regular phrases of "
            f"{phrases.most_common_length_measures} bar(s) each."
        )
    elif _dominant_phrase_share(phrases) >= 0.6:
        score += 16
        strengths.append(
            f"{phrases.phrase_count} phrases, most of them "
            f"{phrases.most_common_length_measures} bar(s) long."
        )
    else:
        score += 11
        issues.append(
            f"Phrase lengths are irregular ({phrases.distinct_lengths} different lengths "
            f"across {phrases.phrase_count} phrases)."
        )
    if phrases.has_anacrusis:
        strengths.append(f"Opens with a {phrases.anacrusis_quarters}-beat anacrusis.")

    return round(max(0.0, min(100.0, score)), 1), strengths, issues


# --------------------------------------------------------------------------- #
# Public entry points
# --------------------------------------------------------------------------- #


def analyze_rhythm_from_score(score: Score) -> RhythmAnalysis:
    """Run the full rhythm analysis on an already-parsed music21 Score."""
    parts = _extract_parts(score)
    if not any(event for part in parts for event in part.events):
        raise AnalysisError("The score has no notes or rests to analyze as rhythm.")
    if not any(not e.is_rest for part in parts for e in part.events):
        raise AnalysisError("The score has no sounding notes to analyze as rhythm.")

    measures = sorted({e.measure for part in parts for e in part.events})
    total_quarters = max(
        (e.offset + e.duration for part in parts for e in part.events), default=0.0
    )

    syncopation = _build_syncopation(parts, measures)
    technical = RhythmTechnicalData(
        time_signatures=_time_signatures(score),
        tempo=_tempo(score),
        measure_count=len(measures),
        total_quarters=round(total_quarters, 3),
        part_count=len(parts),
        density=_build_density(parts, measures, total_quarters),
        repetition=_build_repetition(parts, measures),
        syncopation=syncopation,
        durations=_build_durations(parts),
        phrases=_build_phrases(parts, score),
        parts=_build_parts(parts, measures, syncopation),
    )

    score_value, strengths, issues = _score_rhythm(technical)
    return RhythmAnalysis(
        score=score_value,
        strengths=strengths,
        issues=issues,
        technical_data=technical,
    )


def analyze_rhythm(content: bytes, filename: str) -> RhythmAnalysis:
    """Parse MusicXML bytes and return the rhythm analysis.

    Raises ``AnalysisError`` if music21 cannot parse ``content`` or the score
    contains no sounding notes.
    """
    return analyze_rhythm_from_score(_parse_score(content, filename))
