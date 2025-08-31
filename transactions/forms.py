# transactions/forms.py
from django import forms
from .models import PurchaseTransaction, RedemptionTransaction, DrawdownReceipt, Distribution, InvestorCommitment, CapitalCall
from investee_companies.models import Shareholding, InvesteeCompany
from funds.models import Fund
from investors.models import Investor

# A dictionary of common attributes to apply to form widgets for consistent styling.
form_widget_attrs = {
    'class': 'w-full p-2 border border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'
}

# A list of optional fields common to both transaction types.
COMMON_OPTIONAL_FIELDS = [
    'fees', 'taxes', 'currency', 'fx_rate', 'status', 
    'external_ref', 'import_batch_id', 'notes'
]

# --- Base Forms for Reusability ---

class InvestorTransactionBaseForm(forms.ModelForm):
    """
    A base form for transactions involving a specific fund's investors.
    It filters the 'investor' dropdown to show only relevant investors.
    """
    investor = forms.ModelChoiceField(
        queryset=Investor.objects.none(),  # Start with an empty queryset
        widget=forms.Select(attrs=form_widget_attrs)
    )

    def __init__(self, *args, **kwargs):
        self.fund = kwargs.pop('fund', None)
        super().__init__(*args, **kwargs)
        if self.fund:
            # Get IDs of investors who have committed to this fund
            committed_investor_ids = InvestorCommitment.objects.filter(fund=self.fund).values_list('investor_id', flat=True)
            self.fields['investor'].queryset = Investor.objects.filter(id__in=committed_investor_ids).order_by('name')

class TransactionBaseForm(forms.ModelForm):
    """
    A base form for transactions that handles:
    1. Filtering investee companies to those associated with the current fund.
    2. Dependent dropdown logic for 'share_capital' based on 'investee_company'.
    """
    investee_company = forms.ModelChoiceField(
        queryset=InvesteeCompany.objects.all(),
        widget=forms.Select(attrs=form_widget_attrs)
    )
    share_capital = forms.ModelChoiceField(
        queryset=Shareholding.objects.none(),
        required=False,
        widget=forms.Select(attrs=form_widget_attrs)
    )

    def __init__(self, *args, **kwargs):
        self.fund = kwargs.pop('fund', None)
        super().__init__(*args, **kwargs)

        if not self.fund:
            raise ValueError("A 'fund' instance must be passed to the form.")

        # Filter investee companies based on the fund's portfolio
        self.fields['investee_company'].queryset = InvesteeCompany.objects.all().order_by('name')
        
        # If form is bound with data (e.g., on POST or editing an existing instance)
        if 'investee_company' in self.data:
            try:
                company_id = int(self.data.get('investee_company'))
                self.fields['share_capital'].queryset = Shareholding.objects.filter(
                    investee_company_id=company_id
                ).order_by('share_type')
            except (ValueError, TypeError):
                pass # Gracefully handle cases where company_id is not a valid number
        elif self.instance.pk and self.instance.investee_company:
            self.fields['share_capital'].queryset = self.instance.investee_company.shareholdings.order_by('share_type')


class PurchaseTransactionForm(TransactionBaseForm):
    class Meta:
        model = PurchaseTransaction
        fields = [
            'investee_company', 'share_capital', 'quantity',
            'purchase_rate', 'face_value', 'purchase_date',
            *COMMON_OPTIONAL_FIELDS
        ]
        widgets = {
            'quantity': forms.NumberInput(attrs=form_widget_attrs),
            'purchase_rate': forms.NumberInput(attrs=form_widget_attrs),
            'face_value': forms.NumberInput(attrs=form_widget_attrs),
            'purchase_date': forms.DateInput(attrs={'type': 'date', **form_widget_attrs}),
            'status': forms.Select(attrs=form_widget_attrs),
            'fees': forms.NumberInput(attrs={'placeholder': '0.00', **form_widget_attrs}),
            'taxes': forms.NumberInput(attrs={'placeholder': '0.00', **form_widget_attrs}),
            'currency': forms.TextInput(attrs={'placeholder': 'INR', **form_widget_attrs}),
            'fx_rate': forms.NumberInput(attrs={'placeholder': '1.00', **form_widget_attrs}),
            'external_ref': forms.TextInput(attrs=form_widget_attrs),
            'import_batch_id': forms.TextInput(attrs=form_widget_attrs),
            'notes': forms.Textarea(attrs={'rows': 2, **form_widget_attrs}),
        }

