from django.core.management.base import BaseCommand

from monitor.models import MonitoredToken

TOKENS = [
    {"symbol": "BTC", "coingecko_id": "bitcoin"},
    {"symbol": "ETH", "coingecko_id": "ethereum"},
    {"symbol": "USDC", "coingecko_id": "usd-coin"},
]


class Command(BaseCommand):
    help = "Seed default monitored tokens"

    def handle(self, *args: object, **options: object) -> None:
        for token_data in TOKENS:
            obj, created = MonitoredToken.objects.get_or_create(
                symbol=token_data["symbol"],
                defaults={"coingecko_id": token_data["coingecko_id"]},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created {obj.symbol}"))
            else:
                self.stdout.write(f"Already exists: {obj.symbol}")
