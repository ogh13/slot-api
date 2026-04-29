from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.resource_model import Resource
from app.schemas.resource_schemas import ResourceCreate
from fastapi import HTTPException

async def create_resource(db: AsyncSession, data: ResourceCreate) -> Resource:
    resource = Resource(name=data.name, type=data.type)
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return resource

async def get_resources(db: AsyncSession, skip: int = 0, limit: int = 100) -> tuple[list[Resource], int]:
    # Query for items
    query = select(Resource).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    
    # Query for total count
    count_query = select(func.count()).select_from(Resource)
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return items, total

async def get_resource(db: AsyncSession, resource_id: str) -> Resource:
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource

async def delete_resource(db: AsyncSession, resource_id: str):
    resource = await get_resource(db, resource_id)
    await db.delete(resource)
    await db.commit()