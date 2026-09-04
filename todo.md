# Cadence — build plan

A theory-and-composition roadmap for serious classical musicians. Reading, multiple-choice
checks and real composition tasks entered on a staff, graded first by deterministic rules
and then — for those who want it — by an AI teacher.

## Commit rules

- **One checkbox = one commit.** The text in backticks is the commit message, verbatim.
- **One line only.** `git commit -m "message"` — no body, no trailers, no `Co-Authored-By`.
- **Never signed.** No `-S`, no `--gpg-sign`.
- Every commit leaves the app running. If a change can't stand alone, it's two commits, not one.
- Before committing: backend `ruff check . && mypy app && pytest`, frontend `npm run lint && npm run type-check && npm test`.

## Design decisions already made

- **Nothing is locked.** Order is a recommendation; every lesson is reachable from day one.
- **Practice retries are free and unlimited.** Exams are retakeable, every attempt graded and kept forever.
- **No theory content is ever paywalled.** Only AI feedback is tiered.
- **Deterministic first, AI second.** Rules decide correctness; the AI only ever discusses quality.
- **MusicXML is the interchange format.** Editor and upload both become MusicXML before grading.
- **music21 owns notation conversion.** The editor never writes MusicXML itself.

---

## Phase A — learning domain foundation

Reshapes the uncommitted `backend/app/domains/learning/` scaffold from a flat course list into
stages → lessons → ordered steps, and gets it into the database.

- [x] `reshape learning models into courses lessons and ordered steps` — rewrite `models.py`: `Course` (+`slug`), `Lesson` (+`slug`, `summary`, `estimated_minutes`), drop `Exercise`, add `LessonStep` with `kind` enum (`reading`/`quiz`/`composition`) and `payload` JSONB
- [x] `add topic model and step topic association` — `Topic` (slug, name, area, description) plus `lesson_step_topics` many-to-many; topics are what the skill map is built on
- [x] `add step attempt model` — `(user_id, step_id)` rows with `payload`, `is_correct`, `score`, `passed`, `result` JSONB; one row per attempt, never overwritten
- [x] `add user progress model with lesson status` — `status` enum, `current_step`, `started_at`, `completed_at`
- [x] `add topic mastery model` — `(user_id, topic_id)` with attempt/correct counts, `accuracy`, `last_seen_at`, `status`; materialized so the skill map is one query
- [x] `add learning tables migration` — one Alembic revision for every table above
- [x] `register learning models with alembic env` — folds in the working-tree change to `db/migrations/env.py`
- [x] `add learning schemas for courses and lessons` — rewrite `schemas.py` around steps; discriminated union on `LessonStep.kind`
- [x] `add curriculum seed loader keyed on slug` — idempotent upsert from Python/JSON files under `learning/curriculum/`, so editing a lesson is a normal commit, never a migration
- [x] `add seed curriculum cli command` — `python -m app.cli seed-curriculum`, safe to re-run
- [x] `rewrite learning service for step based lessons` — replaces the flat-course service
- [x] `add roadmap endpoint returning every stage with lesson status` — the single call the roadmap page needs
- [x] `add lesson detail endpoint with ordered steps` — answer keys stripped from quiz payloads
- [x] `add quiz answer endpoint with explanation` — grades against the stored key, records a `StepAttempt`, returns correctness + explanation
- [x] `add lesson progress endpoints` — mark step seen, mark lesson complete, read progress
- [x] `wire learning router into api v1` — folds in the working-tree change to `api/v1/router.py`
- [x] `add learning service tests` — seeding, step ordering, quiz grading, progress transitions
- [x] `add learning router tests` — auth, 404s, answer-key leakage, idempotent completion

## Phase B — roadmap and lesson player

Reading and multiple-choice work end to end. No notation yet.

