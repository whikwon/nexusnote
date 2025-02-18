import pytest
from odmantic import AIOEngine

from app.crud import annotation as crud_annotation
from app.schemas.annotation import AnnotationCreate, AnnotationUpdate, HighlightArea


@pytest.mark.asyncio
async def test_create_annotation(engine: AIOEngine) -> None:
    highlight_area = HighlightArea(
        height=100, left=100, pageIndex=1, top=100, width=100
    )
    annotation_in = AnnotationCreate(
        file_id="file_id",
        comment="comment",
        quote="quote",
        highlight_areas=[highlight_area],
    )
    annotation = await crud_annotation.create(engine, obj_in=annotation_in)
    assert annotation.file_id == annotation_in.file_id
    assert annotation.comment == annotation_in.comment
    assert annotation.quote == annotation_in.quote
    assert len(annotation.highlight_areas) == 1
    assert annotation.highlight_areas[0].height == highlight_area.height
    assert annotation.highlight_areas[0].left == highlight_area.left
    assert annotation.highlight_areas[0].pageIndex == highlight_area.pageIndex
    assert annotation.highlight_areas[0].top == highlight_area.top
    assert annotation.highlight_areas[0].width == highlight_area.width


@pytest.mark.asyncio
async def test_update_annotation(engine: AIOEngine) -> None:
    highlight_area = HighlightArea(
        height=100, left=100, pageIndex=1, top=100, width=100
    )
    annotation_in = AnnotationCreate(
        file_id="file_id",
        comment="comment",
        quote="quote",
        highlight_areas=[highlight_area],
    )
    annotation = await crud_annotation.create(engine, obj_in=annotation_in)

    highlight_area_updated = HighlightArea(
        height=200, left=200, pageIndex=2, top=200, width=200
    )
    annotation_in_update = AnnotationUpdate(
        id=annotation.id,
        comment="comment updated",
        highlight_areas=[highlight_area_updated],
    )
    annotation_updated = await crud_annotation.update(
        engine, db_obj=annotation, obj_in=annotation_in_update
    )
    assert annotation.file_id == annotation_updated.file_id
    assert annotation.quote == annotation_updated.quote
    assert annotation_in_update.comment == annotation_updated.comment
    assert len(annotation_updated.highlight_areas) == 1
    assert annotation_updated.highlight_areas[0].height == highlight_area_updated.height
    assert annotation_updated.highlight_areas[0].left == highlight_area_updated.left
    assert (
        annotation_updated.highlight_areas[0].pageIndex
        == highlight_area_updated.pageIndex
    )
    assert annotation_updated.highlight_areas[0].top == highlight_area_updated.top
    assert annotation_updated.highlight_areas[0].width == highlight_area_updated.width
