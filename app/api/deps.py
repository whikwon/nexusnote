from typing import Generator

from app.core.db import get_mongodb_client, get_mongodb_engine
from app.core.llm import get_llm
from app.core.vector_store import get_vector_store


def get_db() -> Generator:
    try:
        db = get_mongodb_client()
        yield db
    finally:
        pass


def get_engine() -> Generator:
    try:
        engine = get_mongodb_engine()
        yield engine
    finally:
        pass


def get_vector_store() -> Generator:
    try:
        vector_store = get_vector_store()
        yield vector_store
    finally:
        pass


def get_llm() -> Generator:
    try:
        llm = get_llm()
        yield llm
    finally:
        pass
