import itertools
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from functools import partial
from typing import cast

import httpx2 as httpx
import pandas as pd
import pytest
from tests.sanitize import sanitize_response
from tests.unit.providers.vercel.conftest import VERCEL_LOOKBACK_DAYS
from tests.unit.providers.vercel.test_client_billing import policy_vercel_billing

from varne.config import VercelToken
from varne.db.schema import TableName
from varne.db.types import DatabaseBackend
from varne.providers.vercel.client import VercelClient
from varne.providers.vercel.service import VercelService


@pytest.fixture
def vcr_config():
    return {
        "decode_compressed_response": True,
        "filter_headers": ["authorization"],
        "allow_playback_repeats": True,  # the same request is made twice on purpose
        "before_record_response": partial(
            sanitize_response, policy=policy_vercel_billing
        ),
    }


def ticking_clock() -> Callable[[], datetime]:
    ticks = itertools.count()
    return lambda: (
        datetime(2026, 9, 10, 12, 30, tzinfo=UTC) + timedelta(seconds=next(ticks))
    )


@pytest.mark.default_cassette("billing.yaml")
@pytest.mark.vcr
def test_pulling_billing_twice_does_not_double_the_costs(
    db: DatabaseBackend,
    http_client: httpx.Client,
    vercel_token: VercelToken,
    vercel_team_id: str,
):
    service = VercelService(
        db=db,
        client=VercelClient(http_client, api_token=vercel_token),
        stack_id="stack_test",
        source_id="source_test",
        team_id=vercel_team_id,
        lookback_days=VERCEL_LOOKBACK_DAYS,
        now=ticking_clock(),
    )

    def snapshot() -> tuple[int, Decimal, int]:
        df = cast(pd.DataFrame, db.table(TableName.FACT_BILLING).execute())
        total = cast(Decimal, df["billed_cost"].sum())
        return len(df), total, cast(int, df["extracted_at"].nunique())

    service._fetch_source_billing()  # pyright: ignore[reportPrivateUsage]
    rows, total, _ = snapshot()

    service._fetch_source_billing()  # pyright: ignore[reportPrivateUsage]
    rows_again, total_again, pulls_kept = snapshot()

    assert rows > 0
    assert rows_again == rows
    assert total_again == total
    assert pulls_kept == 1  # only the latest pull's rows remain
    # the raw log keeps every response
    assert cast(int, db.table(TableName.RAW).count().execute()) == 2
