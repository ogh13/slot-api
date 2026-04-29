from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import verify_api_key
from app.schemas.waitlist_schemas import WaitlistCreate, WaitlistResponse
from app.schemas.pagination_schemas import PaginatedResponse

from app.services import waitlist_service as ws

router = APIRouter(
    prefix="/slots/{slot_id}/waitlist",
    tags=["Waitlist"]
)

@router.post("/", response_model=WaitlistResponse, status_code=201)
async def join_waitlist_endpoint(slot_id: str, data: WaitlistCreate,
                                 db: AsyncSession = Depends(get_db)):
    return await ws.join_waitlist(db, slot_id, data.client_name, data.client_phone)

@router.get("/", response_model=PaginatedResponse[WaitlistResponse])
async def list_waitlist_endpoint(
    slot_id: str, 
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    items, total = await ws.get_waitlist(db, slot_id, skip, limit)
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }