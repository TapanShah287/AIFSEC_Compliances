from django.db import models
from django.utils import timezone

class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True, help_text="ISO 4217 Code (e.g., USD, INR)")
    symbol = models.CharField(max_length=5, help_text="Symbol (e.g., $, ₹)")
    name = models.CharField(max_length=50)
    is_base = models.BooleanField(default=False, help_text="Is this the system reporting currency (e.g. INR)?")

    class Meta:
        verbose_name_plural = "Currencies"

    def __str__(self):
        return f"{self.code} ({self.symbol})"

class ExchangeRate(models.Model):
    """
    Stores daily exchange rates relative to the BASE currency.
    Example: If Base is INR, and we store USD:
    rate = 83.50 (1 USD = 83.50 INR)
    """
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='rates')
    date = models.DateField(default=timezone.now)
    rate = models.DecimalField(max_digits=20, decimal_places=6, help_text="Conversion rate to Base Currency")

    class Meta:
        unique_together = ('currency', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"1 {self.currency.code} = {self.rate} BASE @ {self.date}"