import logging
from decimal import Decimal

import requests
from celery import shared_task
from django.conf import settings

from .models import MonitoredToken, PriceSnapshot

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def fetch_prices(self) -> dict:
    tokens = list(MonitoredToken.objects.filter(is_active=True))
    if not tokens:
        logger.warning("No active tokens to fetch")
        return {"fetched": 0}

    ids = ",".join(t.coingecko_id for t in tokens)
    url = f"{settings.COINGECKO_API_URL}/simple/price"
    params = {"ids": ids, "vs_currencies": "usd"}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as exc:
        logger.error("CoinGecko fetch failed: %s", exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries * 30)

    data = response.json()
    snapshots = []
    for token in tokens:
        token_data = data.get(token.coingecko_id, {})
        price = token_data.get("usd")
        if price is None:
            logger.warning("No price for %s (%s)", token.symbol, token.coingecko_id)
            continue
        snapshots.append(
            PriceSnapshot(
                symbol=token.symbol,
                price_usd=Decimal(str(price)),
                source="coingecko",
            )
        )

    PriceSnapshot.objects.bulk_create(snapshots)
    logger.info("Saved %d price snapshots", len(snapshots))
    return {"fetched": len(snapshots)}
