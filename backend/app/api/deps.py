from typing import Generator

from app.core.db import get_mongodb_client, get_mongodb_engine
from app.core.llm import get_llm
from app.core.vector_store import get_lancedb_vector_store


def db_generator() -> Generator:
    try:
        db = get_mongodb_client()
        yield db
    finally:
        pass


def engine_generator() -> Generator:
    try:
        engine = get_mongodb_engine()
        yield engine
    finally:
        pass


def vector_store_generator() -> Generator:
    try:
        vector_store = get_lancedb_vector_store()
        yield vector_store
    finally:
        pass


def llm_generator() -> Generator:
    try:
        llm = get_llm()
        yield llm
    finally:
        pass
