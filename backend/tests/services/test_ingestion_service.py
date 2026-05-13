import pytest

from app.agents.browser_agent import RetrievedDocument
from app.agents.summarizer_agent import SummaryPublishResult
from app.config import Settings
from app.services import ingestion


def _settings() -> Settings:
    return Settings(DATABASE_PATH=":memory:")


def _document(title: str = "Audit Report") -> RetrievedDocument:
    return RetrievedDocument(
        title=title,
        source="oagkenya.go.ke",
        source_url="https://example.test/report",
        date="2026-05-13",
        image="",
        full_text="The complete report text.",
    )


@pytest.mark.asyncio
async def test_run_ingestion_aggregates_processed_and_sent_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ingestion, "get_settings", _settings)

    async def retrieve(source_urls: tuple[str, ...], limit: int) -> list[RetrievedDocument]:
        assert limit == 5
        assert source_urls
        return [_document("Saved Report"), _document("Unsaved Report")]

    async def summarize(**kwargs) -> SummaryPublishResult:
        if kwargs["title"] == "Saved Report":
            return SummaryPublishResult(summary="Summary", article_id=10, whatsapp_messages_sent=2)
        return SummaryPublishResult(summary="Summary", article_id=None, whatsapp_messages_sent=1)

    monkeypatch.setattr(ingestion, "retrieve_latest_documents", retrieve)
    monkeypatch.setattr(ingestion, "summarize_and_publish_document", summarize)

    result = await ingestion.run_ingestion()

    assert result.candidates_found == 2
    assert result.articles_processed == 1
    assert result.whatsapp_messages_sent == 3


@pytest.mark.asyncio
async def test_run_ingestion_handles_empty_document_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ingestion, "get_settings", _settings)

    async def retrieve(source_urls: tuple[str, ...], limit: int) -> list[RetrievedDocument]:
        return []

    monkeypatch.setattr(ingestion, "retrieve_latest_documents", retrieve)

    result = await ingestion.run_ingestion()

    assert result.candidates_found == 0
    assert result.articles_processed == 0
    assert result.whatsapp_messages_sent == 0


@pytest.mark.asyncio
async def test_run_ingestion_reraises_retrieval_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ingestion, "get_settings", _settings)

    async def retrieve(source_urls: tuple[str, ...], limit: int) -> list[RetrievedDocument]:
        raise RuntimeError("browser failed")

    monkeypatch.setattr(ingestion, "retrieve_latest_documents", retrieve)

    with pytest.raises(RuntimeError, match="browser failed"):
        await ingestion.run_ingestion()


@pytest.mark.asyncio
async def test_run_ingestion_reraises_summarizer_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ingestion, "get_settings", _settings)

    async def retrieve(source_urls: tuple[str, ...], limit: int) -> list[RetrievedDocument]:
        return [_document()]

    async def summarize(**kwargs) -> SummaryPublishResult:
        raise RuntimeError("summarizer failed")

    monkeypatch.setattr(ingestion, "retrieve_latest_documents", retrieve)
    monkeypatch.setattr(ingestion, "summarize_and_publish_document", summarize)

    with pytest.raises(RuntimeError, match="summarizer failed"):
        await ingestion.run_ingestion()

