# funds/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Fund
from compliances.services import generate_standard_aif_tasks

@receiver(post_save, sender=Fund)
def trigger_fund_compliance_roadmap(sender, instance, created, **kwargs):
    if created:
        # This calls the function we wrote to populate the calendar
        generate_standard_aif_tasks(instance)