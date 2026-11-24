from dataclasses import dataclass
from decimal import Decimal
from importlib.resources import files
from pathlib import Path

from varne.catalog.equivalents import equivalent_of
from varne.catalog.hosted import HostedApp
from varne.catalog.selfhosted import SELF_HOSTED, SelfHostedApp

# Names that say what an image is for, not which application it is.
GENERIC = frozenset(
    {"server", "app", "web", "api", "backend", "frontend", "worker", "core", "latest"}
)
# Publishers of many applications: `linuxserver/sonarr` is Sonarr, not LinuxServer.
DISTRIBUTORS = frozenset(
    {"linuxserver", "bitnami", "library", "hotio", "binhex", "jlesage", "onedr0p"}
)
SUFFIXES = ("-server", "-ce", "-ee", "-alpine", "-web", "-app")

# Logos shipped with the app, by the name of the logo and the file it is in.
ICON_FILES: dict[str, str] = {
    icon.stem: icon.name
    for icon in sorted(
        Path(str(files("varne.ui"))).glob("static/icons/*"), reverse=True
    )
    if icon.suffix in (".svg", ".png")
}
ICONS = frozenset(ICON_FILES)

# Image names that go by another name among the logos.
ICON_ALIASES = {
    "actual-server": "actual-budget",
    "adventurelog": "adventure-log",
    "clamav": "clam-av",
    "crafty": "crafty-controller",
    "grampsweb": "gramps-web",
    "immichframe": "immich-frame",
    "local-ai": "localai",
    "lyrionmusicserver": "lyrion",
    "newt": "pangolin",
    "mylar3": "mylar-3",
    "postgis": "postgres",
    "steamcmd": "steam",
    "zwave-js-ui": "z-wave-js-ui",
}
# Shortest name that may stand for a longer one: `minecraft` for
# `minecraft-bedrock-server`.
MIN_ICON_NAME = 4

INDEX: dict[str, SelfHostedApp] = {
    slug: app for app in SELF_HOSTED for slug in app.slugs
}


def strip_suffix(name: str) -> str:
    for suffix in SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[: -len(suffix)]

    return name


def image_names(image: str) -> list[str]:
    """Names an image reference could be known by, most specific first.

    `lscr.io/linuxserver/sonarr:latest` gives `sonarr`: the registry, the tag
    and the digest are not the application, and neither is its publisher.
    """
    reference = image.split("@")[0]

    if reference.rfind(":") > reference.rfind("/"):
        reference = reference[: reference.rfind(":")]

    segments = reference.split("/")
    if len(segments) > 1 and (
        "." in segments[0] or ":" in segments[0] or segments[0] == "localhost"
    ):
        segments = segments[1:]

    names: list[str] = []
    for segment in reversed(segments[-2:]):
        name = segment.lower().replace("_", "-")

        if not name or name in GENERIC or name in DISTRIBUTORS:
            continue

        names.append(name)

        stripped = strip_suffix(name)
        if stripped != name:
            names.append(stripped)

    return list(dict.fromkeys(names))


def find_app(image: str | None) -> SelfHostedApp | None:
    if image is None:
        return None

    return next(
        (INDEX[name] for name in image_names(image) if name in INDEX),
        None,
    )


def find_icon(names: list[str]) -> str | None:
    """The logo of the first name that has one, or of the start of its name."""
    for name in names:
        words = name.split("-")

        for count in range(len(words), 0, -1):
            start = "-".join(words[:count])
            icon = ICON_ALIASES.get(start, start)

            if len(start) >= MIN_ICON_NAME and start not in GENERIC and icon in ICONS:
                return icon

    return None


@dataclass(frozen=True)
class Application:
    """An application as the user sees it, and the hosted service it stands in for,
    if it is known."""

    name: str
    icon: str | None
    hosted: HostedApp | None = None

    @property
    def alternative(self) -> str | None:
        return None if self.hosted is None else self.hosted.label

    @property
    def usd_per_month(self) -> Decimal | None:
        return None if self.hosted is None else self.hosted.usd_per_month


def identify(image: str | None) -> Application | None:
    """What the user calls the application running from an image.

    An application of the catalog goes by its name there, the others by what
    their image is called: `lscr.io/linuxserver/sonarr` is `Sonarr`.
    """
    if image is None:
        return None

    app = find_app(image)
    if app is not None:
        return Application(app.name, app.icon, equivalent_of(app))

    names = image_names(image)
    if not names:
        return None

    return Application(names[0].replace("-", " ").title(), find_icon(names))


def application_name(image: str | None) -> str | None:
    application = identify(image)
    return None if application is None else application.name
