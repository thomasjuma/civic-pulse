from app.agents.browser_agent import retrieve_latest_documents
from app.agents.summarizer_agent import summarize_and_publish_document
from app.config import get_settings
from app.models import IngestionResult


async def run_ingestion() -> IngestionResult:
    settings = get_settings()
    source_urls = tuple(str(url) for url in settings.source_urls)
    documents = await retrieve_latest_documents(source_urls, limit=5)
    processed_count = 0
    sent_count = 0

    for document in documents:
        result = await summarize_and_publish_document(
            title=document.title,
            source=document.source,
            full_text=document.full_text,
            date=document.date,
            image=document.image,
            source_url=document.source_url,
        )
        if result.article_id is not None:
            processed_count += 1
        sent_count += result.whatsapp_messages_sent

    return IngestionResult(
        candidates_found=len(documents),
        articles_processed=processed_count,
        whatsapp_messages_sent=sent_count,
    )
