from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException
from app.models.slot_model import Slot
from app.models.waitlist_model import Waitlist

async def join_waitlist(db: AsyncSession, slot_id: str, client_name: str, client_phone: str) -> Waitlist:
    """
    Inscrit un client sur la liste d'attente d'un créneau déjà réservé.
    
    Args:
        db (AsyncSession): Session de base de données.
        slot_id (str): Identifiant du créneau.
        client_name (str): Nom du client.
        client_phone (str): Téléphone du client.
        
    Returns:
        Waitlist: L'entrée créée dans la liste d'attente.
        
    Raises:
        HTTPException: Si le créneau n'existe pas (404) ou s'il n'est pas encore réservé (400).
    """
    # Vérifier que le créneau existe et est bien réservé
    result = await db.execute(select(Slot).where(Slot.id == slot_id))
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    if not slot.is_booked:
        raise HTTPException(status_code=400, detail="Slot is not booked, you can book it directly")

    entry = Waitlist(slot_id=slot_id, client_name=client_name, client_phone=client_phone)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry

async def get_waitlist(db: AsyncSession, slot_id: str, skip: int = 0, limit: int = 100) -> tuple[list[Waitlist], int]:
    """
    Récupère la liste d'attente d'un créneau spécifique avec pagination.
    
    Args:
        db (AsyncSession): Session de base de données.
        slot_id (str): Identifiant du créneau.
        skip (int): Offset de pagination.
        limit (int): Limite de pagination.
        
    Returns:
        tuple[list[Waitlist], int]: Liste des entrées et compte total.
    """
    query = select(Waitlist).where(Waitlist.slot_id == slot_id)
    
    # Query for items
    items_query = query.offset(skip).limit(limit)
    result = await db.execute(items_query)
    items = result.scalars().all()
    
    # Query for total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return items, total
