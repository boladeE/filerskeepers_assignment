"""Indexes handled by Beanie model Settings; no manual index creation needed."""

from app.utils.logger import setup_logger

logger = setup_logger("database")


async def create_indexes() -> None:
    """Beanie defines indexes via Document Settings. No action required."""
    logger.info(
        "Beanie models manage indexes via Settings; skipping manual index creation"
    )
