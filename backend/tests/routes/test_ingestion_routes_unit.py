import pytest

from app.models import IngestionResult
from app.routes import ingestion


@pytest.mark.asyncio
async def test_run_ingestion_now_returns_ingestion_result(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = IngestionResult(
        candidates_found=5,
        articles_processed=4,
        whatsapp_messages_sent=3,
    )

    async def run_ingestion() -> IngestionResult:
        return expected

    monkeypatch.setattr(ingestion, "run_ingestion", run_ingestion)

    assert await ingestion.run_ingestion_now() == expected

