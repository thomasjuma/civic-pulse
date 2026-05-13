from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routes.articles import router as articles_router
from app.routes.ingestion import router as ingestion_router
from app.routes.subscribers import router as subscribers_router
from app.services.scheduler import SummaryScheduler

summary_scheduler = SummaryScheduler()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
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

