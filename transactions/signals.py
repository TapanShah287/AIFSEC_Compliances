from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from .models import DrawdownReceipt
from funds.models import InvestorPosition, UnitIssuance 

@receiver(post_save, sender=DrawdownReceipt)
def auto_issue_units(sender, instance, created, **kwargs):
    if created:
        # 1. Determine NAV (Hardcoded to 10.00 for MVP)
        current_nav = Decimal('10.0000') 

        # 2. Calculate Units
        amount_invested = instance.amount_received
        units_to_issue = amount_invested / current_nav

        # 3. Get or Create the Cap Table Entry (InvestorPosition)
        # Note: We now reference 'funds' app models
        position, _ = InvestorPosition.objects.get_or_create(
            investor=instance.investor,
            fund=instance.fund
        )

        # 4. Create the Audit Record
        UnitIssuance.objects.create(
            position=position,
            receipt=instance,
            units_issued=units_to_issue,
            nav_at_issuance=current_nav
        )

        # 5. Update the Master Balance
        position.total_units += units_to_issue
        position.total_capital_contributed += amount_invested
        position.save()

        print(f"CAP TABLE UPDATE: Issued {units_to_issue} units in {instance.fund.name}")