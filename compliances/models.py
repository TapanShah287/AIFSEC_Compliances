from django.db import models
from django.conf import settings
from datetime import date
from django.utils import timezone
from funds.models import Fund


class ComplianceMaster(models.Model):
    """
    A library of standard regulatory requirements (SEBI/IFSCA).
    """
    JURISDICTION_CHOICES = [('DOMESTIC', 'SEBI'), ('IFSC', 'IFSCA')]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    jurisdiction = models.CharField(max_length=10, choices=JURISDICTION_CHOICES)
    frequency = models.CharField(max_length=20, choices=[
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('ANNUAL', 'Annual')
    ])
    days_after_period = models.IntegerField(help_text="Days after month/quarter end to set deadline")

    def __str__(self):
        return f"{self.jurisdiction} - {self.title}"


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

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    topic = models.CharField(max_length=20, choices=TOPIC_CHOICES, default='REPORTING')
    
    # Link to a specific fund (optional, as some tasks are firm-level)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, null=True, blank=True, related_name='compliance_tasks')
    
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