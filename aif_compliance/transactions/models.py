from django.db import models

class PurchaseTransaction(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    def __str__(self):
        return str(self.amount)

class RedemptionTransaction(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    def __str__(self):
        return str(self.amount)
