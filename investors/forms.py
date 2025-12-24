# investors/forms.py
from django import forms
from .models import Investor, InvestorDocument

# Consistent Portal UI Styling
STYLE = {'class': 'w-full px-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all'}

class InvestorForm(forms.ModelForm):
    class Meta:
        model = Investor
        fields = [
            'name', 'investor_type', 'email', 'phone', 'pan', 
            'demat_account_no', 'dp_id', 'accreditation_status', 
            'accreditation_expiry', 'kyc_status', 'risk_appetite'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Full Legal Name', **STYLE}),
            'investor_type': forms.Select(attrs=STYLE),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Address', **STYLE}),
            'phone': forms.TextInput(attrs={'placeholder': '+91 ...', **STYLE}),
            'pan': forms.TextInput(attrs={'placeholder': 'ABCDE1234F', **STYLE}),
            'demat_account_no': forms.TextInput(attrs={'placeholder': '16-digit Client ID', **STYLE}),
            'dp_id': forms.TextInput(attrs={'placeholder': 'IN30...', **STYLE}),
            'accreditation_status': forms.Select(attrs=STYLE),
            'accreditation_expiry': forms.DateInput(attrs={'type': 'date', **STYLE}),
            'kyc_status': forms.Select(attrs=STYLE),
            'risk_appetite': forms.Select(attrs=STYLE),
        }

class InvestorDocumentForm(forms.ModelForm):
    class Meta:
        model = InvestorDocument
        fields = ['doc_type', 'file', 'notes']
        widgets = {
            'doc_type': forms.Select(attrs=STYLE),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional internal notes...', **STYLE}),
            'file': forms.FileInput(attrs={'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
        }