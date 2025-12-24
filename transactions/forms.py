from django import forms
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
from .models import (
    PurchaseTransaction, RedemptionTransaction,
    InvestorCommitment, CapitalCall, DrawdownReceipt, 
    Distribution
)
from investee_companies.models import ShareCapital, InvesteeCompany, Shareholding
from investors.models import Investor
from currencies.utils import get_exchange_rate

# Shared styling for consistent Portal UI
INPUT_STYLE = 'w-full px-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all'

class BaseTransactionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.fund_context = kwargs.pop('fund_context', None)
        super().__init__(*args, **kwargs)
        
        # Apply premium styling to all fields
        for field in self.fields.values():
            field.widget.attrs.update({'class': INPUT_STYLE})
            
        if self.fund_context:
            # Multi-Currency Initialization
            if 'transaction_currency' in self.fields:
                self.fields['transaction_currency'].initial = self.fund_context.currency
            
            if not self.instance.pk and 'exchange_rate' in self.fields:
                rate = get_exchange_rate(self.fund_context.currency.code, timezone.now().date())
                self.fields['exchange_rate'].initial = rate

class PurchaseForm(BaseTransactionForm):
    class Meta:
        model = PurchaseTransaction
        fields = ['investee_company', 'share_capital', 'transaction_currency', 'exchange_rate', 'quantity', 'price', 'trade_date', 'settle_date', 'notes']
        widgets = {
            'trade_date': forms.DateInput(attrs={'type': 'date'}),
            'settle_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['investee_company'].queryset = InvesteeCompany.objects.all().order_by('name')
        
        # Dependent dropdown logic (Share Capital depends on Company)
        if 'investee_company' in self.data:
            try:
                company_id = int(self.data.get('investee_company'))
                self.fields['share_capital'].queryset = ShareCapital.objects.filter(investee_company_id=company_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['share_capital'].queryset = self.instance.investee_company.share_classes.all()
        else:
            self.fields['share_capital'].queryset = ShareCapital.objects.none()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # Update Shareholding (Cap Table)
            if instance.fund:
                obj, created = Shareholding.objects.get_or_create(
                    investee_company=instance.investee_company,
                    share_capital=instance.share_capital,
                    holder_name=instance.fund.name,
                    defaults={
                        'number_of_shares': 0,
                        'face_value': instance.share_capital.face_value,
                        'share_type': instance.share_capital.share_type,
                        # Link a pseudo-investor if needed, or leave blank
                    }
                )
                obj.number_of_shares += instance.quantity
                obj.save()
        return instance

class RedemptionForm(BaseTransactionForm):
    class Meta:
        model = RedemptionTransaction
        fields = ['investee_company', 'share_capital', 'transaction_currency', 'exchange_rate', 'quantity', 'price', 'trade_date', 'settle_date', 'notes']
        widgets = {
            'trade_date': forms.DateInput(attrs={'type': 'date'}),
            'settle_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['investee_company'].queryset = InvesteeCompany.objects.all().order_by('name')
        if self.is_bound: # If form is submitted
            self.fields['share_capital'].queryset = ShareCapital.objects.all()
        elif self.instance.pk:
            self.fields['share_capital'].queryset = ShareCapital.objects.filter(investee_company=self.instance.investee_company)
        elif self.fund_context:
             # Only show companies/shares the fund currently holds
             # This is complex, simplified to all share classes for now
             self.fields['share_capital'].queryset = ShareCapital.objects.all()
        else:
            self.fields['share_capital'].queryset = ShareCapital.objects.none()

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit and hasattr(instance, 'fund') and instance.fund:
            with transaction.atomic():
                try:
                    holding = Shareholding.objects.get(
                        investee_company=instance.investee_company,
                        share_capital=instance.share_capital,
                        holder_name=instance.fund.name
                    )
                    holding.number_of_shares -= instance.quantity
                    holding.save()
                except Shareholding.DoesNotExist:
                    pass
        return instance

class InvestorTransactionBaseForm(BaseTransactionForm):
    """
    A base form for transactions involving a specific fund's investors.
    It filters the 'investor' dropdown to show only relevant investors.
    """
    investor = forms.ModelChoiceField(
        queryset=Investor.objects.none(),  # Start with an empty queryset
        widget=forms.Select(attrs={'class': INPUT_STYLE})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.fund_context:
            # Get IDs of investors who have committed to this fund
            committed_investor_ids = InvestorCommitment.objects.filter(fund=self.fund_context).values_list('investor_id', flat=True)
            self.fields['investor'].queryset = Investor.objects.filter(id__in=committed_investor_ids)


class InvestorCommitmentForm(BaseTransactionForm):
    # Allows adding NEW investors, so we override the base queryset logic
    investor = forms.ModelChoiceField(
        queryset=Investor.objects.all(),
        widget=forms.Select(attrs={'class': INPUT_STYLE})
    )

    class Meta:
        model = InvestorCommitment
        fields = ['investor', 'amount_committed', 'transaction_currency', 'exchange_rate', 'commitment_date']
        widgets = {
            'commitment_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_amount_committed(self):
        amount = self.cleaned_data.get('amount_committed')
        if amount <= 0:
            raise forms.ValidationError("Commitment amount must be positive.")
        
        # Check if total commitments exceed fund corpus (optional business rule)
        if self.fund_context and self.fund_context.corpus:
            current_total = InvestorCommitment.objects.filter(fund=self.fund_context).aggregate(Sum('amount_committed'))['amount_committed__sum'] or 0
            new_total = current_total + amount
            # Warn but don't block, as corpus might be flexible
            # if new_total > self.fund_context.corpus:
            #     pass 
        return amount


class CapitalCallForm(InvestorTransactionBaseForm):
    class Meta:
        model = CapitalCall
        fields = ['investor', 'call_date', 'amount_called', 'reference']
        widgets = {
            'call_date': forms.DateInput(attrs={'type': 'date'}),
        }


class DrawdownReceiptForm(InvestorTransactionBaseForm):
    class Meta:
        model = DrawdownReceipt
        fields = ['investor', 'receipt_date', 'amount_received', 'reference']
        widgets = {
            'receipt_date': forms.DateInput(attrs={'type': 'date'}),
        }


class DistributionForm(InvestorTransactionBaseForm):
    class Meta:
        model = Distribution
        fields = ['investor', 'paid_date', 'gross_amount', 'tax_withheld']
        widgets = {
            'paid_date': forms.DateInput(attrs={'type': 'date'}),
        }