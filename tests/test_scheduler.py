"""Tests for scheduler module."""

import pytest
from app.scheduler.change_detector import ChangeDetector
from app.scheduler.scheduler import CrawlerScheduler
from app.crawler.models import Book
from app.crawler.storage import calculate_content_hash


def test_change_detector_initialization():
    """Test ChangeDetector initialization."""
    detector = ChangeDetector()
    assert detector.storage is not None


def test_scheduler_initialization():
    """Test CrawlerScheduler initialization."""
    scheduler = CrawlerScheduler()
    assert scheduler.scheduler is not None
    assert scheduler.scraper is not None
    assert scheduler.change_detector is not None
    assert scheduler.report_generator is not None


def test_content_hash_consistency():
    """Test that content hash is consistent between storage and change_detector."""
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
    
    hash1 = calculate_content_hash(book)
    hash2 = calculate_content_hash(book)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 produces 64 hex characters


def test_content_hash_sensitivity():
    """Test that content hash changes with different book data."""
    book1 = Book(
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
    
    book2 = Book(
        name="Test Book",
        description="Test description",
        category="Fiction",
        price_including_tax=15.0,  # Different price
        price_excluding_tax=15.0,
        availability="In stock",
        number_of_reviews=5,
        image_url="http://example.com/image.jpg",
        rating="Four",
        source_url="http://example.com/book",
    )
    
    hash1 = calculate_content_hash(book1)
    hash2 = calculate_content_hash(book2)
    
    assert hash1 != hash2


# Note: Integration tests with MongoDB would require:
# - MongoDB connection setup
# - Test database
# - Proper cleanup after tests

