"""Pydantic models for book data."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Book(BaseModel):
    """Book data model."""

    name: str = Field(..., description="Name of the book")
    description: str = Field(default="", description="Description of the book")
    category: str = Field(..., description="Book category")
    price_including_tax: float = Field(..., description="Price including tax")
    price_excluding_tax: float = Field(..., description="Price excluding tax")
    availability: str = Field(..., description="Availability status")
    number_of_reviews: int = Field(default=0, description="Number of reviews")
    image_url: HttpUrl = Field(..., description="Image URL of the book cover")
    rating: Optional[str] = Field(
        default=None, description="Rating of the book (e.g., 'Five', 'Four')"
    )
    source_url: HttpUrl = Field(..., description="Source URL of the book page")
    crawl_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Crawl timestamp",
    )
    status: str = Field(default="active", description="Book status")
    content_hash: Optional[str] = Field(
        default=None, description="Content hash for change detection"
    )
    raw_html: Optional[str] = Field(default=None, description="Raw HTML snapshot")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "A Light in the Attic",
                "description": "It's hard to imagine a world without A Light in the Attic...",
                "category": "Poetry",
                "price_including_tax": 51.77,
                "price_excluding_tax": 51.77,
                "availability": "In stock (22 available)",
                "number_of_reviews": 51,
                "image_url": "http://books.toscrape.com/media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg",
                "rating": "Three",
                "source_url": "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
                "crawl_timestamp": "2024-01-01T00:00:00",
                "status": "active",
            }
        }
    )


class BookMetadata(BaseModel):
    """Crawl metadata for tracking."""

    source_url: HttpUrl
    crawl_timestamp: datetime
    status: str = "success"
    error_message: Optional[str] = None
    retry_count: int = 0
