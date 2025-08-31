# funds/forms.py
from django import forms
from .models import Fund, Document
from investors.models import Investor
# Import the transaction models that these forms will create
from transactions.models import InvestorCommitment, CapitalCall

# Common styling attributes for form widgets
form_widget_attrs = {
    'class': 'w-full p-2 border border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'
}

class FundForm(forms.ModelForm):
    class Meta:
        model = Fund
        fields = ['name', 'sebi_registration_number', 'category', 'corpus', 'date_of_inception', 'manager']
        widgets = {
            'name': forms.TextInput(attrs=form_widget_attrs),
            'sebi_registration_number': forms.TextInput(attrs=form_widget_attrs),
            'category': forms.Select(attrs=form_widget_attrs),
            'corpus': forms.NumberInput(attrs=form_widget_attrs),
            'date_of_inception': forms.DateInput(attrs={'type': 'date', **form_widget_attrs}),
            'manager': forms.Select(attrs=form_widget_attrs),
        }

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file', 'investor']
        widgets = {
            'title': forms.TextInput(attrs=form_widget_attrs),
            'file': forms.FileInput(attrs={'class': 'w-full'}),
            'investor': forms.Select(attrs=form_widget_attrs),
        }

    def __init__(self, *args, **kwargs):
        self.fund = kwargs.pop('fund', None)
        super().__init__(*args, **kwargs)
        if self.fund:
            committed_investor_ids = self.fund.commitments.values_list('investor_id', flat=True)
            self.fields['investor'].queryset = Investor.objects.filter(id__in=committed_investor_ids)
        else:
            self.fields['investor'].queryset = Investor.objects.none()

# --- RESTORED FORMS ---

class FundCommitmentForm(forms.ModelForm):
    """
    Form for adding an investor's commitment to a specific fund.
    This form lives in the 'funds' app for UI purposes but acts on a 'transactions' model.
    """
    class Meta:
        model = InvestorCommitment
        # Note: 'commitment_date' and 'fund' will be set in the view.
        fields = ['investor', 'amount_committed']
        widgets = {
            'investor': forms.Select(attrs=form_widget_attrs),
            'amount_committed': forms.NumberInput(attrs=form_widget_attrs),
        }

    def __init__(self, *args, **kwargs):
        self.fund = kwargs.pop('fund', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        investor = cleaned_data.get('investor')
        
        if self.fund and investor:
            if InvestorCommitment.objects.filter(fund=self.fund, investor=investor).exists():
                self.add_error('investor', f"{investor.name} already has a commitment to this fund.")
        
        return cleaned_data


class CapitalCallForm(forms.ModelForm):
    """
    Form for creating a capital call for a specific fund.
    Lives in the 'funds' app for UI but creates a 'transactions' model instance.
    """
    class Meta:
        model = CapitalCall
        # Note: 'fund' will be set in the view. We assume one call per investor for simplicity here.
        fields = ['investor', 'call_date', 'amount_called', 'reference']
        widgets = {
            'investor': forms.Select(attrs=form_widget_attrs),
            'call_date': forms.DateInput(attrs={'type': 'date', **form_widget_attrs}),
            'amount_called': forms.NumberInput(attrs=form_widget_attrs),
            'reference': forms.TextInput(attrs=form_widget_attrs),
        }

    def __init__(self, *args, **kwargs):
        self.fund = kwargs.pop('fund', None)
        super().__init__(*args, **kwargs)
        if self.fund:
            # Filter investors to only those committed to this fund
            committed_investor_ids = self.fund.commitments.values_list('investor_id', flat=True)
            self.fields['investor'].queryset = Investor.objects.filter(id__in=committed_investor_ids)
