"""A sample stack to look around in, on a database and a configuration of its own.

The Docker host in it is made up, see `usage.py`, so the demo needs no machine and no
network. Its days are the last ten, up to now.
"""

DEMO_STACK_ID = "demo"
# The memory of the made up machine, in GiB. It is small, so that what the containers
# use is most of it and only a third of the cost is idle.
MEMORY_GIB = 14
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
          url: http://demo-hub:8090
          email: demo@example.com
          password: demo
        lookback_days: 10
"""
