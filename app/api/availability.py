from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import verify_api_key
from app.schemas.availability_schemas import AvailabilityCreate, SlotResponse
from app.services.slot_service import add_availability, get_availability
from app.schemas.pagination_schemas import PaginatedResponse

router = APIRouter(
    prefix="/resources/{resource_id}/availability",
    tags=["Availability"]
)

@router.post("/", response_model=list[SlotResponse], status_code=201)
async def create_availability(resource_id: str, data: AvailabilityCreate,
                              db: AsyncSession = Depends(get_db)):
    return await add_availability(db, resource_id, data)

@router.get("/", response_model=PaginatedResponse[SlotResponse])
async def list_availability(
    resource_id: str, 
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    items, total = await get_availability(db, resource_id, skip, limit)
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }