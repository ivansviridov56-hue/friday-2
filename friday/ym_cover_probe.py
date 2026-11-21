"""Diagnostic: lists media sessions and saves each cover to the temp folder."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

from friday.smtc import list_sessions

logger = logging.getLogger(__name__)


def _kind(data: bytes) -> str:
    if data.startswith(b"\x89PNG"):
        return "png"
    if data.startswith(b"\xff\xd8"):
        return "jpg"
    return "bin"


async def main() -> None:
    sessions = await list_sessions()
    logger.info("sessions: %d", len(sessions))
    for index, session in enumerate(sessions):
        info = await session.now_playing()
        data = await session.thumbnail_bytes()
        if not data:
            logger.info(
                "%s | %s | %s | no cover", session.app_id, info.status, info.title
            )
            continue
        path = Path(tempfile.gettempdir()) / f"friday_cover_{index}.{_kind(data)}"
        path.write_bytes(data)
        logger.info(
            "%s | %s | %s | cover %d bytes -> %s",
            session.app_id,
            info.status,
            info.title,
            len(data),
            path,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(main())
