"""Generate daily change reports."""

import csv
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Optional

from app.database.mongodb import MongoDB
from app.utils.logger import setup_logger

logger = setup_logger("reports")


class ReportGenerator:
    """Generate daily change reports."""

    async def generate_daily_report(
        self,
        date: Optional[datetime] = None,
        output_format: str = "json",
        output_dir: str = "reports",
    ) -> str:
        """Generate daily change report.

        Args:
            date: Date for report (defaults to yesterday)
            output_format: 'json' or 'csv'
            output_dir: Output directory

        Returns:
            Path to generated report file
        """
        if date is None:
            date = datetime.now(UTC) - timedelta(days=1)

        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)

        try:
            db = MongoDB.get_database()
            change_log_collection = db["change_log"]

            # Query changes for the date
            changes = []
            async for change in change_log_collection.find(
                {
                    "timestamp": {"$gte": start_date, "$lt": end_date},
                }
            ).sort("timestamp", 1):
                # Convert ObjectId to string for JSON serialization
                change["book_id"] = str(change["book_id"])
                change["timestamp"] = change["timestamp"].isoformat()
                changes.append(change)

            # Generate summary
            summary = {
                "date": start_date.isoformat(),
                "total_changes": len(changes),
                "new_books": sum(1 for c in changes if c["change_type"] == "new_book"),
                "price_changes": sum(1 for c in changes if c["change_type"] == "price"),
                "availability_changes": sum(
                    1 for c in changes if c["change_type"] == "availability"
                ),
                "other_changes": sum(
                    1
                    for c in changes
                    if c["change_type"] not in ["new_book", "price", "availability"]
                ),
            }

            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Generate report file
            date_str = start_date.strftime("%Y-%m-%d")
            if output_format == "json":
                report_data = {
                    "summary": summary,
                    "changes": changes,
                }
                report_file = output_path / f"changes_report_{date_str}.json"
                with open(report_file, "w", encoding="utf-8") as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
            else:  # CSV
                report_file = output_path / f"changes_report_{date_str}.csv"
                with open(report_file, "w", newline="", encoding="utf-8") as f:
                    if changes:
                        writer = csv.DictWriter(f, fieldnames=changes[0].keys())
                        writer.writeheader()
                        writer.writerows(changes)
                    else:
                        # Write summary row
                        writer = csv.writer(f)
                        writer.writerow(["No changes found"])

            logger.info(f"Generated {output_format.upper()} report: {report_file}")
            return str(report_file)

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise
