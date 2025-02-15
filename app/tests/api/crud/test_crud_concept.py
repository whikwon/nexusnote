import pytest
from odmantic import AIOEngine

from app import crud
from app.models.concept import Concept
from app.schemas.concept import ConceptCreate, ConceptUpdate
from app.schemas.link import LinkCreate


@pytest.mark.asyncio
async def test_create_concept(engine: AIOEngine) -> None:
    concept_in = ConceptCreate(
        name="concept", comment="comment", annotation_ids=["annotation_id"]
    )
    concept = await crud.concept.create(engine, obj_in=concept_in)
    assert concept.name == concept_in.name
    assert concept.comment == concept_in.comment
    assert concept.annotation_ids == concept_in.annotation_ids


@pytest.mark.asyncio
async def test_update_concept(engine: AIOEngine) -> None:
    concept_in = ConceptCreate(
        name="concept", comment="comment", annotation_ids=["annotation_id_1"]
    )
    concept = await crud.concept.create(engine, obj_in=concept_in)

    concept_in_update = ConceptUpdate(
        name="concept updated",
        comment="comment updated",
        annotation_ids=["annotation_id_1", "annotation_id_2"],
    )
    concept_2 = await crud.concept.update(
        engine, db_obj=concept, obj_in=concept_in_update
    )
    assert concept.id == concept_2.id
    assert concept_in_update.name == concept_2.name
    assert concept_in_update.comment == concept_2.comment
    assert concept_in_update.annotation_ids == concept_2.annotation_ids


@pytest.mark.asyncio
async def test_remove_concept(engine: AIOEngine) -> None:
    concept_in_1 = ConceptCreate(
        name="concept_1", comment="comment_1", annotation_ids=["annotation_id_1"]
    )
    concept_1 = await crud.concept.create(engine, obj_in=concept_in_1)
    concept_in_2 = ConceptCreate(
        name="concept_2", comment="comment_2", annotation_ids=["annotation_id_2"]
    )
    concept_2 = await crud.concept.create(engine, obj_in=concept_in_2)
    link_in = LinkCreate(concept_ids=[concept_1.id, concept_2.id])
    link = await crud.link.create(engine, obj_in=link_in)

    await crud.concept.delete(engine, id=concept_1.id)

    # Check if the link is removed
    link = await crud.link.get(engine, link.id)
    assert link is None

    # Check if the concept is removed
    concept_1 = await crud.concept.get(engine, id=concept_1.id)
    assert concept_1 is None
