from app.database import get_connection
from app.models import Article, ArticleCreate, Subscriber
from app.repositories import (
    list_consenting_subscribers,
    mark_article_notification_sent,
    upsert_article,
)


def save_article_summary(article: ArticleCreate) -> Article:
    with get_connection() as connection:
        return upsert_article(connection, article)


def get_pending_whatsapp_recipients(article_id: int) -> list[Subscriber]:
    with get_connection() as connection:
        return list_consenting_subscribers(connection, article_id)


def mark_whatsapp_summary_sent(article_id: int, subscriber_id: int) -> None:
    with get_connection() as connection:
        mark_article_notification_sent(connection, article_id, subscriber_id)

