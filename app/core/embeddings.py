from app.core.config import settings
from app.rag.embeddings.registry import create_embedding_model


def init_embeddings():
    return create_embedding_model(
        settings.EMBEDDINGS_MODEL_KEY, **settings.EMBEDDINGS_KWARGS
    )
