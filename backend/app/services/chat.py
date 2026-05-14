import logging
from dataclasses import dataclass

from openai import OpenAI
from pydantic import BaseModel

from app.agents.chat_context import prompt
from app.config import Settings, get_settings
from app.database import get_connection
from app.models import Article
from app.repositories import (
    add_chat_message,
    get_latest_notified_article_for_subscriber,
    get_or_create_chat_conversation,
    get_subscriber_by_whatsapp_number,
    list_chat_messages,
)
from app.services.whatsapp import WhatsAppClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IncomingWhatsAppMessage:
    from_number: str
    text: str
    message_id: str | None = None


class ChatWebhookResult(BaseModel):
    received_messages: int
    replies_sent: int


def _normalize_whatsapp_number(value: str) -> str:
    return value.strip().replace("+", "").replace(" ", "").replace("-", "")


def _article_context(article: Article) -> str:
    return (
        f"Title: {article.title}\n"
        f"Source: {article.source}\n"
        f"Date: {article.date}\n"
        f"Summary: {article.summary}\n\n"
        f"Full text:\n{article.full_text}"
    )


def extract_text_messages(payload: dict) -> list[IncomingWhatsAppMessage]:
    messages: list[IncomingWhatsAppMessage] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue
                text = message.get("text", {}).get("body", "").strip()
                from_number = message.get("from", "").strip()
                if text and from_number:
                    messages.append(
                        IncomingWhatsAppMessage(
                            from_number=_normalize_whatsapp_number(from_number),
                            text=text,
                            message_id=message.get("id"),
                        )
                    )
    return messages


def _generate_response(
    article: Article,
    history: list[dict[str, str]],
    user_message: str,
    settings: Settings,
) -> str:
    if not settings.openai_api_key:
        logger.info("OPENAI_API_KEY is not configured; using chat fallback response")
        return (
            "I can discuss the latest Civic Pulse summary you received, but the AI chat "
            "service is not configured right now. Please try again later."
        )

    messages = [{"role": "system", "content": prompt(_article_context(article))}]
    messages.extend(history[-10:])
    messages.append({"role": "user", "content": user_message})

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    assistant_response = response.choices[0].message.content
    return assistant_response or "I could not prepare a response for that message."


async def handle_incoming_message(
    incoming_message: IncomingWhatsAppMessage,
    settings: Settings | None = None,
    whatsapp_client: WhatsAppClient | None = None,
) -> bool:
    active_settings = settings or get_settings()
    recipient_number = _normalize_whatsapp_number(incoming_message.from_number)
    logger.info("Handling incoming WhatsApp chat message: sender=%s", recipient_number)

    with get_connection(active_settings) as connection:
        subscriber = get_subscriber_by_whatsapp_number(connection, recipient_number)
        if subscriber is None:
            logger.info("No subscriber found for incoming WhatsApp message: sender=%s", recipient_number)
            reply = (
                "Please subscribe to Civic Pulse before chatting about civic summaries. "
                "Once you receive a report summary, you can reply here with questions."
            )
            return await (whatsapp_client or WhatsAppClient(active_settings)).send_text(recipient_number, reply)

        article = get_latest_notified_article_for_subscriber(connection, subscriber.id)
        if article is None:
            logger.info("No notified article found for subscriber chat: subscriber_id=%s", subscriber.id)
            reply = (
                "I do not have a recent Civic Pulse summary linked to your WhatsApp number yet. "
                "After the next report summary is sent, reply here and I will help with it."
            )
            return await (whatsapp_client or WhatsAppClient(active_settings)).send_text(subscriber.whatsapp_number, reply)

        conversation_id = get_or_create_chat_conversation(connection, subscriber.id, article.id)
        history = list_chat_messages(connection, conversation_id)
        add_chat_message(
            connection,
            conversation_id,
            "user",
            incoming_message.text,
            incoming_message.message_id,
        )
        reply = _generate_response(article, history, incoming_message.text, active_settings)
        add_chat_message(connection, conversation_id, "assistant", reply)

    sent = await (whatsapp_client or WhatsAppClient(active_settings)).send_text(recipient_number, reply)
    logger.info(
        "Completed incoming WhatsApp chat message: sender=%s reply_sent=%s",
        recipient_number,
        sent,
    )
    return sent


async def handle_whatsapp_webhook(payload: dict) -> ChatWebhookResult:
    incoming_messages = extract_text_messages(payload)
    replies_sent = 0
    for incoming_message in incoming_messages:
        try:
            if await handle_incoming_message(incoming_message):
                replies_sent += 1
        except Exception:
            logger.error(
                "Failed to process incoming WhatsApp chat message: sender=%s",
                incoming_message.from_number,
                exc_info=True,
            )
            raise
    return ChatWebhookResult(
        received_messages=len(incoming_messages),
        replies_sent=replies_sent,
    )
