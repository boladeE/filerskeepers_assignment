"""Script to create API keys."""

import asyncio

from app.api.auth import create_api_key
from app.database.mongodb import MongoDB
from app.database.schemas import create_indexes
from app.utils.logger import setup_logger

logger = setup_logger("api_key_creator")


async def main():
    """Create an API key."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python create_api_key.py <key_name> [description]")
        sys.exit(1)
    
    name = sys.argv[1]
    description = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        await MongoDB.connect()
        await create_indexes()
        
        api_key = await create_api_key(name=name, description=description)
        
        print(f"\nAPI Key created successfully!")
        print(f"Name: {name}")
        if description:
            print(f"Description: {description}")
        print(f"API Key: {api_key}")
        print(f"\nUse this header in API requests:")
        print(f"X-API-Key: {api_key}\n")
        
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await MongoDB.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

