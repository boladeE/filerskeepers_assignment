"""Beanie document models for MongoDB collections."""

from datetime import datetime
from typing import Annotated, Optional

from beanie import Document, Indexed
from pydantic import HttpUrl


class BookDoc(Document):
    """Book document stored in MongoDB via Beanie."""

    name: str
    description: str = ""
    category: Indexed(str)
    price_including_tax: Indexed(float)
    price_excluding_tax: float
    availability: str
    number_of_reviews: Indexed(int) = 0
    image_url: HttpUrl
    rating: Optional[str] = None
    source_url: Indexed(HttpUrl, unique=True)
    crawl_timestamp: datetime = datetime.utcnow()
    status: str = "active"
    content_hash: Optional[str] = None
    raw_html: Optional[str] = None
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "books"


class ChangeLogDoc(Document):
    """Change log for books."""

    book_id: str
    change_type: Indexed(str)
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    book_url: str
    timestamp: Indexed(datetime) = datetime.utcnow()

    class Settings:
        name = "change_log"


class ApiKeyDoc(Document):
    """API key storage."""

    api_key: Indexed(str, unique=True)
    name: str
    description: Optional[str] = None
    is_active: Annotated[bool, Indexed()] = True
    created_at: datetime = datetime.utcnow()
    last_used: Optional[datetime] = None

    class Settings:
        name = "api_keys"
