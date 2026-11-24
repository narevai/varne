from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class HostedApp:
    """A service that is paid for by the month, and that a self-hosted application
    can stand in for."""

    id: str
    name: str
    # The plan the price is of: the most popular one, for one seat.
    plan: str
    usd_per_month: Decimal
    # Where the price was read, and what is good to know about it.
    source: str
    note: str = ""
    # Name of the logo in `ui/static/icons`, if there is one.
    icon: str | None = None
    # A logo drawn in black only, which is shown light on the dark theme.
    mono: bool = False

    @property
    def label(self) -> str:
        return f"{self.name} {self.plan}".strip()


# Prices checked on 2026-11-20 on the pages given as their source.
HOSTED: tuple[HostedApp, ...] = (
    HostedApp(
        id="adobe-acrobat-pro",
        name="Adobe Acrobat",
        plan="Pro",
        usd_per_month=Decimal("19.99"),
        source="https://www.adobe.com/acrobat/pricing.html?country=US",
        note="annual billed monthly",
        icon="adobe",
    ),
    HostedApp(
        id="audible-premium-plus",
        name="Audible",
        plan="Premium Plus",
        usd_per_month=Decimal("14.95"),
        source="https://www.audible.com/ep/faq",
        icon="audible",
    ),
    HostedApp(
        id="backblaze-personal-backup",
        name="Backblaze",
        plan="Personal Backup",
        usd_per_month=Decimal("9"),
        source="https://www.backblaze.com/cloud-backup/personal/pricing",
        icon="backblaze",
    ),
    HostedApp(
        id="changedetection-io-hosted",
        name="changedetection.io",
        plan="hosted",
        usd_per_month=Decimal("8.99"),
        source="https://changedetection.io/",
        icon="changedetection",
    ),
    HostedApp(
        id="chatgpt-plus",
        name="ChatGPT",
        plan="Plus",
        usd_per_month=Decimal("20"),
        source="https://help.openai.com/en/articles/6950777",
        icon="chatgpt",
    ),
    HostedApp(
        id="datadog-infrastructure-pro",
        name="Datadog",
        plan="Infrastructure Pro",
        usd_per_month=Decimal("18"),
        source="https://www.datadoghq.com/pricing/list/",
        note="per host, billed monthly",
        icon="datadog",
    ),
    HostedApp(
        id="dropbox-plus",
        name="Dropbox",
        plan="Plus",
        usd_per_month=Decimal("9.99"),
        source="https://www.dropbox.com/plans",
        icon="dropbox",
    ),
    HostedApp(
        id="elastic-cloud-standard",
        name="Elastic Cloud",
        plan="Standard",
        usd_per_month=Decimal("99"),
        source="https://www.elastic.co/pricing/cloud-hosted",
        note="from",
        icon="elastic",
    ),
    HostedApp(
        id="google-workspace-business-starter",
        name="Google Workspace",
        plan="Business Starter",
        usd_per_month=Decimal("7"),
        source="https://workspace.google.com/pricing",
        note="annual plan",
        icon="google",
    ),
    HostedApp(
        id="grafana-cloud-pro",
        name="Grafana Cloud",
        plan="Pro",
        usd_per_month=Decimal("19"),
        source="https://grafana.com/pricing/",
        note="base price",
        icon="grafana",
    ),
    HostedApp(
        id="healthchecks-io-business",
        name="Healthchecks.io",
        plan="Business",
        usd_per_month=Decimal("20"),
        source="https://healthchecks.io/pricing/",
        icon="healthchecks",
    ),
    HostedApp(
        id="icloud-2-tb",
        name="iCloud+",
        plan="2 TB",
        usd_per_month=Decimal("9.99"),
        source="https://support.apple.com/en-us/108047",
        icon="icloud",
    ),
    HostedApp(
        id="inoreader-pro",
        name="Inoreader",
        plan="Pro",
        usd_per_month=Decimal("9.99"),
        source="https://www.inoreader.com/pricing",
        note="billed monthly",
        icon="inoreader",
    ),
    HostedApp(
        id="kagi-professional",
        name="Kagi",
        plan="Professional",
        usd_per_month=Decimal("10"),
        source="https://kagi.com/pricing",
        icon="kagi",
    ),
    HostedApp(
        id="kindle-unlimited",
        name="Kindle",
        plan="Unlimited",
        usd_per_month=Decimal("11.99"),
        source="https://www.engadget.com/2193475/kindle-unlimited-cheaper-pay-less/",
    ),
    HostedApp(
        id="minecraft-realms-plus",
        name="Minecraft Realms",
        plan="Plus",
        usd_per_month=Decimal("7.99"),
        source="https://www.minecraft.net/realms",
        icon="minecraft",
    ),
    HostedApp(
        id="nextdns-pro",
        name="NextDNS",
        plan="Pro",
        usd_per_month=Decimal("1.99"),
        source="https://nextdns.io/pricing",
        icon="nextdns",
    ),
    HostedApp(
        id="notion-plus",
        name="Notion",
        plan="Plus",
        usd_per_month=Decimal("10"),
        source="https://www.notion.com/pricing",
        note="per member",
        icon="notion",
    ),
    HostedApp(
        id="slack-pro",
        name="Slack",
        plan="Pro",
        usd_per_month=Decimal("8.75"),
        source="https://slack.com/pricing/pro",
        note="billed monthly",
        icon="slack",
    ),
    HostedApp(
        id="splitwise-pro",
        name="Splitwise",
        plan="Pro",
        usd_per_month=Decimal("4.99"),
        source="https://www.moneycrashers.com/splitwise-review/",
    ),
    HostedApp(
        id="tailscale-standard",
        name="Tailscale",
        plan="Standard",
        usd_per_month=Decimal("8"),
        source="https://tailscale.com/pricing",
        icon="tailscale",
        mono=True,
    ),
    HostedApp(
        id="vercel-pro",
        name="Vercel",
        plan="Pro",
        usd_per_month=Decimal("20"),
        source="https://vercel.com/pricing",
        note="per user",
        icon="vercel",
        mono=True,
    ),
    HostedApp(
        id="ynab",
        name="YNAB",
        plan="",
        usd_per_month=Decimal("14.99"),
        source="https://www.ynab.com/pricing",
        note="billed monthly",
        icon="ynab",
    ),
    HostedApp(
        id="youtube-premium",
        name="YouTube",
        plan="Premium",
        usd_per_month=Decimal("15.99"),
        source="https://techcrunch.com/2026/04/10/youtube-premium-youtube-music-subscription-price-increase/",
        icon="youtube",
    ),
    HostedApp(
        id="zapier-professional",
        name="Zapier",
        plan="Professional",
        usd_per_month=Decimal("19.99"),
        source="https://zapier.com/pricing",
        note="billed annually",
        icon="zapier",
    ),
)

HOSTED_BY_ID: dict[str, HostedApp] = {app.id: app for app in HOSTED}
