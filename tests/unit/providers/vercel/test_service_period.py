from datetime import UTC, datetime, timedelta, timezone

import httpx2 as httpx
import pytest
from pydantic import SecretStr

from varne.db.types import DatabaseBackend
from varne.providers.vercel.client import VercelClient
from varne.providers.vercel.service import VercelService


def make(db: DatabaseBackend, now: datetime, lookback_days: int = 30) -> VercelService:
    client = VercelClient(httpx.Client(), api_token=SecretStr("x"))
    return VercelService(
        db=db,
        client=client,
        stack_id="s",
        source_id="src",
        team_id="team_x",
        lookback_days=lookback_days,
        now=lambda: now,
    )


def test_period_includes_today(db: DatabaseBackend):
    service = make(db, datetime(2026, 9, 10, 12, 30, tzinfo=UTC), lookback_days=9)

    assert service.period() == (
        datetime(2026, 9, 1, tzinfo=UTC),
        datetime(2026, 9, 11, tzinfo=UTC),
    )


def test_period_uses_utc_days_whatever_the_clock_zone(db: DatabaseBackend):
    # 01:30 on the 11th in Warsaw (UTC+2) is still the 10th in UTC
    warsaw = timezone(timedelta(hours=2))
    service = make(db, datetime(2026, 9, 11, 1, 30, tzinfo=warsaw), lookback_days=1)

    assert service.period() == (
        datetime(2026, 9, 9, tzinfo=UTC),
        datetime(2026, 9, 11, tzinfo=UTC),
    )


def test_defaults_come_from_the_config_not_from_the_code(db: DatabaseBackend):
    service = make(db, datetime(2026, 1, 1, tzinfo=UTC))

    assert service.team_id == "team_x"
    assert service.project_ids == []
    assert service.lookback_days == 30


def test_usage_is_skipped_without_project_ids(db: DatabaseBackend):
    # no project_ids: nothing is requested (a real request would fail: no network here)
    make(db, datetime(2026, 9, 10, tzinfo=UTC))._fetch_source_usage()  # pyright: ignore[reportPrivateUsage]


@pytest.mark.parametrize("days", [0, 366])
def test_lookback_days_is_validated_in_the_config(days: int):
    from pydantic import ValidationError

    from varne.config import ConfigVercel

    with pytest.raises(ValidationError):
        ConfigVercel(
            id="v", name="V", api_token=SecretStr("x"), team_id="t", lookback_days=days
        )
