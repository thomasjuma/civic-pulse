from pathlib import Path

import pytest

from app.agents.browser_agent import RetrievedDocument
from app.agents.summarizer_agent import SummaryPublishResult
from app.config import Settings, get_settings
from app.database import init_db
from app.services import ingestion


def _settings(tmp_path: Path) -> Settings:
    return Settings(DATABASE_PATH=tmp_path / "test.db")


@pytest.mark.asyncio
async def test_ingestion_uses_browser_agent_documents(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    init_db(settings)
    get_settings.cache_clear()
    monkeypatch.setattr(ingestion, "get_settings", lambda: settings)

    async def fake_retrieve_latest_documents(
        source_urls: tuple[str, ...],
        limit: int,
    ) -> list[RetrievedDocument]:
        assert limit == 5
        assert source_urls
        return [
            RetrievedDocument(
                title="Latest Appropriation Bill",
                source="parliament.go.ke",
                source_url="https://example.test/bill",
                date="2026-05-13",
                image="",
                full_text="The complete bill text.",
            )
        ]

    async def fake_summarize_and_publish_document(
        title: str,
        source: str,
        full_text: str,
        date: str,
        image: str,
        source_url: str | None,
    ) -> SummaryPublishResult:
        assert title == "Latest Appropriation Bill"
        assert source == "parliament.go.ke"
        assert full_text == "The complete bill text."
        assert date == "2026-05-13"
        assert image == ""
        assert source_url == "https://example.test/bill"
        return SummaryPublishResult(
            summary="A formal summary.",
            article_id=1,
            whatsapp_messages_sent=0,
        )

    monkeypatch.setattr(ingestion, "retrieve_latest_documents", fake_retrieve_latest_documents)
    monkeypatch.setattr(ingestion, "summarize_and_publish_document", fake_summarize_and_publish_document)

    result = await ingestion.run_ingestion()

    assert result.candidates_found == 1
    assert result.articles_processed == 1
    assert result.whatsapp_messages_sent == 0
