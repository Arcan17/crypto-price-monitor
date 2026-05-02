import logging

from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MonitoredToken, PriceSnapshot
from .serializers import MonitoredTokenSerializer, PriceSnapshotSerializer, TokenStatsSerializer

logger = logging.getLogger(__name__)


class ApiRootView(APIView):
    def get(self, request: Request) -> Response:
        return Response(
            {
                "health": request.build_absolute_uri("/api/health/"),
                "prices": request.build_absolute_uri("/api/prices/"),
                "stats": request.build_absolute_uri("/api/stats/"),
                "tokens": request.build_absolute_uri("/api/tokens/"),
                "admin": request.build_absolute_uri("/admin/"),
            }
        )


class HealthView(APIView):
    def get(self, request: Request) -> Response:
        try:
            from config.celery import app as celery_app

            inspect = celery_app.control.inspect(timeout=1.0)
            active = inspect.active()
            workers_online = bool(active)
        except Exception:
            workers_online = False

        return Response({"status": "ok", "workers_online": workers_online})


class PriceListView(APIView):
    def get(self, request: Request) -> Response:
        qs = PriceSnapshot.objects.all()
        symbol = request.query_params.get("symbol")
        if symbol:
            qs = qs.filter(symbol=symbol.upper())

        limit_param = request.query_params.get("limit", "100")
        try:
            limit = min(int(limit_param), 1000)
        except ValueError:
            limit = 100

        paginator = PageNumberPagination()
        paginator.page_size = limit
        page = paginator.paginate_queryset(qs, request)
        serializer = PriceSnapshotSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class StatsView(APIView):
    def get(self, request: Request) -> Response:
        since = timezone.now() - timezone.timedelta(hours=24)
        tokens = MonitoredToken.objects.filter(is_active=True)
        results = []

        for token in tokens:
            snapshots_24h = PriceSnapshot.objects.filter(
                symbol=token.symbol,
                fetched_at__gte=since,
            )
            count = snapshots_24h.count()

            latest = (
                PriceSnapshot.objects.filter(symbol=token.symbol).order_by("-fetched_at").first()
            )
            latest_price = latest.price_usd if latest else None

            if count > 0:
                prices = list(snapshots_24h.values_list("price_usd", flat=True))
                high = max(prices)
                low = min(prices)
                avg = sum(prices) / len(prices)
            else:
                high = low = avg = None

            results.append(
                {
                    "symbol": token.symbol,
                    "latest_price": latest_price,
                    "high_24h": high,
                    "low_24h": low,
                    "avg_24h": avg,
                    "snapshot_count_24h": count,
                }
            )

        serializer = TokenStatsSerializer(results, many=True)
        return Response(serializer.data)


class TokenListView(APIView):
    def get(self, request: Request) -> Response:
        tokens = MonitoredToken.objects.all()
        serializer = MonitoredTokenSerializer(tokens, many=True)
        return Response(serializer.data)
