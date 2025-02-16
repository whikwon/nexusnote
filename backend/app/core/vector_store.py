
from langchain_community.vectorstores import LanceDB

import lancedb
from app.core.config import settings
from lancedb.db import DBConnection


class _VectorStoreSingleton:
    _instance = None
    connection = DBConnection | None
    vector_store = LanceDB | None

    def __new__(cls, embeddings=None, table_name=None):
        if cls._instance is None:
            if embeddings is None or table_name is None:
                raise ValueError(
                    "Please provide both embeddings and table_name for initialization."
                )

            cls._instance = super(_VectorStoreSingleton, cls).__new__(cls)
            connection = lancedb.connect(settings.LANCE_URI)
            cls._instance.connection = connection
            cls._instance.vector_store = LanceDB(
                connection,
                embeddings,
                settings.LANCE_URI,
                table_name=table_name,
            )
        return cls._instance


def get_lancedb_vector_store() -> LanceDB:
    return _VectorStoreSingleton().vector_store


def init_vector_store(embeddings, table_name: str) -> None:
    """
    Initialize the vector store singleton.
    """
    _VectorStoreSingleton(embeddings, table_name)
