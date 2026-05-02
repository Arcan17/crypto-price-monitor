from django.contrib import admin

from .models import MonitoredToken, PriceSnapshot


@admin.register(MonitoredToken)
class MonitoredTokenAdmin(admin.ModelAdmin):
    list_display = ["symbol", "coingecko_id", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["symbol", "coingecko_id"]


@admin.register(PriceSnapshot)
class PriceSnapshotAdmin(admin.ModelAdmin):
    list_display = ["symbol", "price_usd", "fetched_at", "source"]
    list_filter = ["symbol", "source"]
    search_fields = ["symbol"]
    readonly_fields = ["fetched_at"]
