from fastapi import APIRouter

from app.api.routes import document

api_router = APIRouter()
api_router.include_router(document.router)
