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


def sanitize(
    value: JsonValue,
    policy: SanitizePolicy,
    key: str | None = None,
) -> JsonValue:
    field_policy = get_field_policy(key, policy)

    if isinstance(value, dict):
        if field_policy and field_policy.redact_keys:
            return {
                f"<key_{index}>": sanitize(child_value, policy, child_key)
                for index, (child_key, child_value) in enumerate(value.items())
            }

        return {
            child_key: (
                child_value
                if field_policy and child_key in field_policy.keep
                else sanitize(child_value, policy, child_key)
            )
            for child_key, child_value in value.items()
        }

    if isinstance(value, list):
        items = value

        if field_policy and field_policy.limit is not None:
            items = items[: field_policy.limit]

        return [sanitize(item, policy, key) for item in items]

    if isinstance(value, str):
        return f"<{key}>" if key else "<string>"

    if isinstance(value, bool):
        return False

    if isinstance(value, int):
        return 0

    if isinstance(value, float):
        return 0.0

    return None


def sanitize_response(
    response: VcrResponse,
    policy: SanitizePolicy = default_policy,
) -> VcrResponse:
    body = response.get("body", {}).get("string")

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
        payload = cast(JsonValue, json.loads(text))
    except json.JSONDecodeError:
        return response

    sanitized = json.dumps(sanitize(payload, policy))

    response.setdefault("body", {})["string"] = (
        sanitized.encode() if isinstance(body, bytes) else sanitized
    )

    headers = response.get("headers", {})
    headers.pop("content-length", None)
    headers.pop("Content-Length", None)

    return response
