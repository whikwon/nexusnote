from motor import core, motor_asyncio
from odmantic import AIOEngine
from pymongo.driver_info import DriverInfo

from app.__version__ import __version__
from app.core.config import settings

DRIVER_INFO = DriverInfo(name="nexusnote", version=__version__)


class _MongoClientSingleton:
    _instance = None
    mongo_client: motor_asyncio.AsyncIOMotorClient | None
    engine: AIOEngine | None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(_MongoClientSingleton, cls).__new__(cls)
            cls._instance.mongo_client = motor_asyncio.AsyncIOMotorClient(
                settings.MONGO_DATABASE_URI, driver=DRIVER_INFO
            )
            cls._instance.engine = AIOEngine(
                client=cls._instance.mongo_client, database=settings.MONGO_DATABASE
            )
        return cls._instance

    def get_engine(self):
        # Create engine on demand with current database setting
        if not self.engine or self.engine.database_name != settings.MONGO_DATABASE:
            self.engine = AIOEngine(
                client=self.mongo_client, database=settings.MONGO_DATABASE
            )
        return self.engine


def get_mongodb_client() -> core.AgnosticDatabase:
    return _MongoClientSingleton().mongo_client[settings.MONGO_DATABASE]


def get_mongodb_engine() -> AIOEngine:
    return _MongoClientSingleton().get_engine()


async def ping():
    await get_mongodb_client().command("ping")


async def init_db():
    _MongoClientSingleton()
