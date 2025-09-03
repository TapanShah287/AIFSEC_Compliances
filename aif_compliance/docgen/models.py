from django.db import models

class DocGenModel(models.Model):
    name = models.CharField(max_length=255, help_text='DocGen name (init)')
    dummy_field = models.BooleanField(default=False)
    def __str__(self):
        return self.name
