from django.db import models

    name = models.CharField(max_length=255, help_text='Transaction name (init)')
    dummy_field = models.BooleanField(default=False)
    # Additional fields and methods can be added here

class PurchaseTransaction(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    def __str__(self):
        return str(self.amount)

class RedemptionTransaction(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    def __str__(self):
        return str(self.amount)