- [x] `add learning api client` — `frontend/src/features/learning/api/`
- [x] `add learning types` — mirrors the step union
- [x] `add learning store` — roadmap cache, current lesson, step cursor
- [x] `add markdown renderer utility` — `marked` + sanitizer, shared with lesson content
- [x] `add roadmap view with stage sections` — the whole path on one page, nothing greyed out
- [x] `add lesson card with progress ring` — status at a glance per lesson
- [x] `add lesson player shell with step navigation` — stepper over ordered steps, prev/next, progress bar
- [x] `add reading step component` — rendered markdown, musical examples slot
- [x] `add multiple choice step component` — choices, selection, submit
- [x] `add quiz result reveal with explanation` — correct/incorrect state, explanation, retry
- [x] `add lesson completion panel with next lesson link` — what you covered, what's next
- [x] `add learning routes` — `/learn`, `/learn/:lessonSlug` (no course segment: lesson slugs are unique curriculum-wide)
- [x] `add continue lesson title to the progress summary` — so the dashboard card doesn't fetch the whole roadmap for one line of text
- [x] `add continue learning card to the dashboard` — jumps to the furthest incomplete lesson
- [x] `add roadmap view tests` — renders stages, reflects progress
- [x] `add lesson player tests` — step navigation, quiz submit, retry

## Phase C — notation editor, single staff

VexFlow for engraving, custom interaction layer on top. Click **and** keyboard entry from the start.

- [x] `add vexflow dependency` — pinned in `package.json`
- [x] `add notation document types` — `{ key, timeSignature, tempo, staves[{ clef, voices[{ notes[] }] }] }`
- [x] `add notation document helpers` — measure/voice traversal, duration arithmetic, insertion points
- [x] `add duration and accidental constants` — whole through 32nd, dots, ♯ ♭ ♮ ♯♯ ♭♭
- [x] `add staff renderer component` — VexFlow canvas, resize handling
- [x] `add clef key and time signature rendering` — from the document, not hardcoded
- [x] `add note rendering from the notation document` — notes, rests, dots, accidentals, beams
- [x] `add click to pitch mapping` — y-coordinate → staff line/space → diatonic pitch, clef-aware
- [x] `add note placement on staff click` — places at the active duration and accidental
- [x] `add duration palette toolbar` — active duration, dot toggle
- [x] `add accidental palette` — including double accidentals
- [x] `add rest entry` — same placement flow, rest glyphs
- [x] `add tie entry between adjacent notes` — ties render and survive export
- [x] `add note deletion and cursor navigation` — click-select, delete, arrow-key movement
- [x] `add keyboard entry for pitch letters` — `A`–`G` places at the cursor, octave follows proximity
- [x] `fix notation editor cloning a reactive document from v-model` — `toRaw()` at the document boundary; a v-model-bound document arrives as a Vue proxy, which `structuredClone` refuses
- [x] `add keyboard shortcuts for durations and dots` — `1`–`6` (one per named duration), `.`, plus `R`/`T` for the rest and tie toggles already promised in their tooltips
- [x] `add measure add and remove controls` — with the bar count the exercise expects
- [x] `add webaudio playback engine` — pure schedule builder: flattens a document into timed pitches, merging tie chains into one sounding event
- [x] `add webaudio oscillator scheduling to the playback engine` — the AudioContext-touching half: oscillator + gain envelope per note, played via the schedule
- [x] `add playback transport controls` — play, stop, tempo
- [x] `add playback cursor highlight` — follows the sounding note
- [x] `add notation document tests` — helpers, insertion, duration maths
- [x] `add notation editor component tests` — click mapping, keyboard entry, deletion

## Phase D — composition grading pipeline

Editor output becomes MusicXML, gets checked against declarative rules, then optionally graded by Claude.

