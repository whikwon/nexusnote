from fastapi.testclient import TestClient

from app.core.config import settings
from app.schemas.request import UploadDocumentRequest

# def test_upload_document(client: TestClient) -> None:
#     request = UploadDocumentRequest(file_name="test.pdf", content="dGVzdA==")
#     res = client.post(
#         f"{settings.API_V1_STR}/document/upload", data=request.model_dump()
#     )
#     assert res.status_code == 200
