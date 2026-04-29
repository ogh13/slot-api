from pydantic import BaseModel

class WebhookPayload(BaseModel):
    booking_id: str
    client_phone: str
    message: str
    trigger: str