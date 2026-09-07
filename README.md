# Varne

[![GitHub last commit](https://img.shields.io/github/last-commit/narevai/varne)](https://github.com/narevai/varne/commits)
[![Latest tag](https://img.shields.io/github/v/tag/narevai/varne?label=latest)](https://github.com/narevai/varne/tags)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)

## Devlog
| YouTube                                                          | PR                                                |
| ---------------------------------------------------------------- | ------------------------------------------------- |
| [Intro and plans for V1](https://youtube.com/live/obq8IIN0epY)   | N/A                                               |
| [Basic UI 1](https://youtube.com/live/50ahIxMfuJU?feature=share) | [#207](https://github.com/narevai/varne/pull/207) |
| [Basic UI 2](https://www.youtube.com/watch?v=ZE-k7V4Ymk8)        | [#208](https://github.com/narevai/varne/pull/208) |
| [Data pipeline](https://youtu.be/KRvkaM2O2ho)                    | [#212](https://github.com/narevai/varne/pull/212) |

## Run

```bash
docker run -d \
  --name varne \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
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
    restart: unless-stopped
```

```bash
docker compose up -d
```

Open http://localhost:8000.

## License

GNU Affero General Public License v3.0. See [LICENSE](./LICENSE).
