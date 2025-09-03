from django.db import models

class ManagerEntity(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True, help_text='Manager name (init)')
    dummy_field = models.BooleanField(default=False)
    def __str__(self):
        return self.name
