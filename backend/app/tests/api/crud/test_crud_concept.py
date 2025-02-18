import pytest
from odmantic import AIOEngine

from app.crud import concept as crud_concept
from app.crud import link as crud_link
from app.schemas.concept import ConceptCreate, ConceptUpdate
from app.schemas.link import LinkCreate


@pytest.mark.asyncio
async def test_create_concept(engine: AIOEngine) -> None:
    concept_in = ConceptCreate(
        name="concept",
        comment="comment",
        annotation_ids=["annotation_id"],
    )
    concept = await crud_concept.create(engine, obj_in=concept_in)
    assert concept.name == concept_in.name
    assert concept.comment == concept_in.comment
    assert concept.annotation_ids == concept_in.annotation_ids
    assert concept.linked_concept_ids == []


@pytest.mark.asyncio
async def test_update_concept(engine: AIOEngine) -> None:
    concept_in = ConceptCreate(
        name="concept",
        comment="comment",
        annotation_ids=["annotation_id_1"],
    )
    concept = await crud_concept.create(engine, obj_in=concept_in)

    concept_in_update = ConceptUpdate(
        id=concept.id,
        name="concept updated",
        comment="comment updated",
        annotation_ids=["annotation_id_1", "annotation_id_2"],
    )
    concept_updated = await crud_concept.update(
        engine, db_obj=concept, obj_in=concept_in_update
    )
    assert concept.id == concept_updated.id
    assert concept_in_update.name == concept_updated.name
    assert concept_in_update.comment == concept_updated.comment
    assert concept_in_update.annotation_ids == concept_updated.annotation_ids
    assert concept_updated.linked_concept_ids == []


@pytest.mark.asyncio
async def test_remove_concept(engine: AIOEngine) -> None:
    concept_in_1 = ConceptCreate(
        name="concept_1",
        comment="comment_1",
        annotation_ids=["annotation_id_1"],
    )
    concept_1 = await crud_concept.create(engine, obj_in=concept_in_1)
    concept_in_2 = ConceptCreate(
        name="concept_2",
        comment="comment_2",
        annotation_ids=["annotation_id_2"],
    )
    concept_2 = await crud_concept.create(engine, obj_in=concept_in_2)
    link_in = LinkCreate(concept_ids=[concept_1.id, concept_2.id])
    link = await crud_link.create(engine, obj_in=link_in)

    await crud_concept.delete(engine, id=concept_1.id)

    # Check if the link is removed
    link = await crud_link.get(engine, link.id)
    assert link is None

    # Check if the concept is removed
    concept_1 = await crud_concept.get(engine, id=concept_1.id)
    assert concept_1 is None
