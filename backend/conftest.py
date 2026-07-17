"""Redirects the test run at the disposable `cadence_test` database instead
of the dev DB in `.env`, before any test module gets a chance to import
`app.core.config` (which binds `DATABASE_URL` at import time). Root-level
conftest.py files load before anything under app/, which is what makes the
ordering guarantee here hold.

Environment variables take priority over `.env` file values in
pydantic-settings, so `setdefault` is enough - it never overrides an
explicit DATABASE_URL a developer has already exported.
"""

import asyncio
import os
import sys

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://cadence:cadence@localhost:5432/cadence_test"
)

# asyncpg's transport handling is unreliable on Windows' default Proactor
# event loop - pooled connections intermittently come back "attached to a
# different loop" even within a single, correctly session-scoped loop. The
# selector policy is the documented workaround. Must be set before any
# event loop (pytest-asyncio's or otherwise) is created, hence doing it
# here rather than in a fixture.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
