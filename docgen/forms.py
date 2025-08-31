from django import forms
from .models import DocumentTemplate
from transactions.models import PurchaseTransaction, RedemptionTransaction
class DocumentTemplateForm(forms.ModelForm):
    class Meta: model = DocumentTemplate; fields = ["code","name","file","description","sample_context"]
class GenerateFromPurchaseForm(forms.Form):
    purchase = forms.ModelChoiceField(queryset=PurchaseTransaction.objects.all())
    templates = forms.ModelMultipleChoiceField(queryset=DocumentTemplate.objects.all(), help_text="Select templates to generate")
    letter_date = forms.DateField(widget=forms.DateInput(attrs={"type":"date"}), required=False)
    proposer_name = forms.CharField(max_length=255, required=False)
    additional_notes = forms.CharField(widget=forms.Textarea, required=False)
class GenerateFromRedemptionForm(forms.Form):
    redemption = forms.ModelChoiceField(queryset=RedemptionTransaction.objects.all())
    templates = forms.ModelMultipleChoiceField(queryset=DocumentTemplate.objects.all())
    letter_date = forms.DateField(widget=forms.DateInput(attrs={"type":"date"}), required=False)
    proposer_name = forms.CharField(max_length=255, required=False)
    additional_notes = forms.CharField(widget=forms.Textarea, required=False)
