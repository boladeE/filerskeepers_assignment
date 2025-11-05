"""Standalone script to run the crawler."""

import asyncio

from app.crawler.scraper import BookScraper
from app.database.mongodb import MongoDB
from app.database.schemas import create_indexes
from app.utils.logger import setup_logger

logger = setup_logger("crawler_script")


async def main():
    """Run the crawler."""
    try:
        # Connect to MongoDB
        await MongoDB.connect()
        await create_indexes()
        
        # Run crawler
        scraper = BookScraper()
        await scraper.crawl_all(resume=True)
        
        logger.info("Crawler completed successfully")
        
    except Exception as e:
        logger.error(f"Crawler failed: {e}")
        raise
    finally:
        await MongoDB.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

