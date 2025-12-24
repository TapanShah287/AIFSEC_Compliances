from rest_framework import serializers
from .models import Fund, NavSnapshot, Document, StewardshipEngagement

class FundSerializer(serializers.ModelSerializer):
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    
    class Meta:
        model = Fund
        fields = "__all__"

class NavSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = NavSnapshot
        fields = "__all__"

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = "__all__"

class StewardshipEngagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StewardshipEngagement
        fields = "__all__"