import logging
from datetime import datetime, timezone
import httpx
from sqlalchemy import select
from app.config import settings
from app.database import async_session_factory
from app.models.notification_model import Notification, NotificationStatus
from app.models.booking_model import Booking, BookingStatus

logger = logging.getLogger(__name__)

async def send_reminder(ctx, notification_id: str, booking_id: str):
    """
    Tâche de fond appelée par ARQ pour envoyer un rappel de réservation via webhook.
    
    Args:
        ctx: Contexte ARQ.
        notification_id (str): ID de l'enregistrement de notification à mettre à jour.
        booking_id (str): ID de la réservation concernée.
    """
    async with async_session_factory() as session:
        # Récupération de la notification et de la réservation
        notif = (await session.execute(
            select(Notification).where(Notification.id == notification_id)
        )).scalar_one_or_none()
        if not notif:
            logger.error(f"Notification {notification_id} introuvable")
            return

        booking = (await session.execute(
            select(Booking).where(Booking.id == booking_id)
        )).scalar_one_or_none()

        if not booking or booking.status != BookingStatus.CONFIRMED:
            notif.status = NotificationStatus.CANCELLED
            await session.commit()
            return

        # Construction du payload
        trigger_text = "24h" if notif.trigger == "24h_before" else "1h"
        payload = {
            "booking_id": str(booking.id),
            "client_phone": booking.client_phone,
            "message": f"Rappel : votre rendez-vous est dans {trigger_text} avec {booking.resource.name}",
            "trigger": notif.trigger
        }

        # Appel au webhook interne
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.API_BASE_URL}/webhooks/notify",
                    json=payload,
                    headers={"X-API-Key": settings.API_KEY}
                )
                resp.raise_for_status()
                notif.status = NotificationStatus.SENT
                notif.sent_at = datetime.now(timezone.utc)
        except Exception:
            logger.exception("Échec de l'envoi du webhook")
            notif.status = NotificationStatus.FAILED
        await session.commit()

async def send_waitlist_notification(ctx, notification_id: str, payload: dict):
    """
    Tâche de fond appelée par ARQ pour notifier un client en liste d'attente via webhook.
    
    Args:
        ctx: Contexte ARQ.
        notification_id (str): ID de l'enregistrement de notification.
        payload (dict): Données à envoyer au webhook (client_phone, message, etc.).
    """
    async with async_session_factory() as session:
        notif = (await session.execute(
            select(Notification).where(Notification.id == notification_id)
        )).scalar_one_or_none()
        
        if not notif:
            logger.error(f"Notification {notification_id} introuvable")
            return
            
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.API_BASE_URL}/webhooks/notify",
                    json=payload,
                    headers={"X-API-Key": settings.API_KEY}
                )
                resp.raise_for_status()
                notif.status = NotificationStatus.SENT
                notif.sent_at = datetime.now(timezone.utc)
        except Exception:
            logger.exception("Échec de l'envoi du webhook (waitlist)")
            notif.status = NotificationStatus.FAILED
        await session.commit()