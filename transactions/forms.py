from django import forms
from .models import (
    CapitalCall, DrawdownReceipt, PurchaseTransaction, 
    RedemptionTransaction, Distribution, InvestorCommitment
)
from funds.models import Fund
from investors.models import Investor

# Your existing Tailwind Style
INPUT_STYLE = 'w-full px-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all'

# ==========================================
# 1. CASH INFLOW (Fundraising & Calls)
# ==========================================

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
            'due_date': forms.DateInput(attrs={'class': INPUT_STYLE, 'type': 'date'}), # Critical for "Overdue" logic
            'amount_called': forms.NumberInput(attrs={'class': INPUT_STYLE, 'step': '0.01'}),
            'purpose': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'e.g. Investment in ABC Corp'}),
            'reference': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Call Notice Ref #'}),
        }

    def __init__(self, *args, **kwargs):
        # Extract optional fund_context to filter investors
        self.fund_context = kwargs.pop('fund_context', None)
        super().__init__(*args, **kwargs)
        
        if self.fund_context:
            self.fields['fund'].initial = self.fund_context
            self.fields['investor'].queryset = Investor.objects.filter(
                commitments__fund=self.fund_context
            ).distinct()

class DrawdownReceiptForm(forms.ModelForm):
    class Meta:
        model = DrawdownReceipt
        fields = ['fund', 'investor', 'capital_call', 'amount_received', 'date_received', 'transaction_reference', 'remarks']
        
        widgets = {
            'fund': forms.Select(attrs={'class': INPUT_STYLE}),
            'investor': forms.Select(attrs={'class': INPUT_STYLE}),
            'capital_call': forms.Select(attrs={'class': INPUT_STYLE}), # Can also be HiddenInput if strictly linked
            'amount_received': forms.NumberInput(attrs={'class': INPUT_STYLE, 'step': '0.01', 'placeholder': '0.00'}),
            'date_received': forms.DateInput(attrs={'class': INPUT_STYLE, 'type': 'date'}),
            'transaction_reference': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'UTR / Cheque No.'}),
            'remarks': forms.Textarea(attrs={'class': INPUT_STYLE, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # LOGIC: If 'capital_call' is pre-filled (e.g. from Dashboard "Pay" button), 
        # we lock the Investor/Fund fields so they can't be changed.
        if self.initial.get('capital_call') or (self.instance and self.instance.capital_call_id):
            
            # Make fields Read-Only in UI
            self.fields['investor'].widget.attrs['readonly'] = True
            self.fields['fund'].widget.attrs['readonly'] = True
            self.fields['capital_call'].widget.attrs['readonly'] = True
            
            # Visual indication (Greyed out)
            locked_style = INPUT_STYLE + ' bg-slate-100 cursor-not-allowed'
            self.fields['investor'].widget.attrs['class'] = locked_style
            self.fields['fund'].widget.attrs['class'] = locked_style
            self.fields['capital_call'].widget.attrs['class'] = locked_style

# ==========================================
# 2. INVESTMENTS (Portfolio In/Out)
# ==========================================

class PurchaseTransactionForm(forms.ModelForm):
    class Meta:
        model = PurchaseTransaction
        fields = ['fund', 'investee_company', 'share_class', 'transaction_date', 'quantity', 'price_per_share', 'currency', 'transaction_costs']
        widgets = {
            'fund': forms.Select(attrs={'class': INPUT_STYLE}),
            'investee_company': forms.Select(attrs={'class': INPUT_STYLE}),
            'share_class': forms.Select(attrs={'class': INPUT_STYLE}),
            'transaction_date': forms.DateInput(attrs={'class': INPUT_STYLE, 'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Shares Bought'}),
            'price_per_share': forms.NumberInput(attrs={'class': INPUT_STYLE, 'step': '0.01'}),
            'transaction_costs': forms.NumberInput(attrs={'class': INPUT_STYLE, 'step': '0.01', 'placeholder': 'Fees/Taxes'}),
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
            'quantity': forms.NumberInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Shares Sold'}),
            'price_per_share': forms.NumberInput(attrs={'class': INPUT_STYLE, 'step': '0.01', 'placeholder': 'Exit Price'}),
        }

# ==========================================
# 3. CASH OUTFLOW (Distributions)
# ==========================================

class DistributionForm(forms.ModelForm):
    class Meta:
        model = Distribution
        # ENHANCEMENT: Added 'tds_deducted' for tax compliance
        fields = ['fund', 'investor', 'distribution_date', 'gross_amount', 'tds_deducted', 'distribution_type', 'remarks']
        widgets = {
            'fund': forms.Select(attrs={'class': INPUT_STYLE}),
            'investor': forms.Select(attrs={'class': INPUT_STYLE}),
            'distribution_date': forms.DateInput(attrs={'class': INPUT_STYLE, 'type': 'date'}),
            'gross_amount': forms.NumberInput(attrs={'class': INPUT_STYLE, 'step': '0.01', 'placeholder': 'Total Payout'}),
            'tds_deducted': forms.NumberInput(attrs={'class': INPUT_STYLE, 'step': '0.01', 'placeholder': 'Tax Withheld (TDS)'}),
            'distribution_type': forms.Select(attrs={'class': INPUT_STYLE}),
            'remarks': forms.Textarea(attrs={'class': INPUT_STYLE, 'rows': 2}),
        }