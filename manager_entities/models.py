from django.db import models
class ManagerEntity(models.Model):
    name = models.CharField(max_length=255, unique=True)
    sebi_manager_registration_no = models.CharField(max_length=64, blank=True, null=True)
    cin = models.CharField(max_length=21, blank=True, null=True)
    pan = models.CharField(max_length=10, blank=True, null=True)
    gstin = models.CharField(max_length=15, blank=True, null=True)
    registered_address = models.TextField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["name"]
        verbose_name = "Manager Entity"
        verbose_name_plural = "Manager Entities"
    def __str__(self): return self.name
