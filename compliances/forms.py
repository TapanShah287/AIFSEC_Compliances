from django import forms
from .models import ComplianceTask

class ComplianceTaskUpdateForm(forms.ModelForm):
    class Meta:
        model = ComplianceTask
        fields = ["status", "due_date", "assigned_to", "notes"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        status = (cleaned.get("status") or "").upper()
        valid = {s for s, _ in getattr(self._meta.model, "STATUS_CHOICES", [])} or {"PENDING", "DONE", "CANCELLED"}
        if status and status not in valid:
            cleaned["status"] = "PENDING"
        return cleaned

class ComplianceTaskForm(forms.ModelForm):
    class Meta:
        model = ComplianceTask
        fields = ["status", "due_date", "assigned_to", "notes"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        status = (cleaned.get("status") or "").upper()
        valid = {s for s, _ in getattr(self._meta.model, "STATUS_CHOICES", [])} or {"PENDING", "DONE", "CANCELLED"}
        if status and status not in valid:
            cleaned["status"] = "PENDING"
        return cleaned

class ComplianceDocumentForm(forms.ModelForm):
    class Meta:
        model = ComplianceTask
        fields = ["status", "due_date", "assigned_to", "notes"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        status = (cleaned.get("status") or "").upper()
        valid = {s for s, _ in getattr(self._meta.model, "STATUS_CHOICES", [])} or {"PENDING", "DONE", "CANCELLED"}
        if status and status not in valid:
            cleaned["status"] = "PENDING"
        return cleaned