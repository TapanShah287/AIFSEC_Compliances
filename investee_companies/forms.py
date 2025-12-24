from django import forms
from django.forms import modelformset_factory
from .models import InvesteeCompany, Shareholding, ValuationReport, ShareValuation, ShareCapital


# Global style: Changed bg-slate-50 to bg-white for better contrast
INPUT_STYLE = 'w-full px-4 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all'

class InvesteeCompanyForm(forms.ModelForm):
    """Form for creating or updating an investee company."""
    class Meta:
        model = InvesteeCompany
        fields = ['name', 'cin', 'sector', 'incorporation_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Legal Entity Name'}),
            'cin': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'CIN Number'}),
            'sector': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'e.g. Fintech'}),
            'incorporation_date': forms.DateInput(attrs={'class': INPUT_STYLE, 'type': 'date'}),
        }

class ShareCapitalForm(forms.ModelForm):
    """
    Form to define a share class (Equity, Series A, etc.).
    FIXED: Added 'issued_shares' to allow editing Paid-up Units.
    """
    class Meta:
        model = ShareCapital
        fields = ['share_type', 'class_name', 'face_value', 'issued_shares', 'authorized_capital', 'as_on_date']
        widgets = {
            'share_type': forms.Select(attrs={'class': INPUT_STYLE}),
            'class_name': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'e.g. Series A'}),
            'face_value': forms.NumberInput(attrs={'class': INPUT_STYLE, 'placeholder': '10.00'}),
            'issued_shares': forms.NumberInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Paid-up Units'}),
            'authorized_capital': forms.NumberInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Total INR'}),
            'as_on_date': forms.DateInput(attrs={'class': INPUT_STYLE, 'type': 'date'}),
        }

# Formset for managing multiple share classes (Add/Edit/Delete)
ShareCapitalFormSet = modelformset_factory(
    ShareCapital,
    form=ShareCapitalForm,
    extra=1, 
    can_delete=True
)

class ShareholdingForm(forms.ModelForm):
    """
    Form for adding specific shareholder records to the Cap Table.
    Requirements:
    1. Filter instrument selection to the company.
    2. Support for linking to internal Investor registry or manual name.
    """
    class Meta:
        model = Shareholding
        fields = ['investor', 'holder_name', 'share_capital', 'number_of_shares']
        widgets = {
            'investor': forms.Select(attrs={'class': INPUT_STYLE}),
            'holder_name': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Optional: Manual holder name'}),
            'share_capital': forms.Select(attrs={'class': INPUT_STYLE}),
            'number_of_shares': forms.NumberInput(attrs={'class': INPUT_STYLE}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['share_capital'].queryset = ShareCapital.objects.filter(investee_company=company)

class ValuationReportForm(forms.ModelForm):
    """
    FIXED: Removed 'methodology' field as it is not in the ValuationReport model.
    """
    class Meta:
        model = ValuationReport
        fields = ['valuation_date', 'report_file']
        widgets = {
            'valuation_date': forms.DateInput(attrs={'class': INPUT_STYLE, 'type': 'date'}),
            'report_file': forms.FileInput(attrs={'class': 'text-sm'}),
        }

# Formset for handling per-share valuations for multiple classes
ShareValuationFormSet = modelformset_factory(
    ShareValuation,
    fields=('share_capital', 'per_share_value'),
    extra=0,
    widgets={
        'share_capital': forms.HiddenInput(),
        'per_share_value': forms.NumberInput(attrs={'class': INPUT_STYLE, 'placeholder': '0.00'}),
    }
)