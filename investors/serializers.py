from rest_framework import serializers
from .models import Investor, KYCStatus, InvestorDocument

class KYCStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCStatus
        fields = ("kyc_status", "investor_type", "date_completed", "notes")

class InvestorSerializer(serializers.ModelSerializer):
    # Nested KYC (writeable)
    kyc = KYCStatusSerializer(source="kyc_status", required=False)

    class Meta:
        model = Investor
        fields = "__all__"  # includes 'kyc' via source

    def to_representation(self, instance):
        data = super().to_representation(instance)
        kyc_obj = getattr(instance, "kyc_status", None)
        # ✅ Consistent, computed fields for all views (list + detail)
        data["kyc_completed"] = bool(kyc_obj.kyc_status) if kyc_obj else False
        data["kyc_investor_type"] = kyc_obj.investor_type if kyc_obj else None
        data["kyc_date_completed"] = kyc_obj.date_completed if kyc_obj else None
        return data

    def update(self, instance, validated_data):
        # Handle nested kyc updates from detail page modal
        kyc_data = validated_data.pop("kyc_status", None)
        instance = super().update(instance, validated_data)
        if kyc_data is not None:
            kyc_obj, _ = KYCStatus.objects.get_or_create(investor=instance)
            for f, v in kyc_data.items():
                setattr(kyc_obj, f, v)
            if kyc_data.get("kyc_status") and not kyc_obj.date_completed:
                from datetime import date
                kyc_obj.date_completed = date.today()
            kyc_obj.save()
        return instance

class InvestorDocumentSerializer(serializers.ModelSerializer):
    doc_type_label = serializers.CharField(source="get_doc_type_display", read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = InvestorDocument
        fields = ("id", "investor", "doc_type", "doc_type_label", "file", "file_url",
                  "is_verified", "notes", "uploaded_at")
        read_only_fields = ("id", "uploaded_at", "file_url")

    def get_file_url(self, obj):
        try:
            return obj.file.url
        except Exception:
            return None

    def validate(self, attrs):
        investor = attrs.get("investor") or getattr(self.instance, "investor", None)
        doc_type = attrs.get("doc_type") or getattr(self.instance, "doc_type", None)
        if self.context.get("enforce_matrix"):
            # Optional: enforce required docs by investor_type
            kyc = getattr(investor, "kyc_status", None)
            inv_type = getattr(kyc, "investor_type", "IND")
            required = {"IND": {"ACCOUNT_FORM","PAN","AADHAR"}, "NON-IND": {"MOA","AOA","COI","ACCOUNT_FORM"}}[inv_type]
            if doc_type not in required:
                pass  # allow uploads of non-required types too
        return attrs