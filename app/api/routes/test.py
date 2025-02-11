
from fastapi import APIRouter

router = APIRouter(prefix="/test", tags=["test"])


@router.get("/", response_model=None)
def test_api() -> dict:
    """
    Retrieve items.
    """
    return {
        "items": [
            {"item_id": "Foo"},
            {"item_id": "Bar"},
        ]
    }
