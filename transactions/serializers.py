from rest_framework import serializers
from .models import Transaction, InvestorCommitment

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"

class InvestorCommitmentSerializer(serializers.ModelSerializer):
    fund_name = serializers.CharField(source="fund.name", read_only=True)
    investor_name = serializers.CharField(source="investor.name", read_only=True)

    class Meta:
        model = InvestorCommitment
        fields = [
            "id",
            "fund",          # fund id (for linking in frontend)
            "fund_name",     # fund name (convenience)
            "investor",      # investor id
            "investor_name", # investor name
            "commitment_date",
            "amount_committed",
        ]