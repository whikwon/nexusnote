from fastapi import APIRouter

from app.models import Link
from app.schemas.request import CreateConceptLinkRequest, DeleteConceptLinkRequest

router = APIRouter(prefix="/link", tags=["link"])


@router.post("/create")
async def create_concept_link(payload: CreateConceptLinkRequest):
    # return concept_link_id
    pass


@router.post("/delete")
async def delete_concept_link(payload: DeleteConceptLinkRequest):
    pass
