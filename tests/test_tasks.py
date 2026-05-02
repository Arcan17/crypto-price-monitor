from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
import requests

from monitor.models import PriceSnapshot
from monitor.tasks import fetch_prices


@pytest.mark.django_db
def test_fetch_prices_creates_snapshots(all_tokens, coingecko_response):
    with patch("monitor.tasks.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = coingecko_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = fetch_prices()

    assert result["fetched"] == 3
    assert PriceSnapshot.objects.count() == 3


@pytest.mark.django_db
def test_fetch_prices_correct_values(btc_token, coingecko_response):
    with patch("monitor.tasks.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"bitcoin": {"usd": 60000.0}}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        fetch_prices()

    snap = PriceSnapshot.objects.get(symbol="BTC")
    assert snap.price_usd == Decimal("60000.0")
    assert snap.source == "coingecko"


@pytest.mark.django_db
def test_fetch_prices_single_batch_call(all_tokens, coingecko_response):
    with patch("monitor.tasks.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = coingecko_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        fetch_prices()

    assert mock_get.call_count == 1
    call_kwargs = mock_get.call_args
    ids_param = call_kwargs[1]["params"]["ids"]
    assert "bitcoin" in ids_param
    assert "ethereum" in ids_param
    assert "usd-coin" in ids_param


@pytest.mark.django_db
def test_fetch_prices_retries_on_network_error(btc_token):
    task = fetch_prices

    with patch("monitor.tasks.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("Network down")

        with patch.object(task, "retry", side_effect=Exception("retry called")) as mock_retry:
            with pytest.raises(Exception, match="retry called"):
                fetch_prices()

        mock_retry.assert_called_once()


@pytest.mark.django_db
def test_fetch_prices_retries_on_429(btc_token):
    task = fetch_prices

    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Too Many Requests")

    with patch("monitor.tasks.requests.get", return_value=mock_resp):
        with patch.object(task, "retry", side_effect=Exception("retry called")) as mock_retry:
            with pytest.raises(Exception, match="retry called"):
                fetch_prices()

        mock_retry.assert_called_once()


@pytest.mark.django_db
def test_fetch_prices_no_active_tokens(db):
    result = fetch_prices()
    assert result["fetched"] == 0
    assert PriceSnapshot.objects.count() == 0


@pytest.mark.django_db
def test_fetch_prices_skips_missing_token(all_tokens):
    partial_response = {"bitcoin": {"usd": 60000.0}}

    with patch("monitor.tasks.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = partial_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = fetch_prices()

    assert result["fetched"] == 1
    assert PriceSnapshot.objects.filter(symbol="BTC").count() == 1
    assert PriceSnapshot.objects.filter(symbol="ETH").count() == 0
