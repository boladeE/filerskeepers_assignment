"""Storage operations for books using Beanie."""

import hashlib
from typing import Optional

from bson import ObjectId

from app.crawler.models import Book
from app.database.models import BookDoc
from app.utils.logger import setup_logger

logger = setup_logger("storage")


def calculate_content_hash(book: Book) -> str:
    """Calculate content hash for change detection.

    Args:
        book: Book instance

    Returns:
        SHA256 hash string
    """
    # Create hash from key fields that indicate changes
    content_string = (
        f"{book.name}|{book.description}|{book.price_including_tax}|"
        f"{book.price_excluding_tax}|{book.availability}|{book.rating}|"
        f"{book.number_of_reviews}"
    )
    return hashlib.sha256(content_string.encode()).hexdigest()


class BookStorage:
    """Storage operations using Beanie Document API."""

    async def save_book(
        self, book: Book, store_html: bool = True
    ) -> Optional[ObjectId]:
        """Save or update book in database.

        Args:
            book: Book instance to save
            store_html: Whether to store raw HTML

        Returns:
            MongoDB ObjectId if successful, None otherwise
        """
        try:
            # Calculate content hash
            content_hash = calculate_content_hash(book)
            book.content_hash = content_hash

            # Prepare document
            book_dict = book.model_dump()
            book_dict["source_url"] = str(book_dict["source_url"])
            book_dict["image_url"] = str(book_dict["image_url"])

            # Store HTML separately if needed (for large HTML)
            if store_html and book.raw_html:
                # Store in a separate field, but limit size
                if len(book.raw_html) < 1000000:  # 1MB limit
                    book_dict["raw_html"] = book.raw_html
                else:
                    logger.warning(f"HTML too large for {book.source_url}, skipping")

            # Check if book exists and upsert using Beanie
            existing = await BookDoc.find_one(
                BookDoc.source_url == book_dict["source_url"]
            )
            if existing is None:
                doc = BookDoc(**book_dict)
                await doc.insert()
                logger.info(f"Inserted new book: {book.name}")
                return doc.id
            else:
                old_hash = existing.content_hash
                # Update the document
                for key, value in book_dict.items():
                    setattr(existing, key, value)
                await existing.save()
                if old_hash != content_hash:
                    logger.info(f"Updated book {book.name} with changes detected")
                else:
                    logger.debug(f"No changes detected for: {book.name}")
                return existing.id

        except Exception as e:
            logger.error(f"Error saving book {book.name}: {e}")
            return None

    async def get_book_by_url(self, source_url: str) -> Optional[dict]:
        """Get book by source URL.

        Args:
            source_url: Book source URL

        Returns:
            Book document or None
        """
        try:
            doc = await BookDoc.find_one(BookDoc.source_url == source_url)
            if doc:
                return doc.model_dump()
            return None
        except Exception as e:
            logger.error(f"Error getting book by URL {source_url}: {e}")
            return None

    async def get_all_book_urls(self) -> list[str]:
        """Get all book source URLs for resume capability.

        Returns:
            List of source URLs
        """
        try:
            docs = await BookDoc.find_all().to_list()
            return [str(doc.source_url) for doc in docs]
        except Exception as e:
            logger.error(f"Error getting all book URLs: {e}")
            return []
