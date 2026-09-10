import json
from typing import TypedDict, cast

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


def sanitize(value: JsonValue, key: str | None = None) -> JsonValue:
    if isinstance(value, dict):
        return {
            child_key: sanitize(child_value, child_key)
            for child_key, child_value in value.items()
        }

    if isinstance(value, list):
        return [sanitize(item, key) for item in value]

    if isinstance(value, str):
        return f"<{key}>" if key else "<string>"

    if isinstance(value, bool):
        return False

    if isinstance(value, int):
        return 0

    if isinstance(value, float):
        return 0.0

    return None


class VcrBody(TypedDict, total=False):
    string: str | bytes


class VcrResponse(TypedDict, total=False):
    body: VcrBody


def sanitize_response(response: VcrResponse) -> VcrResponse:
    body = response.get("body", {}).get("string")

    if not isinstance(body, str):
        return response

    try:
        payload = cast(JsonValue, json.loads(body))
    except json.JSONDecodeError:
        return response

    response.setdefault("body", {})["string"] = json.dumps(sanitize(payload))

    return response
