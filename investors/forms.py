# investors/forms.py
from django import forms
from .models import Investor, InvestorDocument
from .models import InvestorBankDetail

# Consistent Portal UI Styling
STYLE = {'class': 'w-full px-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all'}

class InvestorForm(forms.ModelForm):
    class Meta:
        model = Investor

        exclude = ['kyc_status', 'created_at', 'updated_at', 'documents']
        
        fields = [
            'name', 'investor_type', 'manager_entities', 'email', 'phone', 'pan', 
            'demat_account_no', 'dp_id', 'accreditation_status', 
            'accreditation_expiry', 'risk_appetite'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Full Legal Name', **STYLE}),
            'investor_type': forms.Select(attrs=STYLE),
            'manager_entities': forms.SelectMultiple(attrs=STYLE),
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
        
    def __init__(self, *args, **kwargs):
        # Optional: Logic to filter or auto-select the active manager entity
        active_manager = kwargs.pop('active_manager', None)
        super().__init__(*args, **kwargs)
        
        if active_manager:
            self.fields['manager_entities'].initial = [active_manager]

class InvestorDocumentForm(forms.ModelForm):
    class Meta:
        model = InvestorDocument
        fields = ['doc_type', 'file', 'notes']
        widgets = {
            'doc_type': forms.Select(attrs=STYLE),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional internal notes...', **STYLE}),
            'file': forms.FileInput(attrs={'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
        }

class BankDetailForm(forms.ModelForm):
    class Meta:
        model = InvestorBankDetail
        fields = ['bank_name', 'account_number', 'ifsc_code', 'account_holder_name', 'is_primary', 'verification_doc']
        widgets = {
            'bank_name': forms.TextInput(attrs={'placeholder': 'e.g. HDFC Bank'}),
            'account_number': forms.TextInput(attrs={'placeholder': 'Account No.'}),
            'ifsc_code': forms.TextInput(attrs={'placeholder': 'HDFC0001234', 'class': 'uppercase'}),
            'account_holder_name': forms.TextInput(attrs={'placeholder': 'Name as per Bank Records'}),
        }

    def clean_ifsc_code(self):
        code = self.cleaned_data['ifsc_code'].upper()
        if len(code) != 11:
            raise forms.ValidationError("IFSC Code must be exactly 11 characters.")
        return code