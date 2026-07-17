# Cadence API — backend foundation

FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + Alembic + JWT auth. The
`auth` domain (register/login/refresh/logout/me) is fully implemented; see
`app/domains/` to add the next one (courses, projects, analysis, feedback, ...).

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
├─ core/                # config, security (JWT + password hashing), logging, shared deps
├─ db/                  # declarative base, async session, Alembic env + migrations
├─ domains/
│  ├─ users/             # User model + read schema
│  └─ auth/               # registration, login, refresh-token rotation, RefreshToken model
├─ api/v1/               # routers, aggregated in router.py
└─ tests/
```

Layering convention: `router → service → repository → ORM model`. A domain
never imports another domain's internals directly — only what that domain
exposes from its own `service.py` (not yet needed until a second domain
exists).
