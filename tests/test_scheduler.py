"""Tests for scheduler module."""

import pytest
from app.scheduler.change_detector import ChangeDetector
from app.crawler.models import Book


def test_change_detector_initialization():
    """Test ChangeDetector initialization."""
    detector = ChangeDetector()
    assert detector.storage is not None


# Note: More comprehensive tests would require MongoDB connection
# These are basic unit tests

