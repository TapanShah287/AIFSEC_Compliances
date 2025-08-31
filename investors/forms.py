from transactions.models import InvestorCommitment
# investors/forms.py
from django import forms
from .models import (
    KYCStatus, FATCADeclaration, Document, Investor,
    CommunicationLog, InvestorBankAccount
)
from funds.models import Fund

class KYCForm(forms.ModelForm):
    class Meta:
        model = KYCStatus
        fields = ['kyc_status', 'investor_type', 'date_completed', 'notes']
        widgets = {
            'date_completed': forms.DateInput(attrs={'type': 'date'}),
        }

class FATCAForm(forms.ModelForm):
    class Meta:
        model = FATCADeclaration
        fields = ['declaration_status', 'is_us_person', 'date_submitted']
        widgets = {
            'date_submitted': forms.DateInput(attrs={'type': 'date'}),
        }

class IndividualDocumentForm(forms.ModelForm):
    title = forms.CharField(max_length=255, required=True)
    file = forms.FileField(required=True)
    class Meta:
        model = Document
        fields = ['title', 'file']

class NonIndividualDocumentForm(forms.ModelForm):
    DOCUMENT_CHOICES = [
        ('COI', 'Certificate of Incorporation'),
        ('AOA', 'Articles of Association (AOA)'),
        ('MOA', 'Memorandum of Association (MOA)'),
        ('PR', 'Partnership Resolution'),
        ('TR', 'Trust Resolution'),
        ('BR', 'Board Resolution'),
    ]
    title = forms.ChoiceField(choices=DOCUMENT_CHOICES)
    file = forms.FileField(required=True)
    class Meta:
        model = Document
        fields = ['title', 'file']

class InvestorCommitmentForm(forms.ModelForm):
    fund = forms.ModelChoiceField(queryset=Fund.objects.all(), required=True, label="Fund")
    class Meta:
        model = InvestorCommitment
        fields = ["fund", "amount_committed"]
        labels = { "amount_committed": "Commitment Amount (₹)" }

class InvestorForm(forms.ModelForm):
    class Meta:
        model = Investor
        fields = ["name", "email", "phone", "type"]

class CommunicationLogForm(forms.ModelForm):
    class Meta:
        model = CommunicationLog
        fields = ['communication_date', 'communication_type', 'notes']
        widgets = {
            'communication_date': forms.DateInput(attrs={'type': 'date'}),
        }

class InvestorBankAccountForm(forms.ModelForm):
    class Meta:
        model = InvestorBankAccount
        fields = ['bank_name', 'account_number', 'ifsc_code', 'is_primary']
