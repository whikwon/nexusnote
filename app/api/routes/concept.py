from fastapi import APIRouter

from app.models import Concept
from app.schemas.request import (
    CreateConceptRequest,
    DeleteConceptRequest,
    UpdateConceptRequest,
)

router = APIRouter(prefix="/concept", tags=["concept"])


@router.post("/create")
async def create_concept(payload: CreateConceptRequest):
    # return concept_id
    pass


@router.post("/delete")
async def delete_concept(payload: DeleteConceptRequest):
    pass


@router.post("/update")
async def update_concept(payload: UpdateConceptRequest):
    pass
