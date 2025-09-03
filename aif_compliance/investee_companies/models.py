from django.db import models

class InvesteeCompany(models.Model):
    name = models.CharField(max_length=255)
        # dummy_field = models.BooleanField(default=False)  # Commenting out for migration
    def __str__(self):
        return self.name
