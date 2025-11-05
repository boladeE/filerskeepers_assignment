"""FastAPI application entry point."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.rate_limit import RateLimitMiddleware
from app.api.routes import auth as auth_routes
from app.api.routes import books, changes
from app.crawler.scraper import BookScraper
from app.database.mongodb import MongoDB
from app.database.schemas import create_indexes
from app.scheduler.scheduler import CrawlerScheduler
from app.utils.logger import setup_logger

logger = setup_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Starting application...")
    scheduler = None
    try:
        await MongoDB.connect()
        await create_indexes()
        
        # Start the scheduler for daily change detection
        try:
            scheduler = CrawlerScheduler()
            scheduler.start()
            logger.info("Scheduler started successfully")
        except Exception as scheduler_err:
            logger.error(f"Failed to start scheduler: {scheduler_err}")
        
        # Kick off initial crawl on startup (non-blocking)
        try:
            asyncio.create_task(BookScraper().crawl_all(resume=True))
            logger.info("Initial crawl started in background")
        except Exception as crawl_err:
            logger.error(f"Failed to start initial crawl: {crawl_err}")
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down application...")
    if scheduler:
        scheduler.stop()
    await MongoDB.disconnect()
    logger.info("Application shut down")


app = FastAPI(
    title="Books Crawler API",
    description="RESTful API for books.toscrape.com crawling and monitoring",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(books.router)
app.include_router(changes.router)
app.include_router(auth_routes.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "books-crawler-api"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Books Crawler API",
        "docs": "/docs",
        "version": "1.0.0",
    }
