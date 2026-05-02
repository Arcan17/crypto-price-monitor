import pytest

from monitor.models import MonitoredToken, PriceSnapshot


@pytest.fixture
def btc_token(db):
    return MonitoredToken.objects.create(symbol="BTC", coingecko_id="bitcoin", is_active=True)


@pytest.fixture
def eth_token(db):
    return MonitoredToken.objects.create(symbol="ETH", coingecko_id="ethereum", is_active=True)


@pytest.fixture
def usdc_token(db):
    return MonitoredToken.objects.create(symbol="USDC", coingecko_id="usd-coin", is_active=True)


@pytest.fixture
def all_tokens(btc_token, eth_token, usdc_token):
    return [btc_token, eth_token, usdc_token]


@pytest.fixture
def btc_snapshots(db, btc_token):
    snapshots = []
    for price in ["60000.00", "61000.00", "59000.00"]:
        snapshots.append(PriceSnapshot.objects.create(symbol="BTC", price_usd=price))
    return snapshots


@pytest.fixture
def coingecko_response():
    return {
        "bitcoin": {"usd": 60000.0},
        "ethereum": {"usd": 3000.0},
        "usd-coin": {"usd": 1.0},
    }
