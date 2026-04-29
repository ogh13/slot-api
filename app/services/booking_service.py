from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.booking_model import Booking, BookingStatus
from app.models.slot_model import Slot
from app.models.notification_model import Notification, NotificationStatus
from app.schemas.booking_schemas import BookingCreate, BookingFilter
from app.services.slot_service import get_slot
from arq.connections import ArqRedis
from fastapi import HTTPException
from app.models.waitlist_model import Waitlist, WaitlistStatus


async def create_booking(db: AsyncSession, data: BookingCreate, arq_queue: ArqRedis) -> Booking:
    """
    Crée une nouvelle réservation, marque le créneau comme réservé et planifie les notifications.
    
    Args:
        db (AsyncSession): Session de base de données.
        data (BookingCreate): Données de la réservation.
        arq_queue (ArqRedis): File d'attente Redis pour les tâches de fond.
        
    Returns:
        Booking: L'objet de réservation créé.
        
    Raises:
        HTTPException: Si le créneau n'appartient pas à la ressource (400), s'il est déjà réservé (409) ou s'il est passé (400).
    """
    slot = await get_slot(db, data.slot_id)

    if slot.resource_id != data.resource_id:
        raise HTTPException(status_code=400, detail="Slot does not belong to this resource")
    if slot.is_booked:
        raise HTTPException(status_code=409, detail="Slot is already booked")
    if slot.start_time <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Cannot book a past slot")

    # Création de la réservation
    booking = Booking(
        resource_id=data.resource_id,
        slot_id=data.slot_id,
        client_name=data.client_name,
        client_phone=data.client_phone,
        status=BookingStatus.CONFIRMED
    )
    db.add(booking)
    slot.is_booked = True
    db.add(slot)
    await db.flush()   # pour obtenir booking.id

    # Planification des notifications (seulement si dans le futur)
    triggers = {
        "24h_before": slot.start_time - timedelta(hours=24),
        "1h_before": slot.start_time - timedelta(hours=1)
    }
    notifications = []
    for trigger, scheduled_for in triggers.items():
        if scheduled_for > datetime.now(timezone.utc):
            notif = Notification(
                booking_id=booking.id,
                trigger=trigger,
                scheduled_for=scheduled_for,
                status=NotificationStatus.PENDING
            )
            db.add(notif)
            notifications.append(notif)

    await db.flush()  # pour obtenir les IDs

    # Enqueue des jobs ARQ différés
    for notif in notifications:
        job_id = f"notif_{notif.id}"
        await arq_queue.enqueue_job(
            "send_reminder",
            notif.id,
            booking.id,
            _job_id=job_id,
            _defer_until=notif.scheduled_for
        )
        notif.job_id = job_id

    await db.commit()
    await db.refresh(booking)
    return booking

async def get_booking(db: AsyncSession, booking_id: str) -> Booking:
    """
    Récupère une réservation par son identifiant unique.
    
    Args:
        db (AsyncSession): Session de base de données.
        booking_id (str): Identifiant de la réservation.
        
    Returns:
        Booking: L'objet de réservation trouvé.
        
    Raises:
        HTTPException: Si la réservation n'est pas trouvée (404).
    """
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.slot))
        .where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

async def cancel_booking(db: AsyncSession, booking_id: str, arq_queue: ArqRedis) -> Booking:
    """
    Annule une réservation et déclenche le processus de liste d'attente.
    
    Args:
        db (AsyncSession): Session de base de données.
        booking_id (str): Identifiant de la réservation à annuler.
        arq_queue (ArqRedis): File d'attente Redis.
        
    Returns:
        Booking: L'objet de réservation mis à jour avec le statut CANCELLED.
        
    Raises:
        HTTPException: Si la réservation est déjà annulée (400) ou si l'annulation intervient moins d'une heure avant le début (400).
    """
    booking = await get_booking(db, booking_id)
    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Booking already cancelled")
    time_left = booking.slot.start_time - datetime.now(timezone.utc)
    if time_left < timedelta(hours=1):
        raise HTTPException(status_code=400,
                            detail="Cannot cancel less than 1 hour before the slot")
    booking.status = BookingStatus.CANCELLED
    booking.slot.is_booked = False
    await db.flush()  # On valide les changements sans commit final

    # Traiter la liste d'attente
    await _process_waitlist(db, booking.slot_id, arq_queue)

    await db.commit()
    await db.refresh(booking)
    return booking

async def list_bookings(db: AsyncSession, filters: BookingFilter, skip: int = 0, limit: int = 100) -> tuple[list[Booking], int]:
    """
    Liste les réservations en fonction de filtres avec pagination.
    
    Args:
        db (AsyncSession): Session de base de données.
        filters (BookingFilter): Critères de filtrage.
        skip (int): Nombre d'éléments à sauter.
        limit (int): Nombre maximum d'éléments à retourner.
        
    Returns:
        tuple[list[Booking], int]: La liste des réservations et le nombre total correspondant aux filtres.
    """
    query = select(Booking)
    if filters.resource_id:
        query = query.where(Booking.resource_id == filters.resource_id)
    if filters.status:
        query = query.where(Booking.status == filters.status)
    if filters.date:
        query = query.join(Slot).where(func.date(Slot.start_time) == filters.date.date())
    if filters.client_name:
        query = query.where(Booking.client_name.ilike(f"%{filters.client_name}%"))
    if filters.client_phone:
        query = query.where(Booking.client_phone == filters.client_phone)
    
    # Query for items
    items_query = query.offset(skip).limit(limit)
    result = await db.execute(items_query)
    items = result.scalars().all()
    
    # Query for total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return items, total


async def _process_waitlist(db: AsyncSession, slot_id: str, arq_queue: ArqRedis):
    """
    Notifie la première personne en liste d'attente pour un créneau qui vient de se libérer.
    
    Args:
        db (AsyncSession): Session de base de données.
        slot_id (str): Identifiant du créneau libéré.
        arq_queue (ArqRedis): File d'attente Redis.
    """
    entry = (await db.execute(
        select(Waitlist)
        .where(Waitlist.slot_id == slot_id, Waitlist.status == WaitlistStatus.WAITING)
        .order_by(Waitlist.created_at.asc())
    )).scalars().first()

    if not entry:
        return

    # Marquer comme notifiée
    entry.status = WaitlistStatus.NOTIFIED

    # Créer une notification (log) pour tracer l’envoi
    notif = Notification(
        booking_id=None,        # pas lié à une réservation
        trigger="slot_available",
        scheduled_for=datetime.now(timezone.utc),
        status=NotificationStatus.PENDING,
    )
    db.add(notif)
    await db.flush()
    
    # Appel via le worker ARQ
    payload = {
        "booking_id": f"waitlist_{entry.id}",
        "client_phone": entry.client_phone,
        "message": f"Un créneau s'est libéré pour le slot {slot_id}. Contactez-nous pour réserver.",
        "trigger": "slot_available"
    }
    job_id = f"notif_{notif.id}"
    await arq_queue.enqueue_job(
        "send_waitlist_notification",
        notif.id,
        payload,
        _job_id=job_id
    )
    notif.job_id = job_id

    await db.flush()



