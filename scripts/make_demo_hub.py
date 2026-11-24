"""Make the recording that the demo plays back, from a recording of a real Beszel hub.

The real one has 100 containers on a machine of 500 GiB, and records for about two
hours, so that most of what a demo would show is idle and the table is a wall of apps.
The demo keeps a dozen containers, with the use of the processor and the memory the
demo wants for them, on a small machine, for every hour of the days it looks at. The
numbers are made up, shaped like the real records, and the same on every run.

    python scripts/make_demo_hub.py
"""

import json
import math
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tests/unit/providers/beszel/cassettes/container_stats.yaml"
TARGET = ROOT / "src/varne/demo/beszel_hub.yaml"

# Total memory of the sample machine, in GiB.
MEMORY_GIB = 14

# The records cover the days the demo looks at, up to the clock of the demo.
DAYS = 10
START = datetime(2026, 11, 20, tzinfo=UTC) - timedelta(days=DAYS)
HOURS = 24 * DAYS + 16

# What each container uses on average: percent of the machine's processor, MiB of
# memory, and how much more (or less) it does at the weekend. Eleven of them stand in
# for a subscription, two do not. None of them is an application whose plan costs so
# much that it dwarfs the rest.
CONTAINERS: dict[str, tuple[float, float, float]] = {
    "compose-lab-open-webui-1": (10, 2800, 0.7),
    "compose-lab-grafana-1": (3, 900, 0.5),
    "compose-lab-healthchecks-1": (2.5, 500, 0.9),
    "compose-lab-immich-db-1": (5, 1500, 1.6),
    "compose-lab-stalwart-1": (1.5, 400, 0.6),
    "compose-lab-searxng-1": (3, 600, 0.8),
    "compose-lab-logseq-1": (1, 350, 1.1),
    "compose-lab-netbird-client-1": (1.5, 200, 1.0),
    "compose-lab-windmill-lsp-1": (4, 1200, 0.4),
    "compose-lab-homeassistant-1": (6, 1800, 1.3),
    "compose-lab-mealie-1": (2.5, 600, 1.8),
    "compose-lab-copyparty-1": (2.5, 900, 1.4),
    "compose-lab-byb-budget-1": (1.5, 300, 1.2),
}

type Json = dict[str, Any]  # pyright: ignore[reportExplicitAny]


def jitter(name: str, index: int, spread: float) -> float:
    """A steady multiplier around 1, the same for the same container and record."""
    return 1 + spread * (random.Random(f"{name}:{index}").random() - 0.5) * 2


def reshape_containers(body: Json) -> None:
    body["items"] = [item for item in body["items"] if item["name"] in CONTAINERS]
    body["totalItems"] = len(body["items"])
    body["totalPages"] = 1


def periods() -> list[str]:
    """When the periods of the made up records end, one every two hours."""
    ends = [START + timedelta(hours=2 * step) for step in range(1, HOURS // 2 + 1)]
    return [end.strftime("%Y-%m-%d %H:%M:%S.000Z") for end in ends]


def day_of(index: int) -> int:
    """Which day, counted from the start, the period of a record ends in."""
    return (2 * (index + 1) - 1) // 24


def daily(name: str, day: int, weekend: float) -> float:
    """How busy a container is on a day: it drifts, now and then it spikes, and at
    the weekend it does what it does at the weekend."""
    generator = random.Random(f"{name}:day:{day}")
    factor = 0.65 + 0.7 * generator.random()
    if generator.random() < 0.1:
        factor *= 1.8
    if (START + timedelta(days=day)).weekday() >= 5:
        factor *= weekend
    return factor


def rhythm(index: int) -> float:
    """More work in the day than in the night, the same every day."""
    hour = (2 * (index + 1)) % 24
    return 1 + 0.45 * math.sin((hour - 9) / 24 * 2 * math.pi)


def reshape_container_stats(body: Json) -> None:
    template = body["items"][0]
    items: list[Json] = []
    for index, created in enumerate(periods()):
        stats: list[Json] = []
        for name, (cpu, memory, weekend) in CONTAINERS.items():
            busy = daily(name, day_of(index), weekend)
            stat = {"n": name, "c": 0.0, "m": 0.0}
            stat["c"] = round(cpu * busy * rhythm(index) * jitter(name, index, 0.15), 3)
            # memory follows the work, but a good deal less
            stat["m"] = round(
                memory * (0.85 + 0.15 * busy) * jitter(name, index, 0.03), 1
            )
            stats.append(stat)
        items.append({**template, "created": created, "type": "120m", "stats": stats})

    body["items"] = items
    body["totalItems"] = len(items)
    body["totalPages"] = 1


def reshape_system_stats(body: Json) -> None:
    template = body["items"][0]
    items: list[Json] = []
    for index, created in enumerate(periods()):
        stats = {**template["stats"], "m": MEMORY_GIB, "mu": round(MEMORY_GIB * 0.7, 2)}
        stats["cpu"] = round(50 * rhythm(index), 2)
        items.append({**template, "created": created, "type": "120m", "stats": stats})

    body["items"] = items
    body["totalItems"] = len(items)
    body["totalPages"] = 1


def main() -> None:
    cassette = cast(Json, yaml.safe_load(SOURCE.read_text()))

    for interaction in cassette["interactions"]:
        uri = cast(str, interaction["request"]["uri"])
        holder = interaction["response"]["body"]
        body = cast(Json, json.loads(holder["string"]))

        if "containers/records" in uri:
            reshape_containers(body)
        elif "container_stats/records" in uri:
            reshape_container_stats(body)
        elif "system_stats/records" in uri:
            reshape_system_stats(body)
        else:
            continue

        holder["string"] = json.dumps(body, separators=(",", ":"))

    _ = TARGET.write_text(yaml.safe_dump(cassette, sort_keys=False, width=10**9))
    print(f"{TARGET.relative_to(ROOT)}: {TARGET.stat().st_size // 1024} KiB")


if __name__ == "__main__":
    main()
