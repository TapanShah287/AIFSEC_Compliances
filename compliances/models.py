from django.db import models
from django.conf import settings
from datetime import date

class ComplianceTask(models.Model):
    TOPIC_CHOICES = [
        ('MCA', 'MCA Filing'),
        ('DOCUMENT', 'Document Collection'),
        ('SEBI', 'SEBI Reporting'),
        ('TAX', 'Tax/Fee Payment'),
        ('OTHER', 'Other Declarations'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]

    # Relationships
    fund = models.ForeignKey('funds.Fund', on_delete=models.CASCADE, related_name='compliance_tasks')
    purchase_transaction = models.ForeignKey('transactions.PurchaseTransaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='compliance_tasks')
    redemption_transaction = models.ForeignKey('transactions.RedemptionTransaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='compliance_tasks')
    
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')

    # Fields
    topic = models.CharField(max_length=20, choices=TOPIC_CHOICES, default='DOCUMENT')
    description = models.TextField()
    notes = models.TextField(blank=True, null=True)
    
    due_date = models.DateField()
    tentative_completion_date = models.DateField(null=True, blank=True)
    final_completion_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    class Meta:
        ordering = ['due_date', 'status']
        indexes = [
            models.Index(fields=['topic', 'due_date']),
            models.Index(fields=['fund', 'status']),
        ]

    def __str__(self):
        return f"{self.get_topic_display()} - {self.fund.name}"

    @property
    def is_overdue(self):
        return self.status != 'COMPLETED' and self.due_date < date.today()

    def save(self, *args, **kwargs):
        # Auto-update status to OVERDUE if needed
        if self.pk and self.status not in ['COMPLETED', 'CANCELLED'] and self.due_date < date.today():
            self.status = 'OVERDUE'
        
        # Auto-set completion date
        if self.status == 'COMPLETED' and not self.final_completion_date:
            self.final_completion_date = date.today()
            
        super().save(*args, **kwargs)


def compliance_upload_path(instance, filename):
    return f"compliances/task_{instance.task.id}/{filename}"

class ComplianceDocument(models.Model):
    task = models.ForeignKey(ComplianceTask, on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to=compliance_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Added remarks field to match the form
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Doc for {self.task} ({self.uploaded_at.date()})"