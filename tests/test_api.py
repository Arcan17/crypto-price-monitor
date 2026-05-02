from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from monitor.models import MonitoredToken, PriceSnapshot


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
def test_health_returns_200(client):
    response = client.get("/api/health/")
    assert response.status_code == 200
    assert response.data["status"] == "ok"
    assert "workers_online" in response.data


@pytest.mark.django_db
def test_health_workers_online_field_is_bool(client):
    response = client.get("/api/health/")
    assert isinstance(response.data["workers_online"], bool)


@pytest.mark.django_db
def test_prices_returns_paginated(client, btc_snapshots):
    response = client.get("/api/prices/")
    assert response.status_code == 200
    assert "results" in response.data
    assert "count" in response.data
    assert response.data["count"] == 3


@pytest.mark.django_db
def test_prices_filter_by_symbol(client, btc_token, eth_token):
    PriceSnapshot.objects.create(symbol="BTC", price_usd="60000")
    PriceSnapshot.objects.create(symbol="ETH", price_usd="3000")
    PriceSnapshot.objects.create(symbol="ETH", price_usd="3100")

    response = client.get("/api/prices/?symbol=BTC")
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["symbol"] == "BTC"


@pytest.mark.django_db
def test_prices_filter_symbol_case_insensitive(client, btc_token):
    PriceSnapshot.objects.create(symbol="BTC", price_usd="60000")

    response = client.get("/api/prices/?symbol=btc")
    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_prices_latest_first(client, btc_token):
    PriceSnapshot.objects.create(symbol="BTC", price_usd="59000")
    PriceSnapshot.objects.create(symbol="BTC", price_usd="61000")

    response = client.get("/api/prices/?symbol=BTC")
    prices = [r["price_usd"] for r in response.data["results"]]
    assert prices[0] == "61000.00000000"


@pytest.mark.django_db
def test_prices_fields(client, btc_token):
    PriceSnapshot.objects.create(symbol="BTC", price_usd="60000")
    response = client.get("/api/prices/")
    result = response.data["results"][0]
    assert set(result.keys()) == {"id", "symbol", "price_usd", "fetched_at"}


@pytest.mark.django_db
def test_stats_has_high_low_avg(client, btc_token):
    PriceSnapshot.objects.create(symbol="BTC", price_usd="59000")
    PriceSnapshot.objects.create(symbol="BTC", price_usd="60000")
    PriceSnapshot.objects.create(symbol="BTC", price_usd="61000")

    response = client.get("/api/stats/")
    assert response.status_code == 200

    btc_stats = next(s for s in response.data if s["symbol"] == "BTC")
    assert btc_stats["high_24h"] is not None
    assert btc_stats["low_24h"] is not None
    assert btc_stats["avg_24h"] is not None
    assert btc_stats["snapshot_count_24h"] == 3


@pytest.mark.django_db
def test_stats_correct_values(client, btc_token):
    PriceSnapshot.objects.create(symbol="BTC", price_usd="59000")
    PriceSnapshot.objects.create(symbol="BTC", price_usd="61000")

    response = client.get("/api/stats/")
    btc_stats = next(s for s in response.data if s["symbol"] == "BTC")

    assert Decimal(btc_stats["high_24h"]) == Decimal("61000")
    assert Decimal(btc_stats["low_24h"]) == Decimal("59000")
    assert Decimal(btc_stats["avg_24h"]) == Decimal("60000")


@pytest.mark.django_db
def test_stats_empty_no_snapshots(client, btc_token):
    response = client.get("/api/stats/")
    assert response.status_code == 200
    btc_stats = next(s for s in response.data if s["symbol"] == "BTC")
    assert btc_stats["high_24h"] is None
    assert btc_stats["snapshot_count_24h"] == 0


@pytest.mark.django_db
def test_tokens_lists_active(client, all_tokens):
    response = client.get("/api/tokens/")
    assert response.status_code == 200
    assert len(response.data) == 3
    symbols = {t["symbol"] for t in response.data}
    assert symbols == {"BTC", "ETH", "USDC"}


@pytest.mark.django_db
def test_tokens_fields(client, btc_token):
    response = client.get("/api/tokens/")
    token = response.data[0]
    assert set(token.keys()) == {"symbol", "coingecko_id", "is_active"}


@pytest.mark.django_db
def test_tokens_includes_inactive(client, db):
    MonitoredToken.objects.create(symbol="BTC", coingecko_id="bitcoin", is_active=True)
    MonitoredToken.objects.create(symbol="DOGE", coingecko_id="dogecoin", is_active=False)

    response = client.get("/api/tokens/")
    assert response.status_code == 200
    assert len(response.data) == 2
