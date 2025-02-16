import pytest
from odmantic import AIOEngine

from app.crud import annotation as crud_annotation
from app.schemas.annotation import AnnotationCreate, AnnotationUpdate


@pytest.mark.asyncio
async def test_create_annotation(engine: AIOEngine) -> None:
    annotation_in = AnnotationCreate(
        file_id="file_id", page_number=1, comment="comment"
    )
    annotation = await crud_annotation.create(engine, obj_in=annotation_in)
    assert annotation.file_id == annotation_in.file_id
    assert annotation.page_number == annotation_in.page_number
    assert annotation.comment == annotation_in.comment


@pytest.mark.asyncio
async def test_update_annotation(engine: AIOEngine) -> None:
    annotation_in = AnnotationCreate(
        file_id="file_id", page_number=1, comment="comment"
    )
    annotation = await crud_annotation.create(engine, obj_in=annotation_in)

    annotation_in_update = AnnotationUpdate(
        id=annotation.id,
        comment="comment updated",
    )
    annotation_updated = await crud_annotation.update(
        engine, db_obj=annotation, obj_in=annotation_in_update
    )
    assert annotation.file_id == annotation_updated.file_id
    assert annotation.page_number == annotation_updated.page_number
    assert annotation_in_update.comment == annotation_updated.comment
