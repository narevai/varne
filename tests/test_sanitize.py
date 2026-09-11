import json
from typing import cast

from tests.policy import FieldPolicy, SanitizePolicy
from tests.sanitize import (
    JsonValue,
    VcrResponse,
    get_nested,
    parse_body,
    sanitize,
    sanitize_response,
    serialize_body,
)


def test_get_nested_returns_nested_value():
    value: dict[str, JsonValue] = {
        "Tags": {
            "ProjectId": "prj_123",
            "ProjectName": "example",
        }
    }
    result = get_nested(value, "Tags.ProjectId")

    assert result == "prj_123"


def test_get_nested_returns_none_when_path_missing():
    value: dict[str, JsonValue] = {
        "Tags": {
            "ProjectId": "prj_123",
        }
    }

    result = get_nested(value, "Tags.ProjectName")

    assert result is None


def test_sanitize_redacts_scalar_values():
    value: dict[str, JsonValue] = {
        "name": "secret-name",
        "count": 42,
        "price": 1.23,
        "enabled": True,
    }

    policy = SanitizePolicy()
    result = sanitize(value, policy)

    assert result == {
        "name": "<name>",
        "count": 0,
        "price": 0.0,
        "enabled": False,
    }


def test_sanitize_keeps_selected_fields():
    value: dict[str, JsonValue] = {
        "projects": [
            {
                "id": "prj_123",
                "accountId": "team_123",
                "name": "secret-project",
            }
        ]
    }

    policy = SanitizePolicy(
        fields=(
            FieldPolicy(
                field="projects",
                keep=("id", "accountId"),
            ),
        )
    )

    result = sanitize(value, policy)

    assert result == {
        "projects": [
            {
                "id": "prj_123",
                "accountId": "team_123",
                "name": "<name>",
            }
        ]
    }


def test_sanitize_filters_list_by_nested_field():
    value: JsonValue = [
        {
            "ServiceName": "Memory",
            "Tags": {
                "ProjectId": "prj_target",
            },
        },
        {
            "ServiceName": "Bandwidth",
            "Tags": {
                "ProjectId": "prj_other",
            },
        },
    ]

    policy = SanitizePolicy(
        root=FieldPolicy(
            match_field="Tags.ProjectId",
            match_value="prj_target",
            keep=("ServiceName",),
        ),
        fields=(
            FieldPolicy(
                field="Tags",
                keep=("ProjectId",),
            ),
        ),
    )

    result = sanitize(value, policy)

    assert result == [
        {
            "ServiceName": "Memory",
            "Tags": {
                "ProjectId": "prj_target",
            },
        }
    ]


def test_sanitize_limits_filtered_items():
    value: JsonValue = [
        {
            "id": 1,
            "Tags": {
                "ProjectId": "prj_target",
            },
        },
        {
            "id": 2,
            "Tags": {
                "ProjectId": "prj_target",
            },
        },
        {
            "id": 3,
            "Tags": {
                "ProjectId": "prj_target",
            },
        },
    ]

    policy = SanitizePolicy(
        root=FieldPolicy(
            match_field="Tags.ProjectId",
            match_value="prj_target",
            limit=2,
            keep=("id",),
        ),
        fields=(
            FieldPolicy(
                field="Tags",
                keep=("ProjectId",),
            ),
        ),
    )

    result = sanitize(value, policy)

    assert result == [
        {
            "id": 1,
            "Tags": {
                "ProjectId": "prj_target",
            },
        },
        {
            "id": 2,
            "Tags": {
                "ProjectId": "prj_target",
            },
        },
    ]


def test_parse_body_parses_regular_json():
    text = '{"projects":[{"id":"prj_123"}]}'

    payload, is_jsonl = parse_body(text)

    assert payload == {
        "projects": [
            {
                "id": "prj_123",
            }
        ]
    }
    assert is_jsonl is False


def test_parse_body_parses_jsonl():
    text = (
        '{"id":1,"Tags":{"ProjectId":"prj_target"}}\n'
        '{"id":2,"Tags":{"ProjectId":"prj_other"}}\n'
    )

    payload, is_jsonl = parse_body(text)

    assert payload == [
        {
            "id": 1,
            "Tags": {
                "ProjectId": "prj_target",
            },
        },
        {
            "id": 2,
            "Tags": {
                "ProjectId": "prj_other",
            },
        },
    ]

    assert is_jsonl is True


def test_serialize_body_serializes_regular_json():
    payload: JsonValue = {
        "projects": [
            {
                "id": "prj_123",
            }
        ]
    }

    result = serialize_body(payload, is_jsonl=False)

    assert json.loads(result) == payload


def test_serialize_body_serializes_jsonl():
    payload: JsonValue = [
        {"id": 1},
        {"id": 2},
    ]

    result = serialize_body(payload, is_jsonl=True)

    lines = result.splitlines()

    assert len(lines) == 2
    assert json.loads(lines[0]) == {"id": 1}
    assert json.loads(lines[1]) == {"id": 2}


def test_sanitize_response_filters_jsonl_and_keeps_values():
    body = (
        '{"ServiceName":"Memory","EffectiveCost":0.5,'
        '"Tags":{"ProjectId":"prj_target","ProjectName":"target"}}\n'
        '{"ServiceName":"Bandwidth","EffectiveCost":1.2,'
        '"Tags":{"ProjectId":"prj_other","ProjectName":"other"}}\n'
    )

    response: VcrResponse = {
        "body": {
            "string": body,
        },
        "headers": {
            "content-length": ["123"],
            "Content-Type": ["application/json"],
        },
    }

    policy = SanitizePolicy(
        root=FieldPolicy(
            match_field="Tags.ProjectId",
            match_value="prj_target",
            keep=(
                "ServiceName",
                "EffectiveCost",
            ),
        ),
        fields=(
            FieldPolicy(
                field="Tags",
                keep=(
                    "ProjectId",
                    "ProjectName",
                ),
            ),
        ),
    )

    result = sanitize_response(
        response,
        policy=policy,
    )

    result_body = result.get("body")
    assert result_body is not None
    sanitized_body = result_body.get("string")
    assert sanitized_body is not None
    assert isinstance(sanitized_body, str)

    lines = sanitized_body.splitlines()

    assert len(lines) == 1

    row = cast(dict[str, JsonValue], json.loads(lines[0]))

    assert row == {
        "ServiceName": "Memory",
        "EffectiveCost": 0.5,
        "Tags": {
            "ProjectId": "prj_target",
            "ProjectName": "target",
        },
    }

    headers = result.get("headers")
    assert headers is not None

    assert "content-length" not in headers
    assert headers["Content-Type"] == ["application/json"]


def test_sanitize_response_handles_bytes_body():
    response: VcrResponse = {
        "body": {
            "string": b'{"name":"secret"}',
        },
        "headers": {},
    }

    result = sanitize_response(response)

    result_body = result.get("body")
    assert result_body is not None
    sanitized_body = result_body.get("string")
    assert sanitized_body is not None

    assert isinstance(sanitized_body, bytes)
    assert json.loads(sanitized_body.decode()) == {
        "name": "<name>",
    }


def test_sanitize_response_returns_original_for_non_json():
    response: VcrResponse = {
        "body": {
            "string": "not-json",
        },
        "headers": {},
    }

    original = response.copy()

    result = sanitize_response(response)

    assert result == original
