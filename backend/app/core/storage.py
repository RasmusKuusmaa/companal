"""Local filesystem storage for uploaded composition files.

A thin, swappable boundary: callers only ever deal in relative keys and
bytes, never filesystem paths, so this could later be pointed at S3 or
another blob store without changing anything upstream. Writes are run off
the event loop via `asyncio.to_thread` rather than pulling in aiofiles -
local disk I/O is fast enough that a thread-pool hop is the only concession
async needs here.
"""

import asyncio
import shutil
from pathlib import Path

from app.core.config import settings


def _root() -> Path:
    return Path(settings.STORAGE_ROOT)


def _resolve(relative_path: str) -> Path:
    return _root() / relative_path


async def save_file(relative_path: str, content: bytes) -> None:
    def _write() -> None:
        path = _resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    await asyncio.to_thread(_write)


async def read_file(relative_path: str) -> bytes:
    return await asyncio.to_thread(_resolve(relative_path).read_bytes)


async def delete_file(relative_path: str) -> None:
    def _remove() -> None:
        _resolve(relative_path).unlink(missing_ok=True)

    await asyncio.to_thread(_remove)


async def delete_directory(relative_path: str) -> None:
    """Removes every file under a relative directory in one shot - used
    when a whole composition (and all its versions) is deleted."""

    def _remove() -> None:
        shutil.rmtree(_resolve(relative_path), ignore_errors=True)

    await asyncio.to_thread(_remove)
