from app.core.config import settings


def init_embeddings():
    return settings.EMBEDDINGS_CLS()
