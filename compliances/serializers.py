from rest_framework import serializers
from .models import ComplianceTask, ComplianceDocument

class ComplianceTaskSerializer(serializers.ModelSerializer):
    fund_name = serializers.CharField(source='fund.name', read_only=True)
    
    class Meta:
        model = ComplianceTask
        fields = '__all__'

class ComplianceDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceDocument
        fields = '__all__'