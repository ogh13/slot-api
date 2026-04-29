from contextlib import asynccontextmanager
from fastapi import FastAPI, Security, HTTPException, status

from fastapi.security import APIKeyHeader
from arq.connections import ArqRedis
from app.config import settings
from app.api import resources, availability, bookings, notifications, webhooks, waitlist

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Vérifie la validité de la clé API."""
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clé API invalide ou manquante",
        )
    return api_key

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = await ArqRedis.from_url(settings.REDIS_URL)
    yield
    # Shutdown
    await app.state.redis.close()

app = FastAPI(
    title="SlotAPI",
    version="1.0.0",
    dependencies=[Security(verify_api_key)],
    lifespan=lifespan
)


# Inclusion des routers
app.include_router(resources.router)
app.include_router(availability.router)
app.include_router(bookings.router)
app.include_router(notifications.router)
app.include_router(webhooks.router)
app.include_router(waitlist.router)
