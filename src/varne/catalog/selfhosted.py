from dataclasses import dataclass


@dataclass(frozen=True)
class SelfHostedApp:
    """An application that is run oneself, and the images it is run from."""

    name: str
    # Names the images of the application go by, see `image_names`.
    slugs: tuple[str, ...]
    # Name of the logo in `ui/static/icons`, if there is one.
    icon: str | None = None


SELF_HOSTED: tuple[SelfHostedApp, ...] = (
    SelfHostedApp(
        "Immich", ("immich", "immich-server", "immich-machine-learning"), "immich"
    ),
    SelfHostedApp("Open WebUI", ("open-webui",), "open-webui"),
    SelfHostedApp("Audiobookshelf", ("audiobookshelf",), "audiobookshelf"),
    SelfHostedApp("Syncthing", ("syncthing",), "syncthing"),
    SelfHostedApp("NetBird", ("netbird",), "netbird"),
    SelfHostedApp("SearXNG", ("searxng",), "searxng"),
    SelfHostedApp("Healthchecks", ("healthchecks",), "healthchecks"),
    SelfHostedApp("PhotoPrism", ("photoprism",), "photoprism"),
    SelfHostedApp("AnythingLLM", ("anything-llm",), "anything-llm"),
    SelfHostedApp("WG Easy", ("wg-easy",), "wireguard"),
    SelfHostedApp(
        "Calibre-Web",
        ("calibre", "calibre-web", "calibre-web-automated"),
        "calibre-web",
    ),
    SelfHostedApp("Stirling PDF", ("stirling-pdf",), "stirling-pdf"),
    SelfHostedApp("Duplicati", ("duplicati",), "duplicati"),
    SelfHostedApp("Pi-hole", ("pihole",), "pi-hole"),
    SelfHostedApp("Stalwart", ("stalwart",), "stalwart"),
    SelfHostedApp("Matrix (Element)", ("element-web", "continuwuity"), "element"),
    SelfHostedApp("changedetection.io", ("changedetection.io",), "changedetection"),
    SelfHostedApp("Grafana", ("grafana",), "grafana"),
    SelfHostedApp(
        "Actual Budget",
        ("actual-server", "actualbudget", "actual-budget"),
        "actual-budget",
    ),
    SelfHostedApp("Byb Budget", ("byb-budget",)),
    SelfHostedApp("Splitpro", ("splitpro",)),
    SelfHostedApp("Beszel", ("beszel", "beszel-agent"), "beszel"),
    SelfHostedApp("Glances", ("glances",), "glances"),
    SelfHostedApp("Elasticsearch", ("elasticsearch",), "elasticsearch"),
    SelfHostedApp("Invidious", ("invidious", "invidious-companion"), "invidious"),
    SelfHostedApp(
        "Minecraft Server",
        ("minecraft", "minecraft-server", "minecraft-bedrock-server"),
        "minecraft",
    ),
    SelfHostedApp("Trilium", ("trilium", "triliumnext"), "trilium"),
    SelfHostedApp("Logseq", ("logseq", "logseq-webapp"), "logseq"),
    SelfHostedApp("FreshRSS", ("freshrss",), "freshrss"),
    SelfHostedApp("Copyparty", ("copyparty", "copyparty-ac"), "copyparty"),
    SelfHostedApp("BentoPDF", ("bentopdf", "bentopdf-simple"), "bentopdf"),
    SelfHostedApp("Technitium DNS", ("technitium",), "technitium"),
    SelfHostedApp("Node-RED", ("node-red", "nodered"), "node-red"),
    SelfHostedApp("Windmill", ("windmill", "windmill-lsp"), "windmill"),
    SelfHostedApp("Coolify", ("coolify", "coolify-realtime"), "coolify"),
    SelfHostedApp("Ollama", ("ollama",), "ollama"),
    SelfHostedApp("LocalAI", ("local-ai", "localai"), "localai"),
    SelfHostedApp("cAdvisor", ("cadvisor",), "cadvisor"),
    SelfHostedApp("Home Assistant", ("home-assistant",), "home-assistant"),
    SelfHostedApp("n8n", ("n8n",), "n8n"),
    SelfHostedApp("Uptime Kuma", ("uptime-kuma", "autokuma"), "uptime-kuma"),
    SelfHostedApp("Prometheus", ("prometheus",), "prometheus"),
    SelfHostedApp("Filebrowser", ("filebrowser",), "filebrowser"),
    SelfHostedApp("Frigate", ("frigate",), "frigate"),
    SelfHostedApp("MinIO", ("minio",), "minio"),
    SelfHostedApp("ntfy", ("ntfy", "ntfy2telegram"), "ntfy"),
    SelfHostedApp("PostgreSQL", ("postgres", "postgresql"), "postgres"),
    SelfHostedApp("Redis", ("redis",), "redis"),
    SelfHostedApp("Valkey", ("valkey",), "valkey"),
    SelfHostedApp(
        "Calibre-Web Automated Book Downloader",
        ("calibre-web-automated-book-downloader",),
        "calibre-web",
    ),
    SelfHostedApp("Radarr", ("radarr",), "radarr"),
    SelfHostedApp("Sonarr", ("sonarr",), "sonarr"),
    SelfHostedApp("Bazarr", ("bazarr",), "bazarr"),
    SelfHostedApp("Prowlarr", ("prowlarr",), "prowlarr"),
    SelfHostedApp("Seerr", ("seerr",), "seerr"),
    SelfHostedApp("qBittorrent", ("qbittorrent",), "qbittorrent"),
    SelfHostedApp("Checkmk", ("check-mk-raw", "checkmk"), "checkmk"),
    SelfHostedApp("Zerobyte", ("zerobyte",), "zerobyte"),
)
