import pytest
from fastapi.testclient import TestClient
from odmantic import AIOEngine

from app.core.config import settings
from app.crud import concept as crud_concept
from app.crud import link as crud_link
from app.schemas.concept import ConceptCreate
from app.schemas.link import LinkCreate


@pytest.mark.asyncio
async def test_create_concept(client: TestClient):
    res = client.post(
        f"{settings.API_V1_STR}/concept/create",
        json={
            "name": "concept",
            "comment": "comment",
            "annotation_ids": ["annotation_id_1"],
        },
    )
    assert res.status_code == 200
    concept = res.json()
    assert "id" in concept
    assert concept["name"] == "concept"
    assert concept["comment"] == "comment"
    assert concept["annotation_ids"] == ["annotation_id_1"]


@pytest.mark.asyncio
async def test_update_concept(engine: AIOEngine, client: TestClient):
    concept = await crud_concept.create(
        engine,
        obj_in=ConceptCreate(
            name="concept",
            comment="comment",
            annotation_ids=["annotation_id_1"],
        ),
    )

    res = client.post(
        f"{settings.API_V1_STR}/concept/update",
        json={
            "id": concept.id,
            "name": "concept updated",
            "comment": "comment updated",
            "annotation_ids": ["annotation_id_1", "annotation_id_2"],
        },
    )
    assert res.status_code == 200
    concept_updated = res.json()
    assert concept_updated["id"] == concept.id
    assert concept_updated["name"] == "concept updated"
    assert concept_updated["comment"] == "comment updated"
    assert concept_updated["annotation_ids"] == ["annotation_id_1", "annotation_id_2"]
    assert concept_updated["linked_concept_ids"] == []


@pytest.mark.asyncio
async def test_delete_concept(engine: AIOEngine, client: TestClient):
    concept_1 = await crud_concept.create(
        engine,
        obj_in=ConceptCreate(
            name="concept_1",
            comment="comment_1",
            annotation_ids=["annotation_id_1"],
        ),
    )
    concept_2 = await crud_concept.create(
        engine,
        obj_in=ConceptCreate(
            name="concept_2",
            comment="comment_2",
            annotation_ids=["annotation_id_2"],
        ),
    )
    link = await crud_link.create(
        engine, obj_in=LinkCreate(concept_ids=[concept_1.id, concept_2.id])
    )

    res = client.post(
        f"{settings.API_V1_STR}/concept/delete",
        json={"id": concept_1.id},
    )
    assert res.status_code == 200
    assert res.json()["msg"] == "Concept deleted successfully."
    assert await crud_link.get(engine, id=link.id) is None