- [ ] `add notation document schemas on the backend` — Pydantic mirror of the editor document
- [ ] `add music21 builder from a notation document` — the one place MusicXML is written
- [ ] `add musicxml export endpoint` — `POST /notation/musicxml`, used for preview and submission
- [ ] `add musicxml import to a notation document` — music21 → editor document
- [ ] `add musicxml import endpoint` — `POST /notation/import`, lets an uploaded score open in the editor
- [ ] `add requirement rule schemas` — declarative rules stored on the composition step payload
- [ ] `add key and time signature validators` — asserts the brief's key and meter
- [ ] `add measure count and length validators` — "exactly 8 measures", anacrusis-aware
- [ ] `add cadence requirement validator` — asserts PAC/IAC/HC/plagal/deceptive using the existing cadence classifier
- [ ] `add range and motion validators` — vocal range, max leap, step/leap ratio, leap recovery
- [ ] `add pitch content validators` — diatonic-only, required scale degrees, forbidden pitches
- [ ] `add requirement validator runner` — runs every rule, returns a pass/fail checklist with bar numbers
- [ ] `add composition submission storage` — MusicXML written through `core.storage`, notation JSON on the attempt
- [ ] `add composition submission endpoint` — accepts a notation document, converts, validates, analyzes, stores
- [ ] `add deterministic grade assembly` — checklist + melody/harmony/rhythm scores, no AI involved
- [ ] `add exercise grading prompt template` — lesson topic, brief, rule results and analysis; never rewrites the student's music
- [ ] `add ai exercise grading service` — structured output, mirrors `feedback/ai_service.py`
- [ ] `add ai grading to composition submissions` — opt-in per submission, deterministic grade always returned first
- [ ] `add requirement validator tests` — one per rule type, pass and fail
- [ ] `add composition submission tests` — round-trip, storage, grading shape

## Phase E — tiers, quota and cost control

Lands directly after the first AI spend appears. Free gets 5 AI gradings a month; everything
deterministic stays free forever.

- [ ] `add subscription model` — one row per user, `tier`, `status`, `current_period_end`, dormant Stripe id columns
- [ ] `add ai usage ledger model` — one row per Claude call with token counts and estimated cost
- [ ] `add subscription and usage migration`
- [ ] `add feature matrix for free and premium tiers` — single source of truth in `core/features.py`
- [ ] `add subscription service with a default free tier` — users without a row are free, no backfill needed
- [ ] `add require feature dependency` — FastAPI dependency raising 402 with an upgrade payload
- [ ] `add monthly ai quota enforcement` — counts the ledger over the current period
- [ ] `add global ai spend cap` — config ceiling that trips before your bill does
- [ ] `record ai usage on every claude call` — feedback and exercise grading both
- [ ] `add feedback result reuse to avoid rebilling` — an unchanged submission returns the stored grade
- [ ] `degrade gracefully when the api key is unset` — deterministic grading everywhere, no upgrade prompts, no 503s
- [ ] `add subscription and usage endpoints` — current tier, quota remaining, period end
- [ ] `add stripe webhook route stub` — signature verification and tier transitions, inert without keys
- [ ] `add billing api client`
- [ ] `add subscription store`
- [ ] `add ai usage meter component` — "3 / 5 this month · resets 1 Oct"
- [ ] `add upgrade card for gated ai feedback` — shown in place of feedback when quota is spent
- [ ] `add pricing page` — what free actually includes, honestly
- [ ] `add tier and feature matrix tests`
- [ ] `add quota enforcement tests` — under, at and over the limit; cap tripped; key absent

## Phase F — editor: grand staff, voices, upload

Everything four-part writing and counterpoint need.

- [ ] `add grand staff support to the notation document` — multiple staves with independent clefs
- [ ] `add second staff rendering` — braced grand staff, aligned barlines
- [ ] `add staff selection in the editor` — entry targets the active staff
- [ ] `add multiple voices per staff` — up to four, stem direction by voice
- [ ] `add voice selection and colouring` — the active voice is unambiguous
- [ ] `add satb template` — two staves, four voices, correct clefs and stems
- [ ] `add starter notation loading` — an exercise can supply a given soprano, bass or cantus firmus
- [ ] `add locked staves for given material` — the given line can't be edited away
- [ ] `add musicxml upload for composition steps` — reuses the existing upload validation
- [ ] `add uploaded score conversion and grading` — same pipeline as editor submissions
- [ ] `add open uploaded score in the editor` — import, then keep editing
- [ ] `add grand staff and voice tests`

## Phase G — classical validators

The rules a conservatory would actually mark you on. All deterministic, all free tier.

