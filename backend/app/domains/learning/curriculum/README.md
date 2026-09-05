# Authoring the curriculum

The curriculum is Python data, not rows typed into an admin UI: `TOPICS` and
`COURSES` in this package's `__init__.py` are the whole syllabus, and
`seed_curriculum` (see `../seeding.py`) makes the database match them
exactly - anything already in the database whose slug isn't found here gets
deleted. That means editing a lesson is a normal, reviewable commit, and
running the seeder is always safe: it's a sync, not an append, so it can be
re-run as often as you like (on every deploy, in particular).

## The shape (see `definitions.py`)

```
TopicDef    - one skill-map topic: slug, name, area, description
CourseDef   - one stage of the roadmap: slug, title, description, level, lessons: list[LessonDef]
LessonDef   - one lesson: slug, title, summary, estimated_minutes, steps: list[StepDef]
StepDef     - one step: slug, kind ("reading" | "quiz" | "composition"), payload, topics: list[str]
```

A few things worth knowing before you add to any of these:

- **Order comes from list order.** There's no `position` field anywhere -
  inserting a lesson in the middle of a stage is inserting a list element
  where you want it, not renumbering everything after it.
- **`slug` is the identity.** Rename a lesson's `title` freely; renaming its
  `slug` deletes the old row and creates a new one, losing whatever mastery
  history and lesson-status the old slug had accumulated. Don't do that for
  a lesson that's already shipped unless you mean to.
- **`topics` on a step feeds the skill map.** Every quiz answer and every
  rule-based finding on a composition submission (parallel fifths, say)
  rolls up into `TopicMastery` for whatever topics that step is tagged
  with - see `../mastery.py`. A step can carry more than one topic; most
  carry exactly one.
- **A step's `payload` is validated at seed time, not read time.** A
  malformed quiz (`answer_index` past the end of `choices`) or a
  composition task naming a requirement that doesn't parse fails loudly
  when you run the seeder, not silently the first time a student opens
  that lesson.

## The three step kinds

### `reading`

```python
StepDef(
    slug="...",
    kind="reading",
    payload={"markdown": "# Heading\n\nProse..."},
    topics=["..."],
)
```

Just markdown (see `learning.schemas.ReadingPayload`), rendered through the
frontend's sanitizing markdown renderer. Write it the way you'd write a
short, focused textbook page - a lesson usually opens with one of these.

### `quiz`

```python
StepDef(
    slug="...",
    kind="quiz",
    payload={
        "question": "...",
        "choices": ["...", "...", "...", "..."],
        "answer_index": 0,
        "explanation": "...",
    },
    topics=["..."],
)
```

Multiple choice, graded server-side (the student's client never sees
`answer_index`). `explanation` is shown after answering regardless of
whether the student got it right - retries are unlimited and unscored, so
the point is teaching, not gatekeeping. See `learning.schemas.QuizPayload`.

### `composition`

```python
StepDef(
    slug="...",
    kind="composition",
    payload={
        "brief": "Write an eight-measure melody in G major.",
        "requirements": [
            {"type": "key", "key": "G major"},
            {"type": "measure_count", "count": 8},
        ],
        "starter_notation": { ... },          # a full NotationDocument
        "locked_staff_indices": [0],           # optional - see below
    },
    topics=["..."],
)
```

Graded deterministically against `requirements` (see
`notation.requirements` and `notation.validation`) - never against a
sample solution, and never by AI alone (see `notation.grading`; AI
commentary is an optional, additive layer on top for premium accounts).
`starter_notation` is a complete `NotationDocument` in the exact shape the
staff editor itself edits - usually built with blank (rest-only) measures
for the student to fill in, sometimes with a locked line already written
(a cantus firmus, a bass to realize, a soprano to harmonize).
`locked_staff_indices` names which staves of `starter_notation` are given
material the student can't edit away; omit it for a fully blank exercise.

#### The requirement vocabulary (`notation.requirements`)

