from rest_framework import serializers

from .models import MonitoredToken, PriceSnapshot


class PriceSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceSnapshot
        fields = ["id", "symbol", "price_usd", "fetched_at"]


class MonitoredTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitoredToken
        fields = ["symbol", "coingecko_id", "is_active"]


class TokenStatsSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    latest_price = serializers.DecimalField(max_digits=18, decimal_places=8, allow_null=True)
    high_24h = serializers.DecimalField(max_digits=18, decimal_places=8, allow_null=True)
    low_24h = serializers.DecimalField(max_digits=18, decimal_places=8, allow_null=True)
    avg_24h = serializers.DecimalField(max_digits=18, decimal_places=8, allow_null=True)
    snapshot_count_24h = serializers.IntegerField()
