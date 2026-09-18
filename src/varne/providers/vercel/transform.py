from pydantic import TypeAdapter

from varne.config import SourceType
from varne.providers.jsonplaceholder.types import JsonPlaceholderPost
from varne.providers.types import RowDimSourceMeta, RowRaw
from varne.providers.vercel.types import VercelProjectsResponse


def project_to_meta(row_raw: RowRaw, value_name: str, value: str) -> RowDimSourceMeta:
    row_staging: RowDimSourceMeta = RowDimSourceMeta(
        stack_id=row_raw.stack_id,
        source_id=row_raw.source_id,
        source_type=row_raw.source_type,
        extracted_at=row_raw.extracted_at,
        value_name=value_name,
        value=value,
    )

    return row_staging

def transform_meta(row: RowRaw) -> list[RowDimSourceMeta]:
    rows_staging: list[RowDimSourceMeta] = []
    adapter = TypeAdapter(VercelProjectsResponse)
    projects_typed = adapter.validate_json(row.payload)
    for project in projects_typed.projects:
        row_id: RowDimSourceMeta = project_to_meta(
            row, value_name="id", value=project.id
        )
        row_name: RowDimSourceMeta = project_to_meta(
            row, value_name="id", value=project.name
        )
        row_account_id: RowDimSourceMeta = project_to_meta(
            row, value_name="id", value=project.account_id
        )
        rows_staging.append(row_id)
        rows_staging.append(row_name)
        rows_staging.append(row_account_id)

    return rows_staging
