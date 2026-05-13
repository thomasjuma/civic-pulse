import logging

from agents import function_tool

from app.models import ArticleCreate
from app.services.database_service import (
    get_pending_whatsapp_recipients,
    mark_whatsapp_summary_sent,
    save_article_summary,
)
from app.services.whatsapp import WhatsAppClient

logger = logging.getLogger(__name__)


def _whatsapp_message(title: str, source: str, summary: str) -> str:
    return f"Civic Pulse Summary\n\n{title}\nSource: {source}\n\n{summary}"


@function_tool
def save_article_summary_tool(
    title: str,
    source: str,
    summary: str,
    full_text: str,
    date: str,
    image: str = "",
    source_url: str | None = None,
) -> dict[str, int | str | bool]:
    """Save a summarized civic document as an article."""
    return save_article_summary_record(
        title=title,
        source=source,
        summary=summary,
        full_text=full_text,
        date=date,
        image=image,
        source_url=source_url,
    )


def save_article_summary_record(
    title: str,
    source: str,
    summary: str,
    full_text: str,
    date: str,
    image: str = "",
    source_url: str | None = None,
) -> dict[str, int | str | bool]:
    logger.info("Saving article summary through agent tool: source=%s title=%s", source, title)
    try:
        article = save_article_summary(
            ArticleCreate(
                title=title,
                source=source,
                source_url=source_url,
                summary=summary,
                full_text=full_text,
                date=date,
                image=image,
            )
        )
    except Exception:
        logger.error("Failed to save article summary through agent tool: source=%s title=%s", source, title, exc_info=True)
        raise
    logger.info("Saved article summary through agent tool: article_id=%s", article.id)
    return {
        "saved": True,
        "article_id": article.id,
        "title": article.title,
        "source": article.source,
    }


@function_tool
async def send_whatsapp_summary_tool(
    article_id: int,
    title: str,
    source: str,
    summary: str,
) -> dict[str, int]:
    """Send an article summary to consenting WhatsApp subscribers."""
    return await send_whatsapp_summary(
        article_id=article_id,
        title=title,
        source=source,
        summary=summary,
    )


async def send_whatsapp_summary(
    article_id: int,
    title: str,
    source: str,
    summary: str,
) -> dict[str, int]:
    logger.info("Sending WhatsApp summary through agent tool: article_id=%s", article_id)
    try:
        recipients = get_pending_whatsapp_recipients(article_id)
    except Exception:
        logger.error("Failed to load WhatsApp recipients through agent tool: article_id=%s", article_id, exc_info=True)
        raise
    whatsapp_client = WhatsAppClient()
    sent_count = 0

    for recipient in recipients:
        try:
            sent = await whatsapp_client.send_text(
                recipient.whatsapp_number,
                _whatsapp_message(title, source, summary),
            )
        except Exception:
            logger.error(
                "Failed to send WhatsApp summary through agent tool: article_id=%s subscriber_id=%s",
                article_id,
                recipient.id,
                exc_info=True,
            )
            raise
        if sent:
            try:
                mark_whatsapp_summary_sent(article_id, recipient.id)
            except Exception:
                logger.error(
                    "Failed to mark WhatsApp summary sent through agent tool: article_id=%s subscriber_id=%s",
                    article_id,
                    recipient.id,
                    exc_info=True,
                )
                raise
            sent_count += 1

    logger.info(
        "Sent WhatsApp summary through agent tool: article_id=%s recipients=%s messages_sent=%s",
        article_id,
        len(recipients),
        sent_count,
    )
    return {
        "article_id": article_id,
        "recipients_found": len(recipients),
        "messages_sent": sent_count,
    }
