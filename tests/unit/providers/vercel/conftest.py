from functools import partial

import pytest
from tests.sanitize import sanitize_response
from tests.unit.providers.vercel.policy import vercel_policy


@pytest.fixture
def vcr_config():
    return {
        "decode_compressed_response": True,
        "filter_headers": ["authorization"],
        "before_record_response": partial(sanitize_response, policy=vercel_policy),
    }
