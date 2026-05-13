import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routes.articles import router as articles_router
from app.routes.ingestion import router as ingestion_router
from app.routes.subscribers import router as subscribers_router
from app.services.scheduler import SummaryScheduler

# Load environment variables
load_dotenv()

summary_scheduler = SummaryScheduler()
logger = logging.getLogger(__name__)

GREEN = "\033[32m"
BLUE = "\033[34m"
RED = "\033[31m"
RESET = "\033[0m"

def configure_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format=f"%(asctime)s {GREEN}%(levelname)s{RESET} [{BLUE}%(name)s{RESET}] %(message)s",
    )
    logging.getLogger().setLevel(level)
    logging.getLogger("app").setLevel(level)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    logger.info("Starting application scheduler")
    init_db()
    summary_scheduler.start()
    yield
    await summary_scheduler.stop()


app = FastAPI(title="Civic Pulse API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles_router)
app.include_router(ingestion_router)
app.include_router(subscribers_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
