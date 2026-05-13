import asyncio
import contextlib
import logging

from app.config import get_settings
from app.services.ingestion import run_ingestion

logger = logging.getLogger(__name__)


class SummaryScheduler:
    def __init__(self) -> None:
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task

    async def _run(self) -> None:
        settings = get_settings()
        if settings.summary_job_run_on_startup:
            await self._run_once()

        interval_seconds = max(settings.summary_job_interval_minutes, 1) * 60
        while True:
            await asyncio.sleep(interval_seconds)
            await self._run_once()

    async def _run_once(self) -> None:
        try:
            await run_ingestion()
        except Exception:
            logger.exception("Scheduled ingestion failed")

