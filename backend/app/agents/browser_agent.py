import json
import os
from dataclasses import dataclass
from typing import Any

from app.agents.mcp_servers import create_browser_agent_mcp_servers


@dataclass(frozen=True)
class RetrievedDocument:
    title: str
    source: str
    source_url: str
    date: str
    image: str
    full_text: str


def _documents_from_json(value: str, limit: int) -> list[RetrievedDocument]:
    value = value.strip()
    if value.startswith("```"):
        value = value.strip("`")
        if value.startswith("json"):
            value = value[4:].strip()

    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return []

    if not isinstance(payload, list):
        return []

    documents: list[RetrievedDocument] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        document = _document_from_mapping(item)
        if document is not None:
            documents.append(document)
        if len(documents) == limit:
            break
    return documents


def _document_from_mapping(item: dict[str, Any]) -> RetrievedDocument | None:
    title = str(item.get("title", "")).strip()
    source = str(item.get("source", "")).strip()
    source_url = str(item.get("source_url") or item.get("url") or "").strip()
    date = str(item.get("date", "")).strip()
    image = str(item.get("image", "")).strip()
    full_text = str(item.get("full_text", "")).strip()

    if not title or not source or not source_url or not full_text:
        return None

    return RetrievedDocument(
        title=title,
        source=source,
        source_url=source_url,
        date=date,
        image=image,
        full_text=full_text,
    )


async def retrieve_latest_documents(source_urls: tuple[str, ...], limit: int = 5) -> list[RetrievedDocument]:
    if not source_urls or not os.getenv("OPENAI_API_KEY"):
        return []

    try:
        from agents import Agent, Runner
        from agents.mcp import MCPServerManager
    except ImportError:
        return []

    mcp_servers = create_browser_agent_mcp_servers(timeout_seconds=90)
    async with MCPServerManager(
        mcp_servers,
        connect_timeout_seconds=60,
        cleanup_timeout_seconds=20,
        drop_failed_servers=True,
        strict=False,
        connect_in_parallel=True,
    ) as manager:
        agent = Agent(
            name="Civic Pulse Browser Agent",
            instructions=(
                "You retrieve Kenyan civic source documents for Civic Pulse. Use Playwright MCP tools "
                "to browse source websites and identify the latest reports, bills, or acts. Use the "
                "PDF Reader MCP tools whenever a selected item is a PDF or a downloaded PDF file. "
                "Return only a valid JSON array. Each object must contain: title, source, source_url, "
                "date, image, and full_text. The full_text must contain the substantive document text "
                "needed for a separate summarizer agent. Return no markdown and no commentary."
            ),
            mcp_servers=manager.active_servers,
            mcp_config={
                "convert_schemas_to_strict": True,
                "include_server_in_tool_names": True,
            },
        )
        prompt = (
            f"Retrieve the latest {limit} reports, bills, or acts from these sources:\n"
            f"{json.dumps(list(source_urls), ensure_ascii=True)}\n\n"
            "Prefer the most recent items shown by the source website. Include the original source URL "
            "for each item. If an image is unavailable, use an empty string. If a date is unavailable, "
            "use an empty string. Return at most the requested number of items."
        )
        result = await Runner.run(agent, prompt)

    return _documents_from_json(str(result.final_output), limit)
