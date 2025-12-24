from datetime import timedelta, date
from .models import ComplianceTask

DEFAULT_RULES = {
    'MCA': 30,
    'DOCUMENT': 3,
    'SEBI': 7,
    'TAX': 15,
    'OTHER': 10
}

def _get_due_date(base_date, days):
    if not base_date:
        return date.today() + timedelta(days=days)
    return base_date + timedelta(days=days)

def generate_for_purchase(purchase, assigned_to=None):
    """
    Generates a set of standard compliance tasks following a portfolio purchase.
    Calculates due dates based on the trade date.
    """
    tasks_data = [
        {
            'topic': 'MCA',
            'description': f"File Form PAS-3 for allotment of shares in {purchase.investee_company.name}",
            'days_after': 30
        },
        {
            'topic': 'SEBI',
            'description': f"Quarterly reporting update for investment in {purchase.investee_company.name}",
            'days_after': 15
        },
        {
            'topic': 'DOCUMENT',
            'description': f"Collect Share Certificates / Demat advice from {purchase.investee_company.name}",
            'days_after': 60
        }
    ]
    
    tasks = []
    for t in tasks_data:
        task = ComplianceTask.objects.create(
            fund=purchase.fund,
            purchase_transaction=purchase,
            assigned_to=assigned_to,
            topic=t['topic'],
            description=t['description'],
            due_date=purchase.trade_date + timedelta(days=t['days_after']),
            status='PENDING'
        )
        tasks.append(task)
    return tasks

def generate_for_redemption(redemption, assigned_to=None):
    """
    Generates compliance tasks following a portfolio exit/redemption.
    """
    task = ComplianceTask.objects.create(
        fund=redemption.fund,
        redemption_transaction=redemption,
        assigned_to=assigned_to,
        topic='SEBI',
        description=f"Report exit from {redemption.investee_company.name} in SEBI quarterly return",
        due_date=redemption.trade_date + timedelta(days=15),
        status='PENDING'
    )
    return [task]

def generate_for_drawdown(receipt, assigned_to=None):
    """
    Generates compliance tasks following a capital drawdown receipt.
    Ensures unit allotment and investor reporting are tracked.
    """
    tasks_data = [
        {
            'topic': 'DOCUMENT',
            'description': f"Issue Statement of Account / Unit Allotment Advice to {receipt.investor.name}",
            'days_after': 15
        },
        {
            'topic': 'SEBI',
            'description': f"Update capital contribution for {receipt.investor.name} in SEBI portal",
            'days_after': 7
        },
        {
            'topic': 'TAX',
            'description': f"Assess GST on management fees associated with drawdown from {receipt.investor.name}",
            'days_after': 10
        }
    ]
    
    tasks = []
    for t in tasks_data:
        task = ComplianceTask.objects.create(
            fund=receipt.fund,
            assigned_to=assigned_to,
            topic=t['topic'],
            description=t['description'],
            due_date=receipt.receipt_date + timedelta(days=t['days_after']),
            status='PENDING'
        )
        tasks.append(task)
    return tasks