"""The declarative rule language a composition task states its brief in.

A requirement is a fact about the piece, not an instruction for how to check
it - "8 measures", not "count the measures and compare to 8". The checking
lives in `validation.py`; this module only defines what a rule *is*, which
is also exactly what gets stored on a `LessonStep`'s `payload.requirements`
(see `learning.schemas.CompositionPayload`) and what the lesson player shows
the student as the task's checklist before they've written a note.

Every requirement is gradeable from what the deterministic analysis engines
already produce - melody, harmony, rhythm - plus the raw notation document
for the one thing those engines don't carry (measure count, pickup-aware).
Nothing here calls the AI: a requirement either holds or it doesn't, and
that verdict has to be the same on every run.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

CadenceKind = Literal["perfect_authentic", "imperfect_authentic", "half", "plagal", "deceptive"]


class KeyRequirement(BaseModel):
    """The piece must be in this key, e.g. "C major" or "F# minor"."""

    type: Literal["key"] = "key"
    key: str


class TimeSignatureRequirement(BaseModel):
    type: Literal["time_signature"] = "time_signature"
    value: str = Field(description='e.g. "4/4", "6/8"')


class MeasureCountRequirement(BaseModel):
    """The piece must be exactly this many full measures long.

    Pickup-aware: a first measure shorter than the time signature calls for
    is treated as an anacrusis and doesn't count toward the total - "write
    an 8-bar melody" is satisfied by 8 full bars whether or not there's a
    two-beat pickup in front of them, matching how the brief would actually
    be marked by a teacher.
    """

    type: Literal["measure_count"] = "measure_count"
    count: int = Field(gt=0)


class CadenceRequirement(BaseModel):
    """The piece's final cadence must be of this kind."""

    type: Literal["cadence"] = "cadence"
    cadence: CadenceKind


class RangeRequirement(BaseModel):
    """Bounds on the melody's total range.

    `max_semitones` bounds the span top-to-bottom (a vocal-range style
    limit); `lowest`/`highest` bound the actual pitches reached, in
    scientific pitch notation (e.g. "G3"). Any subset may be given.
    """

    type: Literal["range"] = "range"
    max_semitones: int | None = Field(default=None, gt=0)
    lowest: str | None = None
    highest: str | None = None


class MaxLeapRequirement(BaseModel):
    """No melodic leap may exceed this many semitones."""

    type: Literal["max_leap"] = "max_leap"
    semitones: int = Field(gt=0)


class LeapRecoveryRequirement(BaseModel):
    """Every leap of a fourth or more must be answered by a step in the
    opposite direction - standard melodic-writing practice, and exactly
    what the melody engine's `leaps.unresolved` count already measures."""

    type: Literal["leap_recovery"] = "leap_recovery"
    # A handful of exceptions before the requirement fails outright, rather
    # than demanding textbook-perfect resolution of every single leap.
    max_unresolved: int = Field(default=0, ge=0)


class DiatonicOnlyRequirement(BaseModel):
    """Every melody note must belong to the stated key - no chromaticism."""

    type: Literal["diatonic_only"] = "diatonic_only"


class RequiredScaleDegreesRequirement(BaseModel):
    """The melody must use every one of these scale degrees (1-7) at least once."""

    type: Literal["required_scale_degrees"] = "required_scale_degrees"
    degrees: list[int] = Field(min_length=1)


class ForbiddenPitchesRequirement(BaseModel):
    """The melody must not use any of these pitch classes, in any octave."""

    type: Literal["forbidden_pitches"] = "forbidden_pitches"
    pitches: list[str] = Field(min_length=1)


class SpeciesCounterpointRequirement(BaseModel):
    """The submission must be a valid species-counterpoint exercise against
    a given cantus firmus.

    `cantus_firmus_staff_index` names the given, locked staff directly
    (see `learning.schemas.CompositionPayload.locked_staff_indices`,
    which an exercise using this requirement should set to the same
    index) - the cantus firmus is identified by which staff it is, not
    guessed at from its shape. `species` picks the rule set: 1 (note
    against note), 2 or 3 (two or three/four notes against one), or 4
    (syncopated suspensions) - see `notation.counterpoint`.
    """

    type: Literal["species_counterpoint"] = "species_counterpoint"
    species: Literal[1, 2, 3, 4]
    cantus_firmus_staff_index: int = Field(ge=0)


class FiguredBassRequirement(BaseModel):
    """The submission must realize a given figured bass correctly.

    `bass_staff_index` names the given, locked staff directly, the same
    way `SpeciesCounterpointRequirement` names its cantus firmus staff.
    `figures` is one entry per measure of that bass, in Kostka & Payne's
    plain-digit notation (`""` for root position, `"6"`, `"6/4"`, `"7"`,
    `"6/5"`, `"4/3"`, `"4/2"` or `"2"`) - see `notation.figured_bass` for
    exactly what each implies.
    """

    type: Literal["figured_bass"] = "figured_bass"
    bass_staff_index: int = Field(ge=0)
    figures: list[str] = Field(min_length=1)


Requirement = Annotated[
    KeyRequirement
    | TimeSignatureRequirement
    | MeasureCountRequirement
    | CadenceRequirement
    | RangeRequirement
    | MaxLeapRequirement
    | LeapRecoveryRequirement
    | DiatonicOnlyRequirement
    | RequiredScaleDegreesRequirement
    | ForbiddenPitchesRequirement
    | SpeciesCounterpointRequirement
    | FiguredBassRequirement,
    Field(discriminator="type"),
]


class RequirementResult(BaseModel):
    """The verdict on one requirement, for the checklist the student sees."""

    requirement: Requirement
    passed: bool
    message: str
    # The bar the failure is anchored to, when the rule can point to one -
    # a wrong key has none, a bad cadence points at the last measure.
    measure: int | None = None
