"""Auth API routes (API key management)."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import create_api_key
from app.utils.logger import setup_logger

logger = setup_logger("api")

router = APIRouter(prefix="/auth", tags=["auth"])


class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., description="A friendly name for the API key")
    description: Optional[str] = Field(None, description="Optional description")


class CreateApiKeyResponse(BaseModel):
    api_key: str


@router.post("/api-keys", response_model=CreateApiKeyResponse)
async def create_api_key_route(payload: CreateApiKeyRequest) -> CreateApiKeyResponse:
    """Create a new API key and return it.

    Note: In production, protect this route with admin auth or IP allowlists.
    """
    try:
        key = await create_api_key(name=payload.name, description=payload.description)
        return CreateApiKeyResponse(api_key=key)
    except Exception as e:
        logger.error(f"Error creating API key via route: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key")