- [ ] `add voicing module for four part checks` — builds on the harmony engine's existing voice grid
- [ ] `add satb voice range checks` — per-voice tessitura with bar numbers
- [ ] `add satb spacing checks` — more than an octave between adjacent upper voices
- [ ] `add satb doubling checks` — doubled leading tone, doubled sevenths, missing thirds
- [ ] `add voice overlap detection` — distinct from the existing crossing detection
- [ ] `add voicing report schema` — one shape the UI and the AI prompt both read
- [ ] `add voicing report to the harmony analysis output`
- [ ] `add species counterpoint module` — cantus firmus alignment, interval classification
- [ ] `add first species rules` — consonance only, no parallel perfects, contrary motion preference, cadence formula
- [ ] `add second and third species rules` — passing dissonance on weak beats, leap treatment
- [ ] `add fourth species rules` — suspension preparation, dissonance, resolution; no unprepared entries
- [ ] `add counterpoint validator report` — per-bar findings tied to the species
- [ ] `add figured bass realization checker` — does the realization match the figures
- [ ] `add non chord tone classification` — passing, neighbour, suspension, anticipation, appoggiatura, escape
- [ ] `add voicing checks tests`
- [ ] `add species counterpoint tests` — a clean exercise and a deliberately faulty one per species
- [ ] `add figured bass checker tests`

## Phase H — skill map and mastery

What you've covered, what you're good at, what needs work — in one glance.

- [ ] `add topic mastery service` — accuracy, recency and volume into a status
- [ ] `add mastery status thresholds` — untouched / learning / solid / needs practice
- [ ] `update mastery on step attempts` — same transaction as the attempt
- [ ] `update mastery on composition rule results` — a parallel-fifths violation is evidence about voice leading
- [ ] `add skill map endpoint` — every topic, mastery, coverage, last seen
- [ ] `add skill map api client`
- [ ] `add skill map view with a topic heatmap` — grouped by stage
- [ ] `add strengths and needs practice lists` — the explicit answer to "what should I work on"
- [ ] `add topic detail panel` — the lessons that teach it, your attempt history, drill links
- [ ] `add coverage summary to the dashboard` — topics touched, mastery split
- [ ] `add skill map link to the roadmap header`
- [ ] `add mastery service tests`
- [ ] `add skill map view tests`

## Phase I — exams

One per stage plus a comprehensive final. Retake as often as you like; every attempt is kept and graded.

- [ ] `add exam and exam question models` — questions parallel lesson steps but live separately
- [ ] `add exam attempt and answer models` — `attempt_number`, `score`, `max_score`, per-answer results
- [ ] `add exam tables migration`
- [ ] `add exam schemas`
- [ ] `add exam service for starting an attempt` — a new attempt never touches previous ones
- [ ] `add exam answer submission` — answers held until the attempt is submitted
- [ ] `add exam grading and scoring` — MCQ sections scored against keys
- [ ] `add exam composition section grading` — the Phase D pipeline, rule-graded for free users
- [ ] `add ai exam rubric grading for premium` — written commentary per composition section
- [ ] `add exam attempt history endpoint` — every attempt with date and score
- [ ] `add exam endpoints`
- [ ] `add exam api client`
- [ ] `add exam overview view` — scope, past attempts, start button
- [ ] `add exam question runner` — sectioned, no answer reveal until submission
- [ ] `add exam result view` — score, per-question breakdown, links to weak topics
- [ ] `add exam attempt history view` — attempts side by side so improvement is visible
- [ ] `add exam entry points to the roadmap` — an exam sits at the end of each stage
- [ ] `add exam service tests` — scoring, retakes, attempt isolation
- [ ] `add exam router tests`

## Phase J — curriculum content

One commit per lesson. Each carries its reading blocks, its multiple-choice checks, its
composition task where the topic calls for one, and its topic tags.

### Topics and stage shells

- [ ] `seed topic catalog` — every topic the skill map tracks, grouped by area
- [ ] `seed stage 0 fundamentals` — course shell
- [ ] `seed stage 1 chords and figures` — course shell
- [ ] `seed stage 2 voice leading` — course shell
- [ ] `seed stage 3 line and counterpoint` — course shell
- [ ] `seed stage 4 chromaticism` — course shell
- [ ] `seed stage 5 form and composition` — course shell

