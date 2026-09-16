from pydantic import TypeAdapter

from varne.providers.types import RowRaw, RowStaging
from varne.providers.vercel.types import VercelProjectsResponse


def transform_projects(row: RowRaw) -> list[RowStaging]:
    rows_staging: list[RowStaging] = []
    adapter = TypeAdapter(list[VercelProjectsResponse])
    projects_list = adapter.validate_json(row.payload)
    for projects_object in projects_list:
        for project in projects_object.projects:
            row_id: RowStaging = RowStaging(
                stack_id=row.stack_id,
                source_id=row.source_id,
                source_type=row.source_type,
                extracted_at=row.extracted_at,
                value_name="id",
                value=project.id,
            )

            row_account_id: RowStaging = RowStaging(
                stack_id=row.stack_id,
                source_id=row.source_id,
                source_type=row.source_type,
                extracted_at=row.extracted_at,
                value_name="account_id",
                value=project.account_id,
            )

            row_name: RowStaging = RowStaging(
                stack_id=row.stack_id,
                source_id=row.source_id,
                source_type=row.source_type,
                extracted_at=row.extracted_at,
                value_name="name",
                value=project.name,
            )
            rows_staging.append(row_id)
            rows_staging.append(row_account_id)
            rows_staging.append(row_name)

    return rows_staging
