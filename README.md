# crypto-price-monitor

Fetches BTC, ETH, USDC prices from CoinGecko every 5 min. Stores in PostgreSQL. Exposes via Django REST Framework.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Docker Compose                        │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  celery  │    │  celery  │    │  django  │              │
│  │   beat   │───▶│  worker  │    │   web    │              │
│  │(schedule)│    │(execute) │    │ :8000    │              │
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
│              │  django_celery_beat tables       │            │
│              └─────────────────────────────────┘            │
│                                                             │
│                      CoinGecko API                          │
│              https://api.coingecko.com/api/v3               │
└─────────────────────────────────────────────────────────────┘
```

## How it works

**Django vs asyncio:** Django's synchronous ORM is battle-tested for DB work. Async Django exists but adds complexity without benefit here — Celery handles concurrency at the process level.

**Why Celery:** Beat scheduler stores tasks in PostgreSQL via `django-celery-beat` — survives restarts, inspectable via admin, configurable without deploys. Workers run in separate processes, isolating failures. Retry logic with exponential backoff handles CoinGecko rate limits (429s).

## Docker quickstart

```bash
cp .env.example .env
docker compose up --build
```

API at `http://localhost:8000/api/`. Admin at `http://localhost:8000/admin/`.

Create superuser:
```bash
docker compose exec web python manage.py createsuperuser
```

## API reference

### GET /api/health/
```json
{"status": "ok", "workers_online": true}
```

### GET /api/prices/?symbol=BTC&limit=50
```json
{
  "count": 288,
  "next": "http://localhost:8000/api/prices/?page=2",
  "previous": null,
  "results": [
    {"id": 1, "symbol": "BTC", "price_usd": "60123.45000000", "fetched_at": "2024-01-01T12:00:00Z"}
  ]
}
```

### GET /api/stats/
```json
[
  {
    "symbol": "BTC",
    "latest_price": "60123.45000000",
    "high_24h": "61000.00000000",
    "low_24h": "59000.00000000",
    "avg_24h": "60050.22500000",
    "snapshot_count_24h": 288
  }
]
```

### GET /api/tokens/
```json
[
  {"symbol": "BTC", "coingecko_id": "bitcoin", "is_active": true},
  {"symbol": "ETH", "coingecko_id": "ethereum", "is_active": true},
  {"symbol": "USDC", "coingecko_id": "usd-coin", "is_active": true}
]
```

## Running tests

```bash
pip install -r requirements.txt

# local postgres + redis required, or use CI env vars
export DATABASE_URL=postgres://postgres:postgres@localhost:5432/crypto_monitor
export REDIS_URL=redis://localhost:6379/0
export DJANGO_SECRET_KEY=test-key

pytest tests/ -v
```

## Why this stack?

| Choice | Reason |
|--------|--------|
| Django ORM | Migrations, admin, signals out of box. No SQLAlchemy mapping layer needed. |
| Celery beat | Periodic tasks in DB — inspectable, restartable, configurable via admin panel. |
| Redis broker | Fast, simple. Celery + Redis is the most battle-tested combo. Zero config. |
| psycopg2 | Official PostgreSQL driver. `psycopg2-binary` skips compile step in Docker. |
| python-decouple | `.env` → settings with type casting. No 12-factor boilerplate. |
