from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from .jina_clip import JinaClipV2Embeddings
from .registry import register_embedding_model

register_embedding_model("openai")(OpenAIEmbeddings)
register_embedding_model("ollama")(OllamaEmbeddings)

__all__ = ["JinaClipV2Embeddings", "OpenAIEmbeddings", "OllamaEmbeddings"]
