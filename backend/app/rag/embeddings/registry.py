# A simple registry for embedding models
EMBEDDING_MODEL_REGISTRY: dict[str, type] = {}


def register_embedding_model(key: str):
    def decorator(cls):
        EMBEDDING_MODEL_REGISTRY[key] = cls
        return cls

    return decorator


def create_embedding_model(key: str, **kwargs):
    model_cls = EMBEDDING_MODEL_REGISTRY.get(key)
    if model_cls is None:
        raise ValueError(f"Embedding model with key '{key}' not found in registry.")
    return model_cls(**kwargs)
