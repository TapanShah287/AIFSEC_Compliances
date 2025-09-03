from django.db import models

class Fund(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    dummy_field = models.BooleanField(default=False)
    def __str__(self):
        return self.name