### Stage 0 — Fundamentals

- [ ] `seed lesson the staff clefs and ledger lines` — treble, bass and the C-clefs
- [ ] `seed lesson note values dots ties and rests`
- [ ] `seed lesson simple and compound meter`
- [ ] `seed lesson irregular meter and anacrusis`
- [ ] `seed lesson major scales and key signatures`
- [ ] `seed lesson minor scales natural harmonic and melodic`
- [ ] `seed lesson intervals number quality and inversion`
- [ ] `seed lesson the church modes`

### Stage 1 — Chords and figures

- [ ] `seed lesson triads and their qualities`
- [ ] `seed lesson triad inversions and figured bass symbols`
- [ ] `seed lesson seventh chords and their figures`
- [ ] `seed lesson roman numeral analysis in major`
- [ ] `seed lesson roman numeral analysis in minor`
- [ ] `seed lesson harmonic function and chord families`
- [ ] `seed lesson realizing a figured bass`

### Stage 2 — Voice leading

- [ ] `seed lesson four part texture ranges spacing and doubling`
- [ ] `seed lesson types of motion and the parallel prohibitions`
- [ ] `seed lesson connecting root position triads`
- [ ] `seed lesson first inversion triads and doubling choices`
- [ ] `seed lesson the three uses of the six four chord`
- [ ] `seed lesson the dominant seventh and its resolution`
- [ ] `seed lesson non chord tones`
- [ ] `seed lesson harmonizing a soprano line` — capstone
- [ ] `seed lesson realizing a figured bass in four parts` — capstone

### Stage 3 — Line and counterpoint

- [ ] `seed lesson melodic construction and tendency tones`
- [ ] `seed lesson phrase structure period and sentence`
- [ ] `seed lesson cadence types and their strength`
- [ ] `seed lesson first species counterpoint`
- [ ] `seed lesson second species counterpoint`
- [ ] `seed lesson third species counterpoint`
- [ ] `seed lesson fourth species and the suspension`
- [ ] `seed lesson florid counterpoint` — capstone

### Stage 4 — Chromaticism

- [ ] `seed lesson secondary dominants`
- [ ] `seed lesson secondary leading tone chords`
- [ ] `seed lesson tonicization versus modulation`
- [ ] `seed lesson pivot chord modulation`
- [ ] `seed lesson modal mixture`
- [ ] `seed lesson the neapolitan sixth`
- [ ] `seed lesson augmented sixth chords`

### Stage 5 — Form and composition

- [ ] `seed lesson binary and ternary form`
- [ ] `seed lesson minuet and trio and rondo`
- [ ] `seed lesson sonata form`
- [ ] `seed lesson theme and variations`
- [ ] `seed lesson motivic development techniques`
- [ ] `seed lesson writing a complete short piece` — final capstone

### Exams

- [ ] `seed stage 0 exam`
- [ ] `seed stage 1 exam`
- [ ] `seed stage 2 exam`
- [ ] `seed stage 3 exam`
- [ ] `seed stage 4 exam`
- [ ] `seed stage 5 exam`
- [ ] `seed comprehensive final exam`

## Phase K — polish, tests and docs

- [ ] `add selection and range operations to the editor`
- [ ] `add copy and paste in the editor`
- [ ] `add undo and redo in the editor`
- [ ] `add beaming control`
- [ ] `add slurs and articulations`
- [ ] `add score export to musicxml download`
- [ ] `add print friendly score view`
- [ ] `add keyboard shortcut help panel`
- [ ] `add empty and error states across learning views`
- [ ] `add mobile layout for the roadmap and lesson player`
- [ ] `add end to end lesson flow test`
- [ ] `add end to end composition submission test`
- [ ] `add ci workflow for backend and frontend`
- [ ] `document the curriculum authoring format`
- [ ] `document local setup without an api key`
- [ ] `update readme with the learning platform`

---

## Housekeeping

- [ ] `add gitignore for local claude workspace files` — `.claude/claude.md` is currently untracked
