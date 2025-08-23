from app.config.loggers import mail_webhook_logger as logger
from app.config.settings import settings
from app.models.webhook_models import ComposioWebhookEvent
from app.services.mail_webhook_service import queue_composio_email_processing
from fastapi import APIRouter, HTTPException, Request
from standardwebhooks.webhooks import Webhook

router = APIRouter()
wh = Webhook(settings.COMPOSIO_WEBHOOK_SECRET)


@router.post(
    "/webhook/composio",
)
async def webhook_composio(request: Request):
    webhook_payload = await request.json()
    webhook_headers = request.headers
    wh.verify(webhook_payload, webhook_headers)  # pyright: ignore[reportArgumentType]

    payload = await request.json()

    event_data = ComposioWebhookEvent(**payload)

    if event_data.type == "GMAIL_NEW_GMAIL_MESSAGE":
        # Extract user_id from the webhook event
        user_id = event_data.user_id

        if not user_id:
            logger.error("User ID is missing in Composio webhook")
            raise HTTPException(
                status_code=422,
                detail="User ID must be provided in webhook data.",
            )

        # Queue email processing with Composio data
        return await queue_composio_email_processing(user_id, event_data.data)

    return {"status": "success", "message": "Webhook received"}
