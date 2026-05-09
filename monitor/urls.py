from django.urls import path

from .views import (
    ApiRootView,
    HealthView,
    PriceExportCsvView,
    PriceListView,
    StatsView,
    TokenListView,
)

urlpatterns = [
    path("", ApiRootView.as_view(), name="api-root"),
    path("health/", HealthView.as_view(), name="health"),
    path("prices/", PriceListView.as_view(), name="prices"),
    path("stats/", StatsView.as_view(), name="stats"),
    path("tokens/", TokenListView.as_view(), name="tokens"),
    path("export/prices.csv", PriceExportCsvView.as_view(), name="export-prices-csv"),
]
