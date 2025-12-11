import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MASTER_DB_NAME = os.getenv("MASTER_DB_NAME", "master_db")

client = AsyncIOMotorClient(MONGO_URL)
master_db = client[MASTER_DB_NAME]

# Utility getters for dependency injection

def get_master_db():
    return master_db

def get_client():
    return client


async def ensure_indexes():
    """Create essential indexes for master DB collections.

    - organizations.organization_name unique
    - admins.email unique
    """
    # organizations
    try:
        await master_db.organizations.create_index("organization_name", unique=True)
    except Exception:
        pass

    # admins
    try:
        await master_db.admins.create_index("email", unique=True)
    except Exception:
        pass
