from datetime import UTC, datetime
from typing import Literal, override

from varne.config import SourceId, SourceType, StackId
from varne.db.types import DatabaseBackend
from varne.providers.base import ProviderService
from varne.providers.types import RowRaw
from varne.providers.vercel.client import VercelClient


class VercelService(ProviderService):
    client: VercelClient

    def __init__(
        self,
        db: DatabaseBackend,
        client: VercelClient,
        stack_id: StackId,
        source_id: SourceId,
    ):
        super().__init__(db, stack_id, source_id)
        self.client = client

    @property
    @override
    def provider(self) -> Literal[SourceType.VERCEL]:
        return SourceType.VERCEL

    @override
    def fetch_meta(self) -> None:
        response = self.client.fetch_projects()

        projects_row = RowRaw(
            stack_id=self.stack_id,
            source_id=self.source_id,
            source_type=self.provider,
            method=response.request.method,
            url=str(response.request.url),
            extracted_at=datetime.now(UTC),
            payload=response.text,
        )

        self.store_raw([projects_row])

    # def fetch_billing(self) -> None:
    #   response_billing = self.client.fetch_billing()
    #   response_web_analytics_visits_count = self.client.fetch_web_analytics_visits_count()
    #   response_web_analytics_visits_aggregate = self.fetch_web_analytics_visits_aggregate()
