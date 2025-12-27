from django.db import models
from django.contrib.auth.models import User


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

class EntityMembership(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Super Admin'),     # Can manage team and all fund data
        ('MANAGER', 'Fund Manager'),  # Can record transactions
        ('COMPLIANCE', 'Officer'),    # Read-only + Reporting access
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    entity = models.ForeignKey(ManagerEntity, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='MANAGER')
    is_active_selection = models.BooleanField(default=False) # Helper for session defaults

    class Meta:
        unique_together = ('user', 'entity') # One user, one role per entity