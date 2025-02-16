from app.core.config import settings
from app.rag.embeddings.registry import create_embedding_model


class _EmbeddingsSingleton:
    _instance = None
    embeddings = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(_EmbeddingsSingleton, cls).__new__(cls)
            cls._instance.embeddings = create_embedding_model(
                settings.EMBEDDINGS_MODEL_KEY, **settings.EMBEDDINGS_KWARGS
            )
        return cls._instance


def get_embeddings():
    return _EmbeddingsSingleton().embeddings


def init_embeddings():
    _EmbeddingsSingleton()
