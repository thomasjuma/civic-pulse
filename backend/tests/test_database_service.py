from pathlib import Path

from app.config import Settings
from app.database import get_connection, init_db
from app.models import ArticleCreate
from app.services import database_service


def _settings(tmp_path: Path) -> Settings:
    return Settings(DATABASE_PATH=tmp_path / "test.db")


def test_save_article_summary_uses_database_service(
    monkeypatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    init_db(settings)
    monkeypatch.setattr(database_service, "get_connection", lambda: get_connection(settings))

    article = database_service.save_article_summary(
        ArticleCreate(
            title="Audit Report",
            source="oagkenya.go.ke",
            source_url="https://example.test/report",
            summary="A formal summary.",
            full_text="The complete report text.",
            date="2026-05-13",
            image="",
        )
    )

    assert article.id == 1
    assert article.title == "Audit Report"
