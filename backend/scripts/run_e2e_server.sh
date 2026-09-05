#!/usr/bin/env bash
# Starts the API for the frontend's Playwright e2e suite (see
# ../../frontend/e2e/ and ../../frontend/playwright.config.ts, which
# launches this as one of its `webServer` entries).
#
# Runs against its own database rather than the one local dev or `pytest`
# use, so a fresh set of users/compositions from an e2e run never mixes
# with either - migrated and seeded from scratch every time this starts,
# which is what makes repeated e2e runs reproducible.
set -euo pipefail
cd "$(dirname "$0")/.."

source .venv/bin/activate

: "${E2E_DB_HOST:=localhost}"
: "${E2E_DB_PORT:=5432}"
: "${E2E_DB_USER:=cadence}"
: "${E2E_DB_PASSWORD:=cadence}"
: "${E2E_DB_NAME:=cadence_e2e}"

# Created through asyncpg directly rather than shelling out to `createdb` -
# this project's own dev setup never assumes the Postgres client tools are
# on PATH, only the server itself (see backend/README.md's native-Postgres
# setup), so this is the one way to guarantee the database exists that
# doesn't add a new prerequisite.
python -c "
import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        host='$E2E_DB_HOST', port=$E2E_DB_PORT, user='$E2E_DB_USER',
        password='$E2E_DB_PASSWORD', database='postgres',
    )
    try:
        exists = await conn.fetchval(
            \"SELECT 1 FROM pg_database WHERE datname = \$1\", '$E2E_DB_NAME'
        )
        if not exists:
            await conn.execute('CREATE DATABASE $E2E_DB_NAME')
    finally:
        await conn.close()

asyncio.run(main())
"

export DATABASE_URL="postgresql+asyncpg://$E2E_DB_USER:$E2E_DB_PASSWORD@$E2E_DB_HOST:$E2E_DB_PORT/$E2E_DB_NAME"
export DEBUG=false

alembic upgrade head
python -m app.cli seed-curriculum

exec uvicorn app.main:app --host 127.0.0.1 --port 8000
