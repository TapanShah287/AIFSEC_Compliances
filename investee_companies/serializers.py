from rest_framework import serializers
from .models import (
    InvesteeCompany, ShareCapital, ShareValuation, 
    CompanyFinancials, CorporateAction, Shareholding
)

class ShareCapitalSerializer(serializers.ModelSerializer):
    instrument_type_display = serializers.CharField(source='get_share_type_display', read_only=True)

    class Meta:
        model = ShareCapital
        fields = '__all__'

class ShareholdingSerializer(serializers.ModelSerializer):
    holder_name_display = serializers.CharField(source='display_holder', read_only=True)
    share_class = serializers.CharField(source='share_capital.class_name', read_only=True)
    share_type = serializers.CharField(source='share_capital.share_type', read_only=True)
    face_value = serializers.DecimalField(source='share_capital.face_value', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Shareholding
        fields = [
            'id', 'investor', 'holder_name', 'holder_name_display', 
            'share_capital', 'share_class', 'share_type', 
            'number_of_shares', 'face_value'
        ]

class CompanySerializer(serializers.ModelSerializer):
    share_classes = ShareCapitalSerializer(many=True, read_only=True)
    
    class Meta:
        model = InvesteeCompany
        fields = '__all__'

class ShareValuationSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='share_capital.class_name', read_only=True)
    valuation_date = serializers.DateField(source='valuation_report.valuation_date', read_only=True)
    
    class Meta:
        model = ShareValuation
        fields = ['id', 'share_capital', 'class_name', 'per_share_value', 'valuation_date']

class CompanyFinancialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyFinancials
        fields = '__all__'

class CorporateActionSerializer(serializers.ModelSerializer):
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)

    class Meta:
        model = CorporateAction
        fields = '__all__'