"""MongoDB connection and Beanie initialization."""

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure

from app.database.models import ApiKeyDoc, BookDoc, ChangeLogDoc
from app.utils.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("database")


class MongoDB:
    """MongoDB client wrapper with Beanie initialization."""

    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None

    @classmethod
    async def connect(cls) -> None:
        """Connect to MongoDB and initialize Beanie."""
        try:
            cls.client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000,
            )
            # Test connection
            await cls.client.admin.command("ping")
            cls.database = cls.client[settings.mongodb_database]
            await init_beanie(
                database=cls.database,
                document_models=[BookDoc, ChangeLogDoc, ApiKeyDoc],
            )
            logger.info(
                f"Connected to MongoDB and initialized Beanie: {settings.mongodb_database}"
            )
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    async def disconnect(cls) -> None:
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB")

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if cls.database is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return cls.database
