from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import httpx2 as httpx
from pydantic import SecretStr

from varne.cassettes import CassetteManager
from varne.providers.beszel.client import BeszelClient
from varne.providers.beszel.usage import BeszelUsage

BESZEL_CASSETTE = (
    Path(__file__).parent
    / "unit"
    / "providers"
    / "beszel"
    / "cassettes"
    / "container_stats.yaml"
)


@contextmanager
def recorded_hub(http: httpx.Client) -> Generator[BeszelUsage]:
    """The usage of a real Beszel hub, played back from its cassette.

    Whatever is asked of the hub gets the recorded answer, as in debug mode.
    Every other request fails while it lasts, so keep it around the pull only.
    """
    manager = CassetteManager([BESZEL_CASSETTE])
    manager.start()

    try:
        yield BeszelUsage(
            BeszelClient(
                http,
                "http://compose-lab:8090",
                "me@example.com",
                SecretStr("secret"),
            )
        )
    finally:
        manager.stop()
