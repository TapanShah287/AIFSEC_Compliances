from datetime import timedelta, date
from .models import ComplianceTask
from django.utils import timezone

DEFAULT_RULES = {
    'MCA': 30,
    'DOCUMENT': 3,
    'SEBI': 7,
    'TAX': 15,
    'OTHER': 10
}

def generate_standard_aif_tasks(fund):
    """
    Automates the creation of standard regulatory tasks based 
    on the Fund's jurisdiction and inception date.
    """
    tasks_to_create = []
    start_date = fund.inception_date or timezone.now().date()
    current_year = start_date.year

# --- 1. REGULATORY FILINGS (CTR/AQR) ---    
    # Define Standard Recurring Deadlines
    if fund.jurisdiction == 'DOMESTIC':
        # SEBI Quarterly CTR (Due 15 days after quarter end)
        quarter_ends = [date(2026, 3, 31), date(2026, 6, 30), date(2026, 9, 30), date(2026, 12, 31)]
        for q_end in quarter_ends:
            if q_end > start_date:
                tasks_to_create.append(ComplianceTask(
                    fund=fund,
                    title=f"Quarterly CTR Filing - {q_end.strftime('%b %Y')}",
                    description="Mandatory SEBI quarterly report submission via SEBI Intermediary Portal.",
                    due_date=q_end + timedelta(days=15),
                    jurisdiction='DOMESTIC',
                    priority='HIGH',
                    status='PENDING'
                ))
    
    elif fund.jurisdiction == 'IFSC':
        # IFSCA specific filings
        tasks_to_create.append(ComplianceTask(
            fund=fund,
            title="IFSCA Annual Compliance Report",
            description="Submit annual compliance certificate to IFSCA authorities.",
            due_date=date(2026, 4, 30),
            jurisdiction='IFSC',
            priority='HIGH'
        ))

# --- 2. STEWARDSHIP CODE TASKS (Annual) ---
    stewardship_tasks = [
        {
            'title': f"Annual Stewardship Disclosure - FY {current_year}",
            'desc': "Public disclosure of voting nature and stewardship responsibilities on the fund website.",
            'due': date(current_year, 6, 30), # Usually 3 months post-FY
            'priority': 'MEDIUM'
        },
        {
            'title': "Annual Voting Policy Review",
            'desc': "Internal review and approval of the fund's voting policy by the Investment Committee.",
            'due': date(current_year, 4, 15),
            'priority': 'LOW'
        }
    ]

    for item in stewardship_tasks:
        if item['due'] > start_date:
            tasks_to_create.append(ComplianceTask(
                fund=fund,
                title=item['title'],
                description=item['desc'],
                due_date=item['due'],
                jurisdiction=fund.jurisdiction,
                priority=item['priority'],
                topic='STEWARDSHIP', # Ensure 'STEWARDSHIP' is a choice in your Model
                status='PENDING'
            ))


    # Bulk create for database efficiency
    if tasks_to_create:
        ComplianceTask.objects.bulk_create(tasks_to_create)
        return len(tasks_to_create)
    return 0

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