import logging
from fastapi import APIRouter
from app.schemas.webhooks_schemas import WebhookPayload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/notify", status_code=200)
async def notify(payload: WebhookPayload):
    logger.info(
        "Webhook reçu — booking=%s trigger=%s msg=%s",
        payload.booking_id, payload.trigger, payload.message
    )
    return {"status": "ok"}
