from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.resource_schemas import ResourceCreate, ResourceResponse
from app.services.resource_service import create_resource, get_resources, delete_resource
from app.schemas.pagination_schemas import PaginatedResponse

router = APIRouter(
    prefix="/resources",
    tags=["Resources"]
)

@router.post("/", response_model=ResourceResponse, status_code=201)
async def create_resource_endpoint(data: ResourceCreate, db: AsyncSession = Depends(get_db)):
    return await create_resource(db, data)

@router.get("/", response_model=PaginatedResponse[ResourceResponse])
async def list_resources(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    items, total = await get_resources(db, skip, limit)
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.delete("/{resource_id}", status_code=204)
async def delete_resource_endpoint(resource_id: str, db: AsyncSession = Depends(get_db)):
    await delete_resource(db, resource_id)