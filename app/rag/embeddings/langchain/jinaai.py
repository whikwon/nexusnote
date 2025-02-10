"""
https://huggingface.co/jinaai/jina-clip-v2/blob/main/README.md
https://python.langchain.com/docs/how_to/custom_embeddings/
"""

from typing import List

from langchain_core.embeddings import Embeddings
from transformers import AutoModel


class JinaClipV2Embeddings(Embeddings):
    def __init__(self):
        self.model = AutoModel.from_pretrained(
            "jinaai/jina-clip-v2", trust_remote_code=True
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.model.encode_text(txt) for txt in texts]

    def embed_query(self, text: str):
        return self.embed_documents([text])[0]
