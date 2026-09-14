import json
from typing import TypedDict, cast

from tests.policy import SanitizePolicy, default_policy, get_field_policy

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


class VcrBody(TypedDict, total=False):
    string: str | bytes


class VcrResponse(TypedDict, total=False):
    body: VcrBody
    headers: dict[str, list[str]]


def get_nested(value: dict[str, JsonValue], path: str) -> JsonValue | None:
    current: JsonValue = value

    for part in path.split("."):
        if not isinstance(current, dict):
            return None

        current = current.get(part)

        if current is None:
            return None

    return current


def sanitize(
    value: JsonValue,
    policy: SanitizePolicy,
    key: str | None = None,
) -> JsonValue:
    if key is None:
        field_policy = policy.root
    else:
        field_policy = get_field_policy(key, policy)

    if isinstance(value, dict):
        sanitized_dict: dict[str, JsonValue] = {}

        for child_key, child_value in value.items():
            should_keep = field_policy is not None and child_key in field_policy.keep

            if should_keep:
                sanitized_dict[child_key] = child_value
                continue

            sanitized_dict[child_key] = sanitize(
                child_value,
                policy,
                child_key,
            )

        return sanitized_dict

    if isinstance(value, list):
        items = value

        should_filter_items = (
            field_policy is not None
            and field_policy.match_field is not None
            and field_policy.match_value is not None
        )

        if should_filter_items and field_policy is not None:
            filtered_items: list[JsonValue] = []
            match_field = field_policy.match_field
            match_value = field_policy.match_value
            for item in items:
                if not isinstance(item, dict):
                    continue

                matched_value = get_nested(
                    item,
                    match_field,  # pyright: ignore[reportArgumentType]
                )

                if matched_value == match_value:
                    filtered_items.append(item)

            items = filtered_items

        if field_policy is not None and field_policy.limit is not None:
            items = items[: field_policy.limit]

        sanitized_items: list[JsonValue] = []

        for item in items:
            sanitized_items.append(
                sanitize(
                    item,
                    policy,
                    key,
                )
            )

        return sanitized_items

    if isinstance(value, str):
        return f"<{key}>" if key is not None else "<string>"

    if isinstance(value, bool):
        return False

    if isinstance(value, int):
        return 0

    if isinstance(value, float):
        return 0.0

    return None


def parse_body(text: str) -> tuple[JsonValue, bool]:
    try:
        payload = cast(JsonValue, json.loads(text))
        return payload, False

    except json.JSONDecodeError:
        rows: list[JsonValue] = []

        for line in text.splitlines():
            if not line.strip():
                continue

            row = cast(JsonValue, json.loads(line))
            rows.append(row)

        return rows, True


def serialize_body(payload: JsonValue, is_jsonl: bool) -> str:
    if not is_jsonl:
        return json.dumps(payload)

    if not isinstance(payload, list):
        raise TypeError("Expected list when serializing JSONL response")

    lines: list[str] = []

    for row in payload:
        line = json.dumps(row)
        lines.append(line)

    return "\n".join(lines)


def sanitize_response(
    response: VcrResponse,
    policy: SanitizePolicy = default_policy,
) -> VcrResponse:
    body_container = response.get("body", {})
    body = body_container.get("string")

    if isinstance(body, bytes):
        try:
            text = body.decode()
        except UnicodeDecodeError:
            return response

    elif isinstance(body, str):
        text = body

    else:
        return response

    try:
        payload, is_jsonl = parse_body(text)
    except json.JSONDecodeError:
        return response

    sanitized_payload = sanitize(
        payload,
        policy,
    )

    sanitized = serialize_body(
        sanitized_payload,
        is_jsonl,
    )

    if isinstance(body, bytes):
        response.setdefault("body", {})["string"] = sanitized.encode()
    else:
        response.setdefault("body", {})["string"] = sanitized

    headers = response.get("headers", {})

    headers.pop("content-length", None)
    headers.pop("Content-Length", None)

    return response
