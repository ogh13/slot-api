from fastapi import Header, HTTPException, Request
from app.config import settings

async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

async def get_arq_queue(request: Request):
    return request.app.state.redis