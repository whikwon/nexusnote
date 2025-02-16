from typing import Any

from fastapi import APIRouter, Body, Depends
from odmantic import AIOEngine

from app import schemas
from app.api import deps
from app.crud import annotation as crud_annotation

router = APIRouter(prefix="/annotation", tags=["annotation"])


@router.post("/create", response_model=schemas.AnnotationBase)
async def create_annotation(
    *,
    engine: AIOEngine = Depends(deps.engine_generator),
    annotation_in: schemas.AnnotationCreate,
) -> Any:
    annotation = await crud_annotation.create(engine, obj_in=annotation_in)
    return annotation


@router.post("/delete", response_model=schemas.Msg)
async def delete_annotation(
    *,
    engine: AIOEngine = Depends(deps.engine_generator),
    id: str = Body(..., embed=True),
) -> Any:
    await crud_annotation.delete(engine, id)
    return {"msg": "Annotation deleted successfully."}


@router.post("/update", response_model=schemas.AnnotationBase)
async def update_annotation(
    *,
    engine: AIOEngine = Depends(deps.engine_generator),
    annotation_in: schemas.AnnotationUpdate,
) -> Any:
    db_obj = await crud_annotation.get(engine, annotation_in.id)
    annotation = await crud_annotation.update(
        engine, db_obj=db_obj, obj_in=annotation_in
    )
    return annotation
