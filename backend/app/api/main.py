from fastapi import APIRouter

from app.api.routes import annotation, concept, document, link

api_router = APIRouter()
api_router.include_router(document.router)
api_router.include_router(concept.router)
api_router.include_router(annotation.router)
api_router.include_router(link.router)
