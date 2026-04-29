from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.slot_model import Slot
from app.schemas.availability_schemas import AvailabilityCreate
from app.services.resource_service import get_resource
from fastapi import HTTPException

async def add_availability(db: AsyncSession, resource_id: str, data: AvailabilityCreate) -> list[Slot]:
    """
    Ajoute des créneaux de disponibilité pour une ressource donnée.
    
    Args:
        db (AsyncSession): Session de base de données.
        resource_id (str): Identifiant de la ressource.
        data (AvailabilityCreate): Liste des créneaux à créer.
        
    Returns:
        list[Slot]: Liste des objets Slot créés.
        
    Raises:
        HTTPException: Si la ressource n'existe pas, si un créneau est dans le passé ou s'il y a un chevauchement.
    """
    # Vérification que la ressource existe
    await get_resource(db, resource_id)

    new_slots = []
    for slot_in in data.slots:
        start = slot_in.start_time
        end = slot_in.end_time
        
        if end <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot create a slot that ends in the past: {start} to {end}"
            )

        # Détection de chevauchement avec les créneaux existants
        overlap = select(Slot).where(
            Slot.resource_id == resource_id,
            Slot.start_time < end,
            Slot.end_time > start
        )
        existing = (await db.execute(overlap)).scalars().first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Slot from {start} to {end} overlaps with an existing slot"
            )

        slot = Slot(resource_id=resource_id, start_time=start, end_time=end, is_booked=False)
        db.add(slot)
        new_slots.append(slot)

    await db.commit()
    for slot in new_slots:
        await db.refresh(slot)
    return new_slots

async def get_availability(db: AsyncSession, resource_id: str, skip: int = 0, limit: int = 100) -> tuple[list[Slot], int]:
    """
    Récupère les créneaux disponibles et futurs pour une ressource avec pagination.
    
    Args:
        db (AsyncSession): Session de base de données.
        resource_id (str): Identifiant de la ressource.
        skip (int): Offset de pagination.
        limit (int): Limite de pagination.
        
    Returns:
        tuple[list[Slot], int]: Liste des créneaux et compte total.
    """
    await get_resource(db, resource_id)
    now = datetime.now(timezone.utc)
    query = select(Slot).where(
        Slot.resource_id == resource_id,
        Slot.is_booked.is_(False),
        Slot.end_time > now
    )
    
    # Query for items
    items_query = query.offset(skip).limit(limit)
    result = await db.execute(items_query)
    items = result.scalars().all()
    
    # Query for total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return items, total

async def get_slot(db: AsyncSession, slot_id: str) -> Slot:
    """
    Récupère un créneau spécifique par son identifiant.
    
    Args:
        db (AsyncSession): Session de base de données.
        slot_id (str): Identifiant du créneau.
        
    Returns:
        Slot: L'objet Slot trouvé.
        
    Raises:
        HTTPException: Si le créneau n'est pas trouvé (404).
    """
    result = await db.execute(select(Slot).where(Slot.id == slot_id))
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return slot