import logging

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def send_text(self, recipient_number: str, message: str) -> bool:
        if not (
            self.settings.whatsapp_access_token
            and self.settings.whatsapp_phone_number_id
        ):
            logger.info("WhatsApp credentials are not configured; message not sent")
            return False

        logger.info("Sending WhatsApp text message: recipient=%s", recipient_number)
        url = (
            f"https://graph.facebook.com/{self.settings.whatsapp_api_version}/"
            f"{self.settings.whatsapp_phone_number_id}/messages"
        )
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_number,
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }
        headers = {"Authorization": f"Bearer {self.settings.whatsapp_access_token}"}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
        except Exception:
            logger.error(
                "Failed to send WhatsApp text message: recipient=%s",
                recipient_number,
                exc_info=True,
            )
            raise
        logger.info("Sent WhatsApp text message: recipient=%s", recipient_number)
        return True
