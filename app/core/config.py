import secrets
from typing import Annotated, Any, Literal, Type

from langchain_ollama import OllamaLLM
from pydantic import AnyUrl, BeforeValidator, HttpUrl, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.rag.embeddings.langchain import JinaClipV2Embeddings


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = (
        []
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str = "NexusNote"
    MONGO_SERVER: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_DB: str = "pdf_contents"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def MONGO_URI(self) -> HttpUrl:
        return MultiHostUrl.build(
            scheme="mongodb",
            host=self.MONGO_SERVER,
            port=self.MONGO_PORT,
        )

    LANCE_URI: str = "db/lancedb"
    LANCE_TABLE_NAME: str = "vectorstore"

    EMBEDDINGS_CLS: Type[JinaClipV2Embeddings] = JinaClipV2Embeddings
    EMBEDDINGS_KWARGS: dict[str, Any] = {}

    LLM_CLS: Type[Any] = OllamaLLM
    LLM_KWARGS: dict[str, Any] = {"model": "llama3.2"}

    DOCUMENT_DIR_PATH: str = "./data/documents"


settings = Settings()  # type: ignore
