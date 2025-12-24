from rest_framework import serializers
from .models import (
    PurchaseTransaction, RedemptionTransaction, 
    InvestorCommitment, CapitalCall, DrawdownReceipt, 
    Distribution, InvestorUnitIssue
)

class CurrencyMetaSerializer(serializers.ModelSerializer):
    """Mixin to add consistent currency codes and symbols to transactions."""
    currency_code = serializers.CharField(source='transaction_currency.code', read_only=True)
    currency_symbol = serializers.CharField(source='transaction_currency.symbol', read_only=True)
    fund_currency_code = serializers.CharField(source='fund.currency.code', read_only=True)
    fund_currency_symbol = serializers.CharField(source='fund.currency.symbol', read_only=True)

    class Meta:
        abstract = True

class PurchaseSerializer(CurrencyMetaSerializer):
    company_name = serializers.CharField(source='investee_company.name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True)

    class Meta:
        model = PurchaseTransaction
        fields = '__all__'
        read_only_fields = ['amount_fund_currency']

class RedemptionSerializer(CurrencyMetaSerializer):
    company_name = serializers.CharField(source='investee_company.name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True)
    
    class Meta:
        model = RedemptionTransaction
        fields = '__all__'
        read_only_fields = ['amount_fund_currency', 'cost_basis', 'realized_gain']

class InvestorCommitmentSerializer(CurrencyMetaSerializer):
    investor_name = serializers.CharField(source='investor.name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True)

    class Meta:
        model = InvestorCommitment
        fields = '__all__'
        read_only_fields = ['amount_committed_fund_ccy']

class CapitalCallSerializer(CurrencyMetaSerializer):
    investor_name = serializers.CharField(source='investor.name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True)
    
    class Meta:
        model = CapitalCall
        fields = '__all__'
        read_only_fields = ['amount_called_fund_ccy']

class DrawdownReceiptSerializer(CurrencyMetaSerializer):
    investor_name = serializers.CharField(source='investor.name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True)

    class Meta:
        model = DrawdownReceipt
        fields = '__all__'
        read_only_fields = ['amount_received_fund_ccy']

class DistributionSerializer(CurrencyMetaSerializer):
    investor_name = serializers.CharField(source='investor.name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True)
    net_amount = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = Distribution
        fields = '__all__'
        read_only_fields = ['gross_amount_fund_ccy']

class InvestorUnitIssueSerializer(CurrencyMetaSerializer):
    investor_name = serializers.CharField(source='investor.name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True)

    class Meta:
        model = InvestorUnitIssue
        fields = '__all__'