"""Operational commands, run as `python -m app.cli <command>`.

argparse rather than click/typer: this is a small, stable set of deploy-time
chores, and it isn't worth a dependency the application itself never imports.

Commands here are expected to run on every deploy, so they must be safe to
run twice - see `seed_curriculum` for how that's guaranteed.
"""

import argparse
import asyncio
import sys
from collections.abc import Sequence

from app.core.logging import configure_logging
from app.db.session import AsyncSessionLocal, engine
from app.domains.learning.curriculum import COURSES, TOPICS
from app.domains.learning.seeding import SeedReport, UnknownTopicError, seed_curriculum


async def _seed_curriculum() -> SeedReport:
    try:
        async with AsyncSessionLocal() as db:
            return await seed_curriculum(db, topics=TOPICS, courses=COURSES)
    finally:
        # The CLI owns the process, so it owns the engine's lifetime too -
        # the app's lifespan handler isn't running to dispose it here.
        await engine.dispose()


def _run_seed_curriculum() -> int:
    try:
        report = asyncio.run(_seed_curriculum())
    except UnknownTopicError as exc:
        print(f"curriculum is invalid: {exc}", file=sys.stderr)
        return 1

    print(f"topics:  {report.topics}")
    print(f"courses: {report.courses}")
    print(f"lessons: {report.lessons}")
    print(f"steps:   {report.steps}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    configure_logging()

    parser = argparse.ArgumentParser(prog="python -m app.cli")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser(
        "seed-curriculum",
        help="Make the database match the authored curriculum. Safe to re-run.",
    )

    args = parser.parse_args(argv)
    if args.command == "seed-curriculum":
        return _run_seed_curriculum()

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
