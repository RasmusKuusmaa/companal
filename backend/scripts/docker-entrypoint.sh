#!/usr/bin/env bash
# The image's entrypoint - wraps whatever CMD the image or a host's
# service config supplies (uvicorn, normally) with the two things every
# deployment of this container needs done first.
#
# Both steps are no-ops for a `docker compose` run that already has an
# up-to-date, asyncpg-scheme DATABASE_URL, so this is safe to be the
# entrypoint everywhere the image runs, not just on a host that needs it.
set -euo pipefail

# Some hosts' managed Postgres (Render's, in particular) hand out a bare
# `postgresql://` connection string; the app requires the asyncpg driver
# scheme (see app/core/config.py). Rewritten here rather than pasted by
# hand into a dashboard every time the database is (re)created.
if [[ "${DATABASE_URL:-}" == postgresql://* ]]; then
  export DATABASE_URL="postgresql+asyncpg://${DATABASE_URL#postgresql://}"
fi

alembic upgrade head

exec "$@"
