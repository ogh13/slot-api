from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import verify_api_key
from app.schemas.notification_schemas import NotificationResponse
from app.services.notification_service import get_booking_notifications

router = APIRouter(
    prefix="/bookings/{booking_id}/notifications",
    tags=["Notifications"]
)

@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(booking_id: str, db: AsyncSession = Depends(get_db)):
    return await get_booking_notifications(db, booking_id)