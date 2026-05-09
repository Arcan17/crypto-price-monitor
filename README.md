# Crypto Price Monitor 📈

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0-092E20?style=flat&logo=django&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.3-37814A?style=flat)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat&logo=docker&logoColor=white)
![CI](https://img.shields.io/github/actions/workflow/status/Arcan17/crypto-price-monitor/ci.yml?label=CI&logo=github)
![License](https://img.shields.io/badge/license-MIT-green?style=flat)

> **Automated crypto price pipeline — fetches, stores, and serves BTC/ETH/USDC data every 5 minutes.**

A production-grade **ETL data pipeline** that continuously pulls cryptocurrency prices from the CoinGecko API, cleans and stores them in PostgreSQL, and exposes a REST API with historical stats and CSV export. Built with Django, Celery, Redis, and Docker Compose.

**The problem it solves:** Manually tracking crypto prices or relying on third-party dashboards means no control over your data. This pipeline gives you full ownership — historical snapshots, custom analytics, and data export in one self-hosted system.

---

## Client Use Case

This project is useful for clients who need to:
- **Monitor prices automatically** from any API on a schedule (every N minutes)
- **Store historical data** in a relational database for trend analysis
- **Build dashboards** on top of structured, queryable price data
- **Export data to CSV/Excel** for reporting or further processing
- **Integrate with other systems** via REST API endpoints
- **Scale data collection** to any number of tokens or data sources

> Adaptable to any data source: stock prices, e-commerce prices, exchange rates, sensor data, etc.

---

## ETL Pipeline

```
EXTRACT                    TRANSFORM                  LOAD
──────────────────         ──────────────────         ──────────────────
CoinGecko API         →    Validate & normalize   →   PostgreSQL
/simple/price             price_usd (Decimal)         PriceSnapshot table
BTC, ETH, USDC            symbol (uppercase)          Queryable via DRF
every 5 minutes           timestamp (UTC)             REST API + CSV export
```

```
Celery Beat (scheduler)
        │  fires every 5 minutes
        ▼
Celery Worker
        │  fetch_prices task
        ▼
CoinGecko API ──── GET /simple/price?ids=bitcoin,ethereum&vs_currencies=usd
        │
        ▼
  Validate & clean
        │
        ▼
PostgreSQL ──── INSERT INTO monitor_pricesnapshot (symbol, price_usd, fetched_at)
        │
        ▼
REST API ──── GET /api/prices/?symbol=BTC&limit=100
             GET /api/stats/
             GET /api/export/prices.csv?symbol=BTC&hours=24
```

---

## Features

- **Automated collection** — Celery Beat pulls prices every 5 minutes (configurable)
- **Full price history** — every snapshot stored with timestamp for trend analysis
- **24h stats API** — high, low, average, and count per token
- **CSV export** — download any symbol's history as `.csv` via API
- **Fault-tolerant** — exponential backoff retries on CoinGecko rate limits (429)
- **Admin panel** — Django admin to inspect data, add tokens, adjust schedules
- **Containerized** — single `docker compose up` runs everything
- **CI/CD** — GitHub Actions runs full test suite on every push

---

## Quickstart

```bash
git clone https://github.com/Arcan17/crypto-price-monitor.git
cd crypto-price-monitor

cp .env.example .env
docker compose up --build
```

- **API:** http://localhost:8000/api/
- **Admin:** http://localhost:8000/admin/ (create superuser below)

```bash
docker compose exec web python manage.py createsuperuser
```

---

## API Reference

### `GET /api/prices/` — Price history
```bash
# Last 100 BTC snapshots
curl "http://localhost:8000/api/prices/?symbol=BTC&limit=100"
```
```json
{
  "count": 288,
  "results": [
    {"id": 1, "symbol": "BTC", "price_usd": "60123.45", "fetched_at": "2024-01-01T12:00:00Z"}
  ]
}
```

### `GET /api/stats/` — 24h stats per token
```bash
curl http://localhost:8000/api/stats/
```
```json
[
  {
    "symbol": "BTC",
    "latest_price": "60123.45",
    "high_24h": "61000.00",
    "low_24h": "59000.00",
    "avg_24h": "60050.22",
    "snapshot_count_24h": 288
  }
]
```

### `GET /api/export/prices.csv` — CSV export
```bash
# Download last 24h of ETH prices as CSV
curl "http://localhost:8000/api/export/prices.csv?symbol=ETH&hours=24" -o eth_prices.csv
```
```csv
id,symbol,price_usd,fetched_at
1,ETH,3200.50,2024-01-01 12:00:00+00:00
2,ETH,3195.20,2024-01-01 12:05:00+00:00
```

| Parameter | Default | Description |
|---|---|---|
| `symbol` | all | Filter by BTC, ETH, USDC |
| `hours` | 24 | How many hours back (max 8760 = 1 year) |

### `GET /api/health/` — System health
```json
{"status": "ok", "workers_online": true}
```

---

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Docker Compose                        │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  celery  │    │  celery  │    │  django  │              │
│  │   beat   │───▶│  worker  │    │   web    │              │
│  │(schedule)│    │(execute) │    │  :8000   │              │
│  └──────────┘    └────┬─────┘    └────┬─────┘              │
│                       │               │                     │
│              ┌────────▼───────────────▼────────┐            │
│              │           Redis :6379            │            │
│              │      (broker + result store)     │            │
│              └─────────────────────────────────┘            │
│                                                             │
│              ┌─────────────────────────────────┐            │
│              │        PostgreSQL :5432          │            │
│              │  PriceSnapshot | MonitoredToken  │            │
│              └─────────────────────────────────┘            │
│                                                             │
│                      CoinGecko API                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | Django 5 + Django REST Framework |
| Task queue | Celery 5 (worker + beat scheduler) |
| Message broker | Redis |
| Database | PostgreSQL 15 |
| HTTP client | httpx (async-ready) |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Roadmap

- [ ] Backfill historical data: `python manage.py backfill_prices --days 30`
- [ ] Add more tokens (SOL, BNB, MATIC)
- [ ] Price alerts via Telegram when % change exceeds threshold
- [ ] Simple web dashboard with price charts
- [ ] Deploy public instance (Railway)
- [ ] Prometheus metrics endpoint

---

## License

MIT
