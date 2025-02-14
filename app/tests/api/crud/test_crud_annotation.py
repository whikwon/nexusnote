import pytest
from odmantic import AIOEngine

from app import crud
from app.schemas.annotation import AnnotationCreate, AnnotationUpdate


@pytest.mark.asyncio
async def test_create_annotation(engine: AIOEngine) -> None:
    annotation_in = AnnotationCreate(
        file_id="file_id", page_number=1, comment="comment"
    )
    annotation = await crud.annotation.create(engine, obj_in=annotation_in)
    assert annotation.file_id == annotation_in.file_id
    assert annotation.page_number == annotation_in.page_number
    assert annotation.comment == annotation_in.comment


@pytest.mark.asyncio
async def test_update_annotation(engine: AIOEngine) -> None:
    annotation_in = AnnotationCreate(
        file_id="file_id", page_number=1, comment="comment"
    )
    annotation = await crud.annotation.create(engine, obj_in=annotation_in)

    annotation_in_update = AnnotationUpdate(
        comment="comment updated",
    )
    annotation_2 = await crud.annotation.update(
        engine, db_obj=annotation, obj_in=annotation_in_update
    )
    assert annotation.file_id == annotation_2.file_id
    assert annotation.page_number == annotation_2.page_number
    assert annotation_in_update.comment == annotation_2.comment
