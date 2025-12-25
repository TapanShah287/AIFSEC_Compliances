from django import forms
from .models import CapitalCall, DrawdownReceipt, PurchaseTransaction, RedemptionTransaction, Distribution, InvestorCommitment

INPUT_STYLE = 'w-full px-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all'

class InvestorCommitmentForm(forms.ModelForm):
    class Meta:
        model = InvestorCommitment
        fields = ['fund', 'investor', 'amount_committed', 'commitment_date']
        widgets = {
            'fund': forms.Select(attrs={'class': INPUT_STYLE}),
            'investor': forms.Select(attrs={'class': INPUT_STYLE}),
            'amount_committed': forms.NumberInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Total Commitment Amount'}),
            'commitment_date': forms.DateInput(attrs={'class': INPUT_STYLE, 'type': 'date'}),
        }

class CapitalCallForm(forms.ModelForm):
    class Meta:
        model = CapitalCall
        fields = ['fund', 'investor', 'call_date', 'due_date', 'amount_called', 'purpose', 'reference']
        widgets = {
            'fund': forms.Select(attrs={'class': INPUT_STYLE}),
            'investor': forms.Select(attrs={'class': INPUT_STYLE}),
            'call_date': forms.DateInput(attrs={'class': INPUT_STYLE, 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': INPUT_STYLE, 'type': 'date'}),
            'amount_called': forms.NumberInput(attrs={'class': INPUT_STYLE, 'step': '0.01'}),
            'purpose': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Reason'}),
            'reference': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Unique Ref'}),
        }

class DrawdownReceiptForm(forms.ModelForm):
    class Meta:
        model = DrawdownReceipt
        fields = ['capital_call', 'received_date', 'amount_received', 'payment_mode', 'transaction_ref']
        widgets = {
            'capital_call': forms.Select(attrs={'class': INPUT_STYLE}),
            'received_date': forms.DateInput(attrs={'class': INPUT_STYLE, 'type': 'date'}),
            'amount_received': forms.NumberInput(attrs={'class': INPUT_STYLE, 'step': '0.01'}),
            'payment_mode': forms.Select(attrs={'class': INPUT_STYLE}),
            'transaction_ref': forms.TextInput(attrs={'class': INPUT_STYLE}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['capital_call'].queryset = CapitalCall.objects.filter(is_paid=False)

class PurchaseTransactionForm(forms.ModelForm):
    class Meta:
        model = PurchaseTransaction
        fields = ['fund', 'investee_company', 'share_class', 'transaction_date', 'quantity', 'price_per_share', 'currency']
        widgets = {
            'fund': forms.Select(attrs={'class': INPUT_STYLE}),
            'investee_company': forms.Select(attrs={'class': INPUT_STYLE}),
            'share_class': forms.Select(attrs={'class': INPUT_STYLE}),
            'transaction_date': forms.DateInput(attrs={'class': INPUT_STYLE, 'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_STYLE}),
            'price_per_share': forms.NumberInput(attrs={'class': INPUT_STYLE, 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': INPUT_STYLE}),
        }

class RedemptionForm(forms.ModelForm):
    class Meta:
        model = RedemptionTransaction
        fields = ['fund', 'investee_company', 'share_class', 'transaction_date', 'quantity', 'price_per_share']
        widgets = {
            'fund': forms.Select(attrs={'class': INPUT_STYLE}),
            'investee_company': forms.Select(attrs={'class': INPUT_STYLE}),
            'share_class': forms.Select(attrs={'class': INPUT_STYLE}),
            'transaction_date': forms.DateInput(attrs={'class': INPUT_STYLE, 'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Number of shares sold'}),
            'price_per_share': forms.NumberInput(attrs={'class': INPUT_STYLE, 'step': '0.01', 'placeholder': 'Sale price per share'}),
        }

class DistributionForm(forms.ModelForm):
    class Meta:
        model = Distribution
        fields = ['fund', 'investor', 'distribution_date', 'gross_amount', 'distribution_type', 'remarks']
        widgets = {
            'fund': forms.Select(attrs={'class': INPUT_STYLE}),
            'investor': forms.Select(attrs={'class': INPUT_STYLE}),
            'distribution_date': forms.DateInput(attrs={'class': INPUT_STYLE, 'type': 'date'}),
            'gross_amount': forms.NumberInput(attrs={'class': INPUT_STYLE, 'step': '0.01'}),
            'distribution_type': forms.Select(attrs={'class': INPUT_STYLE}),
            'remarks': forms.Textarea(attrs={'class': INPUT_STYLE, 'rows': 2}),
        }