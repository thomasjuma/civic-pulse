from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.config import get_settings
from app.services.chat import ChatWebhookResult, handle_whatsapp_webhook

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/webhook", response_class=PlainTextResponse)
def verify_whatsapp_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
) -> str:
    settings = get_settings()
    if mode == "subscribe" and settings.whatsapp_verify_token and token == settings.whatsapp_verify_token:
        return challenge
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/webhook", response_model=ChatWebhookResult)
async def receive_whatsapp_webhook(request: Request) -> ChatWebhookResult:
    payload: dict[str, Any] = await request.json()
    return await handle_whatsapp_webhook(payload)
