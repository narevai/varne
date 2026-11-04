import logging
import uuid
from pathlib import Path

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# Umami ignores requests that look like bots, so use a browser-like User-Agent.
_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def _instance_id(data_dir: Path) -> str | None:
    """Return a random, persistent, anonymous instance ID (stored next to the DB)."""
    path = data_dir / ".instance_id"
    try:
        if path.exists():
            return path.read_text().strip() or None
        data_dir.mkdir(parents=True, exist_ok=True)
        value = str(uuid.uuid4())
        path.write_text(value)
        return value
    except OSError:
        return None


async def track_server_start() -> None:
    """Send an anonymous "server_start" event to Umami (fire-and-forget)."""
    settings = get_settings()
    if (
        settings.do_not_track
        or settings.is_development
        or not settings.umami_website_id
    ):
        return

    data = {
        "version": settings.api_version,
        "environment": settings.environment,
        "demo": settings.demo,
    }
    instance_id = _instance_id(Path(settings.sqlite_path).parent)
    if instance_id:
        data["instance_id"] = instance_id

    payload = {
        "type": "event",
        "payload": {
            "website": settings.umami_website_id,
            "hostname": "varne",
            "url": "/",
            "name": "server_start",
            "data": data,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{settings.umami_host.rstrip('/')}/api/send",
                json=payload,
                headers={"User-Agent": _USER_AGENT},
            )
    except Exception as e:  # never break startup because of analytics
        logger.debug(f"Umami event failed: {e}")
