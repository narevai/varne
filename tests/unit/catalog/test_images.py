import pytest

from varne.catalog.images import (
    ICON_ALIASES,
    ICON_FILES,
    ICONS,
    application_name,
    find_app,
    identify,
    image_names,
)


@pytest.mark.parametrize(
    ("image", "names"),
    [
        ("lscr.io/linuxserver/sonarr:latest", ["sonarr"]),
        (
            "ghcr.io/immich-app/immich-server:release",
            ["immich-server", "immich", "immich-app"],
        ),
        ("nginx", ["nginx"]),
        ("library/nginx:1.27", ["nginx"]),
        ("localhost:5000/team/web-app@sha256:abc", ["web-app", "web", "team"]),
        ("registry.example.com:5000/open-webui:v1", ["open-webui"]),
        ("ghcr.io/shokoanime/server:v5", ["shokoanime"]),
        ("Docker.IO/Some_Org/Some_App:1", ["some-app", "some", "some-org"]),
    ],
)
def test_image_names_leave_out_registry_tag_publisher_and_generic_words(
    image: str, names: list[str]
):
    assert image_names(image) == names


@pytest.mark.parametrize(
    ("image", "app"),
    [
        ("ghcr.io/immich-app/immich-server:release", "Immich"),
        ("ghcr.io/immich-app/immich-machine-learning:release", "Immich"),
        ("ghcr.io/open-webui/open-webui:v0.11.4-ollama", "Open WebUI"),
        ("lscr.io/linuxserver/syncthing:latest", "Syncthing"),
        ("ghcr.io/netbirdio/netbird:0.79.0", "NetBird"),
        ("searxng/searxng:2026.9.23-783a09462", "SearXNG"),
        ("lscr.io/linuxserver/healthchecks:latest", "Healthchecks"),
        ("ghcr.io/stirling-tools/stirling-pdf:2.14.3", "Stirling PDF"),
        ("pihole/pihole:latest", "Pi-hole"),
        ("grafana/grafana:latest", "Grafana"),
        ("ghcr.io/dgtlmoon/changedetection.io:latest", "changedetection.io"),
        ("ghcr.io/crocodilestick/calibre-web-automated:v4.0.6", "Calibre-Web"),
        ("ghcr.io/stalwartlabs/stalwart:v0.16.23", "Stalwart"),
        ("docker.elastic.co/elasticsearch/elasticsearch:9.5.4", "Elasticsearch"),
        ("itzg/minecraft-bedrock-server:2026.9.0", "Minecraft Server"),
        ("ghcr.io/johnrbrady/byb-budget:1.0.0", "Byb Budget"),
        ("actualbudget/actual-server:26.9.0", "Actual Budget"),
        ("henrygd/beszel-agent:latest", "Beszel"),
        ("technitium/dns-server:latest", "Technitium DNS"),
        ("triliumnext/trilium:latest", "Trilium"),
        ("nodered/node-red:4.1.15-18-minimal", "Node-RED"),
        ("ghcr.io/coollabsio/coolify-realtime:1.0.20", "Coolify"),
        ("ollama/ollama:0.34.3", "Ollama"),
        ("checkmk/check-mk-raw:2.4.0-latest", "Checkmk"),
        ("ghcr.io/immich-app/postgres:14-vectorchord0.4.3", "Immich"),
    ],
)
def test_images_are_recognised_as_applications(image: str, app: str | None):
    found = find_app(image)

    assert (found.name if found else None) == app


def test_a_container_of_another_project_is_not_taken_for_an_app():
    assert find_app("ghcr.io/immichframe/immichframe:v1.0.38.0") is None


def test_an_unknown_or_missing_image_is_no_application():
    assert find_app("ghcr.io/someone/their-thing:1") is None
    assert find_app(None) is None


@pytest.mark.parametrize(
    ("image", "name"),
    [
        ("ghcr.io/immich-app/immich-server:release", "Immich"),
        ("lscr.io/linuxserver/sonarr:latest", "Sonarr"),
        ("ghcr.io/home-assistant/home-assistant:stable", "Home Assistant"),
        ("valkey/valkey:9.1.2", "Valkey"),
        ("linuxserver/server:1", None),
        (None, None),
    ],
)
def test_every_image_gives_an_application_name_not_only_the_catalog(
    image: str | None, name: str | None
):
    assert application_name(image) == name


def test_an_application_outside_the_catalog_has_a_logo_when_one_is_shipped():
    dozzle = identify("amir20/dozzle:latest")
    unknown = identify("ghcr.io/someone/their-thing:1")

    assert dozzle is not None and dozzle.icon == "dozzle"
    assert dozzle.alternative is None
    assert unknown is not None and unknown.icon is None


def test_an_application_of_the_catalog_carries_its_subscription():
    chat = identify("ghcr.io/open-webui/open-webui:v0.11.4-ollama")

    assert chat is not None
    assert (chat.alternative, chat.usd_per_month) == ("ChatGPT Plus", 20)


def test_every_logo_alias_points_at_a_logo_that_is_shipped():
    assert [icon for icon in ICON_ALIASES.values() if icon not in ICONS] == []


def test_an_image_that_goes_by_another_name_among_the_logos_gets_it():
    actual = identify("actualbudget/actual-server:26.9.0")

    assert actual is not None and actual.icon == "actual-budget"


def test_a_logo_can_be_a_picture_as_well_as_a_vector():
    assert ICON_FILES["cadvisor"] == "cadvisor.png"
    assert ICON_FILES["immich"] == "immich.svg"


@pytest.mark.parametrize(
    ("image", "icon"),
    [
        ("itzg/minecraft-bedrock-server:2026.9.0", "minecraft"),
        ("ghcr.io/seanmorley15/adventurelog-backend:v0.13.0", "adventure-log"),
        ("ghcr.io/ep1cman/unifi-protect-backup:0.14.3", "unifi-protect"),
        ("lscr.io/linuxserver/speedtest-tracker:latest", "speedtest-tracker"),
    ],
)
def test_the_logo_of_the_start_of_a_name_is_taken_when_the_name_has_none(
    image: str, icon: str
):
    found = identify(image)

    assert found is not None and found.icon == icon


def test_a_generic_word_is_no_logo():
    found = identify("example/web-thing:1")

    assert found is not None and found.icon is None
