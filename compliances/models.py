from django.db import models
from django.conf import settings
from django.utils import timezone

class ComplianceTask(models.Model):
    TOPIC_CHOICES = [('MCA','MCA Filing'),('DOCUMENT','Document'),('SEBI','SEBI Reporting'),('TAX','Tax/Fee Payment'),('OTHER','Other Declarations')]
    STATUS_CHOICES = [('PENDING','Pending'),('IN_PROGRESS','In Progress'),('COMPLETED','Completed'),('OVERDUE','Overdue')]
    fund = models.ForeignKey('funds.Fund', on_delete=models.CASCADE, related_name='compliance_tasks')
    topic = models.CharField(max_length=20, choices=TOPIC_CHOICES, default='DOCUMENT')
    description = models.TextField()
    due_date = models.DateField()
    tentative_completion_date = models.DateField(blank=True, null=True)
    final_completion_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_compliance_tasks')
    notes = models.TextField(blank=True, null=True)
    purchase_transaction = models.ForeignKey('transactions.PurchaseTransaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='compliance_tasks')
    redemption_transaction = models.ForeignKey('transactions.RedemptionTransaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='compliance_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['due_date', 'status', 'pk']
        indexes = [models.Index(fields=['fund','status','due_date']), models.Index(fields=['topic','due_date'])]
    def __str__(self): return f"{self.get_topic_display()} — {self.description[:60]}"
    @property
    def is_overdue(self): return self.status != 'COMPLETED' and self.due_date and self.due_date < timezone.localdate()
    def save(self,*a,**kw):
        if self.status!='COMPLETED' and self.due_date and self.due_date < timezone.localdate(): self.status='OVERDUE'
        if self.status=='COMPLETED' and not self.final_completion_date: self.final_completion_date=timezone.localdate()
        super().save(*a,**kw)

def compliance_upload_path(instance, filename): return f"compliances/{instance.task_id}/{filename}"

class ComplianceDocument(models.Model):
    task = models.ForeignKey(ComplianceTask, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to=compliance_upload_path)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)
    mark_complete = models.BooleanField(default=False)
    class Meta: ordering = ['-uploaded_at']
    def __str__(self): return f"Doc for task #{self.task_id}: {self.file.name}"
    def save(self,*a,**kw):
        super().save(*a,**kw)
        if self.mark_complete and self.task.status!='COMPLETED':
            self.task.status='COMPLETED'; self.task.final_completion_date=timezone.localdate(); self.task.save()
