from datetime import datetime

from varne.providers.beszel.client import BeszelClient
from varne.providers.beszel.transform import transform_stats
from varne.providers.beszel.types import (
    INTERVALS,
    BeszelContainerInfo,
    BeszelContainerStats,
    BeszelPage,
    BeszelSystems,
    BeszelSystemStats,
)
from varne.providers.docker.usage import DockerUsage, RecordResponse


class BeszelUsage:
    client: BeszelClient

    def __init__(self, client: BeszelClient) -> None:
        self.client = client

    def _systems(self, record: RecordResponse) -> dict[str, str]:
        response = self.client.fetch_systems()
        record(response)

        systems = BeszelSystems.model_validate_json(response.text)
        return {system.id: system.name for system in systems.items}

    def _containers(self, record: RecordResponse) -> list[BeszelContainerInfo]:
        containers: list[BeszelContainerInfo] = []
        page = 1

        while True:
            response = self.client.fetch_containers(page)
            record(response)

            parsed = BeszelPage[BeszelContainerInfo].model_validate_json(response.text)
            containers += parsed.items

            if page >= parsed.total_pages:
                return containers

            page += 1

    def _container_stats(
        self, interval: str, date_from: datetime, record: RecordResponse
    ) -> list[BeszelContainerStats]:
        records: list[BeszelContainerStats] = []
        page = 1

        while True:
            response = self.client.fetch_container_stats(interval, date_from, page)
            record(response)

            parsed = BeszelPage[BeszelContainerStats].model_validate_json(response.text)
            records += parsed.items

            if page >= parsed.total_pages:
                return records

            page += 1

    def _system_stats(
        self, interval: str, date_from: datetime, record: RecordResponse
    ) -> list[BeszelSystemStats]:
        records: list[BeszelSystemStats] = []
        page = 1

        while True:
            response = self.client.fetch_system_stats(interval, date_from, page)
            record(response)

            parsed = BeszelPage[BeszelSystemStats].model_validate_json(response.text)
            records += parsed.items

            if page >= parsed.total_pages:
                return records

            page += 1

    def systems(self, record: RecordResponse) -> list[str]:
        return list(self._systems(record).values())

    def fetch(self, date_from: datetime, record: RecordResponse) -> DockerUsage:
        systems = self._systems(record)

        containers: list[BeszelContainerStats] = []
        machines: list[BeszelSystemStats] = []
        for interval, _ in INTERVALS:
            containers += self._container_stats(interval, date_from, record)
            machines += self._system_stats(interval, date_from, record)

        return DockerUsage(
            hours=transform_stats(containers, machines, systems, date_from),
            images={
                (systems.get(info.system, info.system), info.name): info.image
                for info in self._containers(record)
            },
        )
