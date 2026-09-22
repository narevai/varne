from datetime import UTC, datetime
from functools import partial

import httpx2 as httpx
import pytest
from tests.sanitize import sanitize_response
from tests.unit.providers.vercel.test_client_projects import policy_vercel_projects

from varne.config import SourceId, SourceType, StackId, VercelToken
from varne.providers.types import RowDimSourceMeta, RowRaw
from varne.providers.vercel.client import VercelClient
from varne.providers.vercel.transform import transform_meta


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
def test_transform_meta(
    http_client: httpx.Client,
    vercel_token: VercelToken,
    vercel_project_id: str,
    vercel_team_id: str,
):
    stack_id: StackId = "stack_test"
    source_id: SourceId = "source_test"
    source_type = SourceType.VERCEL

    client = VercelClient(http_client, api_token=vercel_token)

    response: httpx.Response = client.fetch_projects()

    row_raw = RowRaw(
        stack_id=stack_id,
        source_id=source_id,
        source_type=source_type,
        extracted_at=datetime.now(UTC),
        method=response.request.method,
        url=str(response.request.url),
        payload=response.text,
    )

    rows = transform_meta(row_raw)

    assert len(rows) == 3
    assert all(isinstance(row, RowDimSourceMeta) for row in rows)

    row_id = next(x for x in rows if x.value_name == "id")

    assert row_id.stack_id == stack_id
    assert row_id.source_id == source_id
    assert row_id.value == vercel_project_id

    row_name = next(x for x in rows if x.value_name == "name")
    assert row_name.value == "<name>"

    row_account_id = next(x for x in rows if x.value_name == "account_id")
    assert row_account_id.value == vercel_team_id
