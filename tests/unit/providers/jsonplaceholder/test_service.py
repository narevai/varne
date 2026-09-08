import httpx2 as httpx
import pytest

from varne.config import SourceId, StackId
from varne.db.types import DatabaseBackend
from varne.providers.jsonplaceholder.client import JsonPlaceholderClient
from varne.providers.jsonplaceholder.service import JsonPlaceholderService


@pytest.mark.vcr
def test_store(db: DatabaseBackend, http_client: httpx.Client):
    stack_id: StackId = "stack_test"
    source_id: SourceId = "source_test"
    client = JsonPlaceholderClient(http_client)
    service = JsonPlaceholderService(
        db=db, client=client, stack_id=stack_id, source_id=source_id
    )

    service.fetch_and_store()

    raw_count = db.table("raw").count().execute()
    staging_count = db.table("staging").count().execute()

    assert raw_count == 1
    assert staging_count == 100
