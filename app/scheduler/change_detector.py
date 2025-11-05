"""Change detection logic for books."""

from datetime import UTC, datetime
from typing import Optional

from bson import ObjectId
from beanie import PydanticObjectId

from app.crawler.models import Book
from app.crawler.storage import BookStorage, calculate_content_hash
from app.database.mongodb import MongoDB
from app.utils.logger import setup_logger

logger = setup_logger("change_detector")


async def log_change(
    book_id: ObjectId,
    change_type: str,
    old_value: Optional[str],
    new_value: Optional[str],
    book_url: str,
) -> None:
    """Log a change to the change_log collection.

    Args:
        book_id: MongoDB book ID
        change_type: Type of change (e.g., 'price', 'availability', 'new_book')
        old_value: Old value
        new_value: New value
        book_url: Book source URL
    """
    try:
        db = MongoDB.get_database()
        change_log_collection = db["change_log"]

        change_entry = {
            "book_id": book_id,
            "change_type": change_type,
            "old_value": old_value,
            "new_value": new_value,
            "book_url": book_url,
            "timestamp": datetime.now(UTC),
        }

        await change_log_collection.insert_one(change_entry)
        logger.info(f"Logged change: {change_type} for book {book_id}")
    except Exception as e:
        logger.error(f"Error logging change: {e}")


class ChangeDetector:
    """Detect changes in book data."""

    def __init__(self):
        """Initialize change detector."""
        self.storage = BookStorage()

    async def detect_changes(
        self, new_book: Book, store_html: bool = True
    ) -> tuple[bool, Optional[ObjectId], list[str]]:
        """Detect changes between new book data and stored data.

        Args:
            new_book: Newly scraped book data
            store_html: Whether to store raw HTML (default: True for initial crawls)

        Returns:
            Tuple of (is_new, book_id, list_of_changes)
        """
        try:
            # Get existing book
            existing_book = await self.storage.get_book_by_url(str(new_book.source_url))

            if not existing_book:
                # New book
                book_id = await self.storage.save_book(new_book, store_html=store_html)
                if book_id:
                    await log_change(
                        book_id,
                        "new_book",
                        None,
                        new_book.name,
                        str(new_book.source_url),
                    )
                    logger.info(f"New book detected: {new_book.name}")
                return True, book_id, ["new_book"]

            # Compare with existing book
            # Ensure book_id is an ObjectId
            book_id_raw = existing_book.get("_id")
            if isinstance(book_id_raw, str):
                book_id = ObjectId(book_id_raw)
            elif isinstance(book_id_raw, PydanticObjectId):
                book_id = ObjectId(str(book_id_raw))
            else:
                book_id = book_id_raw
            
            changes = []

            # Calculate content hash
            new_hash = calculate_content_hash(new_book)
            old_hash = existing_book.get("content_hash")

            if new_hash != old_hash:
                # Content has changed, check individual fields

                # Check price changes
                if (
                    abs(
                        new_book.price_including_tax
                        - existing_book.get("price_including_tax", 0)
                    )
                    > 0.01
                ):
                    old_price = f"{existing_book.get('price_including_tax', 0):.2f}"
                    new_price = f"{new_book.price_including_tax:.2f}"
                    changes.append("price")
                    await log_change(
                        book_id,
                        "price",
                        old_price,
                        new_price,
                        str(new_book.source_url),
                    )

                # Check availability changes
                if new_book.availability != existing_book.get("availability", ""):
                    changes.append("availability")
                    await log_change(
                        book_id,
                        "availability",
                        existing_book.get("availability", ""),
                        new_book.availability,
                        str(new_book.source_url),
                    )

                # Check description changes
                if new_book.description != existing_book.get("description", ""):
                    changes.append("description")
                    await log_change(
                        book_id,
                        "description",
                        "updated",
                        "updated",
                        str(new_book.source_url),
                    )

                # Check rating changes
                if new_book.rating != existing_book.get("rating"):
                    changes.append("rating")
                    await log_change(
                        book_id,
                        "rating",
                        str(existing_book.get("rating", "")),
                        str(new_book.rating),
                        str(new_book.source_url),
                    )

                # Check review count changes
                if new_book.number_of_reviews != existing_book.get(
                    "number_of_reviews", 0
                ):
                    changes.append("reviews")
                    await log_change(
                        book_id,
                        "reviews",
                        str(existing_book.get("number_of_reviews", 0)),
                        str(new_book.number_of_reviews),
                        str(new_book.source_url),
                    )

                # Update the book in database
                if changes:
                    # Store HTML if this is a scheduled update (for fallback)
                    await self.storage.save_book(new_book, store_html=store_html)
                    logger.info(f"Updated book {new_book.name}: {', '.join(changes)}")

            return False, book_id, changes

        except Exception as e:
            logger.error(f"Error detecting changes for {new_book.name}: {e}")
            return False, None, []
