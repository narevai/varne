from dataclasses import dataclass

import pytest

from varne import sync
from varne.config import ConfigDocker, ConfigSource, ConfigStack
from varne.sync import sync_sources


@dataclass
class FakeService:
    fails: bool
    calls: list[str]
    name: str

    def fetch_source_meta(self) -> None:
        self.calls.append(f"meta {self.name}")

    def fetch_source_data(self) -> None:
        if self.fails:
            raise RuntimeError("hub is down")
        self.calls.append(f"data {self.name}")


def docker(source_id: str) -> ConfigDocker:
    return ConfigDocker.model_validate(
        {
            "id": source_id,
            "name": source_id.upper(),
            "type": "docker",
            "cost": {"hourly_cost": 1},
            "usage": {
                "type": "beszel",
                "url": "http://hub",
                "email": "a@b.c",
                "password": "x",
            },
        }
    )


def test_a_failing_source_is_reported_and_the_others_are_still_synced(
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[str] = []

    def get_service(*, stack_id: str, source: ConfigSource) -> FakeService:
        _ = stack_id
        return FakeService(source.id == "bad", calls, source.id)

    monkeypatch.setattr(sync, "get_service", get_service)
    stack = ConfigStack(id="s", name="Stack")

    result = sync_sources(stack, [docker("bad"), docker("good")])

    assert result.synced == 1
    assert [f.source.id for f in result.failures] == ["bad"]
    assert result.failures[0].message == "Sync failed for Stack / BAD: hub is down"
    assert calls == ["meta bad", "meta good", "data good"]