| Requirement | Fields | Checks |
|---|---|---|
| `key` | `key` (e.g. `"C major"`) | The piece is in this key. |
| `time_signature` | `value` (e.g. `"4/4"`, `"6/8"`) | The piece is in this meter. |
| `measure_count` | `count` | Exactly this many full measures - pickup-aware, an anacrusis in the first measure doesn't count. |
| `cadence` | `cadence` (`perfect_authentic` \| `imperfect_authentic` \| `half` \| `plagal` \| `deceptive`) | The final cadence is of this kind. |
| `range` | `max_semitones?`, `lowest?`, `highest?` | Bounds on the melody's span and/or actual extremes. |
| `max_leap` | `semitones` | No melodic leap exceeds this. |
| `leap_recovery` | `max_unresolved` (default 0) | Every leap of a 4th or more is answered by a step the opposite way, with this many exceptions tolerated. |
| `diatonic_only` | - | Every note belongs to the stated key. |
| `required_scale_degrees` | `degrees` (1-7) | Every one of these scale degrees appears at least once. |
| `forbidden_pitches` | `pitches` | None of these pitch classes appear, in any octave. |
| `species_counterpoint` | `species` (1\|2\|3\|4), `cantus_firmus_staff_index` | A valid species exercise against the named locked staff. |
| `figured_bass` | `bass_staff_index`, `figures` (one per measure, Kostka & Payne notation: `""`, `"6"`, `"6/4"`, `"7"`, `"6/5"`, `"4/3"`, `"4/2"`) | Every measure's upper voices realize the bass's figure correctly. |

Only combine requirements a lesson's own point can actually be checked
with this vocabulary - a lesson about naming things (clef names, roman
numeral spelling, cadence taxonomy) is quiz-only, no composition step,
rather than a composition task bolted on for its own sake. `florid-
counterpoint` (`stage3.py`) is the one deliberate exception worth reading
if you're ever tempted to invent a requirement that isn't really checkable
yet: 5th species has no dedicated checker, so that lesson's task reuses
the generic melodic-writing requirements instead of claiming a
verification the tooling can't actually do.

## Adding a lesson: the workflow this curriculum was built with

1. Add the `LessonDef` to the right `stageN.py` (or create a new topic in
   `topics.py` first, if the lesson needs one that doesn't exist yet).
2. `ruff check app/domains/learning/curriculum/` and
   `mypy app/domains/learning/curriculum/` - payload shape errors surface
   here as much as at seed time.
3. Seed against a real database and read the report:
   ```python
   import asyncio
   from app.db.session import AsyncSessionLocal
   from app.domains.learning.curriculum import TOPICS, COURSES
   from app.domains.learning.seeding import seed_curriculum

   async def main():
       async with AsyncSessionLocal() as db:
           print(await seed_curriculum(db, topics=TOPICS, courses=COURSES))

   asyncio.run(main())
   ```
   (or `python -m app.cli seed-curriculum`, which also seeds exams - see
   `../../exams/content.py`). Confirm the counts are what you expect -
   an unexpected `deleted` almost always means a slug typo.
4. **For a composition step, verify it's genuinely gradeable before
   shipping it** - a lesson that always passes (or always fails) teaches
   nothing:
   - Build a hand-written *correct* solution as a `NotationDocument` and
     confirm `notation.grading.grade_submission(document, requirements)`
     passes it.
   - Confirm the unmodified `starter_notation` (or an obviously wrong
     answer) fails, with a message that actually says why.
   - Watch for vacuous passes - a requirement that quietly checks nothing
     when the input is blank/empty is worse than no check at all (see the
     git history around `notation.counterpoint`'s all-rest fix for a real
     example of this actually happening).
5. Run the full `pytest` suite as a regression check - not strictly
   required for a pure-content change, but cheap insurance against a
   requirement combination that trips up an analysis engine in a way unit
   tests didn't anticipate.
6. Commit just the file(s) you touched.
