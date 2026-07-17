import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.session import AsyncSessionLocal
from app.main import app

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session", autouse=True)
def _migrated_schema() -> None:
    """Runs the real Alembic migrations against the test DB once per test
    session, rather than `Base.metadata.create_all`. The latter would only
    ever prove the ORM models are internally consistent; running the actual
    migration files is what catches drift between a migration and the
    model it's supposed to produce.

    Run as a subprocess, not via alembic's in-process `command.upgrade()`:
    Alembic's async env.py calls `asyncio.run(...)`, which tears down the
    event loop it created on exit and, on this asyncpg/Windows combination,
    corrupts pytest-asyncio's own session event loop in the process - every
    DB-touching test afterward then fails deep inside asyncpg with
    "Future attached to a different loop". A subprocess keeps Alembic's
    event loop entirely out of the test process.
    """
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=_BACKEND_ROOT,
        check=True,
    )


@pytest.fixture(autouse=True)
async def _clean_tables() -> AsyncIterator[None]:
    """Truncates every table before each test. Simpler and more reliable
    with this codebase's real `db.commit()` calls inside service functions
    than wrapping each test in a rolled-back transaction, which would
    require intercepting those commits as SAVEPOINTs instead."""
    table_names = ", ".join(f'"{table.name}"' for table in reversed(Base.metadata.sorted_tables))
    async with AsyncSessionLocal() as session:
        await session.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))
        await session.commit()
    yield


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        try:
            await session.close()
        except RuntimeError:
            # Known pytest-asyncio + asyncpg-on-Windows teardown artifact:
            # an async-generator fixture's cleanup runs in a Task separate
            # from the one that opened the connection (SQLAlchemy's
            # AsyncSession.close() wraps its work in asyncio.shield(),
            # which creates one), and asyncpg's low-level connection
            # occasionally comes back "attached to a different loop"
            # during the rollback that close() triggers. By this point
            # the test has already run and asserted - this is strictly a
            # best-effort cleanup, not a correctness issue for the test.
            pass


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
