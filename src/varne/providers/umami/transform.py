from varne.providers.types import RowFactUsage, RowRaw
from varne.providers.umami.types import UmamiDataPoint, UmamiPageviews


def point_to_usage(
    row_raw: RowRaw, point: UmamiDataPoint, usage_name: str
) -> RowFactUsage:
    return RowFactUsage(
        stack_id=row_raw.stack_id,
        source_id=row_raw.source_id,
        source_type=row_raw.source_type,
        extracted_at=row_raw.extracted_at,
        event_time=point.x,
        usage_name=usage_name,
        usage=point.y,
    )


def transform_pageviews(row: RowRaw) -> list[RowFactUsage]:
    report = UmamiPageviews.model_validate_json(row.payload)

    rows_usage = [point_to_usage(row, point, "pageviews") for point in report.pageviews]
    rows_usage += [point_to_usage(row, point, "sessions") for point in report.sessions]

    return rows_usage
