"""A sample stack to look around in, on a database and a configuration of its own.

The hub it reads is a recording of a real Beszel hub, played back, so the demo needs
no machine and no network. The recording ends at `DEMO_NOW`, and so does the clock
of the demo, or its days would be empty.
"""

from datetime import UTC, datetime
from pathlib import Path

DEMO_NOW = datetime(2026, 11, 20, 15, tzinfo=UTC)
DEMO_CASSETTE = Path(__file__).with_name("beszel_hub.yaml")
DEMO_STACK_ID = "demo"
DEMO_CONFIG = """\
stacks:
  - id: demo
    name: Demo homelab
    sources:
      - id: homelab
        name: Homelab
        type: docker
        cost:
          machine_cost: 1200
          amortization_years: 6
          power_draw_watts: 40
          electricity_price_per_kwh: 0.2
        usage:
          type: beszel
          url: http://compose-lab:8090
          email: me@example.com
          password: secret
        lookback_days: 10
"""
