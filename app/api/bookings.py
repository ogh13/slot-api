from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import verify_api_key, get_arq_queue
from app.schemas.booking_schemas import BookingCreate, BookingResponse, BookingFilter
from app.schemas.pagination_schemas import PaginatedResponse
from app.services.booking_service import create_booking, get_booking, cancel_booking, list_bookings

router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)

@router.post("/", response_model=BookingResponse, status_code=201)
async def create_booking_endpoint(data: BookingCreate,
                                  db: AsyncSession = Depends(get_db),
                                  arq=Depends(get_arq_queue)):
    return await create_booking(db, data, arq)

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking_endpoint(booking_id: str, db: AsyncSession = Depends(get_db)):
    return await get_booking(db, booking_id)

@router.get("/", response_model=PaginatedResponse[BookingResponse])
async def get_bookings(
    filters: BookingFilter = Depends(),
    skip: int = 0, 
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    items, total = await list_bookings(db, filters, skip, limit)
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.delete("/{booking_id}", status_code=204)
async def delete_booking_endpoint(
    booking_id: str, 
    db: AsyncSession = Depends(get_db),
    arq=Depends(get_arq_queue)
):
    await cancel_booking(db, booking_id, arq)