import asyncio

import pytest

from app.config import Settings
from app.services import scheduler


class _CompletedTask:
    def done(self) -> bool:
        return True

    def cancel(self) -> None:
        pass

    def __await__(self):
        async def _wait() -> None:
            return None

        return _wait().__await__()


class _PendingTask:
    def __init__(self) -> None:
        self.cancelled = False

    def done(self) -> bool:
        return False

    def cancel(self) -> None:
        self.cancelled = True

    def __await__(self):
        async def _wait() -> None:
            return None

        return _wait().__await__()


class _StopLoop(Exception):
    pass


@pytest.mark.asyncio
async def test_start_creates_task_when_missing_or_done(monkeypatch: pytest.MonkeyPatch) -> None:
    created: list[object] = []
    task = _PendingTask()
    summary_scheduler = scheduler.SummaryScheduler()

    monkeypatch.setattr(scheduler.asyncio, "create_task", lambda coroutine: created.append(coroutine) or task)

    summary_scheduler.start()
    assert summary_scheduler._task is task

    summary_scheduler._task = _CompletedTask()
    summary_scheduler.start()

    assert len(created) == 2
    for coroutine in created:
        coroutine.close()


def test_start_does_not_create_task_when_running(monkeypatch: pytest.MonkeyPatch) -> None:
    summary_scheduler = scheduler.SummaryScheduler()
    summary_scheduler._task = _PendingTask()
    monkeypatch.setattr(scheduler.asyncio, "create_task", lambda coroutine: pytest.fail("should not create task"))

    summary_scheduler.start()


@pytest.mark.asyncio
async def test_stop_returns_when_task_is_missing() -> None:
    summary_scheduler = scheduler.SummaryScheduler()

    await summary_scheduler.stop()

    assert summary_scheduler._task is None


@pytest.mark.asyncio
async def test_stop_cancels_running_task() -> None:
    task = _PendingTask()
    summary_scheduler = scheduler.SummaryScheduler()
    summary_scheduler._task = task

    await summary_scheduler.stop()

    assert task.cancelled is True


@pytest.mark.asyncio
async def test_run_once_calls_ingestion(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    async def run_ingestion() -> None:
        nonlocal calls
        calls += 1

    monkeypatch.setattr(scheduler, "run_ingestion", run_ingestion)
    summary_scheduler = scheduler.SummaryScheduler()

    await summary_scheduler._run_once()

    assert calls == 1


@pytest.mark.asyncio
async def test_run_once_swallows_ingestion_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    async def run_ingestion() -> None:
        raise RuntimeError("ingestion failed")

    monkeypatch.setattr(scheduler, "run_ingestion", run_ingestion)
    summary_scheduler = scheduler.SummaryScheduler()

    await summary_scheduler._run_once()


@pytest.mark.asyncio
async def test_run_executes_startup_job_and_sleeps(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    summary_scheduler = scheduler.SummaryScheduler()
    settings = Settings(
        DATABASE_PATH=":memory:",
        SUMMARY_JOB_RUN_ON_STARTUP=True,
        SUMMARY_JOB_INTERVAL_MINUTES=0,
    )

    async def run_once() -> None:
        nonlocal calls
        calls += 1

    async def sleep(seconds: int) -> None:
        assert seconds == 60
        raise _StopLoop()

    monkeypatch.setattr(scheduler, "get_settings", lambda: settings)
    monkeypatch.setattr(summary_scheduler, "_run_once", run_once)
    monkeypatch.setattr(scheduler.asyncio, "sleep", sleep)

    with pytest.raises(_StopLoop):
        await summary_scheduler._run()

    assert calls == 1


@pytest.mark.asyncio
async def test_run_skips_startup_job_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    summary_scheduler = scheduler.SummaryScheduler()
    settings = Settings(
        DATABASE_PATH=":memory:",
        SUMMARY_JOB_RUN_ON_STARTUP=False,
        SUMMARY_JOB_INTERVAL_MINUTES=2,
    )

    async def run_once() -> None:
        nonlocal calls
        calls += 1

    async def sleep(seconds: int) -> None:
        assert seconds == 120
        raise _StopLoop()

    monkeypatch.setattr(scheduler, "get_settings", lambda: settings)
    monkeypatch.setattr(summary_scheduler, "_run_once", run_once)
    monkeypatch.setattr(scheduler.asyncio, "sleep", sleep)

    with pytest.raises(_StopLoop):
        await summary_scheduler._run()

    assert calls == 0


@pytest.mark.asyncio
async def test_run_executes_job_after_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    sleep_calls = 0
    summary_scheduler = scheduler.SummaryScheduler()
    settings = Settings(
        DATABASE_PATH=":memory:",
        SUMMARY_JOB_RUN_ON_STARTUP=False,
        SUMMARY_JOB_INTERVAL_MINUTES=1,
    )

    async def run_once() -> None:
        nonlocal calls
        calls += 1

    async def sleep(seconds: int) -> None:
        nonlocal sleep_calls
        assert seconds == 60
        sleep_calls += 1
        if sleep_calls == 2:
            raise _StopLoop()

    monkeypatch.setattr(scheduler, "get_settings", lambda: settings)
    monkeypatch.setattr(summary_scheduler, "_run_once", run_once)
    monkeypatch.setattr(scheduler.asyncio, "sleep", sleep)

    with pytest.raises(_StopLoop):
        await summary_scheduler._run()

    assert calls == 1
