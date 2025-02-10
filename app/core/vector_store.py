from langchain_community.vectorstores import LanceDB

from app.core.config import settings


def init_vector_store(connection, embeddings, table_name):
    return LanceDB(connection, embeddings, settings.LANCE_URI, table_name=table_name)
