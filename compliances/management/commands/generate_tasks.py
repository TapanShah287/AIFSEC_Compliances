import calendar
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from funds.models import Fund
from compliances.models import ComplianceMaster, ComplianceTask

class Command(BaseCommand):
    help = 'Generates recurring compliance tasks based on Fund Incorporation or Master Anchor'

    def handle(self, *args, **options):
        self.stdout.write("Mapping out the Compliance Calendar for the next 12 months...")
        
        today = timezone.now().date()
        one_year_later = today + relativedelta(years=1)
        
        # FIX: Define applicable_funds before the loop starts
        applicable_funds = Fund.objects.all()
        rules = ComplianceMaster.objects.all()

        
        tasks_created = 0

        for rule in rules:
            if rule.frequency == 'EVENT_BASED':
                continue

            for fund in applicable_funds:

                if rule.jurisdiction != fund.jurisdiction:
                    continue

                # 1. Determine the Anchor Date
                # Priority: Rule's first_due_date > Fund's date_of_inception > Jan 1st
                anchor_date = rule.first_due_date or fund.date_of_inception or date(today.year, 1, 1)
                
                # 2. Start checking from the anchor, but only create tasks for the future
                check_date = anchor_date
                
                # We loop forward month-by-month for 2 years from anchor to cover 
                # the 1-year window from today
                while check_date <= one_year_later:
                    period_end = None
                    
                    # Calculate months elapsed from the start of the chain
                    diff = relativedelta(check_date, anchor_date)
                    months_elapsed = diff.years * 12 + diff.months
                    
                    # 3. Frequency Logic
                    if rule.frequency == 'MONTHLY':
                        period_end = check_date
                    
                    elif rule.frequency == 'QUARTERLY' and months_elapsed % 3 == 0:
                        period_end = check_date
                        
                    elif rule.frequency == 'HALF_YEARLY' and months_elapsed % 6 == 0:
                        period_end = check_date
                        
                    elif rule.frequency == 'ANNUALLY' and months_elapsed % 12 == 0:
                        period_end = check_date

                    # 4. Create the Task if valid
                    if period_end and period_end >= today:
                        # Normalize to the last day of that month
                        last_day = calendar.monthrange(period_end.year, period_end.month)[1]
                        final_period_end = date(period_end.year, period_end.month, last_day)
                        
                        due_date = final_period_end + timedelta(days=rule.days_after_period)
                        
                        # Generate unique title to prevent duplicates
                        task_title = f"{rule.title} - {final_period_end.strftime('%b %Y')}"
                        
                        task, created = ComplianceTask.objects.get_or_create(
                            fund=fund,
                            compliance_master=rule,
                            due_date=due_date,
                            defaults={
                                'title': task_title,
                                'status': 'PENDING',
                                'description': rule.description,
                            }
                        )
                        if created:
                            tasks_created += 1

                    # Increment by 1 month to check the next "link" in the chain
                    check_date += relativedelta(months=1)

        self.stdout.write(self.style.SUCCESS(f"Successfully created {tasks_created} tasks across {applicable_funds.count()} funds."))