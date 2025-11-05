"""Changes API routes."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth import verify_api_key
from app.database.models import ChangeLogDoc
from app.utils.logger import setup_logger

logger = setup_logger("api")

router = APIRouter(prefix="/changes", tags=["changes"])


@router.get("")
async def get_changes(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    change_type: Optional[str] = Query(None, description="Filter by change type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of changes"),
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Get recent changes.

    Args:
        date: Date filter (YYYY-MM-DD)
        change_type: Change type filter
        limit: Maximum number of changes
        api_key: Verified API key

    Returns:
        Changes response
    """
    try:
        query_expr = {}

        if date:
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                start_date = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date.replace(day=start_date.day + 1)
                query_expr["timestamp"] = {"$gte": start_date, "$lt": end_date}
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
                )

        if change_type:
            query_expr["change_type"] = change_type

        docs = (
            await ChangeLogDoc.find(query_expr)
            .sort("-timestamp")
            .limit(limit)
            .to_list()
        )
        changes = []
        for d in docs:
            data = d.model_dump(mode="json")
            data["_id"] = str(d.id)
            # Convert book_id if it exists
            if "book_id" in data and data["book_id"]:
                data["book_id"] = str(data["book_id"])
            changes.append(data)

        return {
            "changes": changes,
            "count": len(changes),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting changes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
