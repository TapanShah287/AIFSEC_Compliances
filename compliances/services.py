from datetime import timedelta
from django.utils.timezone import localdate
from .models import ComplianceTask
DEFAULT_RULES={'MCA':30,'DOCUMENT':3,'SEBI':7,'TAX':15,'OTHER':10}
def _due(base,days): return base + timedelta(days=days) if base else None
def generate_for_purchase(purchase,rules=None,assigned_to=None,notes=None):
    rules=rules or DEFAULT_RULES; base=purchase.purchase_date or localdate()
    items=[('MCA',f"MCA filing for investment in {purchase.investee_company.name}"),('DOCUMENT',f"Prepare/collect supporting documents for purchase #{purchase.id}"),('SEBI',f"SEBI reporting for purchase in {purchase.investee_company.name}"),('TAX',f"Pay applicable stamp duty/taxes for purchase #{purchase.id}"),('OTHER',f"Other declarations for purchase #{purchase.id}")]
    out=[]; 
    for topic,desc in items:
        out.append(ComplianceTask.objects.create(fund=purchase.fund,topic=topic,description=desc,due_date=_due(base,rules.get(topic,10)),tentative_completion_date=_due(base,rules.get(topic,10)-2) if rules.get(topic) else None,status='PENDING',assigned_to=assigned_to,notes=notes or '',purchase_transaction=purchase))
    return out
def generate_for_redemption(redemption,rules=None,assigned_to=None,notes=None):
    rules=rules or DEFAULT_RULES; base=redemption.redemption_date or localdate(); co=redemption.purchase_transaction.investee_company if redemption.purchase_transaction else None; name=co.name if co else 'investee company'
    items=[('MCA',f"MCA filing for redemption in {name}"),('DOCUMENT',f"Prepare/collect supporting documents for redemption #{redemption.id}"),('SEBI',f"SEBI reporting for redemption in {name}"),('TAX',f"Pay applicable taxes/fees for redemption #{redemption.id}"),('OTHER',f"Other declarations for redemption #{redemption.id}")]
    out=[];
    for topic,desc in items:
        out.append(ComplianceTask.objects.create(fund=redemption.fund,topic=topic,description=desc,due_date=_due(base,rules.get(topic,10)),tentative_completion_date=_due(base,rules.get(topic,10)-2) if rules.get(topic) else None,status='PENDING',assigned_to=assigned_to,notes=notes or '',redemption_transaction=redemption))
    return out
