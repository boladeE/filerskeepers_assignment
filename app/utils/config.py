"""Configuration management using environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # MongoDB Configuration
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "books_crawler"

    # API Configuration
    api_secret_key: str = "your-secret-key-change-in-production"
    api_rate_limit_per_hour: int = 100

    # Crawler Configuration
    base_url: str = "https://books.toscrape.com"
    max_retries: int = 3
    retry_delay: float = 1.0
    request_timeout: float = 30.0
    max_concurrent_requests: int = 10

    # Scheduler Configuration
    scheduler_timezone: str = "UTC"
    scheduler_daily_hour: int = 2  # Run at 2 AM

    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "crawler.log"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
