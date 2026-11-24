"""One anonymous "server started" event, so that we know how many Varnes run.

This is Varne 1. Varne 0 sent a similar event to the same Umami website, so that the
two can be told apart this one goes to its own host name and page, `varne-v1` and
`/v1`, under its own event name, and with its own instance id.

What is sent: the version, the environment, whether it is a demo, and a random id
kept next to the database. Nothing about your sources, your costs or your keys.
Turn it off with `ENABLE_TELEMETRY=false`.
"""

import uuid
from pathlib import Path

import httpx2 as httpx
from loguru import logger

from varne.settings import Settings

EVENT = "server_start_v1"
HOSTNAME = "varne-v1"
URL = "/v1"
INSTANCE_FILE = ".instance_id_v1"

# Umami ignores requests that look like bots, so this looks like a browser.
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def instance_id(directory: Path) -> str | None:
    """A random id that stays the same for this installation."""
    path = directory / INSTANCE_FILE
    try:
        if path.exists():
            return path.read_text().strip() or None

        directory.mkdir(parents=True, exist_ok=True)
        value = str(uuid.uuid4())
        path.write_text(value)
        return value
    except OSError:
        return None


def is_enabled(settings: Settings) -> bool:
    return (
        settings.enable_telemetry
        and settings.environment != "development"
        and bool(settings.umami_website_id)
    )


async def track_server_start(
    settings: Settings, client: httpx.AsyncClient | None = None
) -> None:
    """Send the event once. It never gets in the way of the app starting."""
    if not is_enabled(settings):
        return

    data = {
        "version": settings.api_version,
        "environment": settings.environment,
        "demo": settings.demo_mode,
    }
    # kept next to the database
    identifier = instance_id(Path(settings.database_path).parent)
    if identifier:
        data["instance_id"] = identifier

    payload = {
        "type": "event",
        "payload": {
            "website": settings.umami_website_id,
            "hostname": HOSTNAME,
            "url": URL,
            "name": EVENT,
            "data": data,
        },
    }

    try:
        async with client or httpx.AsyncClient(timeout=5) as active:
            await active.post(
                f"{settings.umami_host.rstrip('/')}/api/send",
                json=payload,
                headers={"User-Agent": USER_AGENT},
            )
    except Exception as exc:
        logger.debug(f"Telemetry event failed: {exc}")
