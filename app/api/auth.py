"""API key authentication."""

import secrets
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.database.models import ApiKeyDoc
from app.utils.logger import setup_logger

logger = setup_logger("api")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verify API key from header.

    Args:
        api_key: API key from header

    Returns:
        API key if valid

    Raises:
        HTTPException: If API key is invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide X-API-Key header.",
        )

    try:
        api_key_doc = await ApiKeyDoc.find_one(ApiKeyDoc.api_key == api_key)

        if not api_key_doc or not api_key_doc.is_active:
            logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
            )

        # Update last used timestamp
        api_key_doc.last_used = datetime.utcnow()
        await api_key_doc.save()

        return api_key

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying API key: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        )


async def create_api_key(name: str, description: Optional[str] = None) -> str:
    """Create a new API key.

    Args:
        name: API key name
        description: Optional description

    Returns:
        Generated API key
    """
    api_key = f"fk_{secrets.token_urlsafe(32)}"

    try:
        doc = ApiKeyDoc(
            api_key=api_key,
            name=name,
            description=description,
            is_active=True,
            created_at=datetime.utcnow(),
            last_used=None,
        )
        await doc.insert()
        logger.info(f"Created API key: {name}")
        return api_key

    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise
