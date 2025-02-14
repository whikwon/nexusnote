import pytest
from odmantic import AIOEngine

from app import crud
from app.models.annotation import Annotation
from app.schemas.annotation import AnnotationCreate, AnnotationUpdate


@pytest.mark.asyncio
async def test_create_annotation(engine: AIOEngine) -> None:
    obj_in = AnnotationCreate(file_id="file_id", page_number=1, comment="comment")
    annotation = await crud.annotation.create(engine, obj_in=obj_in)
    assert annotation.file_id == obj_in.file_id
    assert annotation.page_number == obj_in.page_number
    assert annotation.comment == obj_in.comment


@pytest.mark.asyncio
async def test_update_annotation(engine: AIOEngine) -> None:
    db_obj = Annotation(file_id="file_id", page_number=1, comment="comment")
    obj_in = AnnotationUpdate(
        comment="comment updated",
    )
    annotation = await crud.annotation.update(engine, db_obj=db_obj, obj_in=obj_in)
    assert annotation.file_id == db_obj.file_id
    assert annotation.page_number == db_obj.page_number
    assert annotation.comment == obj_in.comment
