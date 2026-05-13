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
            logger.info("Starting summary scheduler")
            self._task = asyncio.create_task(self._run())
        else:
            logger.info("Summary scheduler already running")

    async def stop(self) -> None:
        if self._task is None:
            logger.info("Summary scheduler is not running")
            return
        logger.info("Stopping summary scheduler")
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        logger.info("Stopped summary scheduler")

    async def _run(self) -> None:
        settings = get_settings()
        if settings.summary_job_run_on_startup:
            logger.info("Running startup ingestion job")
            await self._run_once()

        interval_seconds = max(settings.summary_job_interval_minutes, 1) * 60
        logger.info("Summary scheduler interval configured: seconds=%s", interval_seconds)
        while True:
            await asyncio.sleep(interval_seconds)
            await self._run_once()

    async def _run_once(self) -> None:
        logger.info("Starting scheduled ingestion")
        try:
            await run_ingestion()
        except Exception:
            logger.error("Scheduled ingestion failed", exc_info=True)
            return
        logger.info("Completed scheduled ingestion")
