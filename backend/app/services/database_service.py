import logging

from app.database import get_connection
from app.models import Article, ArticleCreate, Subscriber
from app.repositories import (
    list_consenting_subscribers,
    mark_article_notification_sent,
    upsert_article,
)

logger = logging.getLogger(__name__)


def save_article_summary(article: ArticleCreate) -> Article:
    logger.info("Saving article summary: source=%s title=%s", article.source, article.title)
    try:
        with get_connection() as connection:
            saved_article = upsert_article(connection, article)
    except Exception:
        logger.error(
            "Failed to save article summary: source=%s title=%s",
            article.source,
            article.title,
            exc_info=True,
        )
        raise
    logger.info("Saved article summary: article_id=%s", saved_article.id)
    return saved_article


def get_pending_whatsapp_recipients(article_id: int) -> list[Subscriber]:
    logger.info("Loading pending WhatsApp recipients: article_id=%s", article_id)
    try:
        with get_connection() as connection:
            recipients = list_consenting_subscribers(connection, article_id)
    except Exception:
        logger.error(
            "Failed to load pending WhatsApp recipients: article_id=%s",
            article_id,
            exc_info=True,
        )
        raise
    logger.info(
        "Loaded pending WhatsApp recipients: article_id=%s recipients=%s",
        article_id,
        len(recipients),
    )
    return recipients


def mark_whatsapp_summary_sent(article_id: int, subscriber_id: int) -> None:
    logger.info(
        "Marking WhatsApp summary sent: article_id=%s subscriber_id=%s",
        article_id,
        subscriber_id,
    )
    try:
        with get_connection() as connection:
            mark_article_notification_sent(connection, article_id, subscriber_id)
    except Exception:
        logger.error(
            "Failed to mark WhatsApp summary sent: article_id=%s subscriber_id=%s",
            article_id,
            subscriber_id,
            exc_info=True,
        )
        raise
    logger.info(
        "Marked WhatsApp summary sent: article_id=%s subscriber_id=%s",
        article_id,
        subscriber_id,
    )
