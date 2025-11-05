"""Tests for crawler module."""

import pytest
from app.crawler.models import Book
from app.crawler.storage import calculate_content_hash


def test_book_model():
    """Test Book Pydantic model."""
    book = Book(
        name="Test Book",
        description="Test description",
        category="Fiction",
        price_including_tax=10.0,
        price_excluding_tax=10.0,
        availability="In stock",
        number_of_reviews=5,
        image_url="http://example.com/image.jpg",
        rating="Four",
        source_url="http://example.com/book",
    )
    
    assert book.name == "Test Book"
    assert book.price_including_tax == 10.0
    assert book.rating == "Four"


def test_content_hash():
    """Test content hash calculation."""
    book1 = Book(
        name="Test Book",
        description="Test",
        category="Fiction",
        price_including_tax=10.0,
        price_excluding_tax=10.0,
        availability="In stock",
        number_of_reviews=5,
        image_url="http://example.com/image.jpg",
        rating="Four",
        source_url="http://example.com/book",
    )
    
    book2 = Book(
        name="Test Book",
        description="Test",
        category="Fiction",
        price_including_tax=10.0,
        price_excluding_tax=10.0,
        availability="In stock",
        number_of_reviews=5,
        image_url="http://example.com/image.jpg",
        rating="Four",
        source_url="http://example.com/book",
    )
    
    hash1 = calculate_content_hash(book1)
    hash2 = calculate_content_hash(book2)
    
    assert hash1 == hash2
    
    # Change price
    book2.price_including_tax = 15.0
    hash3 = calculate_content_hash(book2)
    
    assert hash1 != hash3

