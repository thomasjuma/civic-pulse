import json
import os
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from app.agents.tools import (
    save_article_summary_tool,
    send_whatsapp_summary_tool,
)
from app.models import ArticleCreate
from app.services.database_service import (
    get_pending_whatsapp_recipients,
    mark_whatsapp_summary_sent,
    save_article_summary,
)
from app.services.whatsapp import WhatsAppClient


def _fallback_summary(text: str, max_chars: int = 700) -> str:
    clean_text = " ".join(text.split())
    if len(clean_text) <= max_chars:
        return clean_text
    return clean_text[:max_chars].rsplit(" ", 1)[0] + "..."


@dataclass(frozen=True)
class SummaryPublishResult:
    summary: str
    article_id: int | None
    whatsapp_messages_sent: int


class SummaryAgentOutput(BaseModel):
    summary: str
    article_id: int | None = None
    whatsapp_messages_sent: int = 0


def _parse_agent_output(value: Any) -> SummaryPublishResult:
    if isinstance(value, SummaryAgentOutput):
        return SummaryPublishResult(
            summary=value.summary,
            article_id=value.article_id,
            whatsapp_messages_sent=value.whatsapp_messages_sent,
        )

    text = str(value).strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return SummaryPublishResult(summary=text, article_id=None, whatsapp_messages_sent=0)

    if not isinstance(payload, dict):
        return SummaryPublishResult(summary=text, article_id=None, whatsapp_messages_sent=0)

    return SummaryPublishResult(
        summary=str(payload.get("summary", "")).strip(),
        article_id=payload.get("article_id") if isinstance(payload.get("article_id"), int) else None,
        whatsapp_messages_sent=(
            payload.get("whatsapp_messages_sent")
            if isinstance(payload.get("whatsapp_messages_sent"), int)
            else 0
        ),
    )


async def _publish_without_openai(
    title: str,
    source: str,
    full_text: str,
    date: str,
    image: str,
    source_url: str | None,
) -> SummaryPublishResult:
    summary = _fallback_summary(full_text)
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

    whatsapp_client = WhatsAppClient()
    sent_count = 0
    for recipient in get_pending_whatsapp_recipients(article.id):
        sent = await whatsapp_client.send_text(
            recipient.whatsapp_number,
            f"Civic Pulse Summary\n\n{article.title}\nSource: {article.source}\n\n{article.summary}",
        )
        if sent:
            mark_whatsapp_summary_sent(article.id, recipient.id)
            sent_count += 1

    return SummaryPublishResult(
        summary=summary,
        article_id=article.id,
        whatsapp_messages_sent=sent_count,
    )


async def summarize_and_publish_document(
    title: str,
    source: str,
    full_text: str,
    date: str,
    image: str,
    source_url: str | None,
) -> SummaryPublishResult:
    if not os.getenv("OPENAI_API_KEY"):
        return await _publish_without_openai(title, source, full_text, date, image, source_url)

    try:
        from agents import Agent, Runner
    except ImportError:
        return await _publish_without_openai(title, source, full_text, date, image, source_url)

    agent = Agent(
        name="Civic Pulse Summarizer Agent",
        instructions=(
            "Summarize Kenyan civic, audit, legislative, or parliamentary documents in a professional "
            "legal-document tone. Highlight only the material points, legal or institutional relevance, "
            "and likely citizen impact. Keep the summary brief and formal. After drafting the summary, "
            "you must call save_article_summary_tool with the original document fields and the finished "
            "summary. Only after the save tool succeeds, call send_whatsapp_summary_tool with the saved "
            "article id, title, source, and summary. Do not send WhatsApp messages if saving fails. "
            "Your final answer must contain the summary, article_id, and whatsapp_messages_sent."
        ),
        tools=[save_article_summary_tool, send_whatsapp_summary_tool],
        output_type=SummaryAgentOutput,
    )
    prompt = (
        f"Title: {title}\n"
        f"Source: {source}\n\n"
        f"Source URL: {source_url or ''}\n"
        f"Date: {date}\n"
        f"Image: {image}\n\n"
        "Prepare a brief summary of the following document, save it, then send it to consenting "
        "WhatsApp subscribers using your tools:\n"
        f"{full_text[:12000]}"
    )
    result = await Runner.run(agent, prompt)
    return _parse_agent_output(result.final_output)


async def summarize_document(title: str, source: str, full_text: str) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return _fallback_summary(full_text)

    try:
        from agents import Agent, Runner
    except ImportError:
        return _fallback_summary(full_text)

    agent = Agent(
        name="Civic Pulse Summary Drafting Agent",
        instructions=(
            "Summarize Kenyan civic, audit, legislative, or parliamentary documents in a professional "
            "legal-document tone. Highlight only the material points, legal or institutional relevance, "
            "and likely citizen impact. Keep the summary brief and formal."
        ),
    )
    prompt = (
        f"Title: {title}\n"
        f"Source: {source}\n\n"
        "Prepare a brief summary of the following document:\n"
        f"{full_text[:12000]}"
    )
    result = await Runner.run(agent, prompt)
    return str(result.final_output).strip()
