from fastapi import APIRouter

from app.api.routes import test
from app.core.config import settings

api_router = APIRouter()

if settings.ENVIRONMENT == "local":
    api_router.include_router(test.router)
