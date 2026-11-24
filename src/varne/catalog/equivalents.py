from varne.catalog.hosted import HOSTED_BY_ID, HostedApp
from varne.catalog.selfhosted import SelfHostedApp

# The hosted service that a self-hosted application stands in for, by the name of the
# application and the id of the service. Several applications can stand in for one
# service, and an application without one is simply not compared.
EQUIVALENTS: dict[str, str] = {
    "Immich": "icloud-2-tb",
    "Open WebUI": "chatgpt-plus",
    "Audiobookshelf": "audible-premium-plus",
    "Syncthing": "dropbox-plus",
    "NetBird": "tailscale-standard",
    "SearXNG": "kagi-professional",
    "Healthchecks": "healthchecks-io-business",
    "PhotoPrism": "icloud-2-tb",
    "AnythingLLM": "chatgpt-plus",
    "WG Easy": "tailscale-standard",
    "Calibre-Web": "kindle-unlimited",
    "Stirling PDF": "adobe-acrobat-pro",
    "Duplicati": "backblaze-personal-backup",
    "Pi-hole": "nextdns-pro",
    "Stalwart": "google-workspace-business-starter",
    "Matrix (Element)": "slack-pro",
    "changedetection.io": "changedetection-io-hosted",
    "Grafana": "grafana-cloud-pro",
    "Actual Budget": "ynab",
    "Byb Budget": "ynab",
    "Splitpro": "splitwise-pro",
    "Beszel": "datadog-infrastructure-pro",
    "Glances": "datadog-infrastructure-pro",
    "Elasticsearch": "elastic-cloud-standard",
    "Invidious": "youtube-premium",
    "Minecraft Server": "minecraft-realms-plus",
    "Trilium": "notion-plus",
    "Logseq": "notion-plus",
    "FreshRSS": "inoreader-pro",
    "Copyparty": "dropbox-plus",
    "BentoPDF": "adobe-acrobat-pro",
    "Technitium DNS": "nextdns-pro",
    "Node-RED": "zapier-professional",
    "Windmill": "zapier-professional",
    "Coolify": "vercel-pro",
    "Ollama": "chatgpt-plus",
    "LocalAI": "chatgpt-plus",
    "cAdvisor": "datadog-infrastructure-pro",
    "Checkmk": "datadog-infrastructure-pro",
    "Zerobyte": "backblaze-personal-backup",
}


def equivalent_of(app: SelfHostedApp) -> HostedApp | None:
    """The hosted service the application stands in for, if it has one."""
    hosted_id = EQUIVALENTS.get(app.name)
    return None if hosted_id is None else HOSTED_BY_ID[hosted_id]
