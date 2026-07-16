# Cadence API — backend foundation

FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + Alembic + JWT auth scaffolding.
No feature domains beyond a minimal `users` table yet — see `app/domains/` to
add the next one (courses, projects, analysis, feedback, ...).

## Local setup (without Docker)

```bash
python -m venv venv
source venv/Scripts/activate        # Windows Git Bash; use venv\Scripts\activate.bat on cmd
pip install -r requirements-dev.txt

cp .env.example .env
# then edit .env: set SECRET_KEY (see comment in the file) and DATABASE_URL
# to point at a running Postgres instance

alembic upgrade head
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/api/v1/docs
Health check: http://localhost:8000/api/v1/health

## Local setup (with Docker)

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

## Migrations

Alembic runs on the async engine directly (no separate sync DB driver needed).

```bash
alembic revision --autogenerate -m "add something"
alembic upgrade head
alembic downgrade -1
```

## Layout

```
app/
├─ main.py              # app factory / entry point
├─ core/                # config, security (JWT + password hashing), logging, shared deps
├─ db/                  # declarative base, async session, Alembic env + migrations
├─ domains/              # one folder per business domain (users so far)
├─ api/v1/               # routers, aggregated in router.py
└─ tests/
```

Layering convention: `router → service → repository → ORM model`. A domain
never imports another domain's internals directly — only what that domain
exposes from its own `service.py` (not yet needed until a second domain
exists).
