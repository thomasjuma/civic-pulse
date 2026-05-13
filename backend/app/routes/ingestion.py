from fastapi import APIRouter

from app.models import IngestionResult
from app.services.ingestion import run_ingestion

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/run", response_model=IngestionResult)
async def run_ingestion_now() -> IngestionResult:
    return await run_ingestion()

