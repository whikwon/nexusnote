from fastapi import APIRouter

from app.models import Annotation
from app.schemas.request import (
    CreateAnnotationRequest,
    DeleteAnnotationRequest,
    UpdateAnnotationRequest,
)

router = APIRouter(prefix="/annotation", tags=["annotation"])


@router.post("/create")
async def create_annotation(payload: CreateAnnotationRequest):
    # return annotation_id
    pass


@router.post("/delete")
async def delete_annotation(payload: DeleteAnnotationRequest):
    pass


@router.post("/update")
async def update_annotation(payload: UpdateAnnotationRequest):
    pass
