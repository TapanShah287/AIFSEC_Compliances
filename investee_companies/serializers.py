from decimal import Decimal
from rest_framework import serializers
from django.db import models
from .models import InvesteeCompany, ShareValuation, CompanyFinancials, CorporateAction, Shareholding

class CompanySerializer(serializers.ModelSerializer):
    class Meta: 
        model = InvesteeCompany
        fields = "__all__"

class ShareValuationSerializer(serializers.ModelSerializer):
    # Add fields for better display
    share_class = serializers.CharField(source='share_capital.get_share_type_display', read_only=True)
    valuation_date = serializers.DateField(source='valuation_report.valuation_date', read_only=True)
    class Meta: 
        model = ShareValuation
        fields = ['id', 'per_share_value', 'share_class', 'valuation_date']

class CompanyFinancialsSerializer(serializers.ModelSerializer):
    class Meta: 
        model = CompanyFinancials
        fields = "__all__"

class CorporateActionSerializer(serializers.ModelSerializer):
    # Add display field for action_type
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    class Meta: 
        model = CorporateAction
        # Be explicit about the fields you want
        fields = ['id', 'action_date', 'action_type', 'action_type_display', 'details', 'ratio']

class ShareholdingSerializer(serializers.ModelSerializer):
    display_holder = serializers.SerializerMethodField()
    share_type_display = serializers.SerializerMethodField()

    # computed fields we show in the portal
    face_value_per_share = serializers.SerializerMethodField()
    total_face_value = serializers.SerializerMethodField()
    percent_of_company = serializers.SerializerMethodField()

    class Meta:
        model = Shareholding
        fields = [
            "id",
            "investor", "holder_name",
            "display_holder",       
            "share_type", "share_type_display",
            "number_of_shares",
            "face_value_per_share", "total_face_value", "percent_of_company",
        ]

    def get_display_holder(self, obj):
        return obj.investor.name if getattr(obj, "investor_id", None) else (obj.holder_name or "Unspecified Holder")

    def get_share_type_display(self, obj):
        return obj.get_share_type_display() if hasattr(obj, "get_share_type_display") else getattr(obj, "share_type", "")

    def get_face_value_per_share(self, obj):
        return obj.face_value or Decimal("0.00")      # per-share face value

    def get_total_face_value(self, obj):
        return (obj.face_value or Decimal("0.00")) * (obj.number_of_shares or 0)

    def get_percent_of_company(self, obj):
        total = self.context.get("total_company_shares") or 0
        if not total:
            return 0.0
        return (obj.number_of_shares or 0) * 100.0 / float(total)
        

class CompanyShareholdingPatternSerializer(serializers.ModelSerializer):
    display_holder = serializers.SerializerMethodField()
    share_type_display = serializers.SerializerMethodField()
    percent_of_class = serializers.SerializerMethodField()

    class Meta:
        model = Shareholding
        fields = [
            "id",
            "display_holder",
            "share_type_display",
            "number_of_shares",
            "percent_of_class",
            "as_of_date",
        ]

    def get_display_holder(self, obj):
        if getattr(obj, "investor_id", None):
            return obj.investor.name
        return getattr(obj, "holder_name", "") or "Unspecified Holder"

    def get_share_type_display(self, obj):
        return getattr(obj, "get_share_type_display", lambda: getattr(obj, "share_type",""))()

    def get_percent_of_class(self, obj):
        total = self.context.get("total_shares_by_class", {}).get(obj.share_type, 0) or 0
        return (float(obj.number_of_shares or 0) * 100.0 / float(total or 1))