class RedemptionTransactionForm(TransactionBaseForm):
    class Meta:
        model = RedemptionTransaction
        fields = [
            'investee_company', 'share_capital', 'quantity',
            'redemption_rate', 'redemption_date',
            *COMMON_OPTIONAL_FIELDS
        ]
        widgets = {
            'quantity': forms.NumberInput(attrs=form_widget_attrs),
            'redemption_rate': forms.NumberInput(attrs=form_widget_attrs),
            'redemption_date': forms.DateInput(attrs={'type': 'date', **form_widget_attrs}),
            'status': forms.Select(attrs=form_widget_attrs),
            'notes': forms.Textarea(attrs={'rows': 2, **form_widget_attrs}),
        }

# --- Forms for Investor-Specific Transactions ---

class InvestorCommitmentForm(forms.ModelForm):
    class Meta:
        model = InvestorCommitment
        fields = ['investor', 'commitment_date', 'amount_committed']
        widgets = {
            'commitment_date': forms.DateInput(attrs={'type': 'date', **form_widget_attrs}),
            'amount_committed': forms.NumberInput(attrs=form_widget_attrs),
        }

    def __init__(self, *args, **kwargs):
        self.fund = kwargs.pop('fund', None)   # Fund instance passed from view
        super().__init__(*args, **kwargs)
        self.fields['investor'].queryset = Investor.objects.all().order_by('name')

    def clean_amount_committed(self):
        amount = self.cleaned_data['amount_committed']
        if self.fund:
            total_existing = self.fund.commitments.aggregate(total=forms.models.Sum('amount_committed'))['total'] or 0
            new_total = total_existing + amount

            if self.instance.pk:  # Editing existing commitment
                new_total -= self.instance.amount_committed

            if new_total > self.fund.corpus:
                raise forms.ValidationError(
                    f"Total commitments ({new_total}) cannot exceed Fund corpus ({self.fund.corpus})."
                )
        return amount


class CapitalCallForm(InvestorTransactionBaseForm):
    class Meta:
        model = CapitalCall
        fields = ['investor', 'call_date', 'amount_called', 'reference']
        widgets = {
            'call_date': forms.DateInput(attrs={'type': 'date', **form_widget_attrs}),
            'amount_called': forms.NumberInput(attrs=form_widget_attrs),
            'reference': forms.TextInput(attrs=form_widget_attrs),
        }


class DrawdownReceiptForm(InvestorTransactionBaseForm):
    class Meta:
        model = DrawdownReceipt
        fields = ['investor', 'receipt_date', 'amount_received', 'reference']
        widgets = {
            'receipt_date': forms.DateInput(attrs={'type': 'date', **form_widget_attrs}),
            'amount_received': forms.NumberInput(attrs=form_widget_attrs),
            'reference': forms.TextInput(attrs=form_widget_attrs),
        }


class DistributionForm(InvestorTransactionBaseForm):
    class Meta:
        model = Distribution
        fields = ['investor', 'distribution_date', 'amount_distributed', 'notes']
        widgets = {
            'distribution_date': forms.DateInput(attrs={'type': 'date', **form_widget_attrs}),
            'amount_distributed': forms.NumberInput(attrs=form_widget_attrs),
            'notes': forms.Textarea(attrs={'rows': 2, **form_widget_attrs}),
        }

