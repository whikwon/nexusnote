import lancedb
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

import app.models as models
from app.core.config import settings


async def init_mongo_db():
    client = AsyncIOMotorClient(str(settings.MONGO_URI))
    all_models = [getattr(models, model) for model in models.__all__]
    await init_beanie(
        database=client.get_database(settings.MONGO_DB), document_models=all_models
    )
    return client


def init_lance_db():
    lance_db_conn = lancedb.connect(settings.LANCE_URI)
    return lance_db_conn


async def init_db():
    mongo_client = await init_mongo_db()
    lance_db_conn = init_lance_db()
    return {"mongo_db_client": mongo_client, "lance_db_conn": lance_db_conn}
