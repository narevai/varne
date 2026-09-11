from datetime import UTC, datetime
from functools import partial

import httpx2 as httpx
import pytest
from tests.policy import FieldPolicy, SanitizePolicy
from tests.sanitize import sanitize_response

from varne.config import VercelToken
from varne.providers.vercel.client import VercelClient

policy_vercel_billing = SanitizePolicy(
    root=FieldPolicy(
        match_field="Tags.ProjectId",
        match_value="prj_5LAip7eW0S0iDBoLNDwa9gMTye78",
        limit=10,
        keep=(
            "ChargePeriodStart",
            "ChargePeriodEnd",
            "ChargeCategory",
            "BilledCost",
            "BillingCurrency",
            "EffectiveCost",
            "ServiceName",
            "ServiceCategory",
            "ServiceProviderName",
            "ConsumedQuantity",
            "ConsumedUnit",
            "PricingCategory",
            "PricingCurrency",
            "PricingQuantity",
            "PricingUnit",
        ),
    ),
    fields=(
        FieldPolicy(
            field="Tags",
            keep=("ProjectId",),
        ),
    ),
)


@pytest.fixture
def vcr_config():
    return {
        "decode_compressed_response": True,
        "filter_headers": ["authorization"],
        "before_record_response": partial(
            sanitize_response, policy=policy_vercel_billing
        ),
    }


@pytest.mark.vcr
def test_fetch_billing(
    http_client: httpx.Client, vercel_token: VercelToken, vercel_team_id: str
):
    client = VercelClient(http_client, api_token=vercel_token)

    billing = client.fetch_billing(
        team_id=vercel_team_id,
        date_from=datetime(2026, 9, 1, tzinfo=UTC),
        date_to=datetime(2026, 9, 10, tzinfo=UTC),
    )

    assert len(billing) > 0
