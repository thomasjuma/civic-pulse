from pathlib import Path

from app.config import Settings
from app.database import get_connection, init_db
from app.models import ArticleCreate, SubscriberUpsert
from app.repositories import (
    get_article,
    list_articles,
    list_consenting_subscribers,
    mark_article_notification_sent,
    upsert_article,
    upsert_subscriber,
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(DATABASE_PATH=tmp_path / "test.db")


def test_article_upsert_and_lookup(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    init_db(settings)
    article = ArticleCreate(
        title="Public Audit Report",
        source="oagkenya.go.ke",
        source_url="https://example.test/report.pdf",
        summary="A formal summary.",
        full_text="The complete report text.",
        date="2026-05-13",
        image="https://example.test/image.jpg",
    )

    with get_connection(settings) as connection:
        saved = upsert_article(connection, article)
        found = get_article(connection, saved.id)
        articles = list_articles(connection)

    assert found == saved
    assert articles == [saved]


def test_consenting_subscribers_excludes_already_notified(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    init_db(settings)

    with get_connection(settings) as connection:
        article = upsert_article(
            connection,
            ArticleCreate(
                title="National Assembly Bill",
                source="parliament.go.ke",
                source_url="https://example.test/bill",
                summary="A formal summary.",
                full_text="The complete bill text.",
                date="2026-05-13",
                image="",
            ),
        )
        subscriber = upsert_subscriber(
            connection,
            SubscriberUpsert(
                email="reader@example.com",
                whatsapp_number="254700000000",
                has_whatsapp_consent=True,
            ),
        )
        assert list_consenting_subscribers(connection, article.id) == [subscriber]

        mark_article_notification_sent(connection, article.id, subscriber.id)

        assert list_consenting_subscribers(connection, article.id) == []

