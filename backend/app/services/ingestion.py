import logging

from app.agents.browser_agent import retrieve_latest_documents
from app.agents.summarizer_agent import summarize_and_publish_document
from app.config import get_settings
from app.models import IngestionResult

logger = logging.getLogger(__name__)


async def run_ingestion() -> IngestionResult:
    settings = get_settings()
    source_urls = tuple(str(url) for url in settings.source_urls)
    logger.info("Starting ingestion run: sources=%s", len(source_urls))
    try:
        documents = await retrieve_latest_documents(source_urls, limit=2)
    except Exception:
        logger.error("Failed to retrieve latest documents", exc_info=True)
        raise

    logger.info("Retrieved documents for ingestion: count=%s", len(documents))
    processed_count = 0
    sent_count = 0

    for document in documents:
        logger.info("Processing document: source=%s title=%s", document.source, document.title)
        try:
            result = await summarize_and_publish_document(
                title=document.title,
                source=document.source,
                full_text=document.full_text,
                date=document.date,
                image=document.image,
                source_url=document.source_url,
            )
        except Exception:
            logger.error(
                "Failed to summarize and publish document: source=%s title=%s",
                document.source,
                document.title,
                exc_info=True,
            )
            raise
        if result.article_id is not None:
            processed_count += 1
        sent_count += result.whatsapp_messages_sent
        logger.info(
            "Processed document: source=%s title=%s article_id=%s whatsapp_messages_sent=%s",
            document.source,
            document.title,
            result.article_id,
            result.whatsapp_messages_sent,
        )

    ingestion_result = IngestionResult(
        candidates_found=len(documents),
        articles_processed=processed_count,
        whatsapp_messages_sent=sent_count,
    )
    logger.info(
        "Completed ingestion run: candidates_found=%s articles_processed=%s whatsapp_messages_sent=%s",
        ingestion_result.candidates_found,
        ingestion_result.articles_processed,
        ingestion_result.whatsapp_messages_sent,
    )
    return ingestion_result
