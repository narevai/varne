import pytest

from varne.config import SourceType, parse_config
from varne.ui.components.config_form import (
    Data,
    form_to_yaml,
    new_source,
    new_stack,
    yaml_to_form,
)


def test_what_the_form_left_empty_is_not_written():
    source = new_source(SourceType.VERCEL)
    source.update(
        id="web",
        name="Web",
        team_id="team_1",
        project_ids=["prj_1", "prj_2"],
        api_token="",
        api_token_env="VERCEL_TOKEN",
        lookback_days=None,
    )
    stack = new_stack()
    stack.update(id="main", name="Main", sources=[source])

    text = form_to_yaml({"stacks": [stack]})

    (parsed,) = parse_config(text).stacks
    assert parsed.sources[0].model_dump(exclude_none=True) == {
        "id": "web",
        "name": "Web",
        "type": SourceType.VERCEL,
        "lookback_days": 30,
        "api_token_env": "VERCEL_TOKEN",
        "team_id": "team_1",
        "project_ids": ["prj_1", "prj_2"],
    }
    assert "api_token:" not in text


def test_a_docker_source_with_hardware_costs_is_valid_yaml():
    source = new_source(SourceType.DOCKER)
    source.update(
        id="lab",
        name="Lab",
        cost={"machine_cost": 5000.0, "hourly_cost": None, "power_draw_watts": 120.0},
        usage={
            "type": "beszel",
            "url": "http://hub:8090",
            "email": "me@example.com",
            "password": "",
            "password_env": "BESZEL_PASSWORD",
        },
    )
    cost = source["cost"]
    assert isinstance(cost, dict)
    cost["electricity_price_per_kwh"] = 0.2

    (stack,) = parse_config(
        form_to_yaml({"stacks": [{"id": "s", "name": "S", "sources": [source]}]})
    ).stacks

    assert stack.sources[0].type is SourceType.DOCKER


def test_yaml_is_loaded_into_the_form_as_it_is():
    data = yaml_to_form("stacks:\n  - id: a\n    name: A\n")

    assert data == {"stacks": [{"id": "a", "name": "A"}]}
    assert yaml_to_form("") == {"stacks": []}


@pytest.mark.parametrize("text", ["- a\n- b\n", "stacks: 3\n", "stacks: [\n"])
def test_text_that_is_not_a_configuration_is_refused(text: str):
    with pytest.raises(ValueError):
        yaml_to_form(text)


def test_the_form_survives_a_round_trip():
    text = "stacks:\n- id: a\n  name: A\n"
    data: Data = yaml_to_form(text)

    assert form_to_yaml(data) == text
