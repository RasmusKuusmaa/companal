# Cadence API

FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + Alembic + music21, behind
JWT auth. See the root `README.md` for what the app as a whole does; this
one is the backend's own setup and layout.

## Local setup — native Postgres (recommended for this project)

Local dev and tests run against a native PostgreSQL install, not Docker —
lighter on RAM than Docker Desktop's VM, and what this project's own test
suite is validated against. `docker-compose.yml` still exists as an
alternative (see below) but isn't the primary path.

```bash
python -m venv venv
source venv/Scripts/activate        # Windows Git Bash; use venv\Scripts\activate.bat on cmd
pip install -r requirements-dev.txt

cp .env.example .env
# edit .env: set SECRET_KEY (see comment in the file); DATABASE_URL already
# matches the role/db created below

alembic upgrade head
uvicorn app.main:app --reload
```

Provisioning a native Postgres once (Windows, no installer/service — a
portable zip extraction + `initdb`, matching what this project was set up
against):

```bash
# download & extract the portable binaries, then:
initdb -D <data-dir> -U postgres --pwfile=<file with the password> -E UTF8 --locale=C
pg_ctl -D <data-dir> -l <data-dir>/server.log -o "-p 5432 -h localhost" start

# one-time role + databases, matching .env / DATABASE_URL:
psql -h localhost -U postgres -c "CREATE ROLE cadence WITH LOGIN PASSWORD 'cadence' SUPERUSER;"
createdb -h localhost -U postgres -O cadence cadence
createdb -h localhost -U postgres -O cadence cadence_test
```

API docs: http://localhost:8000/api/v1/docs
Health check: http://localhost:8000/api/v1/health

### Running without an Anthropic API key

`ANTHROPIC_API_KEY` in `.env` can be left blank - `.env.example`'s default.
Nothing at startup checks for it; the client that needs it is only built
the moment an AI-touching request actually arrives (`@lru_cache`d, see
`app/domains/feedback/ai_service.py` and `app/domains/notation/
ai_grading.py`), so the app boots and runs exactly the same either way.

Everything that doesn't call Claude works in full: the entire curriculum
(lessons, quizzes, composition tasks), every exam, deterministic
composition grading (`notation.grading` - key, meter, cadence, voice-
leading, species counterpoint, figured bass, all checked by the analysis
engines, no AI involved), the skill map, MusicXML import/export, and the
staff editor itself.

What's unavailable, cleanly:

- **AI composition feedback** (the "get AI feedback" toggle on a lesson's
  composition step) - the request still grades deterministically and
  returns that result; only the AI commentary is missing, and the frontend
  says so rather than showing an error (`CompositionStep.vue`).
- **AI exam rubric grading** for composition questions on a premium
  account - same story, the deterministic grade still comes back.

Both fail with `AIServiceUnavailableError` internally, surfaced as a plain
503 ("AI feedback is not configured") - a deployment state the code
explicitly treats as "this feature doesn't exist here," not a transient
error worth retrying or an upgrade prompt.

## Local setup (with Docker, alternative)

```bash
cp .env.example .env
# edit .env: SECRET_KEY at minimum

docker compose up --build
docker compose exec api alembic upgrade head
```

## Tests

```bash
pytest
```

Tests run against a separate `cadence_test` database (see `conftest.py` at
the repo root — it redirects `DATABASE_URL` before any app module is
imported) and apply the real Alembic migrations at session start, not
`Base.metadata.create_all`, so a migration that doesn't actually match its
model gets caught. Each test gets a clean slate via table truncation, not
a rolled-back transaction, since the service layer commits internally.

`app/db/session.py` uses `NullPool` rather than a persistent connection
pool — deliberately, not just for tests. asyncpg connections are tied to
the event loop that opened them, and pytest-asyncio (like several async
frameworks) doesn't guarantee that stays constant; NullPool means every
checkout opens a fresh connection instead of risking a pooled one from a
dead loop. Revisit this if connection-per-request latency becomes a real
cost — production Postgres access likely wants pooling in front of it
(e.g. PgBouncer) rather than reintroducing this failure mode.

## Migrations

Alembic runs on the async engine directly (no separate sync DB driver needed).

```bash
alembic revision --autogenerate -m "add something"
alembic upgrade head
alembic downgrade -1
```

## Auth

`POST /api/v1/auth/register`, `/login`, `/refresh`, `/logout`, `GET /me`.
Login/refresh/logout take JSON bodies (not `OAuth2PasswordRequestForm`), to
match the axios-based frontend. Refresh tokens are rotated on every use and
tracked (hashed) in `refresh_tokens`, so a session can be revoked and reuse
of an already-rotated token — the signature of a stolen refresh token being
replayed — revokes every session for that user, not just the one token. See
`app/domains/auth/service.py` for the full reasoning.

## Layout

```
app/
├─ main.py              # app factory / entry point
├─ cli.py                # `python -m app.cli seed-curriculum` - migrates nothing, just syncs content
├─ core/                  # config, security (JWT + password hashing), logging, shared deps
├─ db/                     # declarative base, async session, Alembic env + migrations
├─ domains/
│  ├─ users/                # User model + read schema
│  ├─ auth/                  # registration, login, refresh-token rotation, RefreshToken model
│  ├─ learning/                # curriculum content, lessons, mastery/skill-map, progress
│  ├─ exams/                     # per-stage + comprehensive exams, held-and-graded attempts
│  ├─ notation/                   # the shared document model, deterministic grading, MusicXML
│  ├─ projects/                     # standalone composition uploads/versions, outside any lesson
│  ├─ feedback/                       # AI composition feedback (additive, never the grader)
│  ├─ billing/                         # subscription tier, AI usage ledger
│  └─ analysis/                         # melody/harmony/rhythm engines composition grading runs on
├─ api/v1/               # routers, aggregated in router.py
└─ tests/
```

Layering convention: `router → service → repository/ORM model`. A domain
only imports another domain's own `service.py`/`schemas.py`, never another
domain's internals directly.
