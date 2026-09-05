"""Algorithmic harmony analysis, via music21.

The vertical counterpart to `melody.py`, and non-AI in the same deliberate
way: chords come from `Score.chordify()`, roman numerals from
`roman.romanNumeralFromChord`, and parallel motion from music21's
`VoiceLeadingQuartet`. Every number below traces back to a measurement or a
plain counting rule, so the same score always yields the same result and each
finding can be pointed at a specific pair of voices between two specific
chords. (LLM-driven critique lives elsewhere - this module must never import
or call into it.)

Two modelling choices shape everything else:

*Sonorities.* `chordify()` cuts a new vertical slice at every onset in any
part, so a held chord under a moving line becomes several identical slices.
Consecutive slices with the same pitches are merged, so the chord list is the
piece's actual harmonic rhythm rather than its rhythmic grid.

*Voices.* Parallel fifths are a statement about two voices, so the analysis
needs voice identity, which `chordify()` throws away. When every part is a
real monophonic line (SATB, a string quartet) each part is one voice and the
findings are exact. When any part carries written chords - piano writing,
typically - voices are inferred by position within each sonority, counting up
from the bass, and a pair is only compared when both of its voices sound in
both chords. That fallback is conservative (it misses parallels rather than
inventing them) and which strategy was used is reported as
`voice_leading.voice_source`.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Any

from music21 import chord as m21chord
from music21 import interval as m21interval
from music21 import key as m21key
from music21 import note as m21note
from music21 import roman, stream, voiceLeading
from music21.stream.base import Score

from app.domains.analysis.nct import classify_non_chord_tones
from app.domains.analysis.schemas import (
    DissonanceData,
    DissonanceRead,
    FunctionalData,
    HarmonicCadenceRead,
    HarmonicChordRead,
    HarmonyAnalysis,
    HarmonyTechnicalData,
    ParallelMotionRead,
    ProgressionStepRead,
    VoiceCrossingRead,
    VoiceLeadingData,
    VoiceLeapRead,
)
from app.domains.analysis.service import AnalysisError, _parse_score
from app.domains.analysis.voicing import ChordTones, build_voicing_report

_STEP_MAX_SEMITONES = 2
# A voice moving more than a sixth in one chord change is a notable leap;
# below that the line still reads as connected.
_LARGE_LEAP_SEMITONES = 10
_TRITONE_SEMITONES = 6
_LEADING_TONE_SEMITONES = 11  # below the tonic, i.e. 11 above it

# Where each diatonic degree sits in the common-practice T -> PD -> D -> T
# cycle. iii and vi are grouped with the tonic as prolonging harmonies.
_FUNCTION_BY_DEGREE = {
    1: "tonic",
    2: "predominant",
    3: "tonic",
    4: "predominant",
    5: "dominant",
    6: "tonic",
    7: "dominant",
}
_FUNCTION_ORDER = {"tonic": 0, "predominant": 1, "dominant": 2}


@dataclass
class _Slice:
    """One sonority: the pitches sounding together over a span of time."""

    index: int
    measure: int
    offset: float  # absolute, in quarter notes from the start of the score
    duration: float
    chord: Any  # music21 Chord
    pitches: list[str]  # nameWithOctave, low to high


# --------------------------------------------------------------------------- #
# Extracting sonorities and voices
# --------------------------------------------------------------------------- #


def _key_object(score: Score) -> tuple[Any | None, float | None]:
    """The key to read the harmony against, and how much to trust it.

    Mirrors `service._extract_key`: a key written into the score is certain
    (1.0), an estimated one carries music21's correlation coefficient.
    """
    explicit = score.recurse().getElementsByClass(m21key.Key).first()
    if explicit is not None:
        return explicit, 1.0
    try:
        analyzed = score.analyze("key")
    except Exception:
        # No pitched content to estimate a key from - the analysis still runs,
        # but without roman numerals or functions.
        return None, None
    if analyzed is None:
        return None, None
    return analyzed, getattr(analyzed, "correlationCoefficient", None)


def _extract_slices(score: Score) -> list[_Slice]:
    """Chordify the score into sonorities, merging repeats of the same chord.

    Only slices of two or more pitches are kept: a single sounding pitch with
    every other part resting is a melodic event, not a harmony.
    """
    chordified = score.chordify()
    raw: list[tuple[int, float, float, Any, list[str]]] = []
    for chord_obj in chordified.recurse().getElementsByClass(m21chord.Chord):
        if len(chord_obj.pitches) < 2:
            continue
        pitches = sorted((p.nameWithOctave for p in chord_obj.pitches), key=_pitch_sort_key)
        raw.append(
            (
                chord_obj.measureNumber or 0,
                float(chord_obj.getOffsetInHierarchy(chordified)),
                float(chord_obj.quarterLength),
                chord_obj,
                pitches,
            )
        )

    slices: list[_Slice] = []
    for measure, offset, duration, chord_obj, pitches in raw:
        # The same pitches continuing across an onset elsewhere in the texture
        # is one held harmony, not two chords.
        if slices and slices[-1].pitches == pitches:
            slices[-1].duration += duration
            continue
        slices.append(
            _Slice(
                index=len(slices),
                measure=measure,
                offset=offset,
                duration=duration,
                chord=chord_obj,
                pitches=pitches,
            )
        )
    return slices


def _pitch_sort_key(name: str) -> int:
    return int(m21note.Note(name).pitch.midi)


def _parts_are_monophonic(score: Score) -> bool:
    """True when every part is a single line, so parts can serve as voices."""
    parts = list(score.parts)
    if len(parts) < 2:
        return False
    for part in parts:
        if part.recurse().getElementsByClass(m21chord.Chord):
            return False
        # Two independent lines notated on one staff - music21 keeps them in
        # Voice sub-streams, which flatten() would interleave into nonsense.
        if part.recurse().getElementsByClass(stream.Voice):
            return False
    return True


def _voice_grid(
    score: Score, slices: list[_Slice]
) -> tuple[str, list[str], dict[str, list[str | None]]]:
    """Build `voice id -> pitch at each slice`, plus the strategy used.

    Returns ``(voice_source, voice_ids, grid)``. A `None` entry means that
    voice is not sounding at that slice (a rest, or a thinner sonority).
    """
    if _parts_are_monophonic(score):
        return _voice_grid_from_parts(score, slices)
    return _voice_grid_from_positions(slices)


def _voice_grid_from_parts(
    score: Score, slices: list[_Slice]
) -> tuple[str, list[str], dict[str, list[str | None]]]:
    # Highest part first, so voice_ids read soprano-down like a score.
    parts = sorted(score.parts, key=_mean_midi, reverse=True)
    voice_ids: list[str] = []
    grid: dict[str, list[str | None]] = {}
    for position, part in enumerate(parts):
        voice_id = _voice_label(part, position)
        flat: Any = part.flatten().notesAndRests.stream()
        row: list[str | None] = []
        for slice_ in slices:
            sounding = flat.getElementAtOrBefore(
                slice_.offset, classList=(m21note.Note, m21note.Rest)
            )
            row.append(
                sounding.pitch.nameWithOctave
                if isinstance(sounding, m21note.Note)
                else None
            )
        voice_ids.append(voice_id)
        grid[voice_id] = row
    return "parts", voice_ids, grid


def _voice_grid_from_positions(
    slices: list[_Slice],
) -> tuple[str, list[str], dict[str, list[str | None]]]:
    """Fallback: infer voices by position within each sonority, from the bass up.

    Aligning from the bass keeps the bass line - the voice that matters most
    for parallels - stable even when the texture thickens and thins above it.
    """
    width = max((len(s.pitches) for s in slices), default=0)
    voice_ids = [f"v{i + 1}" for i in range(width)]
    grid: dict[str, list[str | None]] = {v: [] for v in voice_ids}
    for slice_ in slices:
        for position, voice_id in enumerate(voice_ids):
            grid[voice_id].append(
                slice_.pitches[position] if position < len(slice_.pitches) else None
            )
    # Report top-down for consistency with the parts strategy.
    return "vertical-positions", list(reversed(voice_ids)), grid


def _mean_midi(part: Any) -> float:
    midis = [n.pitch.midi for n in part.recurse().notes if not n.isChord and not n.isRest]
    return float(sum(midis) / len(midis)) if midis else -1.0


def _voice_label(part: Any, position: int) -> str:
    """A human-readable name for a voice.

    Unlike the `part_id` the rest of this domain reports, these labels end up
    inside findings ("parallel fifths between Bass and Tenor"), so the part's
    written name is preferred over its MusicXML id - music21's own writer
    generates hashed ids like `P689f207b...`, which would make the findings
    unreadable.
    """
    name = getattr(part, "partName", None)
    if name:
        return str(name)
    instrument = part.getInstrument(returnDefault=True) if hasattr(part, "getInstrument") else None
    if instrument is not None and getattr(instrument, "partId", None):
        return str(instrument.partId)
    return str(getattr(part, "id", None) or f"voice-{position + 1}")


# --------------------------------------------------------------------------- #
# Chords, roman numerals and function
# --------------------------------------------------------------------------- #


def _diatonic_pitch_names(key_obj: Any) -> set[str]:
    """Pitch names belonging to the key.

    In minor the raised 6th and 7th are included: harmonic and melodic minor
    are part of the key, so a V or vii(o) built on a raised leading tone is
    diatonic, not a chromatic borrowing.
    """
    names = {p.name for p in key_obj.pitches}
    if key_obj.mode == "minor":
        names.add(key_obj.tonic.transpose(9).name)  # raised 6th
        names.add(key_obj.tonic.transpose(11).name)  # raised 7th
    return names


def _roman_of(chord_obj: Any, key_obj: Any | None) -> Any | None:
    if key_obj is None:
        return None
    try:
        return roman.romanNumeralFromChord(chord_obj, key_obj)
    except Exception:
        # Sonorities music21 can't fit to a numeral (quartal stacks, clusters)
        # are left unlabelled rather than forced into one.
        return None


def _build_chords(
    slices: list[_Slice], key_obj: Any | None
) -> list[HarmonicChordRead]:
    diatonic = _diatonic_pitch_names(key_obj) if key_obj is not None else set()
    reads: list[HarmonicChordRead] = []

    for slice_ in slices:
        chord_obj = slice_.chord
        rn = _roman_of(chord_obj, key_obj)
        degree = rn.scaleDegree if rn is not None else None
        is_diatonic = bool(diatonic) and all(p.name in diatonic for p in chord_obj.pitches)
        function = _classify_function(degree, is_diatonic)

        reads.append(
            HarmonicChordRead(
                index=slice_.index,
                measure=slice_.measure,
                offset=slice_.offset,
                duration=slice_.duration,
                pitches=slice_.pitches,
                bass=slice_.pitches[0],
                root=getattr(_chord_attr(chord_obj, "root"), "name", None),
                quality=_chord_attr(chord_obj, "quality"),
                common_name=_chord_attr(chord_obj, "pitchedCommonName"),
                inversion=_chord_attr(chord_obj, "inversion"),
                roman_numeral=rn.figure if rn is not None else None,
                scale_degree=degree,
                function=function,
                is_diatonic=is_diatonic,
                applied_to=None,  # filled in below, once neighbours are known
                is_consonant=bool(_chord_attr(chord_obj, "isConsonant")),
            )
        )

    _mark_applied_dominants(slices, reads)
    return reads


def _safe(getter: Any) -> Any:
    """music21 raises from several of its accessors on degenerate sonorities."""
    try:
        return getter()
    except Exception:
        return None


def _chord_attr(chord_obj: Any, name: str) -> Any:
    """Read a music21 chord property or method, or `None` if it raises.

    `root()`, `quality`, `seventh` and friends variously blow up on clusters
    and two-note sonorities; this keeps every call site to one line without a
    lambda per lookup.
    """
    try:
        value = getattr(chord_obj, name)
        return value() if callable(value) else value
    except Exception:
        return None


def _classify_function(degree: int | None, is_diatonic: bool) -> str:
    if not is_diatonic:
        return "chromatic"
    if degree is None:
        return "other"
    return _FUNCTION_BY_DEGREE.get(degree, "other")


def _mark_applied_dominants(slices: list[_Slice], reads: list[HarmonicChordRead]) -> None:
    """Label chords that tonicize the harmony that follows them.

    music21 reads a D major triad in C as a chromatic `II`; naming it `V/V`
    needs the next chord, so it's done here rather than in `_roman_of`. The
    test is the standard one: a major triad or dominant seventh, carrying a
    note from outside the key, whose root lies a fifth above the next root.
    """
    for i, read in enumerate(reads[:-1]):
        if read.is_diatonic or read.function != "chromatic":
            continue
        chord_obj = slices[i].chord
        is_dominant_shape = bool(
            _chord_attr(chord_obj, "isDominantSeventh")
            or _chord_attr(chord_obj, "isMajorTriad")
        )
        if not is_dominant_shape:
            continue

        target = reads[i + 1]
        root = _chord_attr(chord_obj, "root")
        target_root_pitch = _chord_attr(slices[i + 1].chord, "root")
        if root is None or target_root_pitch is None:
            continue
        # A perfect fifth down from this root to the next is 5 semitones up.
        if (target_root_pitch.pitchClass - root.pitchClass) % 12 != 5:
            continue
        if target.roman_numeral is None:
            continue
        read.applied_to = f"V/{_numeral_stem(target.roman_numeral)}"


def _numeral_stem(figure: str) -> str:
    """Strip inversion/extension digits, so "V7" -> "V" and "i6" -> "i"."""
    return "".join(ch for ch in figure if not ch.isdigit()) or figure


# --------------------------------------------------------------------------- #
# Progression and cadences
# --------------------------------------------------------------------------- #


def _root_motion(before: HarmonicChordRead, after: HarmonicChordRead) -> str:
    """Directed root motion by the shorter path, e.g. "up P4", "down M2"."""
    if before.root is None or after.root is None:
        return "unknown"
    before_pc = m21note.Note(before.root).pitch.pitchClass
    after_pc = m21note.Note(after.root).pitch.pitchClass
    up = (after_pc - before_pc) % 12
    if up == 0:
        return "same"
    if up <= 6:
        return f"up {m21interval.Interval(up).name}"
    return f"down {m21interval.Interval(12 - up).name}"


def _build_progression(chords: list[HarmonicChordRead]) -> list[ProgressionStepRead]:
    steps: list[ProgressionStepRead] = []
    for before, after in zip(chords, chords[1:], strict=False):
        steps.append(
            ProgressionStepRead(
                from_index=before.index,
                to_index=after.index,
                measure=after.measure,
                from_numeral=before.roman_numeral,
                to_numeral=after.roman_numeral,
                from_function=before.function,
                to_function=after.function,
                root_motion=_root_motion(before, after),
                kind=_classify_step(before, after),
            )
        )
    return steps


def _classify_step(before: HarmonicChordRead, after: HarmonicChordRead) -> str:
    if before.function == "chromatic" or after.function == "chromatic":
        return "chromatic"
    if before.roman_numeral == after.roman_numeral:
        return "repetition"
    before_rank = _FUNCTION_ORDER.get(before.function)
    after_rank = _FUNCTION_ORDER.get(after.function)
    if before_rank is None or after_rank is None:
        return "other"
    # Dominant falling back to a predominant runs against the T -> PD -> D
    # cycle; every other move (including D -> T, which wraps around) is
    # normative.
    if before_rank == 2 and after_rank == 1:
        return "retrogression"
    return "functional"


def _build_cadences(
    chords: list[HarmonicChordRead], progression: list[ProgressionStepRead]
) -> list[HarmonicCadenceRead]:
    """Classify cadential arrivals.

    A cadence is a phrase ending, and nothing in a bare chord list marks
    phrases - so an arrival counts only when it is metrically strong (the
    chord starts a measure) or is the final chord of the piece.
    """
    if not chords:
        return []

    by_index = {c.index: c for c in chords}
    measure_starts = _measure_start_indices(chords)
    last_index = chords[-1].index

    cadences: list[HarmonicCadenceRead] = []
    for step in progression:
        target = by_index[step.to_index]
        is_final = target.index == last_index
        if target.index not in measure_starts and not is_final:
            continue
        kind, strength = _classify_cadence(by_index[step.from_index], target)
        if kind is None:
            continue
        cadences.append(
            HarmonicCadenceRead(
                measure=target.measure,
                chord_index=target.index,
                from_numeral=step.from_numeral,
                to_numeral=step.to_numeral,
                type=kind,
                strength=strength,
                is_final=is_final,
            )
        )
    return cadences


def _measure_start_indices(chords: list[HarmonicChordRead]) -> set[int]:
    seen: set[int] = set()
    starts: set[int] = set()
    for chord in chords:
        if chord.measure not in seen:
            seen.add(chord.measure)
            starts.add(chord.index)
    return starts


def _classify_cadence(
    before: HarmonicChordRead, after: HarmonicChordRead
) -> tuple[str | None, str]:
    before_degree, after_degree = before.scale_degree, after.scale_degree
    dominant_before = before.function == "dominant"

    if dominant_before and after_degree == 1:
        # Perfect authentic: both chords in root position, and the top voice
        # lands on the tonic. Anything weaker is imperfect.
        perfect = (
            before.inversion == 0
            and after.inversion == 0
            and after.root is not None
            and _top_pitch_name(after) == after.root
        )
        return "authentic", "perfect-authentic" if perfect else "imperfect-authentic"
    if dominant_before and after_degree == 6:
        return "deceptive", "weak"
    # A half cadence is an arrival *on* the dominant; a dominant that was
    # already sounding (V -> V7) is the same harmony continuing, not a cadence.
    if after_degree == 5 and after.function == "dominant" and not dominant_before:
        return "half", "strong"
    if before_degree in (4, 2) and after_degree == 1:
        return "plagal", "strong" if before_degree == 4 else "weak"
    return None, "weak"


def _top_pitch_name(chord: HarmonicChordRead) -> str | None:
    return m21note.Note(chord.pitches[-1]).pitch.name if chord.pitches else None


def _build_functional(
    chords: list[HarmonicChordRead], progression: list[ProgressionStepRead]
) -> FunctionalData:
    counts = Counter(c.function for c in chords)
    numerals = [c.roman_numeral for c in chords if c.roman_numeral]
    numeral_counts = Counter(numerals)
    diatonic = sum(1 for c in chords if c.is_diatonic)
    total = len(chords)

    return FunctionalData(
        function_counts=dict(counts),
        diatonic_ratio=round(diatonic / total, 3) if total else 0.0,
        chromatic_chord_indices=[c.index for c in chords if not c.is_diatonic],
        secondary_dominants=[c.applied_to for c in chords if c.applied_to],
        retrogressions=[s for s in progression if s.kind == "retrogression"],
        distinct_numerals=len(numeral_counts),
        most_common_numeral=numeral_counts.most_common(1)[0][0] if numeral_counts else None,
        tonic_ratio=round(counts.get("tonic", 0) / total, 3) if total else 0.0,
    )


# --------------------------------------------------------------------------- #
# Voice leading, parallels
# --------------------------------------------------------------------------- #


def _harmonic_interval(lower: str, upper: str) -> Any:
    return m21interval.Interval(noteStart=m21note.Note(lower), noteEnd=m21note.Note(upper))


def _build_voice_leading(
    slices: list[_Slice],
    voice_source: str,
    voice_ids: list[str],
    grid: dict[str, list[str | None]],
) -> VoiceLeadingData:
    motion_counts: Counter[str] = Counter()
    parallels: dict[str, list[ParallelMotionRead]] = {
        "fifth": [],
        "octave": [],
        "unison": [],
        "hidden": [],
    }
    leaps: list[VoiceLeapRead] = []
    motion_sizes: list[int] = []
    smooth_transitions = 0
    transitions = 0

    for i in range(len(slices) - 1):
        transitions += 1
        moved_by_more_than_a_step = False

        # Per-voice melodic motion.
        for voice_id in voice_ids:
            before, after = grid[voice_id][i], grid[voice_id][i + 1]
            if before is None or after is None:
                continue
            iv = m21interval.Interval(
                noteStart=m21note.Note(before), noteEnd=m21note.Note(after)
            )
            semitones = int(iv.semitones)
            motion_sizes.append(abs(semitones))
            if abs(semitones) > _STEP_MAX_SEMITONES:
                moved_by_more_than_a_step = True
            if abs(semitones) >= _LARGE_LEAP_SEMITONES:
                leaps.append(
                    VoiceLeapRead(
                        voice=voice_id,
                        from_index=slices[i].index,
                        to_index=slices[i + 1].index,
                        measure=slices[i + 1].measure,
                        motion=f"{before}->{after}",
                        semitones=semitones,
                        interval_name=iv.directedName,
                    )
                )
        if not moved_by_more_than_a_step:
            smooth_transitions += 1

        # Pairwise motion between voices.
        for upper_id, lower_id in _voice_pairs(voice_ids):
            u1, u2 = grid[upper_id][i], grid[upper_id][i + 1]
            l1, l2 = grid[lower_id][i], grid[lower_id][i + 1]
            if u1 is None or u2 is None or l1 is None or l2 is None:
                continue
            quartet = voiceLeading.VoiceLeadingQuartet(
                m21note.Note(u1), m21note.Note(u2), m21note.Note(l1), m21note.Note(l2)
            )
            motion_counts[_motion_name(quartet)] += 1

            outer = _is_outer_pair(upper_id, lower_id, grid, i)
            upper_leap = (
                abs(_pitch_sort_key(u2) - _pitch_sort_key(u1)) > _STEP_MAX_SEMITONES
            )
            found = _parallel_kinds(quartet, outer, upper_leap)
            for kind in found:
                bucket = "hidden" if kind.startswith("hidden") else kind
                parallels[bucket].append(
                    ParallelMotionRead(
                        kind=kind,
                        upper_voice=upper_id,
                        lower_voice=lower_id,
                        from_index=slices[i].index,
                        to_index=slices[i + 1].index,
                        measure=slices[i + 1].measure,
                        upper_motion=f"{u1}->{u2}",
                        lower_motion=f"{l1}->{l2}",
                        from_interval=_harmonic_interval(l1, u1).name,
                        to_interval=_harmonic_interval(l2, u2).name,
                        involves_outer_voices=outer,
                    )
                )

    crossings = _find_crossings(slices, voice_ids, grid)

    return VoiceLeadingData(
        voice_source=voice_source,
        voice_count=len(voice_ids),
        voice_ids=voice_ids,
        transitions=transitions,
        motion_counts=dict(motion_counts),
        average_motion_semitones=(
            round(sum(motion_sizes) / len(motion_sizes), 2) if motion_sizes else 0.0
        ),
        smooth_ratio=round(smooth_transitions / transitions, 3) if transitions else 0.0,
        parallel_fifths=parallels["fifth"],
        parallel_octaves=parallels["octave"],
        parallel_unisons=parallels["unison"],
        hidden_parallels=parallels["hidden"],
        large_leaps=leaps,
        voice_crossings=crossings,
    )


def _voice_pairs(voice_ids: list[str]) -> list[tuple[str, str]]:
    return [
        (voice_ids[i], voice_ids[j])
        for i in range(len(voice_ids))
        for j in range(i + 1, len(voice_ids))
    ]


def _parallel_kinds(quartet: Any, outer: bool, upper_leap: bool) -> list[str]:
    kinds: list[str] = []
    if quartet.parallelUnison():
        kinds.append("unison")
    elif quartet.parallelOctave():
        kinds.append("octave")
    if quartet.parallelFifth():
        kinds.append("fifth")
    if kinds:
        return kinds
    # Direct (hidden) fifths and octaves are conventionally a fault only
    # between the outer voices, and only when the upper voice arrives by leap
    # - approaching by step is the standard exemption, so flagging it would
    # bury real faults under ordinary cadential writing.
    if outer and upper_leap:
        if _safe(quartet.hiddenFifth):
            kinds.append("hidden-fifth")
        if _safe(quartet.hiddenOctave):
            kinds.append("hidden-octave")
    return kinds


def _motion_name(quartet: Any) -> str:
    motion = _safe(quartet.motionType)
    if motion is None:
        return "none"
    name = getattr(motion, "name", str(motion))
    return str(name).replace("MotionType.", "")


def _is_outer_pair(
    upper_id: str, lower_id: str, grid: dict[str, list[str | None]], index: int
) -> bool:
    """True when this pair is the highest and lowest voices sounding here."""
    sounding = [
        (voice_id, _pitch_sort_key(pitch))
        for voice_id, row in grid.items()
        if (pitch := row[index]) is not None
    ]
    if len(sounding) < 2:
        return False
    top = max(sounding, key=lambda item: item[1])[0]
    bottom = min(sounding, key=lambda item: item[1])[0]
    return {upper_id, lower_id} == {top, bottom}


def _find_crossings(
    slices: list[_Slice], voice_ids: list[str], grid: dict[str, list[str | None]]
) -> list[VoiceCrossingRead]:
    """Voices out of order: a nominally higher voice sounding below a lower one.

    Only meaningful when voices are real parts - the positional fallback sorts
    every sonority from the bass up, so it can never cross by construction.
    """
    crossings: list[VoiceCrossingRead] = []
    for i, slice_ in enumerate(slices):
        for upper_id, lower_id in _voice_pairs(voice_ids):
            upper, lower = grid[upper_id][i], grid[lower_id][i]
            if upper is None or lower is None:
                continue
            if _pitch_sort_key(upper) < _pitch_sort_key(lower):
                crossings.append(
                    VoiceCrossingRead(
                        upper_voice=upper_id,
                        lower_voice=lower_id,
                        chord_index=slice_.index,
                        measure=slice_.measure,
                        upper_pitch=upper,
                        lower_pitch=lower,
                    )
                )
    return crossings


# --------------------------------------------------------------------------- #
# Dissonance treatment
# --------------------------------------------------------------------------- #


def _build_dissonances(
    slices: list[_Slice],
    chords: list[HarmonicChordRead],
    voice_ids: list[str],
    grid: dict[str, list[str | None]],
    key_obj: Any | None,
) -> DissonanceData:
    unresolved: list[DissonanceRead] = []
    resolved = 0
    seventh_count = 0

    for i, slice_ in enumerate(slices):
        seventh = _chord_attr(slice_.chord, "seventh")
        if seventh is not None:
            seventh_count += 1
            for finding in _check_seventh(i, slices, seventh, voice_ids, grid):
                if finding.resolved:
                    resolved += 1
                else:
                    unresolved.append(finding)

        if key_obj is not None and chords[i].function == "dominant":
            for finding in _check_leading_tone(i, slices, voice_ids, grid, key_obj):
                if finding.resolved:
                    resolved += 1
                else:
                    unresolved.append(finding)

        for finding in _check_tritones(i, slices, voice_ids, grid):
            if finding.resolved:
                resolved += 1
            else:
                unresolved.append(finding)

    ends_dissonant = bool(chords) and not chords[-1].is_consonant
    if ends_dissonant:
        last = chords[-1]
        unresolved.append(
            DissonanceRead(
                kind="final-chord",
                chord_index=last.index,
                measure=last.measure,
                voice=None,
                pitch=", ".join(last.pitches),
                expected="the piece to end on a consonant chord",
                actual=f"ends on {last.common_name or 'a dissonant sonority'}",
                resolved=False,
            )
        )

    dissonant_chords = sum(1 for c in chords if not c.is_consonant)
    return DissonanceData(
        dissonant_chord_count=dissonant_chords,
        dissonance_ratio=round(dissonant_chords / len(chords), 3) if chords else 0.0,
        seventh_count=seventh_count,
        unresolved=unresolved,
        resolved_count=resolved,
        ends_dissonant=ends_dissonant,
    )


def _chord_root_pc(slice_: _Slice) -> int | None:
    root = _chord_attr(slice_.chord, "root")
    return int(root.pitchClass) if root is not None else None


def _resolution_target(slices: list[_Slice], index: int) -> int | None:
    """Index of the next slice carrying a *different* harmony.

    A dissonance is only obliged to resolve when the harmony changes: a
    seventh held while the same chord continues under a moving inner part
    hasn't failed to resolve, it simply hasn't resolved yet. Returns `None`
    when this harmony is the last in the piece.
    """
    root_pc = _chord_root_pc(slices[index])
    for j in range(index + 1, len(slices)):
        other_pc = _chord_root_pc(slices[j])
        if root_pc is None or other_pc is None or other_pc != root_pc:
            return j
    return None


def _is_last_of_harmony(slices: list[_Slice], index: int) -> bool:
    """True when the next slice is a genuinely new harmony (or there is none).

    Dissonance checks run only at this point, so a chord prolonged over
    several slices is judged once rather than once per slice.
    """
    if index + 1 >= len(slices):
        return True
    return _resolution_target(slices, index) == index + 1


def _voices_on(
    pitch_name: str, voice_ids: list[str], grid: dict[str, list[str | None]], index: int
) -> list[str]:
    """Which voices are sounding a given pitch class at this slice."""
    target = m21note.Note(pitch_name).pitch.pitchClass
    return [
        voice_id
        for voice_id in voice_ids
        if (p := grid[voice_id][index]) is not None
        and m21note.Note(p).pitch.pitchClass == target
    ]


def _check_seventh(
    index: int,
    slices: list[_Slice],
    seventh: Any,
    voice_ids: list[str],
    grid: dict[str, list[str | None]],
) -> list[DissonanceRead]:
    """The seventh of a chord is expected to fall by step into the next chord."""
    findings: list[DissonanceRead] = []
    if not _is_last_of_harmony(slices, index):
        return findings
    holders = _voices_on(seventh.name, voice_ids, grid, index)
    if not holders:
        return findings

    target = _resolution_target(slices, index)
    for voice_id in holders:
        before = grid[voice_id][index]
        after = None if target is None else grid[voice_id][target]
        if before is None:
            continue
        if after is None:
            findings.append(
                _dissonance(
                    "chordal-seventh",
                    slices[index],
                    voice_id,
                    before,
                    "to fall by step into the next chord",
                    "the piece ends here" if target is None else "the voice drops out",
                    False,
                )
            )
            continue
        semitones = int(
            m21interval.Interval(
                noteStart=m21note.Note(before), noteEnd=m21note.Note(after)
            ).semitones
        )
        ok = -_STEP_MAX_SEMITONES <= semitones <= -1
        findings.append(
            _dissonance(
                "chordal-seventh",
                slices[index],
                voice_id,
                before,
                "to fall by step into the next chord",
                f"moves to {after}" if semitones else f"is held as {after}",
                ok,
            )
        )
    return findings


def _check_leading_tone(
    index: int,
    slices: list[_Slice],
    voice_ids: list[str],
    grid: dict[str, list[str | None]],
    key_obj: Any,
) -> list[DissonanceRead]:
    """In a dominant chord the leading tone should rise to the tonic.

    Only checked in the outer voices: an inner-voice leading tone falling to
    the fifth is normal practice, not an error.
    """
    findings: list[DissonanceRead] = []
    if not _is_last_of_harmony(slices, index):
        return findings
    tonic_pc = key_obj.tonic.pitchClass
    sounding = [
        (voice_id, pitch)
        for voice_id in voice_ids
        if (pitch := grid[voice_id][index]) is not None
    ]
    if len(sounding) < 2:
        return findings
    outer_ids = {
        max(sounding, key=lambda item: _pitch_sort_key(item[1]))[0],
        min(sounding, key=lambda item: _pitch_sort_key(item[1]))[0],
    }

    target = _resolution_target(slices, index)
    for voice_id, pitch in sounding:
        if voice_id not in outer_ids:
            continue
        if (m21note.Note(pitch).pitch.pitchClass - tonic_pc) % 12 != _LEADING_TONE_SEMITONES:
            continue
        after = None if target is None else grid[voice_id][target]
        if after is None:
            findings.append(
                _dissonance(
                    "leading-tone",
                    slices[index],
                    voice_id,
                    pitch,
                    "to rise a semitone to the tonic",
                    "the piece ends here" if target is None else "the voice drops out",
                    False,
                )
            )
            continue
        semitones = int(
            m21interval.Interval(
                noteStart=m21note.Note(pitch), noteEnd=m21note.Note(after)
            ).semitones
        )
        findings.append(
            _dissonance(
                "leading-tone",
                slices[index],
                voice_id,
                pitch,
                "to rise a semitone to the tonic",
                f"moves to {after}",
                semitones == 1,
            )
        )
    return findings


def _check_tritones(
    index: int,
    slices: list[_Slice],
    voice_ids: list[str],
    grid: dict[str, list[str | None]],
) -> list[DissonanceRead]:
    """A tritone between two voices should resolve by step in both of them."""
    findings: list[DissonanceRead] = []
    if not _is_last_of_harmony(slices, index):
        return findings
    target = _resolution_target(slices, index)

    for upper_id, lower_id in _voice_pairs(voice_ids):
        upper, lower = grid[upper_id][index], grid[lower_id][index]
        if upper is None or lower is None:
            continue
        gap = abs(_pitch_sort_key(upper) - _pitch_sort_key(lower))
        if gap % 12 != _TRITONE_SEMITONES:
            continue

        upper_next = None if target is None else grid[upper_id][target]
        lower_next = None if target is None else grid[lower_id][target]
        pair = f"{lower}/{upper}"
        if upper_next is None or lower_next is None:
            findings.append(
                _dissonance(
                    "tritone",
                    slices[index],
                    f"{lower_id}+{upper_id}",
                    pair,
                    "both voices to resolve by step",
                    "the piece ends here" if target is None else "a voice drops out",
                    False,
                )
            )
            continue

        moves = [
            abs(_pitch_sort_key(upper_next) - _pitch_sort_key(upper)),
            abs(_pitch_sort_key(lower_next) - _pitch_sort_key(lower)),
        ]
        still_tritone = (
            abs(_pitch_sort_key(upper_next) - _pitch_sort_key(lower_next)) % 12
            == _TRITONE_SEMITONES
        )
        ok = all(1 <= m <= _STEP_MAX_SEMITONES for m in moves) and not still_tritone
        findings.append(
            _dissonance(
                "tritone",
                slices[index],
                f"{lower_id}+{upper_id}",
                pair,
                "both voices to resolve by step",
                f"moves to {lower_next}/{upper_next}",
                ok,
            )
        )
    return findings


def _dissonance(
    kind: str,
    slice_: _Slice,
    voice: str | None,
    pitch: str,
    expected: str,
    actual: str,
    resolved: bool,
) -> DissonanceRead:
    return DissonanceRead(
        kind=kind,
        chord_index=slice_.index,
        measure=slice_.measure,
        voice=voice,
        pitch=pitch,
        expected=expected,
        actual=actual,
        resolved=resolved,
    )


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #


def _score_harmony(technical: HarmonyTechnicalData) -> tuple[float, list[str], list[str]]:
    """Turn the measurements into a 0-100 score with matching strengths/issues.

    Six weighted components covering what common-practice harmony asks of a
    passage. Every band and threshold is a heuristic, not a law - the goal is
    a transparent, repeatable rubric, not a verdict.
    """
    strengths: list[str] = []
    issues: list[str] = []

    if technical.chord_count < 2:
        issues.append("Too few chords to analyze (needs at least two sonorities).")
        return 0.0, strengths, issues

    score = 0.0
    functional = technical.functional
    leading = technical.voice_leading
    dissonances = technical.dissonances

    # 1. Functional coherence (25) -------------------------------------------
    steps = technical.progression
    functional_steps = sum(1 for s in steps if s.kind in ("functional", "repetition"))
    functional_ratio = functional_steps / len(steps) if steps else 0.0
    score += 25 * functional_ratio
    if functional_ratio >= 0.85:
        strengths.append(
            f"Progressions follow a clear functional logic ({functional_ratio:.0%} "
            "move with the tonic-predominant-dominant cycle)."
        )
    if functional.retrogressions:
        issues.append(
            f"{len(functional.retrogressions)} retrogression(s) - dominant falling back "
            "to a predominant weakens the harmonic drive."
        )
    if functional.secondary_dominants:
        score = min(100.0, score + 2)
        strengths.append(
            f"Uses applied dominants ({', '.join(sorted(set(functional.secondary_dominants)))}) "
            "to colour the harmony."
        )

    # 2. Cadences (20) --------------------------------------------------------
    cadences = technical.cadences
    final = next((c for c in cadences if c.is_final), None)
    if final is not None and final.strength == "perfect-authentic":
        score += 20
        strengths.append("Closes with a perfect authentic cadence.")
    elif final is not None and final.type == "authentic":
        score += 16
        strengths.append("Closes with an authentic cadence.")
    elif final is not None and final.type == "plagal":
        score += 13
        strengths.append("Closes with a plagal cadence.")
    elif final is not None:
        score += 8
        issues.append(f"Ends on a {final.type} cadence rather than a conclusive one.")
    else:
        score += 4
        issues.append("No cadence at the end - the passage stops rather than closes.")
    if len(cadences) > 1:
        score = min(100.0, score + 2)
        strengths.append(f"{len(cadences)} cadential arrivals give the passage shape.")

    # 3. Voice leading (20) ---------------------------------------------------
    voice_score = 20.0
    if leading.transitions:
        contrary = leading.motion_counts.get("contrary", 0)
        oblique = leading.motion_counts.get("oblique", 0)
        pairs = sum(leading.motion_counts.values())
        independent = (contrary + oblique) / pairs if pairs else 0.0
        if independent >= 0.4:
            strengths.append(
                f"Voices stay independent ({independent:.0%} contrary or oblique motion)."
            )
        else:
            voice_score -= 5
            issues.append(
                f"Only {independent:.0%} of voice pairs move in contrary or oblique "
                "motion - the parts shadow each other."
            )
        if leading.average_motion_semitones <= 3.0:
            strengths.append(
                f"Smooth part-writing (voices move {leading.average_motion_semitones} "
                "semitones on average)."
            )
        else:
            voice_score -= 4
            issues.append(
                f"Voices move {leading.average_motion_semitones} semitones on average - "
                "the part-writing is angular."
            )
    if leading.large_leaps:
        voice_score -= min(len(leading.large_leaps) * 2, 6)
        issues.append(f"{len(leading.large_leaps)} large leap(s) in individual voices.")
    if leading.voice_crossings:
        voice_score -= min(len(leading.voice_crossings), 4)
        issues.append(f"{len(leading.voice_crossings)} voice crossing(s).")
    score += max(voice_score, 0.0)

    # 4. Parallel perfect intervals (15) --------------------------------------
    fifths = len(leading.parallel_fifths)
    octaves = len(leading.parallel_octaves) + len(leading.parallel_unisons)
    parallel_score = 15.0 - min((fifths + octaves) * 5, 15)
    score += parallel_score
    if fifths:
        issues.append(_parallel_issue("fifths", leading.parallel_fifths))
    if octaves:
        issues.append(
            _parallel_issue("octaves", leading.parallel_octaves + leading.parallel_unisons)
        )
    if not fifths and not octaves and leading.transitions:
        strengths.append("No parallel fifths or octaves.")
    outer_hidden = [p for p in leading.hidden_parallels if p.involves_outer_voices]
    if outer_hidden:
        score = max(0.0, score - min(len(outer_hidden), 3))
        issues.append(
            f"{len(outer_hidden)} direct (hidden) fifth/octave(s) between the outer voices."
        )

    # 5. Dissonance treatment (15) --------------------------------------------
    dissonance_score = 15.0
    if dissonances.unresolved:
        dissonance_score -= min(len(dissonances.unresolved) * 3, 12)
        by_kind = Counter(d.kind for d in dissonances.unresolved)
        detail = ", ".join(f"{count} {kind}" for kind, count in sorted(by_kind.items()))
        issues.append(f"{len(dissonances.unresolved)} unresolved dissonance(s): {detail}.")
    elif dissonances.seventh_count:
        strengths.append(
            f"All {dissonances.seventh_count} chordal seventh(s) resolve correctly."
        )
    score += max(dissonance_score, 0.0)

    # 6. Harmonic variety (5) -------------------------------------------------
    variety = functional.distinct_numerals
    if variety >= 4:
        score += 5
    elif variety >= 3:
        score += 3.5
    else:
        score += 1.5
        issues.append(
            f"Limited harmonic vocabulary - only {variety} distinct chord(s) in the passage."
        )
    if functional.tonic_ratio > 0.7:
        score = max(0.0, score - 3)
        issues.append(
            f"{functional.tonic_ratio:.0%} of chords are tonic-function - the harmony "
            "rarely leaves home."
        )

    return round(max(0.0, min(100.0, score)), 1), strengths, issues


def _parallel_issue(label: str, found: list[ParallelMotionRead]) -> str:
    first = found[0]
    where = (
        f"m.{first.measure} between {first.lower_voice} and {first.upper_voice} "
        f"({first.lower_motion} under {first.upper_motion})"
    )
    if len(found) == 1:
        return f"Parallel {label} at {where}."
    return f"{len(found)} parallel {label}, the first at {where}."


# --------------------------------------------------------------------------- #
# Public entry points
# --------------------------------------------------------------------------- #


def _chord_tones(slices: list[_Slice]) -> list[ChordTones]:
    """Reads each slice's root/third/seventh pitch classes, for the doubling
    and missing-third checks in `voicing.py`."""
    tones: list[ChordTones] = []
    for slice_ in slices:
        root = _chord_attr(slice_.chord, "root")
        third = _chord_attr(slice_.chord, "third")
        seventh = _chord_attr(slice_.chord, "seventh")
        tones.append(
            ChordTones(
                root=root.pitchClass if root is not None else None,
                third=third.pitchClass if third is not None else None,
                seventh=seventh.pitchClass if seventh is not None else None,
            )
        )
    return tones


_MIN_PITCHES_FOR_ROOT = 3


def _chord_tone_pitch_classes(slices: list[_Slice]) -> list[set[int]]:
    """The pitch classes music21 identifies as members of each slice's
    chord (root, third, fifth, seventh) - not every pitch sounding in the
    sonority, which is exactly what a non-chord tone (`analysis.nct`) is
    not.

    Empty for a sonority of fewer than three distinct pitches: music21's
    `.root()` on a bare dyad picks whichever note fits its interval-
    stacking heuristic best, which is frequently *not* the actual bass -
    a fourth or a second between two voices has no reliable root to find,
    and guessing one would misclassify the other note as a chord tone
    when it's exactly the kind of note this module exists to catch.
    """
    classes: list[set[int]] = []
    for slice_ in slices:
        members: set[int] = set()
        if len(set(slice_.pitches)) >= _MIN_PITCHES_FOR_ROOT:
            for name in ("root", "third", "fifth", "seventh"):
                tone = _chord_attr(slice_.chord, name)
                if tone is not None:
                    members.add(tone.pitchClass)
        classes.append(members)
    return classes


def _leading_tone_pitch_class(key_obj: Any | None) -> int | None:
    """A half step below the tonic, regardless of mode.

    Not `key_obj.pitchFromDegree(7)`: that reads the key's own scale, which
    for a minor key gives the natural-minor subtonic rather than the raised
    leading tone a dominant-function chord actually uses. The rule this
    supports ("don't double the leading tone") is about that half-step
    pull toward the tonic, which holds regardless of mode.
    """
    if key_obj is None:
        return None
    tonic = _chord_attr(key_obj, "tonic")
    if tonic is None:
        return None
    return int((tonic.pitchClass - 1) % 12)


def analyze_harmony_from_score(score: Score) -> HarmonyAnalysis:
    """Run the full harmony analysis on an already-parsed music21 Score."""
    slices = _extract_slices(score)
    if not slices:
        raise AnalysisError(
            "The score has no chords to analyze - harmony analysis needs at least "
            "two pitches sounding together."
        )

    key_obj, key_confidence = _key_object(score)
    voice_source, voice_ids, grid = _voice_grid(score, slices)

    chords = _build_chords(slices, key_obj)
    progression = _build_progression(chords)
    voicing_report = build_voicing_report(
        voice_source,
        voice_ids,
        grid,
        [s.measure for s in slices],
        _chord_tones(slices),
        _leading_tone_pitch_class(key_obj),
    )
    non_chord_tones = classify_non_chord_tones(
        voice_ids, grid, [s.measure for s in slices], _chord_tone_pitch_classes(slices)
    )

    technical = HarmonyTechnicalData(
        key=str(key_obj) if key_obj is not None else None,
        key_confidence=key_confidence,
        mode=getattr(key_obj, "mode", None) if key_obj is not None else None,
        chord_count=len(chords),
        measure_count=len({s.measure for s in slices}),
        chords=chords,
        progression=progression,
        functional=_build_functional(chords, progression),
        cadences=_build_cadences(chords, progression),
        voice_leading=_build_voice_leading(slices, voice_source, voice_ids, grid),
        dissonances=_build_dissonances(slices, chords, voice_ids, grid, key_obj),
        voicing=voicing_report,
        non_chord_tones=non_chord_tones,
    )

    score_value, strengths, issues = _score_harmony(technical)
    return HarmonyAnalysis(
        score=score_value,
        strengths=strengths,
        issues=issues,
        technical_data=technical,
    )


def analyze_harmony(content: bytes, filename: str) -> HarmonyAnalysis:
    """Parse MusicXML bytes and return the harmony analysis.

    Raises ``AnalysisError`` if music21 cannot parse ``content`` or the score
    contains no simultaneous pitches to read as harmony.
    """
    return analyze_harmony_from_score(_parse_score(content, filename))
