from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class App:
    """A self-hosted application and the subscription it stands in for."""

    name: str
    # Names the images of the application go by, see `image_names`.
    slugs: tuple[str, ...]
    alternative: str
    # Most popular plan, one seat, USD per month.
    usd_per_month: Decimal
    # Name of the logo in `ui/static/icons`, if there is one.
    icon: str | None = None


# Prices checked on 2026-11-20 on the pricing pages given next to them.
APPS: tuple[App, ...] = (
    App(
        "Immich",
        ("immich", "immich-server", "immich-machine-learning"),
        "iCloud+ 2 TB",
        Decimal("9.99"),  # https://support.apple.com/en-us/108047
        "immich",
    ),
    App(
        "Open WebUI",
        ("open-webui",),
        "ChatGPT Plus",
        Decimal("20"),  # https://help.openai.com/en/articles/6950777
        "open-webui",
    ),
    App(
        "Audiobookshelf",
        ("audiobookshelf",),
        "Audible Premium Plus",
        Decimal("14.95"),  # https://www.audible.com/ep/faq
        "audiobookshelf",
    ),
    App(
        "Syncthing",
        ("syncthing",),
        "Dropbox Plus",
        Decimal("9.99"),  # https://www.dropbox.com/plans
        "syncthing",
    ),
    App(
        "NetBird",
        ("netbird",),
        "Tailscale Standard",
        Decimal("8"),  # https://tailscale.com/pricing
        "netbird",
    ),
    App(
        "SearXNG",
        ("searxng",),
        "Kagi Professional",
        Decimal("10"),  # https://kagi.com/pricing
        "searxng",
    ),
    App(
        "Healthchecks",
        ("healthchecks",),
        "Healthchecks.io Business",
        Decimal("20"),  # https://healthchecks.io/pricing/
        "healthchecks",
    ),
    App(
        "PhotoPrism",
        ("photoprism",),
        "iCloud+ 2 TB",
        Decimal("9.99"),  # https://support.apple.com/en-us/108047
        "photoprism",
    ),
    App(
        "AnythingLLM",
        ("anything-llm",),
        "ChatGPT Plus",
        Decimal("20"),  # https://help.openai.com/en/articles/6950777
        "anything-llm",
    ),
    App(
        "WG Easy",
        ("wg-easy",),
        "Tailscale Standard",
        Decimal("8"),  # https://tailscale.com/pricing
        "wireguard",
    ),
    App(
        "Calibre-Web",
        ("calibre", "calibre-web", "calibre-web-automated"),
        "Kindle Unlimited",
        Decimal(
            "11.99"
        ),  # https://www.engadget.com/2193475/kindle-unlimited-cheaper-pay-less/
        "calibre-web",
    ),
    App(
        "Stirling PDF",
        ("stirling-pdf",),
        "Adobe Acrobat Pro",
        Decimal(
            "19.99"
        ),  # https://www.adobe.com/acrobat/pricing.html?country=US, annual billed monthly
        "stirling-pdf",
    ),
    App(
        "Duplicati",
        ("duplicati",),
        "Backblaze Personal Backup",
        Decimal("9"),  # https://www.backblaze.com/cloud-backup/personal/pricing
        "duplicati",
    ),
    App(
        "Pi-hole",
        ("pihole",),
        "NextDNS Pro",
        Decimal("1.99"),  # https://nextdns.io/pricing
        "pi-hole",
    ),
    App(
        "Stalwart",
        ("stalwart",),
        "Google Workspace Business Starter",
        Decimal("7"),  # https://workspace.google.com/pricing, annual plan
        "stalwart",
    ),
    App(
        "Matrix (Element)",
        ("element-web", "continuwuity"),
        "Slack Pro",
        Decimal("8.75"),  # https://slack.com/pricing/pro, billed monthly
        "element",
    ),
    App(
        "changedetection.io",
        ("changedetection.io",),
        "changedetection.io hosted",
        Decimal("8.99"),  # https://changedetection.io/
        "changedetection",
    ),
    App(
        "Grafana",
        ("grafana",),
        "Grafana Cloud Pro",
        Decimal("19"),  # https://grafana.com/pricing/, base price
        "grafana",
    ),
    App(
        "Actual Budget",
        ("actual-server", "actualbudget", "actual-budget"),
        "YNAB",
        Decimal("14.99"),  # https://www.ynab.com/pricing, billed monthly
        "actual-budget",
    ),
    App(
        "Byb Budget",
        ("byb-budget",),
        "YNAB",
        Decimal("14.99"),  # https://www.ynab.com/pricing, billed monthly
    ),
    App(
        "Splitpro",
        ("splitpro",),
        "Splitwise Pro",
        Decimal("4.99"),  # https://www.moneycrashers.com/splitwise-review/
    ),
    App(
        "Beszel",
        ("beszel", "beszel-agent"),
        "Datadog Infrastructure Pro",
        Decimal(
            "18"
        ),  # https://www.datadoghq.com/pricing/list/, per host, billed monthly
        "beszel",
    ),
    App(
        "Glances",
        ("glances",),
        "Datadog Infrastructure Pro",
        Decimal(
            "18"
        ),  # https://www.datadoghq.com/pricing/list/, per host, billed monthly
        "glances",
    ),
    App(
        "Elasticsearch",
        ("elasticsearch",),
        "Elastic Cloud Standard",
        Decimal("99"),  # https://www.elastic.co/pricing/cloud-hosted, from
        "elasticsearch",
    ),
    App(
        "Invidious",
        ("invidious", "invidious-companion"),
        "YouTube Premium",
        Decimal(
            "15.99"
        ),  # https://techcrunch.com/2026/04/10/youtube-premium-youtube-music-subscription-price-increase/
        "invidious",
    ),
    App(
        "Minecraft Server",
        ("minecraft", "minecraft-server", "minecraft-bedrock-server"),
        "Minecraft Realms Plus",
        Decimal("7.99"),  # https://www.minecraft.net/realms
        "minecraft",
    ),
    App(
        "Trilium",
        ("trilium", "triliumnext"),
        "Notion Plus",
        Decimal("10"),  # https://www.notion.com/pricing, per member
        "trilium",
    ),
    App(
        "Logseq",
        ("logseq", "logseq-webapp"),
        "Notion Plus",
        Decimal("10"),  # https://www.notion.com/pricing, per member
        "logseq",
    ),
    App(
        "FreshRSS",
        ("freshrss",),
        "Inoreader Pro",
        Decimal("9.99"),  # https://www.inoreader.com/pricing, billed monthly
        "freshrss",
    ),
    App(
        "Copyparty",
        ("copyparty", "copyparty-ac"),
        "Dropbox Plus",
        Decimal("9.99"),  # https://www.dropbox.com/plans
        "copyparty",
    ),
    App(
        "BentoPDF",
        ("bentopdf", "bentopdf-simple"),
        "Adobe Acrobat Pro",
        Decimal(
            "19.99"
        ),  # https://www.adobe.com/acrobat/pricing.html?country=US, annual billed monthly
        "bentopdf",
    ),
    App(
        "Technitium DNS",
        ("technitium",),
        "NextDNS Pro",
        Decimal("1.99"),  # https://nextdns.io/pricing
        "technitium",
    ),
    App(
        "Node-RED",
        ("node-red", "nodered"),
        "Zapier Professional",
        Decimal("19.99"),  # https://zapier.com/pricing, billed annually
        "node-red",
    ),
    App(
        "Windmill",
        ("windmill", "windmill-lsp"),
        "Zapier Professional",
        Decimal("19.99"),  # https://zapier.com/pricing, billed annually
        "windmill",
    ),
    App(
        "Coolify",
        ("coolify", "coolify-realtime"),
        "Vercel Pro",
        Decimal("20"),  # https://vercel.com/pricing, per user
        "coolify",
    ),
    App(
        "Ollama",
        ("ollama",),
        "ChatGPT Plus",
        Decimal("20"),  # https://help.openai.com/en/articles/6950777
        "ollama",
    ),
    App(
        "LocalAI",
        ("local-ai", "localai"),
        "ChatGPT Plus",
        Decimal("20"),  # https://help.openai.com/en/articles/6950777
        "localai",
    ),
    App(
        "cAdvisor",
        ("cadvisor",),
        "Datadog Infrastructure Pro",
        Decimal(
            "18"
        ),  # https://www.datadoghq.com/pricing/list/, per host, billed monthly
        "cadvisor",
    ),
    App(
        "Checkmk",
        ("check-mk-raw", "checkmk"),
        "Datadog Infrastructure Pro",
        Decimal(
            "18"
        ),  # https://www.datadoghq.com/pricing/list/, per host, billed monthly
        "checkmk",
    ),
    App(
        "Zerobyte",
        ("zerobyte",),
        "Backblaze Personal Backup",
        Decimal("9"),  # https://www.backblaze.com/cloud-backup/personal/pricing
        "zerobyte",
    ),
)
