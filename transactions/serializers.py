from rest_framework import serializers
from .models import (
    PurchaseTransaction, RedemptionTransaction, 
    InvestorCommitment, CapitalCall, DrawdownReceipt, 
    Distribution, InvestorUnitIssue
)

class CurrencyMetaSerializer(serializers.ModelSerializer):
    """Mixin to add consistent currency codes and symbols to transactions."""
    # Note: 'currency' is the field name in our latest models.py
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)
    fund_currency_code = serializers.CharField(source='fund.currency.code', read_only=True)
    fund_currency_symbol = serializers.CharField(source='fund.currency.symbol', read_only=True)

    class Meta:
        abstract = True

class PurchaseSerializer(CurrencyMetaSerializer):
    company_name = serializers.CharField(source='investee_company.name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True)
    total_val = serializers.DecimalField(source='total_amount', max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = PurchaseTransaction
        fields = '__all__'

class RedemptionSerializer(CurrencyMetaSerializer):
    company_name = serializers.CharField(source='investee_company.name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True)
    total_proceeds = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    
    class Meta:
        model = RedemptionTransaction
        fields = '__all__'
        read_only_fields = ['cost_basis', 'realized_gain']

class InvestorCommitmentSerializer(CurrencyMetaSerializer):
    investor_name = serializers.CharField(source='investor.name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True)

    class Meta:
        model = InvestorCommitment
        fields = '__all__'

class CapitalCallSerializer(CurrencyMetaSerializer):
    investor_name = serializers.CharField(source='investor.name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True)
    
    class Meta:
        model = CapitalCall
        fields = '__all__'

class DrawdownReceiptSerializer(CurrencyMetaSerializer):
    investor_name = serializers.CharField(source='capital_call.investor.name', read_only=True)
    fund_name = serializers.CharField(source='capital_call.fund.name', read_only=True)

    class Meta:
        model = DrawdownReceipt
        fields = '__all__'

class DistributionSerializer(CurrencyMetaSerializer):
    investor_name = serializers.CharField(source='investor.name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True)

    class Meta:
        model = Distribution
        fields = '__all__'

class InvestorUnitIssueSerializer(CurrencyMetaSerializer):
    investor_name = serializers.CharField(source='investor.name', read_only=True)
    fund_name = serializers.CharField(source='fund.name', read_only=True)

    class Meta:
        model = InvestorUnitIssue
        fields = '__all__'