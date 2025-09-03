from django.db import models

class ComplianceModel(models.Model):
    name = models.CharField(max_length=255, help_text='Compliance name (init)')
    dummy_field = models.BooleanField(default=False)
    def __str__(self):
        return self.name
