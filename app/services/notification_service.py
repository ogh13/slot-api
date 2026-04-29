from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.notification_model import Notification
from app.services.booking_service import get_booking

async def get_booking_notifications(db: AsyncSession, booking_id: str):
    await get_booking(db, booking_id)   # vérifier que la réservation existe
    result = await db.execute(
        select(Notification).where(Notification.booking_id == booking_id)
    )
    return result.scalars().all()