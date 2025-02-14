from typing import Generator

from app.db.session import MongoDatabase


def get_db() -> Generator:
    try:
        db = MongoDatabase()
        yield db
    finally:
        pass
