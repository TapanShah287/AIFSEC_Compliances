from rest_framework import serializers
from .models import Fund
# This is the line that was missing. It tells this file where to find the transaction models.
from transactions.models import InvestorCommitment, CapitalCall, Distribution

class FundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fund
        fields = "__all__"

class InvestorCommitmentSerializer(serializers.ModelSerializer):
    # This makes the API show the investor's name instead of just their ID.
    investor_name = serializers.CharField(source='investor.name', read_only=True)

    class Meta:
        model = InvestorCommitment
        fields = ['id', 'investor_name', 'commitment_date', 'amount_committed']

class CapitalCallSerializer(serializers.ModelSerializer):
    investor_name = serializers.CharField(source='investor.name', read_only=True)

    class Meta:
        model = CapitalCall
        fields = ['id', 'investor_name', 'call_date', 'amount_called', 'reference']

class DistributionSerializer(serializers.ModelSerializer):
    investor_name = serializers.CharField(source='investor.name', read_only=True)

    class Meta:
        model = Distribution
        fields = ['id', 'investor_name', 'distribution_date', 'amount_distributed', 'notes']