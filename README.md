# Varne

[![GitHub last commit](https://img.shields.io/github/last-commit/narevai/varne)](https://github.com/narevai/varne/commits)
[![Latest tag](https://img.shields.io/github/v/tag/narevai/varne?label=latest)](https://github.com/narevai/varne/tags)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)

## Devlog
| YouTube                                                          | PR                                                |
| ---------------------------------------------------------------- | ------------------------------------------------- |
| [Cassette Replay for Vercel](https://youtu.be/QZhYUPvFr_c)       | [#222](https://github.com/narevai/varne/pull/222) |
| [ConfigManager](https://youtu.be/qYlT9Y-A7Lg)                    | [#219](https://github.com/narevai/varne/pull/219) |
| [Stronger typing part 2](https://youtube.com/live/uE0IJrpH270)   | [#217](https://github.com/narevai/varne/pull/217) |
| [Stronger typing part 1](https://youtube.com/live/Zfq7MEACyYA).  | [#217](https://github.com/narevai/varne/pull/217) |
| [Data pipeline](https://youtu.be/KRvkaM2O2ho)                    | [#212](https://github.com/narevai/varne/pull/212) |
| [Basic UI 2](https://www.youtube.com/watch?v=ZE-k7V4Ymk8)        | [#208](https://github.com/narevai/varne/pull/208) |
| [Basic UI 1](https://youtube.com/live/50ahIxMfuJU?feature=share) | [#207](https://github.com/narevai/varne/pull/207) |
| [Intro and plans for V1](https://youtube.com/live/obq8IIN0epY)   | N/A                                               |

## Documentation

Read the [Varne v1 documentation](https://www.narev.ai/docs/varne/v1/index). Its source is in [`docs/`](./docs). The [narevai/docs](https://github.com/narevai/docs) repository imports it with `node scripts/pull-varne-v1.js`.

## Run

```bash
docker run -d \
  --name varne \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config:/app/config \
  ghcr.io/narevai/varne:latest
```

Open http://localhost:8000.

## Docker Compose

```yaml
services:
  varne:
    image: ghcr.io/narevai/varne:latest
    container_name: varne
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    restart: unless-stopped
```

```bash
docker compose up -d
```

Open http://localhost:8000.

## Telemetry

When Varne starts, it sends one anonymous event to [Umami](https://umami.is): the Varne version, the environment, whether it is a demo, and a random instance id. It sends nothing about your stacks, your sources, your costs, or your keys. As with any request, Umami sees the server's IP address. It is skipped in development.

Turn it off with `ENABLE_TELEMETRY=false`.

## Demo mode

`DEMO_MODE=true` runs a sample stack on a database and a configuration of its own (`demo.duckdb` and `demo.yaml` next to yours), filled in with made up data once the app is up. Nothing of yours is touched, its configuration cannot be changed, and every start puts the demo back as it was.

```bash
docker run -p 8000:8000 -e DEMO_MODE=true ghcr.io/narevai/varne:nightly
```

## License

GNU Affero General Public License v3.0. See [LICENSE](./LICENSE).
