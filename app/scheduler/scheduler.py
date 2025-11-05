"""APScheduler setup for daily change detection."""

from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.crawler.scraper import BookScraper
from app.database.mongodb import MongoDB
from app.scheduler.change_detector import ChangeDetector
from app.scheduler.reports import ReportGenerator
from app.utils.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("scheduler")


class CrawlerScheduler:
    """Scheduler for daily change detection."""

    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
        self.scraper = BookScraper()
        self.change_detector = ChangeDetector()
        self.report_generator = ReportGenerator()

    async def run_change_detection(self) -> None:
        """Run daily change detection task."""
        logger.info("Starting daily change detection...")

        try:
            # Scrape all books
            # Change detection is integrated into the scraper via ChangeDetector
            # The scraper automatically detects and logs changes during scraping
            await self.scraper.crawl_all(resume=True)

            # Generate daily report
            try:
                report_file = await self.report_generator.generate_daily_report(
                    output_format="json",
                )
                logger.info(f"Daily report generated: {report_file}")
            except Exception as e:
                logger.error(f"Error generating report: {e}")

            # Check for significant changes and alert
            db = MongoDB.get_database()
            change_log_collection = db["change_log"]

            # Count changes in last 24 hours
            yesterday = datetime.now(UTC) - timedelta(days=1)
            change_count = await change_log_collection.count_documents(
                {
                    "timestamp": {"$gte": yesterday},
                }
            )

            if change_count > 0:
                logger.warning(
                    f"ALERT: {change_count} changes detected in the last 24 hours",
                )
            else:
                logger.info("No changes detected in the last 24 hours")

        except Exception as e:
            logger.error(f"Error in change detection task: {e}")
            raise

    def start(self) -> None:
        """Start the scheduler."""
        # Schedule daily task
        self.scheduler.add_job(
            self.run_change_detection,
            trigger=CronTrigger(
                hour=settings.scheduler_daily_hour,
                minute=0,
                timezone=settings.scheduler_timezone,
            ),
            id="daily_change_detection",
            name="Daily Change Detection",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info(
            f"Scheduler started. Daily task scheduled at {settings.scheduler_daily_hour}:00 {settings.scheduler_timezone}",
        )

    def stop(self) -> None:
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
