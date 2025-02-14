import asyncio
from typing import Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import MongoDatabase, _MongoClientSingleton, get_engine
from app.main import app

TEST_DATABASE = "test"
settings.MONGO_DATABASE = TEST_DATABASE


@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db() -> Generator:
    db = MongoDatabase()
    _MongoClientSingleton.instance.mongo_client.get_io_loop = asyncio.get_event_loop
    await init_db(db)
    yield db


@pytest_asyncio.fixture(scope="session")
async def engine() -> Generator:
    yield get_engine()  # This will now use the TEST_DATABASE name


@pytest.fixture(scope="session")
def client(db) -> Generator:
    with TestClient(app) as c:
        yield c
