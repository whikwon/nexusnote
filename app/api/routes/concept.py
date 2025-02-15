from typing import Any

from fastapi import APIRouter, Body, Depends
from odmantic import AIOEngine

from app import schemas
from app.api import deps
from app.crud import concept as crud_concept
from app.models import Concept

router = APIRouter(prefix="/concept", tags=["concept"])


@router.post("/create", response_model=schemas.ConceptBase)
async def create_concept(
    *, engine: AIOEngine = Depends(deps.get_engine), concept_in: schemas.ConceptCreate
) -> Any:
    concept = await crud_concept.create(engine, obj_in=concept_in)
    return concept


@router.post("/delete", response_model=schemas.Msg)
async def delete_concept(
    *, engine: AIOEngine = Depends(deps.get_engine), id: str = Body(..., embed=True)
) -> Any:
    await crud_concept.delete(engine, id)
    return {"msg": "Concept deleted"}


@router.post("/update", response_model=schemas.ConceptBase)
async def update_concept(
    *, engine: AIOEngine = Depends(deps.get_engine), concept_in: schemas.ConceptUpdate
) -> Any:
    concept = await crud_concept.update(engine, obj_in=concept_in)
    return concept
