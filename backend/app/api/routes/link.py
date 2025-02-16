from typing import Any

from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from app import schemas
from app.api import deps
from app.crud import link as crud_link

router = APIRouter(prefix="/link", tags=["link"])


@router.post("/create")
async def create_concept_link(
    *, engine: AIOEngine = Depends(deps.engine_generator), link_in: schemas.LinkCreate
) -> Any:
    link = await crud_link.create(engine, obj_in=link_in)
    return link


@router.post("/delete")
async def delete_concept_link():
    await crud_link.delete()
    return {"msg": "Link deleted"}
