from django.db import models
from django.conf import settings
from datetime import date
from django.utils import timezone

from funds.models import Fund
from manager_entities.models import ManagerEntity


class ComplianceMaster(models.Model):
    """
    A library of standard regulatory requirements (SEBI/IFSCA).
    """
    JURISDICTION_CHOICES = [('DOMESTIC', 'SEBI'), ('IFSC', 'IFSCA')]

    SCOPE_CHOICES = [
        ('FUND', 'Fund Level (Specific Scheme)'),
        ('MANAGER', 'Manager Level (Entity Wide)'),
    ]

    FREQUENCY_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('HALF_YEARLY', 'Half Yearly'),
        ('ANNUALLY', 'Annually'),
        ('EVENT_BASED', 'Event Based'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='FUND')
    jurisdiction = models.CharField(max_length=10, choices=JURISDICTION_CHOICES)
    
    applicable_categories = models.CharField(
        max_length=255, 
        help_text="Comma-separated list of categories (e.g., 'CAT_I,CAT_II'). Leave blank if applying to all.",
        blank=True
    )

    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='ANNUALLY')
    
    first_due_date = models.DateField(
        null=True, blank=True, 
        help_text="Override: If set, the recurring chain starts from this date. If blank, it uses Fund Incorporation Date."
    )
   
    days_after_period = models.IntegerField(
        default=7,
        help_text="Days after month/quarter end to set deadline"
    )

    def __str__(self):
        return f"{self.title} ({self.jurisdiction} - {self.get_scope_display()})"

class ComplianceTask(models.Model):
    TOPIC_CHOICES = [
        ('REPORTING', 'Regulatory Reporting'),
        ('STEWARDSHIP', 'Stewardship & Voting'),
        ('TAX', 'Tax & Audit'),
        ('DOCUMENT', 'Transactional/KYC'),
    ]

    PRIORITY_CHOICES = [
        ('HIGH', 'Critical / High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low / Routine'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('OVERDUE', 'Overdue'),
    ]

    JURISDICTION_CHOICES = [
        ('DOMESTIC', 'SEBI (Domestic)'),
        ('IFSC', 'IFSCA (GIFT City)'),
        ('TAX', 'Income Tax / TDS'),
    ]

    compliance_master = models.ForeignKey(
        ComplianceMaster, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='tasks'
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    topic = models.CharField(max_length=20, choices=TOPIC_CHOICES, default='REPORTING')

    manager = models.ForeignKey(
        ManagerEntity, 
        on_delete=models.CASCADE, 
        related_name='manager_compliance_tasks',
        null=True, blank=True  # Null allowed temporarily for migration, but should be filled
    )
        
    # Link to a specific fund (optional, as some tasks are firm-level)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, null=True, blank=True, related_name='fund_compliance_tasks')
    
    jurisdiction = models.CharField(max_length=10, choices=JURISDICTION_CHOICES, default='DOMESTIC')
    due_date = models.DateField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    assigned_to = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date']
        # Optional: Prevent duplicate tasks for the same rule/fund/date
        # unique_together = ('compliance_master', 'fund', 'due_date')
    
    def clean(self):
        """Validate that Fund is present if the Master Rule says it's a FUND scope."""
        if self.compliance_master and self.compliance_master.scope == 'FUND' and not self.fund:
            raise ValidationError("Fund is required for Fund-level compliance tasks.")

    def __str__(self):
        return f"{self.title} ({self.due_date})"

    @property
    def days_remaining(self):
        """Returns the integer difference between today and the due date."""
        today = timezone.now().date()
        return (self.due_date - today).days

    @property
    def urgency_color(self):
        """Returns a CSS color class based on urgency."""
        days = self.days_remaining
        if self.status == 'COMPLETED':
            return 'emerald'
        if days < 0:
            return 'rose' # Overdue
        if days < 3:
            return 'red'  # Urgent
        if days < 7:
            return 'amber' # Warning
        return 'emerald'   # Safe
        
    @property
    def is_overdue(self):
        return self.status != 'COMPLETED' and self.due_date < timezone.now().date()


def compliance_upload_path(instance, filename):
    return f"compliances/task_{instance.task.id}/{filename}"

class ComplianceDocument(models.Model):
    task = models.ForeignKey(ComplianceTask, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to=compliance_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Added remarks field to match the form
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Doc for {self.task} ({self.uploaded_at.date()})"