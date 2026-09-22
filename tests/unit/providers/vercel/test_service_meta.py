from functools import partial

import httpx2 as httpx
import pytest
from tests.sanitize import sanitize_response
from tests.unit.providers.vercel.test_client_projects import policy_vercel_projects

from varne.config import SourceId, SourceType, StackId, VercelToken
from varne.db.schema import TableName
from varne.db.types import DatabaseBackend
from varne.providers.vercel.client import VercelClient
from varne.providers.vercel.service import VercelService


@pytest.fixture
def vcr_config():
    return {
        "decode_compressed_response": True,
        "filter_headers": ["authorization"],
        "before_record_response": partial(
            sanitize_response, policy=policy_vercel_projects
        ),
    }

@pytest.mark.default_cassette("projects.yaml")
@pytest.mark.vcr
def test_fetch_source_meta(
    db: DatabaseBackend, http_client: httpx.Client, vercel_token: VercelToken
):
    stack_id: StackId = "stack_test"
    source_id: SourceId = "source_test"
    client = VercelClient(http_client, api_token=vercel_token)
    service = VercelService(
        db=db, client=client, stack_id=stack_id, source_id=source_id
    )

    assert service.provider == "vercel"
    assert service.provider == SourceType.VERCEL

    service.fetch_source_meta()

    raw_count = db.table(TableName.RAW).count().execute()
    staging_count = db.table(TableName.DIM_SOURCE_META).count().execute()

    assert raw_count == 1
    assert staging_count == 3
