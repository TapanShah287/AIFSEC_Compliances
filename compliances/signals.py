from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Fund
from compliances.models import ComplianceMaster, ComplianceTask
from datetime import date, timedelta

@receiver(post_save, sender=Fund)
def auto_generate_initial_tasks(sender, instance, created, **kwargs):
    """
    Triggers only when a NEW Fund is created.
    """
    if created:
        # Find all Master Rules that match this Fund's Jurisdiction
        rules = ComplianceMaster.objects.filter(jurisdiction=instance.jurisdiction)
        
        today = date.today()
        
        for rule in rules:
            due_date = today + timedelta(days=rule.days_after_period)
            
            ComplianceTask.objects.create(
                compliance_master=rule,
                fund=instance,
                manager=instance.manager,
                title=f"Initial Setup: {rule.title}",
                due_date=due_date,
                status='PENDING',
                priority='HIGH'
            )