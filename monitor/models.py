from django.db import models


class MonitoredToken(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    coingecko_id = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.symbol

    class Meta:
        ordering = ["symbol"]


class PriceSnapshot(models.Model):
    symbol = models.CharField(max_length=20, db_index=True)
    price_usd = models.DecimalField(max_digits=18, decimal_places=8)
    fetched_at = models.DateTimeField(auto_now_add=True, db_index=True)
    source = models.CharField(max_length=50, default="coingecko")

    def __str__(self) -> str:
        return f"{self.symbol} @ {self.price_usd} ({self.fetched_at})"

    class Meta:
        ordering = ["-fetched_at"]
