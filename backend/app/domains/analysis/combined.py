"""Runs the melody, harmony and rhythm engines over one uploaded file.

Each engine gets its own parse of the file. Sharing a single `Score` between
them looks tempting - parsing is much slower than the measurements built on
top of it - but it is not safe: `Score.chordify()`, which the harmony engine
depends on, leaves the source score in a state where
`Music21Object.getOffsetInHierarchy` resolves some elements differently, and
the rhythm engine (which reads absolute offsets to place events in time)
then reports a shorter piece than it should. Rather than order the engines
around that, or audit every engine for similar sensitivities whenever one
changes, each simply starts from a clean parse - which is also exactly what
the three standalone endpoints do, so the combined result always matches
them note for note.

The three are independent, and a score that defeats one need not defeat the
others: a single melodic line has no harmony to read, a rests-only part has
no melody. An engine that cannot run therefore records why and drops out of
the overall score, rather than failing the whole bundle. Only a file that no
engine can analyze is an error.
"""

from typing import Any

from app.domains.analysis.harmony import analyze_harmony
from app.domains.analysis.melody import analyze_melody
from app.domains.analysis.rhythm import analyze_rhythm
from app.domains.analysis.schemas import AnalysisBundle, EngineUnavailable
from app.domains.analysis.service import AnalysisError


def _run(
    engine: Any, content: bytes, filename: str, name: str
) -> tuple[Any, EngineUnavailable | None]:
    try:
        return engine(content, filename), None
    except AnalysisError as exc:
        # The engine ruled itself out for a musical reason ("no pitched
        # notes", "no chords") - that is a result about this score, not a
        # failure of the request. A file that cannot be *parsed* fails every
        # engine the same way, and is re-raised by the caller below.
        return None, EngineUnavailable(engine=name, reason=str(exc))


def run_all_analyses(content: bytes, filename: str) -> AnalysisBundle:
    """Run all three engines over MusicXML bytes.

    Raises ``AnalysisError`` if music21 cannot parse ``content`` at all, or if
    every engine rules itself out for musical reasons.
    """
    melody, melody_missing = _run(analyze_melody, content, filename, "melody")
    harmony, harmony_missing = _run(analyze_harmony, content, filename, "harmony")
    rhythm, rhythm_missing = _run(analyze_rhythm, content, filename, "rhythm")

    unavailable = [m for m in (melody_missing, harmony_missing, rhythm_missing) if m]
    if len(unavailable) == 3:
        raise AnalysisError(
            "No analysis could be run on this score: "
            + "; ".join(f"{m.engine} - {m.reason}" for m in unavailable)
        )

    scores = [a.score for a in (melody, harmony, rhythm) if a is not None]
    return AnalysisBundle(
        melody_analysis=melody,
        harmony_analysis=harmony,
        rhythm_analysis=rhythm,
        overall_score=round(sum(scores) / len(scores), 1),
        unavailable=unavailable,
    )
