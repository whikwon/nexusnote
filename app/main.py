from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.api.routes.test import router as TestRouter
from app.core.config import settings
from app.core.db import init_db
from app.core.embeddings import init_embeddings
from app.core.llm import init_llm
from app.core.vector_store import init_vector_store


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


async def lifespan(app: FastAPI):
    db = await init_db()
    lance_db_conn = db["lance_db_conn"]
    mongo_db_client = db["mongo_db_client"]

    embeddings = init_embeddings()
    llm = init_llm()
    vector_store = init_vector_store(
        connection=lance_db_conn,
        embeddings=embeddings,
        table_name=settings.LANCE_TABLE_NAME,
    )

    app.state.lance_db_conn = lance_db_conn
    app.state.mongo_db_client = mongo_db_client
    app.state.embeddings = embeddings
    app.state.llm = llm
    app.state.vector_store = vector_store
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)


# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(api_router, prefix=settings.API_V1_STR)
