"""Books API routes."""

from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth import verify_api_key
from app.database.models import BookDoc
from app.utils.logger import setup_logger

logger = setup_logger("api")

router = APIRouter(prefix="/books", tags=["books"])


@router.get("")
async def get_books(
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    rating: Optional[str] = Query(
        None, description="Filter by rating (One, Two, Three, Four, Five)"
    ),
    sort_by: Optional[str] = Query(
        "rating", description="Sort by: rating, price, reviews"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Get books with filtering and pagination.

    Args:
        category: Book category filter
        min_price: Minimum price filter
        max_price: Maximum price filter
        rating: Rating filter
        sort_by: Sort field
        page: Page number
        limit: Items per page
        api_key: Verified API key

    Returns:
        Paginated books response
    """
    try:
        # Build Beanie query
        query_expr = {}
        if category:
            query_expr["category"] = category
        if rating:
            query_expr["rating"] = rating
        if min_price is not None or max_price is not None:
            price_filters = {}
            if min_price is not None:
                price_filters["$gte"] = min_price
            if max_price is not None:
                price_filters["$lte"] = max_price
            query_expr["price_including_tax"] = price_filters

        sort_field = "-rating"
        if sort_by == "price":
            sort_field = "-price_including_tax"
        elif sort_by == "reviews":
            sort_field = "-number_of_reviews"

        skip = (page - 1) * limit

        total = await BookDoc.find(query_expr).count()
        docs = (
            await BookDoc.find(query_expr)
            .sort(sort_field)
            .skip(skip)
            .limit(limit)
            .to_list()
        )

        books = []
        for d in docs:
            data = d.model_dump(mode="json")
            data["_id"] = str(d.id)
            data.pop("raw_html", None)
            books.append(data)

        return {
            "books": books,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
            },
        }

    except Exception as e:
        logger.error(f"Error getting books: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{book_id}")
async def get_book(
    book_id: str,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Get book details by ID.

    Args:
        book_id: Book MongoDB ID
        api_key: Verified API key

    Returns:
        Book details
    """
    try:
        try:
            object_id = PydanticObjectId(book_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid book ID format")

        book = await BookDoc.get(object_id)

        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Convert to dict and format
        data = book.model_dump(mode="json")
        data["_id"] = str(book.id)
        data.pop("raw_html", None)
        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting book {book_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
