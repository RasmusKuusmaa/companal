# Cadence

A self-paced music theory and composition learning platform: a structured
curriculum a student works through stage by stage, graded exams at each
checkpoint, and a real staff-notation editor to write and submit music in,
all backed by a deterministic grading engine that reasons about actual
music theory - not a rubric an LLM guesses at.

## What's here

- **A curriculum**, six stages from fundamentals through chromaticism and
  form, each lesson a mix of reading, multiple-choice checks, and
  composition tasks - see `backend/app/domains/learning/curriculum/README.md`
  for how it's authored and how it's graded.
- **Exams**, one per stage plus a comprehensive final, each a held-and-
  graded-together attempt (unlike a lesson step, nothing is revealed until
  the whole attempt is submitted) with unlimited retakes.
- **A skill map**, mastery tracked per topic from both quiz answers and
  rule-level findings on composition submissions (parallel fifths, a
  missed cadence, ...), independent of which lesson or exam surfaced them.
- **A staff-notation editor** (VexFlow-based): click-or-keyboard note
  entry, selection and range operations, copy/paste, undo/redo, ties,
  slurs, articulations, manual beam breaks, MusicXML import/export, a
  print-friendly score view, and a keyboard-shortcut reference panel - see
  `frontend/src/features/notation/`.
- **Deterministic composition grading**: every composition task states its
  brief as a checklist of requirements (key, meter, cadence, voice-leading
  rules, species counterpoint, a figured bass to realize, ...), checked
  against the same melody/harmony/rhythm analysis engines every submission
  goes through - see `backend/app/domains/notation/`. AI feedback is an
  optional, additive layer on top for premium accounts, never the grader
  itself, and the whole app works with no AI configured at all (see
  `backend/README.md`'s "Running without an Anthropic API key").
- **Projects**: a composition workspace independent of the curriculum,
  for uploading, versioning, and reviewing a score outside any lesson.

## Architecture

```
backend/    FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + Alembic + music21
frontend/   Vue 3 + TypeScript + Pinia + VexFlow
```

The backend and frontend each own their own domain/feature split, tests,
and setup instructions - see `backend/README.md` and `frontend/README.md`.
`frontend/vite.config.ts` proxies API calls to the backend in dev, so
running both is normally just `uvicorn app.main:app --reload` in one
terminal and `npm run dev` in another.

## Testing

- **Backend**: `pytest` (unit + integration, against a real Postgres).
- **Frontend**: `npm test` (Vitest + Vue Test Utils, component-level,
  APIs mocked) and `npm run test:e2e` (Playwright, a real browser against
  a real backend - see `frontend/e2e/`).
- **CI**: `.github/workflows/ci.yml` runs all three (backend, frontend,
  then e2e) on every push and pull request.

## Deploying

`render.yaml` at the repo root is a [Render Blueprint](https://render.com/docs/blueprint-spec):
point Render at this repo ("New +" -> "Blueprint") and it provisions a
Postgres database, the API (`backend/Dockerfile`, unchanged image, just a
migrate-then-serve entrypoint - see `backend/scripts/docker-entrypoint.sh`),
and the frontend as a static site, together. Two values the file can't fill
in for you - both called out in `render.yaml`'s own comments - need setting
once after the first deploy: the API's `DATABASE_URL` (paste the database's
connection string from its Info tab as-is; the entrypoint adds the asyncpg
driver scheme) and the frontend's `VITE_API_BASE_URL`/the API's
`CORS_ORIGINS` (each service's public URL isn't known until it exists).

Nothing here is Render-specific beyond the blueprint file itself - the same
Dockerfile runs on any container host, and the frontend is a static build
`npm run build` produces same as it would for Vercel/Netlify/Cloudflare
Pages. Storage note: composition file uploads land on the container's own
disk (`STORAGE_ROOT`), which most container hosts - Render's free/starter
web services included - don't persist across restarts or redeploys unless
you attach a persistent disk; fine for evaluating the app, worth revisiting
before real user uploads matter.
